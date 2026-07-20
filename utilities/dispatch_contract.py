#!/usr/bin/env python3
"""Portable SD-48/49 primitives used by headless dispatch adapters."""

from __future__ import annotations

from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid
from typing import Callable


ELIGIBILITY = {"supported", "unsupported", "unknown"}
LAUNCH_AUTHORITIES = {"conductor", "ancestor-broker"}
ATTEMPT_SCHEMA_VERSION = 2
WRAPPER_TRANSPORTS = {"headless", "interactive"}
CANONICAL_PARENT_TRANSPORTS = WRAPPER_TRANSPORTS
EXECUTION_SURFACES = {
    "registered-headless",
    "codex-native-subagent",
    "claude-subagent",
    "claude-agent-team-teammate",
    "inline",
}
FALLBACK_HOPS = {
    "same-harness-headless",
    "cross-harness-headless",
    "native-subagent",
    "inline",
}
ATTEMPT_MUTABLE_METADATA = {
    "launch_claimed",
    "pid",
    "pid_start",
    "pid_scope",
    "updated_at",
    "note",
    "completion_marker",
    "completion_marker_history",
    "watchdog",
    "heartbeat",
}
_MODULE_ROOT = Path(__file__).resolve().parents[1]
_CAPACITY_TERMINAL_RE = re.compile(
    r"(?:error\s*[:\-]\s*)?(?:selected\s+)?model(?:\s+[A-Za-z0-9._:/-]+)?\s+"
    r"(?:is\s+)?at\s+capacity[.!]?",
    re.I,
)


def anchored_capacity_failure(text: str) -> bool:
    """Accept only a terminal capacity error, never prose discussing one.

    Adapters may emit either a plain CLI line or a JSON event.  The bounded
    last-three-line rule is shared by the early wrapper watch and the SD-58
    foreground watchdog so delayed failures receive the same classification.
    """

    def terminal(value: str) -> bool:
        return bool(_CAPACITY_TERMINAL_RE.fullmatch(value.strip()))

    lines = [line.strip() for line in text.splitlines() if line.strip()][-3:]
    for line in lines:
        if len(line) > 200:
            continue
        if terminal(line):
            return True
        try:
            payload = json.loads(line)
        except (TypeError, ValueError):
            continue
        if not isinstance(payload, dict):
            continue
        pending = [payload]
        while pending:
            item = pending.pop()
            for key, value in item.items():
                if isinstance(value, dict):
                    pending.append(value)
                elif key in {"message", "error", "detail"} and isinstance(value, str) and terminal(value):
                    return True
    return False


def resolve_agent_home() -> Path:
    """Validated AGENT_HOME resolution shared by writers and readers of
    dispatch state that must agree on one root (jobs.log, completion markers).

    Mirrors adapters/claude/bin/dispatch-headless.py:546-558's preference
    order. A naive `os.environ.get("AGENT_HOME", ROOT)` falls back to the
    caller's own worktree when AGENT_HOME is unset, which previously split
    the global registry between the wrapper (writer, worktree-relative) and
    the liveness/Stop readers (agent-home-relative) -- SD-14b(2). Every
    consumer that must land in the SAME directory as another process has to
    go through this one function, not re-derive its own fallback.
    """

    def _valid(candidate: str | None) -> bool:
        return bool(candidate) and (Path(candidate) / "core" / "CORE.md").is_file()

    for candidate in (
        os.environ.get("AGENT_HOME"),
        os.environ.get("CLAUDE_HOME"),
        str(Path.home() / "agent_setting"),
        str(Path.home() / ".claude"),
    ):
        if _valid(candidate):
            return Path(candidate)
    return _MODULE_ROOT


class DispatchContractError(ValueError):
    """Structured dispatch-contract failure."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(detail or reason)
        self.reason = reason
        self.detail = detail or reason


@dataclass(frozen=True)
class RegistrySelection:
    path: Path
    source: str
    inherited: bool


@dataclass(frozen=True)
class BrokerSelection:
    root: Path
    instance_id: str
    pid: int
    start_ticks: str
    jobs: Path


def parse_registry_metadata(pipe: str) -> dict[str, str]:
    """Parse the stable six-column registry's comma-delimited metadata."""

    return dict(part.split("=", 1) for part in pipe.split(",") if "=" in part)


