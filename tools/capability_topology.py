#!/usr/bin/env python3
"""Validate and query the portable capability execution-topology registry."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "utilities"))
from dispatch_contract import EXECUTION_SURFACES, FALLBACK_HOPS, WRAPPER_TRANSPORTS  # noqa: E402

REGISTRY = ROOT / "capabilities" / "topologies.json"
MANIFEST = ROOT / "harness-manifest.json"
UNITS = ROOT / "roles" / "units"
UNIT_REF_RE = re.compile(r"^[a-z-]+/[a-z-]+$")
_UNIT_CACHE: dict = {}


class TopologyError(ValueError):
    pass


def load_registry(path: Path | str = REGISTRY):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def canonical_registry_bytes(registry):
    return json.dumps(registry, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def registry_digest(registry):
    return "sha256:" + hashlib.sha256(canonical_registry_bytes(registry)).hexdigest()


def expected_recipe_keys(manifest=None):
    if manifest is None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {(name, mode) for name, spec in manifest["capabilities"].items()
            if spec["group"] == "entry" for mode in (spec["modes"] or ["default"])}


def recipe_keys(registry):
    return {(r["capability"], mode) for r in registry["recipes"] for mode in r["modes"]}


def _scope_root(scope):
    if not isinstance(scope, str) or not scope or scope.startswith("/") or ".." in scope.split("/"):
        raise TopologyError(f"unsafe write scope: {scope!r}")
    return scope[:-3] if scope.endswith("/**") else scope


def _overlap(a, b):
    a, b = _scope_root(a), _scope_root(b)
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def _touches_artifact(scope, artifact):
    root = _scope_root(scope)
    return root == artifact or root.startswith(artifact + "/")


def _validate_guard_scope(recipe, scopes, preconditions, registry, node_id):
    declared = set(preconditions or [])
    unknown = declared - set(registry["guard_preconditions"])
    if unknown:
        raise TopologyError(f"{recipe['capability']}:{node_id}: unknown guard preconditions {sorted(unknown)}")
    if any(_touches_artifact(scope, "spec") for scope in scopes):
        owner = registry["artifact_owners"].get("spec")
        if recipe["capability"] != owner and "artifact-order-prechecked" not in declared:
            raise TopologyError(
                f"{recipe['capability']}:{node_id}: spec write scope requires sole owner "
                "or artifact-order-prechecked"
            )


def _unit_frontmatter(unit):
    """Read the few scalars the validator needs from a unit file (stdlib regex only)."""
    key = (str(UNITS), unit)
    if key in _UNIT_CACHE:
        return _UNIT_CACHE[key]
    path = UNITS / f"{unit}.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        raise TopologyError(f"unknown unit: {unit} (no roles/units/{unit}.md)")
    match = re.match(r"\A---\n(.*?\n)---\n", text, re.DOTALL)
    if not match:
        raise TopologyError(f"unit {unit}: missing frontmatter block")
    block = match.group(1)

    def scalar(name):
        found = re.search(rf"^{name}:\s*([^#\n]+?)\s*(?:#.*)?$", block, re.MULTILINE)
        return found.group(1).strip() if found else None

    fields = {name: scalar(name) for name in ("unit", "role", "worker_type", "read_only")}
    if fields["unit"] != unit:
        raise TopologyError(f"unit {unit}: frontmatter unit id mismatch ({fields['unit']!r})")
    if not fields["role"]:
        raise TopologyError(f"unit {unit}: frontmatter role required")
    if fields["worker_type"] not in ("owner", "stage", "review", "support"):
        raise TopologyError(f"unit {unit}: invalid worker_type {fields['worker_type']!r}")
    if fields["read_only"] not in ("true", "false"):
        raise TopologyError(f"unit {unit}: read_only must be true or false")
    _UNIT_CACHE[key] = fields
    return fields


def _validate_unit_ref(recipe, node, registry):
    capability, node_id, kind = recipe.get("capability"), node.get("id"), node.get("kind")
    unit = node.get("unit")
    compat = registry.get("unit_kind_compatibility", {}).get(kind)
    if compat is None:
        raise TopologyError(f"{capability}:{node_id}: no unit compatibility row for kind {kind}")
    if not isinstance(unit, str) or not unit:
        raise TopologyError(f"{capability}:{node_id}: node unit ref required")
    if kind in ("capability-owner", "resource-runner"):
        if unit not in compat or unit not in registry.get("reserved_units", {}):
            raise TopologyError(
                f"{capability}:{node_id}: kind {kind} requires reserved unit {sorted(compat)}"
            )
        # Reserved refs carry no catalog frontmatter, so their role must be pinned here
        # (2026-07-22 verify finding: _kernel/owner previously accepted any role).
        reserved_roles = {"_kernel/owner": {"deep orchestrator", "deep maker"},
                          "_kernel/resource": {"orchestrator"}}
        allowed = reserved_roles.get(unit)
        if allowed is not None and node.get("role") not in allowed:
            raise TopologyError(
                f"{capability}:{node_id}: reserved unit {unit} allows roles {sorted(allowed)}, got {node.get('role')}"
            )
        if "unit_choices" in node:
            raise TopologyError(f"{capability}:{node_id}: reserved-unit node cannot carry unit_choices")
        return
    if unit in registry.get("reserved_units", {}):
        raise TopologyError(f"{capability}:{node_id}: reserved unit {unit} not allowed on kind {kind}")
    choices = node.get("unit_choices")
    if choices is not None:
        if not isinstance(choices, list) or not choices:
            raise TopologyError(f"{capability}:{node_id}: unit_choices must be a non-empty list")
        if unit not in choices:
            raise TopologyError(f"{capability}:{node_id}: unit {unit} not in unit_choices")
    members = [unit] + [c for c in (choices or []) if c != unit]
    for member in members:
        if not UNIT_REF_RE.match(member or ""):
            raise TopologyError(f"{capability}:{node_id}: invalid unit ref {member!r}")
        fields = _unit_frontmatter(member)
        if fields["worker_type"] not in compat:
            raise TopologyError(
                f"{capability}:{node_id}: unit {member} worker_type {fields['worker_type']} "
                f"incompatible with kind {kind}"
            )
        if kind == "review-worker" and fields["read_only"] != "true":
            raise TopologyError(
                f"{capability}:{node_id}: review-worker unit {member} must declare read_only: true"
            )
    if node.get("role") != _unit_frontmatter(unit)["role"]:
        raise TopologyError(
            f"{capability}:{node_id}: node role {node.get('role')!r} differs from "
            f"unit role {_unit_frontmatter(unit)['role']!r}"
        )


def _validate_gate_contracts(recipe, registry):
    contracts = registry.get("completion_gate_contracts")
    if not isinstance(contracts, dict):
        raise TopologyError("completion_gate_contracts table required")
    node_by_gate = {
        node.get("completion_gate"): node
        for node in recipe["standard_plus"].get("nodes", [])
    }
    for gate in recipe["completion_gates"]:
        entry = contracts.get(gate)
        if not isinstance(entry, dict):
            raise TopologyError(f"{recipe['capability']}: gate {gate} lacks a completion_gate_contracts entry")
        kind = entry.get("kind")
        if kind == "unit-io":
            node = node_by_gate.get(gate)
            if node is None or entry.get("unit") != node.get("unit"):
                raise TopologyError(
                    f"{recipe['capability']}: unit-io gate {gate} must name the carrying node's unit"
                )
        elif kind == "capability-doc":
            contract = entry.get("contract")
            if not contract or not (ROOT / contract).is_file():
                raise TopologyError(
                    f"{recipe['capability']}: capability-doc contract missing for gate {gate}: {contract!r}"
                )
        elif kind == "custom":
            if not entry.get("doc"):
                raise TopologyError(f"{recipe['capability']}: custom gate {gate} requires a recorded reason")
        else:
            raise TopologyError(f"{recipe['capability']}: unknown gate contract kind {kind!r} for {gate}")


def _validate_recipe(recipe, registry):
    required = {"capability", "modes", "topology_class", "direct_predicates", "promotion_signals",
                "quick", "standard_plus", "completion_gates", "human_gates", "resume_retry_boundaries"}
    missing = required - recipe.keys()
    if missing:
        raise TopologyError(f"{recipe.get('capability')}: missing {sorted(missing)}")
    bare_depth_keys = {"depth", "owner_depth", "max_depth"}
    if any(key in recipe for key in bare_depth_keys):
        raise TopologyError(f"{recipe['capability']}: bare recipe dispatch-depth fields are forbidden")
    quick = recipe["quick"]
    if any(key in quick for key in bare_depth_keys):
        raise TopologyError(f"{recipe['capability']}: bare quick dispatch-depth fields are forbidden")
    if quick.get("owner_dispatch_depth") != 1 or quick.get("max_dispatch_depth") != 1:
        raise TopologyError(f"{recipe['capability']}: quick topology must be dispatch depth 1")
    for scope in quick.get("write_scope", []): _scope_root(scope)
    _validate_guard_scope(recipe, quick.get("write_scope", []), quick.get("guard_preconditions", []), registry, "quick")
    graph = recipe["standard_plus"]
    if any(key in graph for key in bare_depth_keys):
        raise TopologyError(f"{recipe['capability']}: bare standard+ dispatch-depth fields are forbidden")
    if graph.get("owner_dispatch_depth") != 1:
        raise TopologyError(f"{recipe['capability']}: owner dispatch depth must be 1")
    nodes = graph.get("nodes", [])
    ids = [n.get("id") for n in nodes]
    if len(ids) != len(set(ids)) or not all(ids):
        raise TopologyError(f"{recipe['capability']}: duplicate/empty node id")
    by_id = {n["id"]: n for n in nodes}
    actual_max_dispatch_depth = max(
        (
            node.get("dispatch_depth", 0)
            for node in nodes
            if node.get("kind") != "resource-runner"
        ),
        default=0,
    )
    if graph.get("max_dispatch_depth") != actual_max_dispatch_depth:
        raise TopologyError(
            f"{recipe['capability']}: max_dispatch_depth must equal "
            f"{actual_max_dispatch_depth}"
        )
    gates = set(recipe["completion_gates"])
    for node in nodes:
        if node.get("kind") not in registry["worker_kinds"]:
            raise TopologyError(f"{recipe['capability']}:{node['id']}: invalid worker kind")
        _validate_unit_ref(recipe, node, registry)
        if node["kind"] == "resource-runner":
            if any(
                key in node
                for key in (
                    "depth", "owner_depth", "max_depth", "dispatch_depth",
                    "transport", "fallback_hops",
                )
            ):
                raise TopologyError(
                    f"{recipe['capability']}:{node['id']}: resource runner lifecycle is not an agent dispatch"
                )
            if node.get("resource_transport") != "detached-process":
                raise TopologyError(
                    f"{recipe['capability']}:{node['id']}: detached resource transport required"
                )
        else:
            if any(key in node for key in bare_depth_keys) or node.get("dispatch_depth") not in (1, 2):
                raise TopologyError(f"{recipe['capability']}:{node['id']}: dispatch_depth must be 1 or 2")
            unknown_hops = set(node.get("fallback_hops", [])) - FALLBACK_HOPS
            if unknown_hops:
                raise TopologyError(
                    f"{recipe['capability']}:{node['id']}: unknown fallback hops {sorted(unknown_hops)}"
                )
        if not node.get("inputs") or not node.get("outputs") or not node.get("write_scope"):
            raise TopologyError(f"{recipe['capability']}:{node['id']}: inputs/outputs/write_scope required")
        if node.get("completion_gate") not in gates:
            raise TopologyError(f"{recipe['capability']}:{node['id']}: missing completion gate")
        if not set(node.get("depends_on", [])) <= set(ids):
            raise TopologyError(f"{recipe['capability']}:{node['id']}: unknown dependency")
        scopes = node["write_scope"]
        for scope in scopes: _scope_root(scope)
        _validate_guard_scope(recipe, scopes, node.get("guard_preconditions", []), registry, node["id"])
        if node["kind"] == "review-worker" and any(not (s.startswith("reviews/") or s.startswith("_internal/")) for s in scopes):
            raise TopologyError(f"{recipe['capability']}:{node['id']}: reviewer may write isolated verdicts only")
        if node["kind"] == "map-worker" and any(not s.startswith("shards/") for s in scopes):
            raise TopologyError(f"{recipe['capability']}:{node['id']}: map worker may write shards only")
    if "replication" in graph:
        raise TopologyError(
            f"{recipe['capability']}: v4 declares replication anchors under 'replications'"
        )
    replications = graph.get("replications")
    if replications is not None:
        # v4 multi-anchor 2-way cross-harness replicate-and-merge (CONVENTIONS
        # §3.12, strengthened 2026-07-21; framing anchors added 2026-07-24 on
        # the user directive that direction-setting points get independent
        # cross-model exploration from `standard`, because early direction
        # errors cascade into hotfix/patch work). The compiler expands each
        # anchor; the registry only names the nodes and the independence axis.
        if not isinstance(replications, list) or not replications:
            raise TopologyError(
                f"{recipe['capability']}: replications must be a non-empty list of anchors"
            )
        required_rep = {"node", "min_intensity", "ways", "independence_axis"}
        anchored = set()
        for replication in replications:
            if not isinstance(replication, dict) or set(replication) != required_rep:
                raise TopologyError(
                    f"{recipe['capability']}: replication anchors require exactly {sorted(required_rep)}"
                )
            if replication["node"] in anchored:
                raise TopologyError(
                    f"{recipe['capability']}: duplicate replication anchor {replication['node']!r}"
                )
            anchored.add(replication["node"])
            target = by_id.get(replication["node"])
            if target is None:
                raise TopologyError(
                    f"{recipe['capability']}: replication node {replication['node']!r} not in graph"
                )
            kind = target.get("kind")
            if kind not in ("review-worker", "map-worker", "pipeline-stage"):
                raise TopologyError(
                    f"{recipe['capability']}: replication target {replication['node']} "
                    "must be a review-worker, map-worker, or pipeline-stage"
                )
            dependents = [n for n in nodes if replication["node"] in n.get("depends_on", [])]
            if kind != "review-worker" and not dependents:
                raise TopologyError(
                    f"{recipe['capability']}: non-review replication anchor "
                    f"{replication['node']} requires a downstream consumer"
                )
            if kind == "pipeline-stage" and not any(
                d.get("kind") == "review-worker" for d in dependents
            ):
                raise TopologyError(
                    f"{recipe['capability']}: pipeline-stage replication anchor "
                    f"{replication['node']} requires a direct review-worker arbiter"
                )
            tiers = registry["intensities"]
            if (replication["min_intensity"] not in tiers
                    or tiers.index(replication["min_intensity"]) < tiers.index("standard")):
                raise TopologyError(
                    f"{recipe['capability']}: replication min_intensity must be a standard+ tier"
                )
            if replication["ways"] != 2:
                raise TopologyError(f"{recipe['capability']}: replication ways must be 2")
            if replication["independence_axis"] != "cross-harness":
                raise TopologyError(
                    f"{recipe['capability']}: replication independence_axis must be cross-harness"
                )
            for out in target.get("outputs", []):
                if "*" not in out:
                    continue
                if kind == "map-worker" and out.endswith("/**") and "*" not in out[:-3]:
                    continue
                raise TopologyError(
                    f"{recipe['capability']}: replication target outputs must be concrete "
                    "files (or a map-worker '<dir>/**' shard tree)"
                )
    visiting, done = set(), set()
    def visit(node_id):
        if node_id in visiting: raise TopologyError(f"{recipe['capability']}: cycle")
        if node_id in done: return
        visiting.add(node_id)
        for dep in by_id[node_id].get("depends_on", []): visit(dep)
        visiting.remove(node_id); done.add(node_id)
    for node_id in ids: visit(node_id)
    ancestors = {}
    def deps(node_id):
        if node_id not in ancestors:
            ancestors[node_id] = set(by_id[node_id].get("depends_on", []))
            for dep in list(ancestors[node_id]): ancestors[node_id] |= deps(dep)
        return ancestors[node_id]
    for i, left in enumerate(nodes):
        for right in nodes[i + 1:]:
            if left["id"] in deps(right["id"]) or right["id"] in deps(left["id"]): continue
            if any(_overlap(a, b) for a in left["write_scope"] for b in right["write_scope"]):
                raise TopologyError(f"{recipe['capability']}: concurrent scope overlap {left['id']}/{right['id']}")
    if not recipe["resume_retry_boundaries"] or not set(recipe["resume_retry_boundaries"]) <= set(ids):
        raise TopologyError(f"{recipe['capability']}: invalid retry boundaries")


def validate_registry(registry, manifest=None):
    if registry.get("schema_version") != 4:
        raise TopologyError("legacy topology registry is read-only")
    if set(registry.get("transports", [])) != WRAPPER_TRANSPORTS:
        raise TopologyError("transport vocabulary differs from portable dispatch contract")
    if set(registry.get("execution_surfaces", [])) != EXECUTION_SURFACES:
        raise TopologyError("execution-surface vocabulary differs from portable dispatch contract")
    if set(registry.get("fallback_hops", [])) != FALLBACK_HOPS:
        raise TopologyError("fallback-hop vocabulary differs from portable dispatch contract")
    if registry.get("tracking_values") != ["tracked", "untracked"]:
        raise TopologyError("tracking_values must declare tracked and untracked independently")
    if set(registry.get("tracked_gate_evidence", [])) != {
        "spec_read", "drift_verdict", "workflow_mode", "artifact_guard"
    }:
        raise TopologyError("tracked_gate_evidence must contain the four SD-45 fields")
    if "artifact-order-prechecked" not in registry.get("guard_preconditions", []):
        raise TopologyError("artifact-order-prechecked guard precondition missing")
    if registry.get("artifact_owners", {}).get("spec") != "autopilot-spec":
        raise TopologyError("spec sole-update-path owner must be autopilot-spec")
    if registry.get("rollout", {}).get("route_compiler") != "enforced":
        raise TopologyError("route compiler rollout must be enforced")
    if "legacy_low_level_dispatch" in registry.get("rollout", {}):
        raise TopologyError("legacy_low_level_dispatch is retired")
    actual, expected = recipe_keys(registry), expected_recipe_keys(manifest)
    if actual != expected:
        raise TopologyError(f"coverage mismatch missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
    for recipe in registry["recipes"]:
        _validate_recipe(recipe, registry)
        _validate_gate_contracts(recipe, registry)
    return {"capabilities": len({x[0] for x in actual}), "recipes": len(actual), "registry_digest": registry_digest(registry)}


def resolve_recipe(registry, capability, capability_mode="default"):
    for recipe in registry["recipes"]:
        if recipe["capability"] == capability and capability_mode in recipe["modes"]:
            return recipe
    raise TopologyError(f"unknown capability/mode: {capability}/{capability_mode}")


def capability_summary(registry, capability):
    rows = [r for r in registry["recipes"] if r["capability"] == capability]
    if not rows: raise TopologyError(f"unknown capability: {capability}")
    return {"topology_registry": "capabilities/topologies.json", "registry_digest": registry_digest(registry),
            "capability_modes": sorted({m for r in rows for m in r["modes"]}),
            "topology_classes": sorted({r["topology_class"] for r in rows})}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=("validate", "summary", "digest")); parser.add_argument("--capability")
    args = parser.parse_args(); registry = load_registry()
    if args.command == "validate": output = validate_registry(registry)
    elif args.command == "digest": output = {"registry_digest": registry_digest(registry)}
    else: output = capability_summary(registry, args.capability or "")
    for key, value in output.items(): print(f"{key}={','.join(value) if isinstance(value, list) else value}")


if __name__ == "__main__": main()
