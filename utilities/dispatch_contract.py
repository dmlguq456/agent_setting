#!/usr/bin/env python3
"""Portable SD-48/49 primitives used by headless dispatch adapters."""

from __future__ import annotations

from dataclasses import dataclass
import fcntl
import os
from pathlib import Path
import uuid


ELIGIBILITY = {"supported", "unsupported", "unknown"}
LAUNCH_AUTHORITIES = {"conductor", "ancestor-broker"}


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


def new_attempt_id(value: str | None = None) -> str:
    if value:
        if not value.startswith("att-") or len(value) < 12:
            raise DispatchContractError("invalid-attempt-id", value)
        return value
    return "att-" + uuid.uuid4().hex


def row_has_attempt(pipe: str, attempt_id: str) -> bool:
    return f"attempt_id={attempt_id}" in ("," + pipe + ",")


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