def _registered_worker(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if str(value).lower() in {"1", "true"}:
        return True
    if str(value).lower() in {"0", "false"}:
        return False
    raise DispatchContractError("invalid-registered-worker", str(value))


def validate_attempt_metadata(
    metadata: dict[str, object],
    *,
    registered_headless_wrapper: bool = False,
) -> None:
    """Validate independent v20 attempt axes before claim, spawn, or completion."""

    try:
        schema_version = int(metadata.get("attempt_schema_version", 0))
        dispatch_depth = int(metadata.get("dispatch_depth", -1))
    except (TypeError, ValueError) as exc:
        raise DispatchContractError("invalid-attempt-metadata", str(exc)) from exc
    if schema_version != ATTEMPT_SCHEMA_VERSION:
        raise DispatchContractError(
            "legacy-attempt-row-read-only",
            f"attempt schema v{schema_version or 1} cannot be claimed or completed",
        )
    if any(key in metadata for key in ("depth", "owner_depth", "max_depth")):
        raise DispatchContractError(
            "bare-dispatch-depth-field",
            "current attempt metadata accepts dispatch_depth only",
        )
    if dispatch_depth not in {0, 1, 2}:
        raise DispatchContractError("invalid-dispatch-depth", str(dispatch_depth))

    transport = str(metadata.get("transport", ""))
    surface = str(metadata.get("execution_surface", ""))
    fallback_hop = str(metadata.get("fallback_hop", ""))
    registered = _registered_worker(metadata.get("registered_worker"))
    if transport not in WRAPPER_TRANSPORTS:
        raise DispatchContractError("invalid-transport", transport)
    if surface not in EXECUTION_SURFACES:
        raise DispatchContractError("invalid-execution-surface", surface)
    if fallback_hop not in FALLBACK_HOPS and not (
        dispatch_depth == 0 and fallback_hop == ""
    ):
        raise DispatchContractError("invalid-fallback-hop", fallback_hop)
    if dispatch_depth == 0 and (
        surface != "inline"
        or registered
        or transport != "interactive"
        or fallback_hop
    ):
        raise DispatchContractError("direct-attempt-axes-mismatch", surface)
    if surface == "claude-agent-team-teammate":
        raise DispatchContractError(
            "teammate-not-dispatch-attempt",
            "Claude agent-team teammates carry peer-session lifecycle, not dispatch depth",
        )
    if registered != (surface == "registered-headless"):
        raise DispatchContractError("attempt-registration-surface-mismatch", surface)
    if registered and transport != "headless":
        raise DispatchContractError("registered-worker-transport-mismatch", transport)
    if surface == "registered-headless" and fallback_hop not in {
        "same-harness-headless",
        "cross-harness-headless",
    }:
        raise DispatchContractError("registered-worker-fallback-mismatch", fallback_hop)
    native_surfaces = {"codex-native-subagent", "claude-subagent"}
    if surface in native_surfaces and (
        fallback_hop != "native-subagent" or transport != "headless"
    ):
        raise DispatchContractError(
            "native-surface-axes-mismatch",
            f"transport={transport},fallback_hop={fallback_hop}",
        )
    if surface == "inline" and dispatch_depth > 0 and fallback_hop != "inline":
        raise DispatchContractError("inline-surface-fallback-mismatch", fallback_hop)
    if registered_headless_wrapper and (surface != "registered-headless" or not registered):
        raise DispatchContractError("headless-wrapper-surface-mismatch", surface)


def headless_attempt_policy(
    *,
    route_file: str | None,
    route_node: str | None,
    intensity: str,
    harness: str,
    dispatch_depth: int,
    parent_slug: str | None,
    execution_surface: str,
    registered_worker: bool,
    fallback_hop: str | None,
    fallback_ordinal: int,
    parent_harness: str,
    parent_transport: str,
    parent_sandbox: str,
    launch_authority: str,
) -> dict[str, object]:
    """Bind one registered wrapper invocation to its immutable route axes."""

    effective_hop = fallback_hop or {
        1: "same-harness-headless",
        2: "cross-harness-headless",
    }.get(fallback_ordinal, "same-harness-headless")
    metadata: dict[str, object] = {
        "attempt_schema_version": ATTEMPT_SCHEMA_VERSION,
        "dispatch_depth": dispatch_depth,
        "transport": "headless",
        "execution_surface": execution_surface,
        "registered_worker": registered_worker,
        "fallback_hop": effective_hop,
    }
    validate_attempt_metadata(metadata, registered_headless_wrapper=True)
    policy: dict[str, object] = {
        "fallback_hop": effective_hop,
        "fallback_ordinal": fallback_ordinal,
        "quick": False,
        "terminal_attempt_limit": None,
    }

    if not route_file:
        if intensity == "direct":
            raise DispatchContractError("direct-main-inline-only", "direct routes do not register workers")
        if intensity == "quick":
            raise DispatchContractError(
                "quick-headless-unavailable",
                "quick dispatch requires a current immutable route",
            )
        return policy
    try:
        route = json.loads(Path(route_file).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DispatchContractError("route-record-unreadable", str(exc)) from exc
    if route.get("schema_version") != 2:
        raise DispatchContractError(
            "legacy-route-read-only",
            f"route schema v{route.get('schema_version', 1)} cannot register or start workers",
        )
    node = next((row for row in route.get("nodes", []) if row.get("id") == route_node), None)
    if node is None:
        raise DispatchContractError("route-node-unknown", str(route_node))
    if route.get("effective_intensity") == "direct":
        raise DispatchContractError("direct-main-inline-only", "direct routes do not register workers")
    if int(node.get("dispatch_depth", -1)) != dispatch_depth:
        raise DispatchContractError("route-dispatch-depth-mismatch", str(node.get("dispatch_depth")))

    if route.get("effective_intensity") == "quick":
        if dispatch_depth != 1 or parent_slug or route_node != "one-shot":
            raise DispatchContractError("quick-route-shape-invalid", str(route_node))
        if node.get("execution_surface") != "registered-headless" or node.get("registered_worker") is not True:
            raise DispatchContractError("quick-route-surface-invalid", str(node.get("execution_surface")))
        if effective_hop != "same-harness-headless":
            raise DispatchContractError("quick-fallback-forbidden", effective_hop)
        candidates = [
            row
            for row in route.get("registered_headless_candidates") or []
            if row.get("status") == "supported"
            and row.get("harness") == harness
            and row.get("transport") == "headless"
            and row.get("surface") == "registered-headless"
        ]
        if not candidates:
            raise DispatchContractError("quick-headless-unavailable", harness)
        policy.update(quick=True, terminal_attempt_limit=len(candidates))
        return policy

    chain = node.get("fallback_hops")
    if not isinstance(chain, list):
        raise DispatchContractError("route-fallback-hops-missing", str(route_node))
    expected_candidate = {
        "parent_harness": parent_harness,
        "parent_transport": parent_transport,
        "parent_sandbox": parent_sandbox,
        "child_harness": harness,
        "launch_authority": launch_authority,
        "status": "supported",
    }

    def candidate_matches(candidate: object) -> bool:
        return isinstance(candidate, dict) and all(
            candidate.get(key) == value for key, value in expected_candidate.items()
        )

    selected = None
    if fallback_ordinal == 0:
        selected = next(
            (
                row
                for row in chain
                if any(candidate_matches(candidate) for candidate in row.get("candidates", []))
            ),
            None,
        )
        if selected is not None:
            fallback_ordinal = int(selected["ordinal"])
            effective_hop = str(selected["fallback_hop"])
            policy.update(fallback_ordinal=fallback_ordinal, fallback_hop=effective_hop)
    else:
        selected = next(
            (row for row in chain if int(row.get("ordinal", 0)) == fallback_ordinal),
            None,
        )
    if selected is None or selected.get("fallback_hop") != effective_hop:
        raise DispatchContractError("route-fallback-hop-mismatch", effective_hop)
    if not any(candidate_matches(candidate) for candidate in selected.get("candidates", [])):
        raise DispatchContractError(
            "route-fallback-candidate-mismatch",
            json.dumps(expected_candidate, sort_keys=True),
        )
    if effective_hop not in {"same-harness-headless", "cross-harness-headless"}:
        raise DispatchContractError("headless-wrapper-fallback-mismatch", effective_hop)
    return policy


def _absolute(path: str | Path, field: str) -> Path:
    value = Path(path).expanduser()
    if not value.is_absolute():
        raise DispatchContractError(f"{field}-must-be-absolute", str(value))
    return value.resolve(strict=False)


def resolve_global_registry(
    agent_home: Path,
    explicit_jobs: str | None,
    dispatch_depth: int,
    action: str,
    environ: dict[str, str] | os._Environ[str] | None = None,
) -> RegistrySelection:
    """Resolve the one authoritative registry and reject nested overrides.

    Dispatch-depth-0/root dispatch may select an explicit registry once. The wrapper then
    exports it through AGENT_DISPATCH_JOBS. A real nested start must inherit that
    path; argv may repeat it, but cannot replace it.
    """

    env = os.environ if environ is None else environ
    inherited_raw = env.get("AGENT_DISPATCH_JOBS")
    explicit = _absolute(explicit_jobs, "jobs") if explicit_jobs else None
    inherited = _absolute(inherited_raw, "agent-dispatch-jobs") if inherited_raw else None

    if dispatch_depth > 1 and inherited and explicit and inherited != explicit:
        raise DispatchContractError(
            "noncanonical-nested-jobs",
            f"explicit={explicit} inherited={inherited}",
        )

    nested_start = dispatch_depth > 1 and action == "start"
    if nested_start and inherited is None:
        raise DispatchContractError(
            "global-registry-unset",
            "nested --start requires inherited AGENT_DISPATCH_JOBS",
        )

    # A dispatch-depth-1 invocation is the root dispatch boundary. It may deliberately
    # choose a new canonical registry even when the invoking shell carries an
    # unrelated ambient value.  Only nested invocations must inherit exactly.
    if dispatch_depth <= 1 and explicit:
        return RegistrySelection(explicit, "root-explicit", False)
    if inherited:
        return RegistrySelection(inherited, "inherited-env", True)
    if explicit:
        return RegistrySelection(explicit, "root-explicit", False)
    return RegistrySelection((agent_home / ".dispatch" / "jobs.log").resolve(), "agent-home", False)


def ensure_global_registry_writable(path: Path) -> None:
    """Open the global registry and its lock before any child spawn."""

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = Path(f"{path}.lock")
        with lock_path.open("a", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            with path.open("a", encoding="utf-8") as registry:
                registry.flush()
                os.fsync(registry.fileno())
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    except OSError as exc:
        raise DispatchContractError("global-registry-unwritable", f"{path}: {exc}") from exc


def ensure_launch_broker(
    agent_home: Path,
    jobs: Path,
    *,
    dispatch_depth: int,
    action: str,
    intensity: str,
    environ: dict[str, str] | os._Environ[str] | None = None,
) -> BrokerSelection | None:
    """Reject production launch-broker creation after dispatch contract v3.

    The callable remains for one compatibility release so an overlooked caller
    fails closed with a stable reason instead of silently resurrecting the
    resident broker. Diagnostic ``status``/``stop`` remain in dispatch-broker.py.
    """

    if (
        action != "start"
        or dispatch_depth != 1
        or intensity not in {"standard", "strong", "thorough", "adversarial"}
    ):
        return None
    raise DispatchContractError(
        "launch-broker-retired",
        "dispatch contract v3 launches checked headless adapters directly from the conductor",
    )


def validate_nested_eligibility(
    *,
    dispatch_depth: int,
    action: str,
    parent_harness: str,
    parent_transport: str,
    parent_sandbox: str,
    child_harness: str,
    launch_authority: str,
    status: str,
    source: str,
) -> None:
    if dispatch_depth < 2:
        return
    if launch_authority not in LAUNCH_AUTHORITIES:
        raise DispatchContractError("invalid-launch-authority", launch_authority)
    if status not in ELIGIBILITY:
        raise DispatchContractError("invalid-nested-eligibility", status)
    if parent_transport not in CANONICAL_PARENT_TRANSPORTS and parent_transport != "unknown":
        raise DispatchContractError(
            "invalid-parent-transport",
            f"{parent_transport}; expected one of {sorted(CANONICAL_PARENT_TRANSPORTS)}",
        )
    missing = [
        name
        for name, value in (
            ("parent_harness", parent_harness),
            ("parent_transport", parent_transport),
            ("parent_sandbox", parent_sandbox),
            ("child_harness", child_harness),
            ("eligibility_source", source),
        )
        if not value or value == "unknown"
    ]
    if action == "start" and missing:
        raise DispatchContractError("nested-eligibility-evidence-missing", ",".join(missing))
    if action == "start" and status != "supported":
        raise DispatchContractError(f"nested-child-spawn-{status}", source or "no checked evidence")


def completion_marker_gate(
    route_file: str | None,
    route_node: str | None,
    action: str,
    agent_home: Path,
) -> None:
    """SD-56 decision gate: a record-bound ``--start`` must not spawn a node
    whose ``depends_on`` predecessors have no completion marker.

    ``agent_home`` is an explicit argument, not re-read from the environment,
    so the writer (capability-route.py complete) and every reader (this gate,
    called once per wrapper) are structurally forced to agree on one root.
    """

    if not route_file:
        return
    route = json.loads(Path(route_file).read_text(encoding="utf-8"))
    contract_version = route.get("dispatch_contract_version") or route.get("broker_contract_version")
    contract_version = contract_version or 1
    if action in {"register", "start"} and contract_version != 3:
        raise DispatchContractError(
            "legacy-broker-route-read-only",
            f"dispatch contract v{contract_version} cannot register or start workers",
        )
    if action != "start" or contract_version != 3:
        return
    node = next((row for row in route.get("nodes", []) if row.get("id") == route_node), None)
    if node is None:
        return
    missing = []
    for dep in node.get("depends_on", []):
        marker_path = Path(agent_home) / ".dispatch" / "completion" / route["route_id"] / f"{dep}.json"
        if not marker_path.is_file():
            missing.append(dep)
            continue
        try:
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            missing.append(dep)
            continue
        dep_node = next((row for row in route.get("nodes", []) if row.get("id") == dep), None)
        if dep_node is None or not completion_marker_is_current(route, dep_node, marker_path, marker):
            missing.append(dep)
    if missing:
        raise DispatchContractError("completion-marker-missing", ",".join(missing))


def completion_marker_is_current(
    route: dict[str, object],
    node: dict[str, object],
    marker_path: Path,
    marker: dict[str, object] | None = None,
) -> bool:
    """Prove one schema-v2 marker and its immutable history/attempt linkage."""

    try:
        marker = marker or json.loads(marker_path.read_text(encoding="utf-8"))
        if not isinstance(marker, dict) or marker.get("schema_version") != 2:
            return False
        node_id = str(node["id"])
        sequence = int(marker.get("sequence", 0))
        if sequence < 1:
            return False
        expected = {
            "route_id": route.get("route_id"),
            "route_hash": route.get("route_hash"),
            "registry_digest": route.get("registry_digest"),
            "node_id": node_id,
            "completion_gate": node.get("completion_gate"),
        }
        if any(marker.get(key) != value for key, value in expected.items()):
            return False
        evidence_record = marker.get("evidence")
        if not isinstance(evidence_record, dict):
            return False
        evidence = Path(str(evidence_record.get("path", "")))
        if not evidence.is_absolute() or not evidence.is_file():
            return False
        if hashlib.sha256(evidence.read_bytes()).hexdigest() != evidence_record.get("sha256"):
            return False
        history_path = marker_path.parent / f"{node_id}.{sequence}.json"
        history = json.loads(history_path.read_text(encoding="utf-8"))
        if history != marker:
            return False

        if node.get("kind") == "resource-runner":
            return (
                marker.get("attempt_id") is None
                and marker.get("dispatch_depth") is None
                and marker.get("transport") is None
                and marker.get("execution_surface") is None
                and marker.get("registered_worker") is False
                and marker.get("fallback_hop") is None
            )

        attempt_id = marker.get("attempt_id")
        if not isinstance(attempt_id, str) or not attempt_id:
            return False
        axes = {
            "attempt_schema_version": ATTEMPT_SCHEMA_VERSION,
            "dispatch_depth": marker.get("dispatch_depth"),
            "transport": marker.get("transport"),
            "execution_surface": marker.get("execution_surface"),
            "registered_worker": marker.get("registered_worker"),
            "fallback_hop": marker.get("fallback_hop") or "",
        }
        validate_attempt_metadata(axes)
        if int(axes["dispatch_depth"]) != node.get("dispatch_depth"):
            return False
        safe_attempt = "".join(
            character if character.isalnum() or character in "._-" else "_"
            for character in attempt_id
        )
        link_path = marker_path.parent / f"{node_id}.{safe_attempt}.attempt.json"
        link = json.loads(link_path.read_text(encoding="utf-8"))
        link_expected = {
            "schema_version": 2,
            "route_id": route.get("route_id"),
            "node_id": node_id,
            "attempt_id": attempt_id,
            "dispatch_depth": marker.get("dispatch_depth"),
            "transport": marker.get("transport"),
            "execution_surface": marker.get("execution_surface"),
            "registered_worker": marker.get("registered_worker"),
            "fallback_hop": marker.get("fallback_hop"),
            "evidence_sha256": evidence_record.get("sha256"),
            "completion_marker": str(marker_path),
            "completion_marker_history": str(history_path),
        }
        return all(link.get(key) == value for key, value in link_expected.items())
    except (DispatchContractError, KeyError, OSError, TypeError, ValueError):
        return False


def new_attempt_id(value: str | None = None) -> str:
    if value:
        if not value.startswith("att-") or len(value) < 12:
            raise DispatchContractError("invalid-attempt-id", value)
        return value
    return "att-" + uuid.uuid4().hex


def row_has_attempt(pipe: str, attempt_id: str) -> bool:
    metadata = parse_registry_metadata(pipe)
    return metadata.get("attempt_id") == attempt_id


def _immutable_attempt_identity(fields: list[str]) -> tuple[object, ...]:
    if len(fields) != 6:
        raise DispatchContractError("invalid-registry-row", "expected six tab-separated fields")
    metadata = parse_registry_metadata(fields[5])
    validate_attempt_metadata(metadata)
    immutable_metadata = tuple(
        sorted(
            (key, value)
            for key, value in metadata.items()
            if key not in ATTEMPT_MUTABLE_METADATA
        )
    )
    return fields[2], fields[3], fields[4], immutable_metadata


def _atomic_registry_replace(jobs: Path, lines: list[str]) -> None:
    """Replace the registry after fsync without exposing a truncated file."""
    fd, tmp_name = tempfile.mkstemp(prefix=f".{jobs.name}.claim-", dir=str(jobs.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as registry:
            registry.write("\n".join(lines) + "\n")
            registry.flush()
            os.fsync(registry.fileno())
        os.replace(tmp_name, jobs)
        dir_fd = os.open(str(jobs.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


def claim_attempt_row(
    jobs: Path,
    attempt_id: str,
    row: str,
    *,
    launch: bool = False,
    exclusive_metadata: dict[str, str] | None = None,
    exclusive_live_metadata: dict[str, str] | None = None,
    terminal_attempt_limit: int | None = None,
) -> bool:
    """Atomically register ``attempt_id`` and claim its launch at most once.

    A prior ``--register`` row may transition from ``launch_claimed=0`` to 1 on
    the first ``--start``. Concurrent starts serialize on the same lock; callers
    must not spawn a child when this returns ``False``.
    """

    if not attempt_id:
        raise DispatchContractError("attempt-id-required", "registered dispatches require an attempt id")
    row_fields = row.rstrip("\n").split("\t")
    if len(row_fields) != 6:
        raise DispatchContractError("invalid-registry-row", "expected six tab-separated fields")
    row_metadata = parse_registry_metadata(row_fields[5])
    validate_attempt_metadata(row_metadata)
    if row_metadata.get("attempt_id") != attempt_id:
        raise DispatchContractError("attempt-row-identity-mismatch", attempt_id)
    ensure_global_registry_writable(jobs)
    lock_path = Path(f"{jobs}.lock")
    with lock_path.open("a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        lines = jobs.read_text(encoding="utf-8", errors="replace").splitlines()
        for index, existing in enumerate(lines):
            fields = existing.split("\t")
            if len(fields) == 6 and row_has_attempt(fields[5], attempt_id):
                metadata = parse_registry_metadata(fields[5])
                validate_attempt_metadata(metadata)
                if _immutable_attempt_identity(fields) != _immutable_attempt_identity(row_fields):
                    raise DispatchContractError(
                        "attempt-identity-conflict",
                        f"attempt_id={attempt_id}",
                    )
                if not launch or metadata.get("launch_claimed") == "1" or fields[1] != "open":
                    return False
                pipe = ",".join(part for part in fields[5].split(",") if not part.startswith("launch_claimed="))
                fields[5] = pipe + ",launch_claimed=1"
                lines[index] = "\t".join(fields)
                _atomic_registry_replace(jobs, lines)
                return True
        if exclusive_metadata:
            for existing in lines:
                fields = existing.split("\t")
                if len(fields) != 6:
                    continue
                metadata = parse_registry_metadata(fields[5])
                if all(metadata.get(key) == value for key, value in exclusive_metadata.items()):
                    return False
        if exclusive_live_metadata:
            matching_terminal_attempts = set()
            for existing in lines:
                fields = existing.split("\t")
                if len(fields) != 6:
                    continue
                metadata = parse_registry_metadata(fields[5])
                if not all(
                    metadata.get(key) == value
                    for key, value in exclusive_live_metadata.items()
                ):
                    continue
                validate_attempt_metadata(metadata)
                if fields[1] in {"open", "running"}:
                    return False
                if fields[1] == "done" and metadata.get("attempt_id"):
                    matching_terminal_attempts.add(metadata["attempt_id"])
            if (
                terminal_attempt_limit is not None
                and len(matching_terminal_attempts) >= terminal_attempt_limit
            ):
                raise DispatchContractError(
                    "quick-registered-headless-exhausted",
                    f"terminal_attempts={len(matching_terminal_attempts)} limit={terminal_attempt_limit}",
                )
        row_fields[5] += f",launch_claimed={1 if launch else 0}"
        with jobs.open("a", encoding="utf-8") as registry:
            registry.write("\t".join(row_fields) + "\n")
            registry.flush()
            os.fsync(registry.fileno())
        return True


def _row_identity(fields: list[str]) -> tuple[str, ...] | None:
    if len(fields) != 6:
        return None
    metadata = dict(part.split("=", 1) for part in fields[5].split(",") if "=" in part)
    if metadata.get("attempt_id"):
        return ("attempt", metadata["attempt_id"])
    route_id = metadata.get("route_id")
    route_node = metadata.get("route_node")
    parent = metadata.get("parent")
    if route_id and route_node and parent:
        return ("legacy", route_id, route_node, parent, fields[4])
    return None


def close_attempt_row(
    jobs: Path,
    attempt_id: str,
    note: str,
    *,
    evidence: dict[str, str] | None = None,
) -> bool:
    """Close one exact SD-49 attempt atomically and idempotently."""
    if not attempt_id or not note:
        raise DispatchContractError("attempt-close-invalid", "attempt_id and note are required")
    ensure_global_registry_writable(jobs)
    lock_path = Path(f"{jobs}.lock")
    with lock_path.open("a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        lines = jobs.read_text(encoding="utf-8", errors="replace").splitlines()
        for index, line in enumerate(lines):
            fields = line.split("\t")
            if len(fields) != 6 or fields[1] not in {"open", "running"}:
                continue
            metadata = parse_registry_metadata(fields[5])
            if metadata.get("attempt_id") != attempt_id:
                continue
            validate_attempt_metadata(metadata)
            fields[1] = "done"
            additions = [f"note={note}"]
            for key, value in sorted((evidence or {}).items()):
                if value not in (None, ""):
                    additions.append(f"{key}={str(value).replace(',', ';')}")
            fields[5] += "," + ",".join(additions)
            lines[index] = "\t".join(fields)
            _atomic_registry_replace(jobs, lines)
            return True
    return False


def launch_orphan_watch(
    jobs: Path,
    agent_home: Path,
    attempt_id: str,
    pid: int,
    pid_start: str,
) -> int:
    """Start one exact post-exit owner watcher outside the model governor.

    The watcher is deterministic infrastructure, not a model worker. It only
    waits for the recorded PID/start identity to end and then asks the shared
    registry classifier to close a true orphan; it never resumes work.
    """
    if not attempt_id or pid <= 0 or not pid_start:
        raise DispatchContractError(
            "orphan-watch-identity-invalid",
            "attempt_id, pid, and pid_start are required",
        )
    script = _MODULE_ROOT / "utilities" / "dispatch-orphan-watch.py"
    try:
        proc = subprocess.Popen(
            [
                sys.executable, str(script),
                "--jobs", str(Path(jobs).resolve()),
                "--agent-home", str(Path(agent_home).resolve()),
                "--attempt-id", attempt_id,
                "--pid", str(pid),
                "--pid-start", str(pid_start),
            ],
            cwd="/",
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise DispatchContractError("orphan-watch-launch-failed", str(exc)) from exc
    return proc.pid


def close_attempt_row_if(
    jobs: Path,
    attempt_id: str,
    note: str,
    predicate: Callable[[list[str]], bool],
    *,
    evidence: dict[str, str] | None = None,
) -> bool:
    """Revalidate and close one exact attempt inside the SD-49 lock.

    Reconciliation decisions depend on mutable process, worktree, marker and
    heartbeat evidence.  A read-then-``close_attempt_row`` sequence leaves a
    race between the decision and mutation.  This primitive re-reads the row
    and invokes the caller's safety predicate while the canonical registry is
    locked; a changed or newly-live row is therefore left untouched.
    """
    if not attempt_id or not note:
        raise DispatchContractError("attempt-close-invalid", "attempt_id and note are required")
    ensure_global_registry_writable(jobs)
    with Path(f"{jobs}.lock").open("a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        lines = jobs.read_text(encoding="utf-8", errors="replace").splitlines()
        for index, line in enumerate(lines):
            fields = line.split("\t")
            if len(fields) != 6 or fields[1] not in {"open", "running"}:
                continue
            metadata = parse_registry_metadata(fields[5])
            if metadata.get("attempt_id") != attempt_id:
                continue
            validate_attempt_metadata(metadata)
            if not predicate(fields.copy()):
                continue
            fields[1] = "done"
            additions = [f"note={note}"]
            for key, value in sorted((evidence or {}).items()):
                if value not in (None, ""):
                    additions.append(f"{key}={str(value).replace(',', ';')}")
            fields[5] += "," + ",".join(additions)
            lines[index] = "\t".join(fields)
            _atomic_registry_replace(jobs, lines)
            return True
    return False


def annotate_attempt_row(jobs: Path, attempt_id: str, values: dict[str, str]) -> bool:
    """Append bounded metadata to one exact attempt under the SD-49 lock."""
    ensure_global_registry_writable(jobs)
    with Path(f"{jobs}.lock").open("a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        lines = jobs.read_text(encoding="utf-8", errors="replace").splitlines()
        for index, line in enumerate(lines):
            fields = line.split("\t")
            if len(fields) != 6:
                continue
            metadata = parse_registry_metadata(fields[5])
            if metadata.get("attempt_id") != attempt_id:
                continue
            validate_attempt_metadata(metadata)
            additions = [f"{key}={str(value).replace(',', ';')}" for key, value in sorted(values.items())]
            fields[5] += "," + ",".join(additions)
            lines[index] = "\t".join(fields)
            _atomic_registry_replace(jobs, lines)
            return True
    return False


def reconcile_local_registry(global_jobs: Path, local_jobs: Path) -> tuple[int, int]:
    """Copy only current-contract local rows into the global registry once."""

    ensure_global_registry_writable(global_jobs)
    if not local_jobs.is_file():
        return 0, 0
    local_lines = local_jobs.read_text(encoding="utf-8").splitlines()
    lock_path = Path(f"{global_jobs}.lock")
    reconciled = 0
    malformed = 0
    with lock_path.open("a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        global_lines = global_jobs.read_text(encoding="utf-8").splitlines()
        identities = {
            identity for line in global_lines
            if (identity := _row_identity(line.split("\t"))) is not None
        }
        additions: list[str] = []
        for line in local_lines:
            fields = line.split("\t")
            identity = _row_identity(fields)
            if identity is None:
                malformed += 1
                continue
            metadata=parse_registry_metadata(fields[5])
            try:
                validate_attempt_metadata(metadata)
            except DispatchContractError:
                malformed += 1
                continue
            if identity in identities:
                continue
            fields[5] += f",reconciled_from={local_jobs}"
            additions.append("\t".join(fields))
            identities.add(identity)
            reconciled += 1
        if additions:
            with global_jobs.open("a", encoding="utf-8") as registry:
                for line in additions:
                    registry.write(line + "\n")
                registry.flush()
                os.fsync(registry.fileno())
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return reconciled, malformed
