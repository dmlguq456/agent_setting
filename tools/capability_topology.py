#!/usr/bin/env python3
"""Validate and query the portable capability execution-topology registry."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "capabilities" / "topologies.json"
MANIFEST = ROOT / "harness-manifest.json"


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


def _validate_recipe(recipe, registry):
    required = {"capability", "modes", "topology_class", "direct_predicates", "promotion_signals",
                "quick", "standard_plus", "completion_gates", "human_gates", "resume_retry_boundaries"}
    missing = required - recipe.keys()
    if missing:
        raise TopologyError(f"{recipe.get('capability')}: missing {sorted(missing)}")
    quick = recipe["quick"]
    if quick.get("owner_depth") != 1 or quick.get("max_depth") != 1:
        raise TopologyError(f"{recipe['capability']}: quick topology must be depth 1")
    for scope in quick.get("write_scope", []): _scope_root(scope)
    graph = recipe["standard_plus"]
    if graph.get("owner_depth") != 1:
        raise TopologyError(f"{recipe['capability']}: owner depth must be 1")
    nodes = graph.get("nodes", [])
    ids = [n.get("id") for n in nodes]
    if len(ids) != len(set(ids)) or not all(ids):
        raise TopologyError(f"{recipe['capability']}: duplicate/empty node id")
    by_id = {n["id"]: n for n in nodes}
    gates = set(recipe["completion_gates"])
    for node in nodes:
        if node.get("kind") not in registry["worker_kinds"]:
            raise TopologyError(f"{recipe['capability']}:{node['id']}: invalid worker kind")
        if node["kind"] == "resource-runner":
            if "depth" in node or node.get("transport") != ["detached-process"]:
                raise TopologyError(f"{recipe['capability']}:{node['id']}: resource runner is detached, not an agent depth")
        elif node.get("depth") not in (1, 2):
            raise TopologyError(f"{recipe['capability']}:{node['id']}: depth must be 1 or 2")
        if not node.get("inputs") or not node.get("outputs") or not node.get("write_scope"):
            raise TopologyError(f"{recipe['capability']}:{node['id']}: inputs/outputs/write_scope required")
        if node.get("completion_gate") not in gates:
            raise TopologyError(f"{recipe['capability']}:{node['id']}: missing completion gate")
        if not set(node.get("depends_on", [])) <= set(ids):
            raise TopologyError(f"{recipe['capability']}:{node['id']}: unknown dependency")
        scopes = node["write_scope"]
        for scope in scopes: _scope_root(scope)
        if node["kind"] == "review-worker" and any(not (s.startswith("reviews/") or s.startswith("_internal/")) for s in scopes):
            raise TopologyError(f"{recipe['capability']}:{node['id']}: reviewer may write isolated verdicts only")
        if node["kind"] == "map-worker" and any(not s.startswith("shards/") for s in scopes):
            raise TopologyError(f"{recipe['capability']}:{node['id']}: map worker may write shards only")
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
    actual, expected = recipe_keys(registry), expected_recipe_keys(manifest)
    if actual != expected:
        raise TopologyError(f"coverage mismatch missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
    for recipe in registry["recipes"]: _validate_recipe(recipe, registry)
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
