#!/usr/bin/env python3
"""Portable contract helpers for splitting one route stage into worker sessions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

SCHEMA_VERSION = 1
MODES = {"serial", "parallel"}
ADAPTERS = {"claude", "codex", "opencode"}
_ID = re.compile(r"^(?:ssc|ss)-[A-Za-z0-9._-]{4,200}$")
_ATTEMPT = re.compile(r"^att-[A-Za-z0-9._-]{8,240}$")


class StageSessionError(ValueError):
    """Raised when a stage-session manifest is unsafe or incomplete."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _absolute(value: object, *, base: Path, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise StageSessionError(f"{field}-missing")
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    return path.resolve(strict=False)


def _fixed_files(values: object, *, worktree: Path, session_id: str) -> list[str]:
    if not isinstance(values, list) or not values:
        raise StageSessionError(f"fixed-files-missing:{session_id}")
    result: list[str] = []
    for raw in values:
        path = _absolute(raw, base=worktree, field=f"fixed-file:{session_id}")
        try:
            path.relative_to(worktree)
        except ValueError as exc:
            raise StageSessionError(f"fixed-file-outside-worktree:{session_id}:{path}") from exc
        if any(char in str(raw) for char in "*?[]"):
            raise StageSessionError(f"fixed-file-must-be-exact:{session_id}:{raw}")
        value = str(path)
        if value not in result:
            result.append(value)
    return sorted(result)


def load_manifest(
    path: Path | str,
    *,
    route: dict[str, Any] | None = None,
    node: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load and normalize a bounded stage-session chain manifest."""

    manifest_path = Path(path).resolve()
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        raise StageSessionError(f"manifest-unreadable:{manifest_path}") from exc
    if not isinstance(raw, dict) or raw.get("schema_version") != SCHEMA_VERSION:
        raise StageSessionError("manifest-schema-invalid")
    if raw.get("kind") != "stage-session-chain":
        raise StageSessionError("manifest-kind-invalid")
    chain_id = raw.get("chain_id")
    if not isinstance(chain_id, str) or not _ID.fullmatch(chain_id) or not chain_id.startswith("ssc-"):
        raise StageSessionError("chain-id-invalid")
    mode = raw.get("mode")
    if mode not in MODES:
        raise StageSessionError("session-mode-invalid")
    worktree = _absolute(raw.get("worktree"), base=manifest_path.parent, field="worktree")
    route_file = _absolute(raw.get("route_file"), base=manifest_path.parent, field="route-file")
    if route is not None:
        expected = {"route_id": route.get("route_id"), "route_hash": route.get("route_hash")}
        if any(raw.get(key) != value for key, value in expected.items()):
            raise StageSessionError("manifest-route-identity-mismatch")
        expected_file = route.get("_route_file")
        if expected_file and route_file != Path(str(expected_file)).resolve():
            raise StageSessionError("manifest-route-file-mismatch")
    if node is not None:
        if raw.get("route_node") != node.get("id"):
            raise StageSessionError("manifest-route-node-mismatch")
        if raw.get("completion_gate") != node.get("completion_gate"):
            raise StageSessionError("manifest-completion-gate-mismatch")
    sessions = raw.get("sessions")
    if not isinstance(sessions, list) or not 1 <= len(sessions) <= 16:
        raise StageSessionError("session-count-invalid")
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_attempts: set[str] = set()
    for offset, item in enumerate(sessions, 1):
        if not isinstance(item, dict):
            raise StageSessionError(f"session-invalid:{offset}")
        session_id = item.get("subsession_id")
        if not isinstance(session_id, str) or not _ID.fullmatch(session_id) or not session_id.startswith("ss-"):
            raise StageSessionError(f"subsession-id-invalid:{offset}")
        if session_id in seen_ids:
            raise StageSessionError(f"subsession-id-duplicate:{session_id}")
        seen_ids.add(session_id)
        attempt_id = item.get("attempt_id")
        if not isinstance(attempt_id, str) or not _ATTEMPT.fullmatch(attempt_id):
            raise StageSessionError(f"attempt-id-invalid:{session_id}")
        if attempt_id in seen_attempts:
            raise StageSessionError(f"attempt-id-duplicate:{attempt_id}")
        seen_attempts.add(attempt_id)
        adapter = item.get("adapter")
        if adapter not in ADAPTERS:
            raise StageSessionError(f"adapter-invalid:{session_id}")
        slug = item.get("slug")
        if not isinstance(slug, str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,120}", slug):
            raise StageSessionError(f"slug-invalid:{session_id}")
        phase_brief = _absolute(
            item.get("phase_brief"), base=manifest_path.parent, field=f"phase-brief:{session_id}"
        )
        if not phase_brief.is_file():
            raise StageSessionError(f"phase-brief-missing:{session_id}")
        narrow_verify = item.get("narrow_verify")
        if not isinstance(narrow_verify, str) or not narrow_verify.strip() or "\n" in narrow_verify:
            raise StageSessionError(f"narrow-verify-invalid:{session_id}")
        rounds = item.get("expected_round_trips")
        if isinstance(rounds, bool) or not isinstance(rounds, int) or not 1 <= rounds <= 20:
            raise StageSessionError(f"expected-round-trips-invalid:{session_id}")
        fixed = _fixed_files(item.get("fixed_files"), worktree=worktree, session_id=session_id)
        normalized.append({
            **item,
            "index": offset,
            "count": len(sessions),
            "subsession_id": session_id,
            "attempt_id": attempt_id,
            "adapter": adapter,
            "slug": slug,
            "phase_brief": str(phase_brief),
            "fixed_files": fixed,
            "narrow_verify": narrow_verify.strip(),
            "expected_round_trips": rounds,
        })
    if mode == "parallel":
        owners: dict[str, str] = {}
        for item in normalized:
            for file in item["fixed_files"]:
                prior = owners.setdefault(file, item["subsession_id"])
                if prior != item["subsession_id"]:
                    raise StageSessionError(
                        f"parallel-fixed-file-overlap:{file}:{prior}:{item['subsession_id']}"
                    )
    return {
        **raw,
        "_manifest_path": str(manifest_path),
        "_manifest_sha256": sha256_file(manifest_path),
        "worktree": str(worktree),
        "route_file": str(route_file),
        "sessions": normalized,
    }
