#!/usr/bin/env python3
"""Render the portable minimal worker bootstrap and deterministic type overlay."""

from __future__ import annotations

import re
from pathlib import Path

WORKER_TYPES = ("owner", "stage", "review", "support")
REVIEW_MARKERS = (
    "review",
    "reviewer",
    "verify",
    "verifier",
    "audit",
    "adversary",
    "perspective",
    "plan-check",
)
STAGE_NODE_CONTRACT = {
    "plan": "code-plan",
    "planning": "code-plan",
    "execute": "code-execute",
    "implementation": "code-execute",
    "test": "code-test",
    "verification": "code-test",
    "report": "code-report",
    "reporting": "code-report",
}


def profile_worker_type(root: Path, profile: str | None) -> str | None:
    """Read the single scalar needed from a profile without loading its full schema."""
    if not profile:
        return None
    path = root / "profiles" / f"{profile}.yaml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(r"^worker_type:\s*([a-z-]+)\s*$", text, re.MULTILINE)
    return match.group(1) if match and match.group(1) in WORKER_TYPES else None


def resolve_worker_type(
    *,
    explicit: str | None,
    depth: int,
    worker_role: str | None = None,
    route_node: str | None = None,
    profile_type: str | None = None,
) -> str:
    """Resolve one worker type; explicit/profile declarations beat fallback inference."""
    for candidate in (explicit, profile_type):
        if candidate:
            if candidate not in WORKER_TYPES:
                raise ValueError(f"invalid worker type: {candidate}")
            return candidate
    if depth == 1:
        return "owner"
    signal = " ".join(filter(None, (worker_role, route_node))).lower()
    if any(marker in signal for marker in REVIEW_MARKERS):
        return "review"
    if signal:
        return "stage"
    return "support"


def render_worker_bootstrap(root: Path, worker_type: str) -> str:
    """Return exactly one canonical kernel plus one type fragment."""
    if worker_type not in WORKER_TYPES:
        raise ValueError(f"invalid worker type: {worker_type}")
    paths = (
        root / "roles" / "worker-bootstrap.md",
        root / "roles" / "worker-types" / f"{worker_type}.md",
    )
    return "\n\n".join(path.read_text(encoding="utf-8").strip() for path in paths) + "\n"


def assigned_contract(
    *, capability: str, worker_type: str, worker_role: str | None, route_node: str | None
) -> str:
    """Resolve the one capability/stage Skill a worker should read."""
    if worker_type in {"stage", "review"}:
        if worker_role and worker_role.startswith("code-"):
            return worker_role
        if route_node and route_node.lower() in STAGE_NODE_CONTRACT:
            return STAGE_NODE_CONTRACT[route_node.lower()]
    return capability


def handoff_template() -> str:
    return (
        "artifact: <canonical path | ->\n"
        "verdict: PASS | FAIL | BLOCKED\n"
        "blocker: none | <one line>"
    )
