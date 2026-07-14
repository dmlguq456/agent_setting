#!/usr/bin/env python3
"""Offline proposal and runtime-realization lifecycle.

This tool deliberately has no source-edit, runtime-config, plugin, activation,
network, or Git mutation command.  It writes only bounded evidence records to
an XDG state inbox outside runtime discovery paths.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import secrets
import stat
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple


SCHEMA_VERSION = 1
MAX_CONTEXT_BYTES = 256 * 1024
MAX_RECORD_BYTES = 1024 * 1024
MAX_EVIDENCE_BYTES = 2 * 1024 * 1024
MAX_EVIDENCE_ITEMS = 128
MAX_INCIDENT_KEY_LENGTH = 512
ID_RE = re.compile(r"^imp-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:[a-z0-9._-]*[a-z0-9])?$")

PROPOSAL_TRANSITIONS = {
    "observed": {"reproduced", "deferred", "rejected"},
    "reproduced": {"proposed", "deferred", "rejected"},
    "proposed": {"reviewed", "reproduced", "deferred", "rejected"},
    "reviewed": {"adopted", "superseded-by-native", "rejected", "deferred"},
    "deferred": {"observed", "reproduced", "rejected"},
    "adopted": {"superseded-by-native"},
    "superseded-by-native": set(),
    "rejected": set(),
}
REALIZATION_TRANSITIONS = {
    "unverified": {"active", "incompatible", "retired"},
    "active": {"needs-revalidation", "retired"},
    "needs-revalidation": {
        "active",
        "incompatible",
        "superseded-by-native",
        "retired",
    },
    "incompatible": {"needs-revalidation", "retired"},
    "superseded-by-native": set(),
    "retired": set(),
}
APPROVAL_PROPOSAL_STATES = {
    "reviewed",
    "adopted",
    "superseded-by-native",
    "rejected",
}
APPROVAL_REALIZATION_STATES = {"active", "superseded-by-native", "retired"}
BASE_FRESH_TARGETS = {"reviewed", "adopted"}
CONTEXT_FIELDS = {
    "source_revision",
    "source_dirty",
    "portable_fingerprint",
    "runtimes",
    "docs_fingerprint",
    "fixture_fingerprints",
    "active_providers",
}


class ProposalError(RuntimeError):
    """A stable, machine-readable proposal lifecycle failure."""

    def __init__(self, reason: str, message: str, exit_code: int = 5):
        super().__init__(message)
        self.reason = reason
        self.exit_code = exit_code


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compact_utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def default_store() -> Path:
    override = os.environ.get("HARNESS_IMPROVEMENT_HOME")
    if override:
        return Path(override).expanduser()
    state = os.environ.get("XDG_STATE_HOME")
    base = Path(state).expanduser() if state else Path.home() / ".local" / "state"
    return base / "agent-harness" / "improvement"


def _resolved(path: Path) -> Path:
    try:
        return path.expanduser().resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise ProposalError("unsafe-path", f"cannot resolve path safely: {path}") from exc


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _protected_roots() -> List[Path]:
    home = Path.home()
    xdg_config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config")).expanduser()
    xdg_data = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share")).expanduser()
    repo_root = Path(__file__).resolve().parents[2]
    values = [
        repo_root,
        Path(os.environ.get("AGENT_HOME", repo_root)).expanduser(),
        Path(os.environ.get("CLAUDE_CONFIG_DIR", home / ".claude")).expanduser(),
        Path(os.environ.get("CODEX_HOME", home / ".codex")).expanduser(),
        Path(os.environ.get("OPENCODE_CONFIG_DIR", xdg_config / "opencode")).expanduser(),
        xdg_data / "agent-harness",
    ]
    result: List[Path] = []
    for value in values:
        resolved = _resolved(value)
        if resolved not in result:
            result.append(resolved)
    return result


def validate_store_path(store: Path) -> Path:
    requested = store.expanduser()
    if requested.exists() and requested.is_symlink():
        raise ProposalError("unsafe-store", f"proposal store must not be a symlink: {requested}")
    resolved = _resolved(requested)
    for protected in _protected_roots():
        if _is_within(resolved, protected):
            raise ProposalError(
                "protected-store",
                f"proposal store is inside a source/runtime/activation path: {resolved}",
            )
    return resolved


def _ensure_plain_dir(path: Path, mode: int = 0o700) -> None:
    if path.exists() and (path.is_symlink() or not path.is_dir()):
        raise ProposalError("unsafe-directory", f"expected a plain directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or not path.is_dir():
        raise ProposalError("unsafe-directory", f"directory changed during creation: {path}")
    try:
        path.chmod(mode)
    except OSError as exc:
        raise ProposalError("permission-error", f"cannot protect directory: {path}") from exc


def _prepare_store(store: Path) -> Path:
    root = validate_store_path(store)
    _ensure_plain_dir(root)
    _ensure_plain_dir(root / "proposals")
    return root


@contextmanager
def _mutation_lock(store: Path) -> Iterator[Path]:
    root = _prepare_store(store)
    lock_path = root / ".lock"
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(str(lock_path), flags, 0o600)
    except OSError as exc:
        raise ProposalError("lock-error", f"cannot open proposal lock: {lock_path}") from exc
    try:
        os.fchmod(fd, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield root
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _read_bounded(path: Path, limit: int, label: str) -> bytes:
    try:
        info = path.lstat()
    except OSError as exc:
        raise ProposalError("missing-file", f"{label} is unavailable: {path}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ProposalError("unsafe-file", f"{label} must be a regular non-symlink file: {path}")
    if info.st_size > limit:
        raise ProposalError("file-too-large", f"{label} exceeds {limit} bytes: {path}")
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ProposalError("read-error", f"cannot read {label}: {path}") from exc
    if len(data) > limit:
        raise ProposalError("file-too-large", f"{label} exceeds {limit} bytes: {path}")
    return data


def _load_json_bytes(data: bytes, label: str) -> Any:
    try:
        return json.loads(
            data.decode("utf-8"),
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ProposalError("invalid-json", f"{label} is not strict UTF-8 JSON") from exc


def _nonempty_string(value: Any, field: str, limit: int = 512) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ProposalError("invalid-context", f"context.{field} must be a non-empty string")
    return value


def validate_context(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ProposalError("invalid-context", "context root must be an object")
    missing = sorted(CONTEXT_FIELDS - set(value))
    if missing:
        raise ProposalError("invalid-context", f"context is missing fields: {', '.join(missing)}")
    _nonempty_string(value["source_revision"], "source_revision")
    if not isinstance(value["source_dirty"], bool):
        raise ProposalError("invalid-context", "context.source_dirty must be boolean")
    _nonempty_string(value["portable_fingerprint"], "portable_fingerprint")
    _nonempty_string(value["docs_fingerprint"], "docs_fingerprint")
    runtimes = value["runtimes"]
    if not isinstance(runtimes, list) or not runtimes:
        raise ProposalError("invalid-context", "context.runtimes must be a non-empty list")
    seen = set()
    for index, runtime in enumerate(runtimes):
        if not isinstance(runtime, dict):
            raise ProposalError("invalid-context", f"context.runtimes[{index}] must be an object")
        name = _nonempty_string(runtime.get("name"), f"runtimes[{index}].name", 64)
        _nonempty_string(runtime.get("version"), f"runtimes[{index}].version", 128)
        if name in seen:
            raise ProposalError("invalid-context", f"duplicate runtime in context: {name}")
        seen.add(name)
        plugin = runtime.get("plugin")
        if plugin is not None:
            if not isinstance(plugin, dict):
                raise ProposalError("invalid-context", f"runtime {name} plugin must be an object")
            for field in ("name", "version", "fingerprint"):
                _nonempty_string(plugin.get(field), f"runtime.{name}.plugin.{field}")
    fixtures = value["fixture_fingerprints"]
    if not isinstance(fixtures, list) or not all(
        isinstance(item, str) and item.strip() for item in fixtures
    ):
        raise ProposalError("invalid-context", "context.fixture_fingerprints must be a string list")
    providers = value["active_providers"]
    if not isinstance(providers, dict) or not all(
        isinstance(key, str)
        and key.strip()
        and isinstance(provider, str)
        and provider.strip()
        for key, provider in providers.items()
    ):
        raise ProposalError("invalid-context", "context.active_providers must map strings to strings")
    return value


def load_context(path: Path) -> Tuple[Dict[str, Any], str]:
    value = validate_context(_load_json_bytes(_read_bounded(path, MAX_CONTEXT_BYTES, "context"), "context"))
    canonical = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return value, hashlib.sha256(canonical).hexdigest()


def _atomic_bytes(path: Path, data: bytes, mode: int = 0o600) -> None:
    _ensure_plain_dir(path.parent)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
        path.chmod(mode)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _atomic_json(path: Path, value: Dict[str, Any]) -> None:
    data = json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
    _atomic_bytes(path, data + b"\n")


def _validate_id(proposal_id: str) -> str:
    if not ID_RE.fullmatch(proposal_id):
        raise ProposalError("invalid-id", f"invalid proposal id: {proposal_id}")
    return proposal_id


def _proposal_dir(root: Path, proposal_id: str) -> Path:
    return root / "proposals" / _validate_id(proposal_id)


def _record_path(root: Path, proposal_id: str) -> Path:
    return _proposal_dir(root, proposal_id) / "record.json"


def _load_record(root: Path, proposal_id: str) -> Dict[str, Any]:
    path = _record_path(root, proposal_id)
    if not path.exists():
        raise ProposalError("not-found", f"proposal not found: {proposal_id}", 3)
    value = _load_json_bytes(_read_bounded(path, MAX_RECORD_BYTES, "proposal record"), "proposal record")
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise ProposalError("invalid-record", f"unsupported proposal record: {path}")
    if value.get("id") != proposal_id or value.get("state") not in PROPOSAL_TRANSITIONS:
        raise ProposalError("invalid-record", f"corrupt proposal record: {path}")
    return value


def _approval(actor: str, approval_ref: Optional[str]) -> None:
    if not actor.startswith("human:") or len(actor) > 128:
        raise ProposalError(
            "approval-required", "approval transitions require --actor human:<reviewer>"
        )
    if not approval_ref or not approval_ref.strip() or len(approval_ref) > 512:
        raise ProposalError(
            "approval-required", "approval transitions require a non-empty --approval-ref"
        )


def _validate_actor(actor: str) -> str:
    if not actor or len(actor) > 128 or "\n" in actor or "\r" in actor:
        raise ProposalError("invalid-actor", "actor must be a one-line string up to 128 characters")
    return actor


def _validate_incident_key(incident_key: Optional[str]) -> Optional[str]:
    if incident_key is None:
        return None
    normalized = incident_key.strip()
    if (
        not normalized
        or len(normalized) > MAX_INCIDENT_KEY_LENGTH
        or "\n" in normalized
        or "\r" in normalized
    ):
        raise ProposalError(
            "invalid-incident-key",
            f"incident key must be one line up to {MAX_INCIDENT_KEY_LENGTH} characters",
        )
    return normalized


def _ensure_evidence_capacity(record: Dict[str, Any]) -> None:
    evidence = record.get("evidence")
    history = record.get("history")
    if not isinstance(evidence, list) or not isinstance(history, list):
        raise ProposalError("invalid-record", "proposal evidence/history must be lists")
    if len(evidence) >= MAX_EVIDENCE_ITEMS or len(history) >= MAX_EVIDENCE_ITEMS:
        raise ProposalError(
            "proposal-full",
            f"proposal reached the bounded evidence limit ({MAX_EVIDENCE_ITEMS})",
        )


def _evidence_suffix(path: Path) -> str:
    suffix = path.suffix.lower()
    return suffix if suffix in {".json", ".md", ".txt", ".patch", ".diff", ".log"} else ".bin"


def _copy_evidence(root: Path, proposal_id: str, source: Path, kind: str) -> Dict[str, Any]:
    if not SLUG_RE.fullmatch(kind):
        raise ProposalError("invalid-evidence-kind", f"invalid evidence kind: {kind}")
    data = _read_bounded(source, MAX_EVIDENCE_BYTES, "evidence")
    digest = hashlib.sha256(data).hexdigest()
    evidence_dir = _proposal_dir(root, proposal_id) / "evidence"
    _ensure_plain_dir(evidence_dir)
    name = f"{_compact_utc_now()}-{kind}-{digest[:12]}-{secrets.token_hex(2)}{_evidence_suffix(source)}"
    destination = evidence_dir / name
    _atomic_bytes(destination, data)
    return {
        "kind": kind,
        "recorded_at": _utc_now(),
        "sha256": digest,
        "size": len(data),
        "source_name": source.name,
        "stored_path": str(destination.relative_to(root)),
    }


def _records_with_incident_key(root: Path, incident_key: str) -> List[Dict[str, Any]]:
    proposals = root / "proposals"
    matches: List[Dict[str, Any]] = []
    for child in sorted(proposals.iterdir(), key=lambda item: item.name):
        if not child.is_dir() or child.is_symlink() or not ID_RE.fullmatch(child.name):
            continue
        record = _load_record(root, child.name)
        if record.get("incident_key") == incident_key:
            matches.append(record)
    return matches


def _ingest_result(record: Dict[str, Any], outcome: str) -> Dict[str, Any]:
    result = dict(record)
    result["ingest_result"] = outcome
    return result


def observe(
    store: Path,
    title: str,
    summary: str,
    context_path: Path,
    evidence_path: Path,
    actor: str = "loop",
    incident_key: Optional[str] = None,
) -> Dict[str, Any]:
    actor = _validate_actor(actor)
    incident_key = _validate_incident_key(incident_key)
    if actor.startswith("loop:") and incident_key is None:
        raise ProposalError(
            "incident-key-required",
            "named automated collectors require an exact --incident-key",
        )
    if not title.strip() or len(title) > 200:
        raise ProposalError("invalid-title", "title must be 1-200 characters")
    if not summary.strip() or len(summary) > 4000:
        raise ProposalError("invalid-summary", "summary must be 1-4000 characters")
    context, fingerprint = load_context(context_path)
    with _mutation_lock(store) as root:
        if incident_key is not None:
            matches = _records_with_incident_key(root, incident_key)
            if len(matches) > 1:
                raise ProposalError(
                    "ambiguous-incident-key",
                    f"multiple proposals share incident key: {incident_key}",
                )
            if matches:
                record = matches[0]
                _ensure_evidence_capacity(record)
                evidence = _copy_evidence(
                    root, record["id"], evidence_path, "incident-recurrence"
                )
                now = _utc_now()
                record["occurrences"] = int(record.get("occurrences", 1)) + 1
                record["latest_observation_fingerprint"] = fingerprint
                record["latest_observed_at"] = now
                record["updated_at"] = now
                record["evidence"].append(evidence)
                record["history"].append(
                    {
                        "event": "incident-recurrence",
                        "from": record["state"],
                        "to": record["state"],
                        "actor": actor,
                        "at": now,
                        "evidence_sha256": evidence["sha256"],
                        "context_fingerprint": fingerprint,
                        "context_changed": fingerprint != record["base_fingerprint"],
                    }
                )
                _atomic_json(_record_path(root, record["id"]), record)
                return _ingest_result(record, "evidence-appended")
        proposal_id = f"imp-{_compact_utc_now()}-{secrets.token_hex(4)}"
        proposal_dir = _proposal_dir(root, proposal_id)
        _ensure_plain_dir(proposal_dir)
        evidence = _copy_evidence(root, proposal_id, evidence_path, "incident")
        now = _utc_now()
        record = {
            "schema_version": SCHEMA_VERSION,
            "id": proposal_id,
            "title": title.strip(),
            "summary": summary.strip(),
            "incident_key": incident_key,
            "occurrences": 1,
            "state": "observed",
            "created_at": now,
            "updated_at": now,
            "base_context": context,
            "base_fingerprint": fingerprint,
            "latest_observation_fingerprint": fingerprint,
            "latest_observed_at": now,
            "evidence": [evidence],
            "realizations": {},
            "history": [
                {
                    "from": None,
                    "to": "observed",
                    "actor": actor,
                    "at": now,
                    "evidence_sha256": evidence["sha256"],
                }
            ],
        }
        _atomic_json(_record_path(root, proposal_id), record)
        return _ingest_result(record, "created")


def _fresh(record: Dict[str, Any], context_path: Path) -> Tuple[Dict[str, Any], str]:
    context, fingerprint = load_context(context_path)
    if fingerprint != record["base_fingerprint"]:
        raise ProposalError(
            "stale-context",
            "current context differs from the proposal base; reproduce or defer before review",
            4,
        )
    return context, fingerprint


def transition(
    store: Path,
    proposal_id: str,
    target: str,
    evidence_path: Path,
    context_path: Optional[Path] = None,
    actor: str = "loop",
    approval_ref: Optional[str] = None,
) -> Dict[str, Any]:
    actor = _validate_actor(actor)
    if target not in PROPOSAL_TRANSITIONS:
        raise ProposalError("invalid-state", f"unknown proposal state: {target}")
    with _mutation_lock(store) as root:
        record = _load_record(root, proposal_id)
        current = record["state"]
        if target not in PROPOSAL_TRANSITIONS[current]:
            raise ProposalError("invalid-transition", f"proposal transition not allowed: {current} -> {target}")
        if target in APPROVAL_PROPOSAL_STATES:
            _approval(actor, approval_ref)
        decision_context = None
        decision_fingerprint = None
        if target == "reproduced" and actor.startswith("loop:") and context_path is None:
            raise ProposalError(
                "context-required",
                "named automated collectors must bind reproduction to current context",
            )
        if target == "reproduced" and context_path is not None:
            decision_context, decision_fingerprint = load_context(context_path)
        elif target in BASE_FRESH_TARGETS:
            if context_path is None:
                raise ProposalError("context-required", f"{target} requires --context")
            decision_context, decision_fingerprint = _fresh(record, context_path)
        elif target in {"superseded-by-native", "rejected"}:
            if context_path is None:
                raise ProposalError("context-required", f"{target} requires --context")
            decision_context, decision_fingerprint = load_context(context_path)
        _ensure_evidence_capacity(record)
        evidence = _copy_evidence(root, proposal_id, evidence_path, target)
        now = _utc_now()
        event = {
            "from": current,
            "to": target,
            "actor": actor,
            "at": now,
            "evidence_sha256": evidence["sha256"],
        }
        if approval_ref:
            event["approval_ref"] = approval_ref.strip()
        if decision_fingerprint:
            event["context_fingerprint"] = decision_fingerprint
            event["context"] = decision_context
        if target == "reproduced" and decision_fingerprint:
            event["base_rebased"] = decision_fingerprint != record["base_fingerprint"]
            record["base_context"] = decision_context
            record["base_fingerprint"] = decision_fingerprint
            record["latest_observation_fingerprint"] = decision_fingerprint
            record["latest_observed_at"] = now
        record["state"] = target
        record["updated_at"] = now
        record["evidence"].append(evidence)
        record["history"].append(event)
        _atomic_json(_record_path(root, proposal_id), record)
        return record


def realization(
    store: Path,
    proposal_id: str,
    runtime: str,
    target: str,
    runtime_version: str,
    plugin_name: str,
    plugin_version: str,
    context_path: Path,
    evidence_path: Path,
    actor: str = "loop",
    approval_ref: Optional[str] = None,
) -> Dict[str, Any]:
    actor = _validate_actor(actor)
    if not SLUG_RE.fullmatch(runtime):
        raise ProposalError("invalid-runtime", f"invalid runtime name: {runtime}")
    if target not in REALIZATION_TRANSITIONS:
        raise ProposalError("invalid-state", f"unknown realization state: {target}")
    for value, label in (
        (runtime_version, "runtime-version"),
        (plugin_name, "plugin-name"),
        (plugin_version, "plugin-version"),
    ):
        if not value.strip() or len(value) > 256:
            raise ProposalError("invalid-realization", f"{label} must be a non-empty string")
    context, fingerprint = load_context(context_path)
    with _mutation_lock(store) as root:
        record = _load_record(root, proposal_id)
        existing = record["realizations"].get(runtime)
        current = existing["state"] if existing else "unverified"
        if target not in REALIZATION_TRANSITIONS[current]:
            raise ProposalError(
                "invalid-transition", f"realization transition not allowed: {current} -> {target}"
            )
        if target in APPROVAL_REALIZATION_STATES:
            _approval(actor, approval_ref)
        if target == "active" and record["state"] != "adopted":
            raise ProposalError(
                "proposal-not-adopted", "an active realization requires an adopted portable proposal"
            )
        if target == "needs-revalidation" and existing:
            verified = existing.get("verified_context_fingerprint")
            if verified and verified == fingerprint:
                raise ProposalError(
                    "context-unchanged", "active realization context has not changed"
                )
        _ensure_evidence_capacity(record)
        evidence = _copy_evidence(root, proposal_id, evidence_path, f"realization-{target}")
        now = _utc_now()
        event = {
            "from": current,
            "to": target,
            "actor": actor,
            "at": now,
            "runtime_version": runtime_version.strip(),
            "plugin_name": plugin_name.strip(),
            "plugin_version": plugin_version.strip(),
            "context_fingerprint": fingerprint,
            "evidence_sha256": evidence["sha256"],
        }
        if approval_ref:
            event["approval_ref"] = approval_ref.strip()
        item = existing or {"runtime": runtime, "history": []}
        item.update(
            {
                "state": target,
                "runtime_version": runtime_version.strip(),
                "plugin_name": plugin_name.strip(),
                "plugin_version": plugin_version.strip(),
                "last_context": context,
                "last_context_fingerprint": fingerprint,
                "updated_at": now,
            }
        )
        if target == "active":
            item["verified_context"] = context
            item["verified_context_fingerprint"] = fingerprint
            item["verified_at"] = now
        item["history"].append(event)
        record["realizations"][runtime] = item
        record["evidence"].append(evidence)
        record["updated_at"] = now
        _atomic_json(_record_path(root, proposal_id), record)
        return record


def check(
    store: Path, proposal_id: str, context_path: Path, runtime: Optional[str] = None
) -> Dict[str, Any]:
    root = validate_store_path(store)
    record = _load_record(root, proposal_id)
    _context, fingerprint = load_context(context_path)
    if runtime:
        item = record["realizations"].get(runtime)
        if not item:
            raise ProposalError("not-found", f"realization not found: {runtime}", 3)
        expected = item.get("verified_context_fingerprint")
        fresh = bool(item.get("state") == "active" and expected == fingerprint)
        return {
            "id": proposal_id,
            "scope": "realization",
            "runtime": runtime,
            "state": item["state"],
            "fresh": fresh,
            "expected_fingerprint": expected,
            "current_fingerprint": fingerprint,
        }
    fresh = record["base_fingerprint"] == fingerprint
    return {
        "id": proposal_id,
        "scope": "proposal",
        "state": record["state"],
        "fresh": fresh,
        "expected_fingerprint": record["base_fingerprint"],
        "current_fingerprint": fingerprint,
    }


def show(store: Path, proposal_id: str) -> Dict[str, Any]:
    return _load_record(validate_store_path(store), proposal_id)


def list_records(store: Path, state: Optional[str] = None) -> List[Dict[str, Any]]:
    if state is not None and state not in PROPOSAL_TRANSITIONS:
        raise ProposalError("invalid-state", f"unknown proposal state: {state}")
    root = validate_store_path(store)
    proposals = root / "proposals"
    if not proposals.exists():
        return []
    if proposals.is_symlink() or not proposals.is_dir():
        raise ProposalError("unsafe-directory", f"invalid proposal directory: {proposals}")
    result = []
    for child in sorted(proposals.iterdir(), key=lambda item: item.name):
        if not child.is_dir() or child.is_symlink() or not ID_RE.fullmatch(child.name):
            continue
        record = _load_record(root, child.name)
        if state is None or record["state"] == state:
            result.append(
                {
                    "id": record["id"],
                    "title": record["title"],
                    "incident_key": record.get("incident_key"),
                    "occurrences": record.get("occurrences", 1),
                    "state": record["state"],
                    "updated_at": record["updated_at"],
                }
            )
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=None, help="override safe XDG inbox")
    sub = parser.add_subparsers(dest="command", required=True)

    observe_parser = sub.add_parser("observe", help="create an observed incident")
    observe_parser.add_argument("--title", required=True)
    observe_parser.add_argument("--summary", required=True)
    observe_parser.add_argument("--context", type=Path, required=True)
    observe_parser.add_argument("--evidence", type=Path, required=True)
    observe_parser.add_argument("--actor", default="loop")
    observe_parser.add_argument(
        "--incident-key",
        help="agent-authored exact identity; a match appends recurrence evidence",
    )

    transition_parser = sub.add_parser("transition", help="advance portable proposal state")
    transition_parser.add_argument("id")
    transition_parser.add_argument("state", choices=sorted(PROPOSAL_TRANSITIONS))
    transition_parser.add_argument("--evidence", type=Path, required=True)
    transition_parser.add_argument("--context", type=Path)
    transition_parser.add_argument("--actor", default="loop")
    transition_parser.add_argument("--approval-ref")

    realization_parser = sub.add_parser("realization", help="record version-bound realization state")
    realization_parser.add_argument("id")
    realization_parser.add_argument("--runtime", required=True)
    realization_parser.add_argument("--state", choices=sorted(REALIZATION_TRANSITIONS), required=True)
    realization_parser.add_argument("--runtime-version", required=True)
    realization_parser.add_argument("--plugin-name", required=True)
    realization_parser.add_argument("--plugin-version", required=True)
    realization_parser.add_argument("--context", type=Path, required=True)
    realization_parser.add_argument("--evidence", type=Path, required=True)
    realization_parser.add_argument("--actor", default="loop")
    realization_parser.add_argument("--approval-ref")

    check_parser = sub.add_parser("check", help="compare a current context fingerprint")
    check_parser.add_argument("id")
    check_parser.add_argument("--context", type=Path, required=True)
    check_parser.add_argument("--runtime")

    show_parser = sub.add_parser("show", help="show one proposal")
    show_parser.add_argument("id")

    list_parser = sub.add_parser("list", help="list proposals")
    list_parser.add_argument("--state", choices=sorted(PROPOSAL_TRANSITIONS))
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    store = args.store or default_store()
    try:
        if args.command == "observe":
            result: Any = observe(
                store,
                args.title,
                args.summary,
                args.context,
                args.evidence,
                args.actor,
                args.incident_key,
            )
        elif args.command == "transition":
            result = transition(
                store,
                args.id,
                args.state,
                args.evidence,
                args.context,
                args.actor,
                args.approval_ref,
            )
        elif args.command == "realization":
            result = realization(
                store,
                args.id,
                args.runtime,
                args.state,
                args.runtime_version,
                args.plugin_name,
                args.plugin_version,
                args.context,
                args.evidence,
                args.actor,
                args.approval_ref,
            )
        elif args.command == "check":
            result = check(store, args.id, args.context, args.runtime)
            print(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2))
            return 0 if result["fresh"] else 4
        elif args.command == "show":
            result = show(store, args.id)
        else:
            result = list_records(store, args.state)
        print(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2))
        return 0
    except ProposalError as exc:
        print(
            json.dumps(
                {"status": "error", "reason": exc.reason, "message": str(exc)},
                sort_keys=True,
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
