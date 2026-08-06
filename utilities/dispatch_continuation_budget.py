#!/usr/bin/env python3
"""Resolve a finite owner continuation budget from its bound route."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path


COMPATIBILITY_FLOOR = 12


@dataclass(frozen=True)
class ContinuationBudget:
    limit: int
    source: str
    declared_nodes: int = 0
    retry_slots: int = 0


def positive_continuation_limit(raw: str) -> int:
    """Argparse converter for an explicit, finite owner-launch override."""

    value = int(raw)
    if value <= 0:
        raise ValueError("continuation limit must be positive")
    return value


def resolve_continuation_budget(
    *,
    explicit: int | None = None,
    route_file: str | Path | None = None,
    route_id: str = "",
    route_hash: str = "",
    expected_cwd: str | Path | None = None,
) -> ContinuationBudget:
    """Return an explicit limit or a conservative route-derived default.

    The route is usable only when the supervisor receives the complete owner
    binding. Unreadable, malformed, or mismatched input keeps the historical
    finite floor; it never turns a supervisor into an unbounded loop.
    """

    if explicit is not None:
        if explicit <= 0:
            raise ValueError("continuation limit must be positive")
        return ContinuationBudget(explicit, "explicit-owner-override")
    if not route_file or not route_id or not route_hash:
        return ContinuationBudget(COMPATIBILITY_FLOOR, "compatibility-floor")
    try:
        route = json.loads(Path(route_file).read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return ContinuationBudget(COMPATIBILITY_FLOOR, "compatibility-floor")
    if not isinstance(route, dict) or route.get("schema_version") != 2:
        return ContinuationBudget(COMPATIBILITY_FLOOR, "compatibility-floor")
    if route.get("route_id") != route_id or route.get("route_hash") != route_hash:
        return ContinuationBudget(COMPATIBILITY_FLOOR, "compatibility-floor")
    bare = {key: value for key, value in route.items() if key not in {"route_hash", "route_id"}}
    sealed_hash = "sha256:" + hashlib.sha256(
        json.dumps(
            bare, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    if route_hash != sealed_hash or route_id != "rt-" + sealed_hash.split(":", 1)[1][:16]:
        return ContinuationBudget(COMPATIBILITY_FLOOR, "compatibility-floor")
    if expected_cwd is not None:
        raw_cwd = route.get("cwd")
        if (
            not isinstance(raw_cwd, str)
            or not Path(raw_cwd).is_absolute()
            or Path(raw_cwd).resolve() != Path(expected_cwd).resolve()
        ):
            return ContinuationBudget(COMPATIBILITY_FLOOR, "compatibility-floor")
    nodes = route.get("nodes")
    boundaries = route.get("resume_retry_boundaries")
    if not isinstance(nodes, list) or not isinstance(boundaries, list):
        return ContinuationBudget(COMPATIBILITY_FLOOR, "compatibility-floor")
    node_ids = [
        node.get("id") for node in nodes
        if isinstance(node, dict) and isinstance(node.get("id"), str) and node.get("id")
    ]
    if len(node_ids) != len(nodes) or len(set(node_ids)) != len(node_ids):
        return ContinuationBudget(COMPATIBILITY_FLOOR, "compatibility-floor")
    retry_ids = [item for item in boundaries if isinstance(item, str) and item]
    if len(retry_ids) != len(boundaries) or not set(retry_ids).issubset(node_ids):
        return ContinuationBudget(COMPATIBILITY_FLOOR, "compatibility-floor")
    retry_slots = len(set(retry_ids))
    return ContinuationBudget(
        max(COMPATIBILITY_FLOOR, len(node_ids) + retry_slots),
        "bound-route",
        declared_nodes=len(node_ids),
        retry_slots=retry_slots,
    )
