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


ROOT = Path(__file__).resolve().parents[1]
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


@dataclass(frozen=True)
class SupervisorShellAction:
    kind: str
    attempt_id: str = ""


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


def classify_supervised_shell_command(
    *,
    base: Path,
    command: str,
    open_attempt_ids: set[str],
    parent_slug: str,
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

    dispatch_tokens = tokens
    if tokens[0] in {"python", "python3"}:
        if len(tokens) < 2:
            return None
        dispatch_tokens = tokens[1:]
    if not _local_contract_path(base, dispatch_tokens[0], "utilities/dispatch-node.py"):
        return None
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
        )

    if expected_attempts is not None:
        missing = expected_attempts.difference(latest)
        if missing:
            raise JoinContractError("expected-attempt-missing")
    return sorted(latest.values(), key=lambda row: row.order)


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
            if row.status == "done":
                readiness, reason = "ready", "registry-closed"
            elif row.status in OPEN_STATES:
                observed = _liveness_state(row, command, runtime_env)
                if observed == "alive":
                    readiness, reason = "pending", "process-alive"
                    pending = True
                else:
                    readiness, reason = "ready", "terminal-observed"
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
