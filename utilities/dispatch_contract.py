#!/usr/bin/env python3
"""Portable SD-48/49 primitives used by headless dispatch adapters."""

from __future__ import annotations

from dataclasses import dataclass
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid


ELIGIBILITY = {"supported", "unsupported", "unknown"}
LAUNCH_AUTHORITIES = {"conductor", "ancestor-broker"}
_MODULE_ROOT = Path(__file__).resolve().parents[1]


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


def _absolute(path: str | Path, field: str) -> Path:
    value = Path(path).expanduser()
    if not value.is_absolute():
        raise DispatchContractError(f"{field}-must-be-absolute", str(value))
    return value.resolve(strict=False)


def resolve_global_registry(
    agent_home: Path,
    explicit_jobs: str | None,
    depth: int,
    action: str,
    environ: dict[str, str] | os._Environ[str] | None = None,
) -> RegistrySelection:
    """Resolve the one authoritative registry and reject nested overrides.

    Depth-0/root dispatch may select an explicit registry once. The wrapper then
    exports it through AGENT_DISPATCH_JOBS. A real nested start must inherit that
    path; argv may repeat it, but cannot replace it.
    """

    env = os.environ if environ is None else environ
    inherited_raw = env.get("AGENT_DISPATCH_JOBS")
    explicit = _absolute(explicit_jobs, "jobs") if explicit_jobs else None
    inherited = _absolute(inherited_raw, "agent-dispatch-jobs") if inherited_raw else None

    if depth > 1 and inherited and explicit and inherited != explicit:
        raise DispatchContractError(
            "noncanonical-nested-jobs",
            f"explicit={explicit} inherited={inherited}",
        )

    nested_start = depth > 1 and action == "start"
    if nested_start and inherited is None:
        raise DispatchContractError(
            "global-registry-unset",
            "nested --start requires inherited AGENT_DISPATCH_JOBS",
        )

    # A depth-1 invocation is the root dispatch boundary.  It may deliberately
    # choose a new canonical registry even when the invoking shell carries an
    # unrelated ambient value.  Only nested invocations must inherit exactly.
    if depth <= 1 and explicit:
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
    depth: int,
    action: str,
    intensity: str,
    environ: dict[str, str] | os._Environ[str] | None = None,
) -> BrokerSelection | None:
    """Reject production launch-broker creation after dispatch contract v3.

    The callable remains for one compatibility release so an overlooked caller
    fails closed with a stable reason instead of silently resurrecting the
    resident broker. Diagnostic ``status``/``stop`` remain in dispatch-broker.py.
    """

    if action != "start" or depth != 1 or intensity not in {"standard", "strong", "thorough", "adversarial"}:
        return None
    raise DispatchContractError(
        "launch-broker-retired",
        "dispatch contract v3 launches checked headless adapters directly from the conductor",
    )


def validate_nested_eligibility(
    *,
    depth: int,
    action: str,
    parent_harness: str,
    parent_transport: str,
    parent_sandbox: str,
    child_harness: str,
    launch_authority: str,
    status: str,
    source: str,
) -> None:
    if depth < 2:
        return
    if launch_authority not in LAUNCH_AUTHORITIES:
        raise DispatchContractError("invalid-launch-authority", launch_authority)
    if status not in ELIGIBILITY:
        raise DispatchContractError("invalid-nested-eligibility", status)
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
        if marker.get("route_id") != route["route_id"] or marker.get("route_hash") != route["route_hash"]:
            missing.append(dep)
    if missing:
        raise DispatchContractError("completion-marker-missing", ",".join(missing))


def new_attempt_id(value: str | None = None) -> str:
    if value:
        if not value.startswith("att-") or len(value) < 12:
            raise DispatchContractError("invalid-attempt-id", value)
        return value
    return "att-" + uuid.uuid4().hex


def row_has_attempt(pipe: str, attempt_id: str) -> bool:
    metadata = dict(part.split("=", 1) for part in pipe.split(",") if "=" in part)
    return metadata.get("attempt_id") == attempt_id


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


def claim_attempt_row(jobs: Path, attempt_id: str, row: str, *, launch: bool = False) -> bool:
    """Atomically register ``attempt_id`` and claim its launch at most once.

    A prior ``--register`` row may transition from ``launch_claimed=0`` to 1 on
    the first ``--start``. Concurrent starts serialize on the same lock; callers
    must not spawn a child when this returns ``False``.
    """

    if not attempt_id:
        raise DispatchContractError("attempt-id-required", "registered dispatches require an attempt id")
    ensure_global_registry_writable(jobs)
    lock_path = Path(f"{jobs}.lock")
    with lock_path.open("a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        lines = jobs.read_text(encoding="utf-8", errors="replace").splitlines()
        for index, existing in enumerate(lines):
            fields = existing.split("\t")
            if len(fields) == 6 and row_has_attempt(fields[5], attempt_id):
                metadata = dict(part.split("=", 1) for part in fields[5].split(",") if "=" in part)
                if not launch or metadata.get("launch_claimed") == "1" or fields[1] != "open":
                    return False
                pipe = ",".join(part for part in fields[5].split(",") if not part.startswith("launch_claimed="))
                fields[5] = pipe + ",launch_claimed=1"
                lines[index] = "\t".join(fields)
                _atomic_registry_replace(jobs, lines)
                return True
        row_fields = row.rstrip("\n").split("\t")
        if len(row_fields) != 6:
            raise DispatchContractError("invalid-registry-row", "expected six tab-separated fields")
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


def reconcile_local_registry(global_jobs: Path, local_jobs: Path) -> tuple[int, int]:
    """Copy legacy local-only rows into the global registry exactly once."""

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
