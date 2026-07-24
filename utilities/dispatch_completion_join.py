#!/usr/bin/env python3
"""Runtime-owned exact-batch join for registered headless children.

The joiner never returns child output.  It snapshots attempts bound to one
``parent_attempt_id``, waits until every attempt is either closed or requires
typed harvest, and emits one bounded JSON receipt for the session supervisor.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import time
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "utilities"))
from dispatch_contract import (  # noqa: E402
    observed_attempt_liveness,
)
from codex_dispatch_terminal import terminal_envelope_observed  # noqa: E402
OPEN_STATES = frozenset({"open", "running"})
SCHEMA_VERSION = 1
STATE_SCHEMA_VERSION = 1
MAX_STATE_BYTES = 16384


class JoinContractError(RuntimeError):
    """A registry or liveness boundary could not be proved."""


@dataclass(frozen=True)
class ChildRow:
    order: int
    status: str
    slug: str
    attempt_id: str
    raw: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class SupervisorShellAction:
    kind: str
    attempt_id: str = ""


@dataclass(frozen=True)
class SupervisedDispatchContext:
    """Immutable owner boundary used while a supervised batch is parked."""

    jobs: Path
    route_file: Path
    route_id: str
    parent_attempt_id: str
    route: dict[str, object]
    rows: tuple[ChildRow, ...]


def _safe_identity(value: str) -> bool:
    return (
        0 < len(value.encode("utf-8")) <= 256
        and "," not in value
        and not any(ord(char) < 32 or ord(char) == 127 for char in value)
    )


def write_supervisor_state(
    path: Path | None,
    parent_attempt_id: str,
    delivered_attempt_ids: set[str],
) -> None:
    """Atomically publish the bounded phase state consumed by native hooks."""

    if path is None:
        return
    if (
        not path.is_absolute()
        or not _safe_identity(parent_attempt_id)
        or any(not _safe_identity(attempt) for attempt in delivered_attempt_ids)
    ):
        raise JoinContractError("supervisor-state-contract-invalid")
    value = {
        "schema_version": STATE_SCHEMA_VERSION,
        "parent_attempt_id": parent_attempt_id,
        "delivered_attempt_ids": sorted(delivered_attempt_ids),
    }
    encoded = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    if len(encoded) > MAX_STATE_BYTES:
        raise JoinContractError("supervisor-state-oversized")
    temporary: Path | None = None
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "wb", dir=path.parent, prefix=".supervisor-state.", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o600)
        os.replace(temporary, path)
    except OSError as exc:
        if temporary is not None:
            try:
                temporary.unlink()
            except OSError:
                pass
        raise JoinContractError("supervisor-state-unwritable") from exc


def read_supervisor_state(
    path: Path | None,
    parent_attempt_id: str,
) -> set[str] | None:
    """Return delivered attempts, or None for missing/invalid state."""

    if path is None or not path.is_absolute() or not _safe_identity(parent_attempt_id):
        return None
    try:
        if path.stat().st_size > MAX_STATE_BYTES:
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError):
        return None
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != STATE_SCHEMA_VERSION
        or value.get("parent_attempt_id") != parent_attempt_id
    ):
        return None
    raw = value.get("delivered_attempt_ids")
    if not isinstance(raw, list) or len(raw) > 64:
        return None
    delivered: set[str] = set()
    for attempt in raw:
        if not isinstance(attempt, str) or not _safe_identity(attempt) or attempt in delivered:
            return None
        delivered.add(attempt)
    return delivered


def remove_supervisor_state(path: Path | None) -> None:
    if path is None:
        return
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError:
        # A unique attempt path cannot wake a later owner. Reconciliation may
        # remove an unreadable leftover after the process exits.
        pass


def _local_contract_path(base: Path, raw: str, relative: str) -> bool:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = base / candidate
    try:
        resolved = candidate.resolve()
    except OSError:
        return False
    roots = [ROOT]
    agent_home = os.environ.get("AGENT_HOME")
    if agent_home and (Path(agent_home) / "core" / "CORE.md").is_file():
        roots.append(Path(agent_home))
    resolved_base = base.resolve()
    for parent in (resolved_base, *resolved_base.parents):
        if (parent / "core" / "CORE.md").is_file():
            roots.append(parent)
            break
    return any(resolved == (root / relative).resolve() for root in roots)


def _parse_long_options(
    tokens: list[str],
    valued: set[str],
    switches: set[str],
) -> dict[str, list[str]] | None:
    parsed: dict[str, list[str]] = {}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in switches:
            parsed.setdefault(token, []).append("1")
            index += 1
            continue
        if token.startswith("--") and "=" in token:
            option, option_value = token.split("=", 1)
            if option not in valued or not option_value:
                return None
            parsed.setdefault(option, []).append(option_value)
            index += 1
            continue
        if token not in valued or index + 1 >= len(tokens):
            return None
        parsed.setdefault(token, []).append(tokens[index + 1])
        index += 2
    return parsed


def _resolved_from(base: Path, raw: str) -> Path | None:
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = base / candidate
    try:
        return candidate.resolve()
    except OSError:
        return None


def _selected_long_options(
    tokens: list[str], selected: set[str]
) -> dict[str, list[str]] | None:
    """Read selected opaque adapter options without accepting missing values."""

    values: dict[str, list[str]] = {}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        matched = next(
            (option for option in selected if token.startswith(option + "=")),
            None,
        )
        if matched is not None:
            value = token[len(matched) + 1 :]
            if not value:
                return None
            values.setdefault(matched, []).append(value)
            index += 1
            continue
        if token in selected:
            if index + 1 >= len(tokens) or tokens[index + 1].startswith("--"):
                return None
            values.setdefault(token, []).append(tokens[index + 1])
            index += 2
            continue
        index += 1
    return values


def _strict_supervisor_binding_requested(
    *,
    jobs: Path | None,
    parent_attempt_id: str,
    route_file: Path | None,
    route_id: str,
) -> bool:
    return bool(
        jobs
        or parent_attempt_id
        or route_file
        or route_id
        or os.environ.get("AGENT_DISPATCH_COMPLETION_MODE") == "supervised"
    )


def _supervised_dispatch_context(
    *,
    jobs: Path | None,
    parent_attempt_id: str,
    route_file: Path | None,
    route_id: str,
    open_attempt_ids: set[str],
) -> SupervisedDispatchContext:
    """Resolve the exact owner route/registry tuple or fail closed."""

    raw_jobs = jobs or (
        Path(os.environ["AGENT_DISPATCH_JOBS"])
        if os.environ.get("AGENT_DISPATCH_JOBS")
        else None
    )
    raw_route = route_file or (
        Path(os.environ["AGENT_ROUTE_FILE"])
        if os.environ.get("AGENT_ROUTE_FILE")
        else None
    )
    expected_parent = parent_attempt_id or os.environ.get(
        "AGENT_DISPATCH_ATTEMPT_ID", ""
    )
    expected_route_id = route_id or os.environ.get("AGENT_ROUTE_ID", "")
    if (
        raw_jobs is None
        or raw_route is None
        or not raw_jobs.is_absolute()
        or not raw_route.is_absolute()
        or not expected_parent
        or not expected_route_id
    ):
        raise JoinContractError("supervisor-dispatch-binding-missing")
    try:
        canonical_jobs = raw_jobs.resolve()
        canonical_route = raw_route.resolve()
        route = json.loads(canonical_route.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise JoinContractError("supervisor-dispatch-binding-unreadable") from exc
    if not isinstance(route, dict) or route.get("route_id") != expected_route_id:
        raise JoinContractError("supervisor-route-id-mismatch")
    rows = current_children(canonical_jobs, expected_parent)
    indexed = {row.attempt_id: row for row in rows}
    if not open_attempt_ids or not open_attempt_ids.issubset(indexed):
        raise JoinContractError("supervisor-open-attempt-binding-mismatch")
    return SupervisedDispatchContext(
        jobs=canonical_jobs,
        route_file=canonical_route,
        route_id=expected_route_id,
        parent_attempt_id=expected_parent,
        route=route,
        rows=tuple(rows),
    )


def _command_paths_match(
    *,
    base: Path,
    route_values: list[str],
    jobs_values: list[str],
    context: SupervisedDispatchContext,
) -> bool:
    return (
        len(route_values) == 1
        and len(jobs_values) == 1
        and _resolved_from(base, route_values[0]) == context.route_file
        and _resolved_from(base, jobs_values[0]) == context.jobs
    )


def _row_matches_current_route(
    row: ChildRow, context: SupervisedDispatchContext
) -> bool:
    route_path = _resolved_from(
        Path(row.metadata.get("worktree", "/")),
        row.metadata.get("route_file", ""),
    )
    return (
        row.metadata.get("parent_attempt_id") == context.parent_attempt_id
        and row.metadata.get("route_id") == context.route_id
        and route_path == context.route_file
    )


def _declared_replica_nodes(
    route: dict[str, object], group: str
) -> dict[str, dict[str, object]] | None:
    raw_nodes = route.get("nodes")
    if not isinstance(raw_nodes, list):
        return None
    nodes = {
        str(node.get("id")): node
        for node in raw_nodes
        if isinstance(node, dict) and node.get("replica_group") == group
    }
    if (
        len(nodes) != 2
        or "" in nodes
        or any(node.get("dispatch_depth") != 2 for node in nodes.values())
    ):
        return None
    return nodes


def _replica_row_matches(
    row: ChildRow,
    *,
    context: SupervisedDispatchContext,
    group: str,
    node_ids: set[str],
) -> bool:
    metadata = row.metadata
    node = metadata.get("route_node", "")
    return (
        _row_matches_current_route(row, context)
        and node in node_ids
        and metadata.get("replica_group") == group
        and metadata.get("reservation_kind") == "replica-batch"
        and metadata.get("batch_declared_size") == "2"
        and metadata.get("batch_group") == group
        and metadata.get("batch_route_id") == context.route_id
        and metadata.get("batch_parent_attempt_id") == context.parent_attempt_id
        and metadata.get("batch_attempt_id") == row.attempt_id
        and metadata.get("batch_route_node") == node
    )


def _bound_batch_start(
    *,
    base: Path,
    options: dict[str, list[str]],
    open_attempt_ids: set[str],
    context: SupervisedDispatchContext,
) -> bool:
    if not _command_paths_match(
        base=base,
        route_values=options.get("--route", []),
        jobs_values=options.get("--jobs", []),
        context=context,
    ):
        return False
    group = options["--replica-group"][0]
    declared = _declared_replica_nodes(context.route, group)
    if declared is None:
        return False
    node_ids = set(declared)
    pending_rows = [
        row for row in context.rows if row.attempt_id in open_attempt_ids
    ]
    if not pending_rows or any(
        not _replica_row_matches(
            row, context=context, group=group, node_ids=node_ids
        )
        for row in pending_rows
    ):
        return False

    route_group_rows = [
        row
        for row in context.rows
        if row.metadata.get("route_node") in node_ids
        or row.metadata.get("replica_group") == group
        or row.metadata.get("batch_group") == group
    ]
    exact_rows = [
        row
        for row in route_group_rows
        if _replica_row_matches(
            row, context=context, group=group, node_ids=node_ids
        )
    ]
    # The only parked recovery admission is one exact manifest-bound leg. A
    # second exact row means the whole two-way group has already been claimed;
    # zero or malformed rows cannot authorize a fresh batch from this phase.
    return (
        len(route_group_rows) == 1
        and len(exact_rows) == 1
        and len({row.metadata.get("route_node") for row in exact_rows}) == 1
    )


def _bound_dispatch_node_start(
    *,
    base: Path,
    options: dict[str, list[str]],
    trailing: list[str],
    open_attempt_ids: set[str],
    context: SupervisedDispatchContext,
) -> bool:
    selected = _selected_long_options(
        trailing,
        {
            "--jobs",
            "--parent-attempt-id",
            "--route-file",
            "--route-id",
            "--route-node",
            "--dispatch-depth",
            "--parent",
        },
    )
    if selected is None or any(
        option in selected
        for option in {
            "--route-file",
            "--route-id",
            "--route-node",
            "--dispatch-depth",
            "--parent",
        }
    ):
        return False
    if not _command_paths_match(
        base=base,
        route_values=options.get("--route", []),
        jobs_values=selected.get("--jobs", []),
        context=context,
    ):
        return False
    explicit_parent = selected.get("--parent-attempt-id", [])
    if len(explicit_parent) > 1 or (
        explicit_parent and explicit_parent != [context.parent_attempt_id]
    ):
        return False
    raw_nodes = context.route.get("nodes")
    if not isinstance(raw_nodes, list):
        return False
    node_id = options["--node"][0]
    matches = [
        node
        for node in raw_nodes
        if isinstance(node, dict) and node.get("id") == node_id
    ]
    if (
        len(matches) != 1
        or matches[0].get("dispatch_depth") != 2
        or matches[0].get("replica_group")
    ):
        return False
    pending_rows = [
        row for row in context.rows if row.attempt_id in open_attempt_ids
    ]
    if not pending_rows or any(
        not _row_matches_current_route(row, context) for row in pending_rows
    ):
        return False
    return not any(row.metadata.get("route_node") == node_id for row in context.rows)


def classify_supervised_shell_command(
    *,
    base: Path,
    command: str,
    open_attempt_ids: set[str],
    parent_slug: str,
    jobs: Path | None = None,
    parent_attempt_id: str = "",
    route_file: Path | None = None,
    route_id: str = "",
) -> SupervisorShellAction | None:
    """Recognize only exact harvest or one additional parent-bound dispatch."""

    if not command or not open_attempt_ids or re_search_shell_composition(command):
        return None
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return None
    if not tokens:
        return None

    if (
        len(tokens) >= 2
        and _local_contract_path(base, tokens[0], "adapters/codex/bin/preflight.sh")
        and tokens[1] == "harvest"
    ):
        options = _parse_long_options(
            tokens[2:],
            {"--attempt-id", "--status", "--completion"},
            {"--mark-done", "--keep-home", "--failure-detail"},
        )
        if options is None or len(options.get("--attempt-id", [])) != 1:
            return None
        if any(len(values) != 1 for values in options.values()):
            return None
        attempt = options["--attempt-id"][0]
        if (
            attempt not in open_attempt_ids
            or options.get("--status", ["open"])[0] != "open"
        ):
            return None
        return SupervisorShellAction("harvest", attempt)

    strict_binding = _strict_supervisor_binding_requested(
        jobs=jobs,
        parent_attempt_id=parent_attempt_id,
        route_file=route_file,
        route_id=route_id,
    )
    context: SupervisedDispatchContext | None = None
    if strict_binding:
        try:
            context = _supervised_dispatch_context(
                jobs=jobs,
                parent_attempt_id=parent_attempt_id,
                route_file=route_file,
                route_id=route_id,
                open_attempt_ids=open_attempt_ids,
            )
        except JoinContractError:
            return None

    dispatch_tokens = tokens
    if tokens[0] in {"python", "python3"}:
        if len(tokens) < 2:
            return None
        dispatch_tokens = tokens[1:]
    is_batch = False
    if _local_contract_path(base, dispatch_tokens[0], "adapters/codex/bin/preflight.sh"):
        if len(dispatch_tokens) < 2 or dispatch_tokens[1] != "dispatch-batch":
            return None
        dispatch_tokens = [str(ROOT / "utilities" / "dispatch-batch.py"), *dispatch_tokens[2:]]
        is_batch = True
    elif _local_contract_path(base, dispatch_tokens[0], "utilities/dispatch-batch.py"):
        is_batch = True
    elif not _local_contract_path(base, dispatch_tokens[0], "utilities/dispatch-node.py"):
        return None

    if is_batch:
        options = _parse_long_options(
            dispatch_tokens[1:],
            {
                "--route",
                "--replica-group",
                "--action",
                "--slug-prefix",
                "--parent",
                "--qa",
                "--jobs",
                "--prompt-text",
            },
            {"--allow-degraded-independence"},
        )
        required = {
            "--route",
            "--replica-group",
            "--action",
            "--slug-prefix",
            "--parent",
        }
        if (
            options is None
            or not parent_slug
            or any(len(values) != 1 for values in options.values())
            or not required.issubset(options)
            or options["--action"] != ["start"]
            or options["--parent"] != [parent_slug]
        ):
            return None
        if context is not None and not _bound_batch_start(
            base=base,
            options=options,
            open_attempt_ids=open_attempt_ids,
            context=context,
        ):
            return None
        return SupervisorShellAction("dispatch-batch")

    try:
        separator = dispatch_tokens.index("--")
    except ValueError:
        separator = len(dispatch_tokens)
    options = _parse_long_options(
        dispatch_tokens[1:separator],
        {
            "--route",
            "--node",
            "--adapter",
            "--action",
            "--slug",
            "--qa",
            "--parent",
            "--prompt-text",
        },
        set(),
    )
    required = {"--route", "--node", "--adapter", "--action", "--slug", "--parent"}
    if (
        options is None
        or not parent_slug
        or any(len(values) != 1 for values in options.values())
        or not required.issubset(options)
        or options["--action"] != ["start"]
        or options["--parent"] != [parent_slug]
        or options["--adapter"][0] not in {"claude", "codex", "opencode"}
    ):
        return None
    if context is not None and not _bound_dispatch_node_start(
        base=base,
        options=options,
        trailing=dispatch_tokens[separator + 1 :] if separator < len(dispatch_tokens) else [],
        open_attempt_ids=open_attempt_ids,
        context=context,
    ):
        return None
    return SupervisorShellAction("dispatch")


def re_search_shell_composition(command: str) -> bool:
    return (
        any(char in command for char in "\n\r;&|<>")
        or chr(96) in command
        or "$(" in command
    )


def _metadata(raw: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for part in raw.split(","):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        values[key] = value
    return values


def current_children(
    jobs: Path,
    parent_attempt_id: str,
    expected_attempts: set[str] | None = None,
) -> list[ChildRow]:
    """Return latest exact-attempt rows owned by ``parent_attempt_id``.

    Foreign parents, legacy slug-only rows, and same-slug retries are ignored.
    A matching v2 row that lacks its attempt identity fails closed.
    """

    if not parent_attempt_id:
        raise JoinContractError("parent-attempt-id-missing")
    try:
        lines = jobs.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        lines = []
    except OSError as exc:
        raise JoinContractError("registry-unreadable") from exc

    latest: dict[str, ChildRow] = {}
    for order, line in enumerate(lines):
        fields = line.split("\t")
        if len(fields) != 6:
            continue
        meta = _metadata(fields[5])
        if meta.get("parent_attempt_id") != parent_attempt_id:
            continue
        if meta.get("attempt_schema_version") != "2":
            raise JoinContractError("owned-row-schema-invalid")
        attempt_id = meta.get("attempt_id", "")
        if not attempt_id:
            raise JoinContractError("owned-row-attempt-id-missing")
        if expected_attempts is not None and attempt_id not in expected_attempts:
            continue
        latest[attempt_id] = ChildRow(
            order=order,
            status=fields[1],
            slug=fields[4],
            attempt_id=attempt_id,
            raw=line,
            metadata=meta,
        )

    if expected_attempts is not None:
        missing = expected_attempts.difference(latest)
        if missing:
            raise JoinContractError("expected-attempt-missing")
    return sorted(latest.values(), key=lambda row: row.order)


def pending_attempt_ids(rows: list[ChildRow]) -> set[str]:
    """Return children that are open or terminal-but-not-yet-quiescent."""

    pending: set[str] = set()
    for row in rows:
        observed = observed_attempt_liveness(
            row.status,
            row.metadata,
            terminal_envelope=terminal_envelope_observed(
                row.metadata.get("log_file")
            ),
        )
        if observed.state in {"alive", "unverifiable"}:
            pending.add(row.attempt_id)
    return pending


def _liveness_state(row: ChildRow, command: list[str], env: dict[str, str]) -> str:
    """Return ``alive`` or ``terminal`` without exposing liveness output."""

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        fields = row.raw.split("\t")
        if len(fields) == 6 and fields[1] == "running":
            fields[1] = "open"
        handle.write("\t".join(fields) + "\n")
        registry = Path(handle.name)
    try:
        result = subprocess.run(
            [*command, str(registry)],
            env={**env, "AGENT_DISPATCH_JOBS": str(registry)},
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise JoinContractError("liveness-contract-unavailable") from exc
    finally:
        try:
            registry.unlink()
        except OSError:
            pass
    if result.returncode == 0:
        return "alive"
    if result.returncode == 3:
        return "terminal"
    raise JoinContractError("liveness-contract-failed")


def join_batch(
    *,
    jobs: Path,
    parent_attempt_id: str,
    expected_attempts: set[str] | None = None,
    interval: float = 2.0,
    timeout: float = 3600.0,
    liveness_command: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, object]:
    """Join one immutable child batch and return a bounded typed receipt."""

    command = liveness_command or [str(ROOT / "utilities" / "dispatch-liveness.sh")]
    runtime_env = dict(os.environ if env is None else env)
    interval = max(0.05, interval)
    timeout = max(0.0, timeout)
    initial = current_children(jobs, parent_attempt_id, expected_attempts)
    if not initial:
        return {
            "schema_version": SCHEMA_VERSION,
            "state": "no-children",
            "parent_attempt_id": parent_attempt_id,
            "children": [],
        }
    snapshot = {row.attempt_id for row in initial}
    started = time.monotonic()

    while True:
        rows = current_children(jobs, parent_attempt_id, snapshot)
        children: list[dict[str, str]] = []
        pending = False
        for row in rows:
            observed = observed_attempt_liveness(
                row.status,
                row.metadata,
                terminal_envelope=terminal_envelope_observed(
                    row.metadata.get("log_file")
                ),
            )
            if row.status == "done":
                if observed.state == "terminal":
                    readiness, reason = "ready", "registry-closed"
                else:
                    readiness = "pending"
                    reason = (
                        "process-alive"
                        if observed.state == "alive"
                        else "process-unverifiable"
                    )
                    pending = True
            elif row.status in OPEN_STATES:
                if observed.state == "alive":
                    readiness, reason = "pending", "process-alive"
                    pending = True
                elif observed.state == "reconcile-needed":
                    readiness, reason = "ready", "terminal-observed"
                else:
                    _liveness_state(row, command, runtime_env)
                    readiness = "pending"
                    reason = "process-unverifiable"
                    pending = True
            else:
                raise JoinContractError("owned-row-status-invalid")
            children.append(
                {
                    "attempt_id": row.attempt_id,
                    "slug": row.slug,
                    "status": row.status,
                    "readiness": readiness,
                    "reason": reason,
                }
            )
        if not pending:
            return {
                "schema_version": SCHEMA_VERSION,
                "state": "ready",
                "parent_attempt_id": parent_attempt_id,
                "children": children,
            }
        if time.monotonic() - started >= timeout:
            return {
                "schema_version": SCHEMA_VERSION,
                "state": "timeout",
                "parent_attempt_id": parent_attempt_id,
                "children": children,
            }
        time.sleep(interval)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--jobs", default=os.environ.get("AGENT_DISPATCH_JOBS"))
    value.add_argument(
        "--parent-attempt-id",
        default=os.environ.get("AGENT_DISPATCH_ATTEMPT_ID"),
    )
    value.add_argument("--attempt-id", action="append", default=[])
    value.add_argument("--interval", type=float, default=2.0)
    value.add_argument("--timeout", type=float, default=3600.0)
    value.add_argument("--liveness-command")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if not args.jobs:
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "state": "contract-error",
            "parent_attempt_id": args.parent_attempt_id or "-",
            "reason": "jobs-path-missing",
            "children": [],
        }
        print(json.dumps(receipt, separators=(",", ":"), sort_keys=True))
        return 69
    liveness = [args.liveness_command] if args.liveness_command else None
    try:
        receipt = join_batch(
            jobs=Path(args.jobs),
            parent_attempt_id=args.parent_attempt_id or "",
            expected_attempts=set(args.attempt_id) if args.attempt_id else None,
            interval=args.interval,
            timeout=args.timeout,
            liveness_command=liveness,
        )
    except JoinContractError as exc:
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "state": "contract-error",
            "parent_attempt_id": args.parent_attempt_id or "-",
            "reason": str(exc),
            "children": [],
        }
    print(json.dumps(receipt, separators=(",", ":"), sort_keys=True))
    return {"ready": 0, "no-children": 2, "timeout": 3}.get(str(receipt["state"]), 69)


if __name__ == "__main__":
    raise SystemExit(main())
