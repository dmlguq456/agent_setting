#!/usr/bin/env python3
"""Canonical immutable identity for one exact two-way replica batch."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
SUPPORTED_HARNESSES = frozenset({"codex", "claude"})
SUPPORTED_INDEPENDENCE = frozenset({"cross-harness", "degraded-same-harness"})


class ReplicaBatchContractError(ValueError):
    pass


def _digest(value: dict[str, Any]) -> str:
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def build_manifest(
    *,
    replica_group: str,
    route_id: str,
    parent_attempt_id: str,
    independence: str,
    members: list[dict[str, object]],
) -> tuple[dict[str, object], str, dict[str, str]]:
    """Validate and seal the full declared group plus each exact leg binding."""

    common = {
        "schema_version": 1,
        "kind": "replica-batch",
        "declared_size": 2,
        "replica_group": replica_group,
        "route_id": route_id,
        "parent_attempt_id": parent_attempt_id,
        "independence": independence,
    }
    if any(not isinstance(value, str) or not value for value in (
        replica_group, route_id, parent_attempt_id, independence
    )):
        raise ReplicaBatchContractError("replica batch identity must be nonempty")
    if independence not in SUPPORTED_INDEPENDENCE:
        raise ReplicaBatchContractError("unsupported replica batch independence")
    if not isinstance(members, list) or len(members) != 2:
        raise ReplicaBatchContractError("replica batch must declare exactly two members")
    normalized: list[dict[str, object]] = []
    required = {
        "assignment_sha256",
        "attempt_id",
        "route_node",
        "harness",
        "fallback_hop",
        "fallback_ordinal",
    }
    for raw in members:
        if not isinstance(raw, dict) or set(raw) != required:
            raise ReplicaBatchContractError("invalid replica batch member shape")
        if any(
            not isinstance(raw[key], str) or not raw[key]
            for key in (
                "assignment_sha256",
                "attempt_id",
                "route_node",
                "harness",
                "fallback_hop",
            )
        ):
            raise ReplicaBatchContractError("invalid replica batch member identity")
        if not DIGEST.fullmatch(str(raw["assignment_sha256"])):
            raise ReplicaBatchContractError("invalid replica assignment digest")
        ordinal = raw["fallback_ordinal"]
        if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 1:
            raise ReplicaBatchContractError("invalid replica batch fallback ordinal")
        if raw["harness"] not in SUPPORTED_HARNESSES:
            raise ReplicaBatchContractError("unsupported replica batch harness")
        normalized.append({key: raw[key] for key in sorted(required)})
    if len({str(member["attempt_id"]) for member in normalized}) != 2:
        raise ReplicaBatchContractError("replica batch attempts must be distinct")
    if len({str(member["route_node"]) for member in normalized}) != 2:
        raise ReplicaBatchContractError("replica batch nodes must be distinct")
    harness_count = len({str(member["harness"]) for member in normalized})
    if independence == "cross-harness" and harness_count != 2:
        raise ReplicaBatchContractError("cross-harness replica batch must use distinct harnesses")
    if independence == "degraded-same-harness" and harness_count != 1:
        raise ReplicaBatchContractError("degraded replica batch must use one harness")
    normalized.sort(key=lambda member: (str(member["route_node"]), str(member["attempt_id"])))
    manifest = {**common, "members": normalized}
    manifest_digest = _digest(manifest)
    leg_digests = {
        str(member["attempt_id"]): _digest({**common, "member": member})
        for member in normalized
    }
    return manifest, manifest_digest, leg_digests


def verify_manifest(
    manifest: object,
) -> tuple[dict[str, object], str, dict[str, str]]:
    if not isinstance(manifest, dict):
        raise ReplicaBatchContractError("replica batch manifest must be an object")
    expected_keys = {
        "schema_version",
        "kind",
        "declared_size",
        "replica_group",
        "route_id",
        "parent_attempt_id",
        "independence",
        "members",
    }
    if set(manifest) != expected_keys:
        raise ReplicaBatchContractError("invalid replica batch manifest shape")
    if (
        manifest.get("schema_version") != 1
        or manifest.get("kind") != "replica-batch"
        or manifest.get("declared_size") != 2
    ):
        raise ReplicaBatchContractError("unsupported replica batch manifest")
    rebuilt, digest, legs = build_manifest(
        replica_group=manifest.get("replica_group"),
        route_id=manifest.get("route_id"),
        parent_attempt_id=manifest.get("parent_attempt_id"),
        independence=manifest.get("independence"),
        members=manifest.get("members"),
    )
    if rebuilt != manifest:
        raise ReplicaBatchContractError("replica batch manifest is not canonical")
    return rebuilt, digest, legs
