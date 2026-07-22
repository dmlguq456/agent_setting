#!/usr/bin/env python3
"""Assemble a compose-on-demand route for a capability that owns no registry recipe.

`pre`/`ops` capabilities (analyze-project, analyze-user, audit) are not `entry`
group, so `capabilities/topologies.json` carries no recipe for them. Their only
dispatch path is compose-on-demand: a full-shape recipe plus checked dispatch
evidence, compiled through the SAME validate/seal path as a registry recipe
(`capability-route.py compile --composed-recipe`).

This helper is the ASSEMBLY SHELL only. It turns a unit list into a full-shape
recipe, assembles dispatch evidence from the nested-eligibility probe (or a
caller-supplied file), and delegates to `capability-route.py compile`. It never
re-implements recipe validation or route sealing -- those stay owned by
`compile_composed_route`, so a malformed assembly fails closed at compile.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNITS = ROOT / "roles" / "units"
COMPILE = ROOT / "utilities" / "capability-route.py"
PROBE = ROOT / "utilities" / "nested-dispatch-eligibility.py"

# Portable predicate/signal/hop vocabularies (mirrors the registry recipes). The
# route compiler re-validates every one of these, so a drift here fails closed.
STANDARD_DIRECT_PREDICATES = [
    "atomic-outcome", "known-scope", "no-shared-contract", "no-resource-run",
    "no-artifact-handoff", "no-independent-verifier", "focused-verification",
]
STANDARD_PROMOTION_SIGNALS = [
    "source-fanout", "artifact-fanout", "claim-verification", "independent-verifier",
]
STANDARD_FALLBACK_HOPS = [
    "same-harness-headless", "cross-harness-headless", "native-subagent", "inline",
]
# Default kind per unit worker_type; `owner` has no composed-node kind (reserved
# units only), so it must be set explicitly and will fail closed at compile.
WORKER_TYPE_DEFAULT_KIND = {
    "stage": "pipeline-stage", "support": "pipeline-stage", "review": "review-worker",
}


def _load_topology():
    spec = importlib.util.spec_from_file_location("capability_topology", ROOT / "tools/capability_topology.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _scope_touches_spec(scope: str) -> bool:
    root = scope[:-3] if scope.endswith("/**") else scope
    return root == "spec" or root.startswith("spec/")


def _unit_meta(unit: str) -> dict:
    """Read the role/worker_type the node needs from the unit frontmatter.

    role is derived here (never taken from the caller) because the compiler
    requires node.role to equal the unit's declared role; a caller-supplied role
    would only be a second, mismatchable copy.
    """
    if not re.fullmatch(r"[a-z0-9-]+/[a-z0-9-]+", unit or ""):
        raise ValueError(f"invalid unit ref {unit!r} (expected <family>/<name>)")
    path = UNITS / f"{unit}.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        raise ValueError(f"unknown unit: {unit} (no roles/units/{unit}.md)")
    match = re.match(r"\A---\n(.*?\n)---\n", text, re.DOTALL)
    if not match:
        raise ValueError(f"unit {unit}: missing frontmatter block")
    block = match.group(1)

    def scalar(name: str):
        found = re.search(rf"^{name}:\s*([^#\n]+?)\s*(?:#.*)?$", block, re.MULTILINE)
        return found.group(1).strip() if found else None

    role = scalar("role")
    if not role:
        raise ValueError(f"unit {unit}: frontmatter role required")
    return {"role": role, "worker_type": scalar("worker_type"), "read_only": scalar("read_only")}


def unit_io_gate_index(registry) -> dict:
    """Map each unit to the unit-io completion gates that name it (for auto-derive)."""
    index: dict = {}
    for gate, entry in (registry.get("completion_gate_contracts") or {}).items():
        if isinstance(entry, dict) and entry.get("kind") == "unit-io" and entry.get("unit"):
            index.setdefault(entry["unit"], []).append(gate)
    for unit in index:
        index[unit] = sorted(index[unit])
    return index


def _derive_gate(node_id: str, unit: str, gate_index: dict) -> str:
    candidates = gate_index.get(unit, [])
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise ValueError(
            f"node {node_id}: unit {unit} has no unit-io gate to auto-derive; set 'gate' explicitly"
        )
    raise ValueError(
        f"node {node_id}: unit {unit} maps to multiple gates {candidates}; set 'gate' explicitly"
    )


def build_recipe(capability, capability_mode, unit_specs, *, topology_class, quick_write_scope, gate_index):
    """Turn the unit list into a full-shape composed recipe (compile validates it)."""
    if not isinstance(unit_specs, list) or not unit_specs:
        raise ValueError("compose requires a non-empty unit list")
    ids = [u.get("id") for u in unit_specs]
    if not all(ids):
        raise ValueError("every unit node requires an id")
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate node id in unit list")
    scope_by_id = {
        u["id"]: list(u["write_scope"]) for u in unit_specs if u.get("write_scope")
    }
    nodes = []
    for spec in unit_specs:
        node_id = spec["id"]
        unit = spec.get("unit")
        if not unit:
            raise ValueError(f"node {node_id}: unit ref required")
        write_scope = spec.get("write_scope")
        if not isinstance(write_scope, list) or not write_scope:
            raise ValueError(f"node {node_id}: non-empty write_scope required")
        meta = _unit_meta(unit)
        kind = spec.get("kind") or WORKER_TYPE_DEFAULT_KIND.get(meta["worker_type"])
        if not kind:
            raise ValueError(
                f"node {node_id}: cannot derive kind for unit {unit} "
                f"(worker_type={meta['worker_type']!r}); set 'kind' explicitly"
            )
        gate = spec.get("gate") or _derive_gate(node_id, unit, gate_index)
        depends_on = list(spec.get("depends_on", []))
        if spec.get("inputs"):
            inputs = list(spec["inputs"])
        elif depends_on:
            inputs = sorted({s for dep in depends_on for s in scope_by_id.get(dep, [])}) or ["task"]
        else:
            inputs = ["task"]
        node = {
            "id": node_id,
            "kind": kind,
            "unit": unit,
            "role": meta["role"],
            "dispatch_depth": 2,
            "depends_on": depends_on,
            "inputs": inputs,
            "outputs": list(spec.get("outputs") or write_scope),
            "write_scope": list(write_scope),
            "resource_class": spec.get("resource_class", "normal"),
            "completion_gate": gate,
            "fallback_hops": list(STANDARD_FALLBACK_HOPS),
        }
        if spec.get("unit_choices"):
            node["unit_choices"] = list(spec["unit_choices"])
        if spec.get("guard_preconditions"):
            node["guard_preconditions"] = list(spec["guard_preconditions"])
        nodes.append(node)

    if not quick_write_scope:
        quick_write_scope = sorted(
            {s for node in nodes for s in node["write_scope"] if not _scope_touches_spec(s)}
        )
        if not quick_write_scope:
            raise ValueError("every node scope touches spec/; pass --quick-write-scope explicitly")

    return {
        "capability": capability,
        "modes": [capability_mode],
        "topology_class": topology_class,
        "direct_predicates": list(STANDARD_DIRECT_PREDICATES),
        "promotion_signals": list(STANDARD_PROMOTION_SIGNALS),
        "quick": {
            "topology": "one-shot-owner",
            "worker_kind": "capability-owner",
            "write_scope": list(quick_write_scope),
            "owner_dispatch_depth": 1,
            "max_dispatch_depth": 1,
        },
        "standard_plus": {
            "owner_dispatch_depth": 1,
            "max_dispatch_depth": 2,
            "nodes": nodes,
        },
        "completion_gates": sorted({node["completion_gate"] for node in nodes}),
        "human_gates": [],
        "resume_retry_boundaries": list(ids),
    }


def probe_child(child, *, parent_harness, parent_transport, parent_sandbox, launch_authority, worktree) -> dict:
    """Run the nested-eligibility probe for one child harness and return its tuple.

    The probe prints its checked tuple on both supported (exit 0) and probed-
    unsupported (exit 69); either is real evidence and is collected verbatim.
    Only a non-JSON result is a hard error -- the status is never rewritten here.
    """
    command = [
        sys.executable, str(PROBE),
        "--parent-harness", parent_harness,
        "--parent-transport", parent_transport,
        "--parent-sandbox", parent_sandbox,
        "--child-harness", child,
        "--launch-authority", launch_authority,
        "--worktree", str(worktree),
        "--json",
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        detail = (result.stderr or result.stdout).strip()
        raise ValueError(f"nested-eligibility probe failed for child {child}: {detail or 'no output'}")


def assemble_dispatch_evidence(args) -> dict:
    """Caller-supplied evidence passes through; otherwise probe each child live."""
    if args.dispatch_evidence:
        return json.loads(Path(args.dispatch_evidence).read_text(encoding="utf-8"))
    children = args.probe_child or ["claude"]
    tuples = [
        probe_child(
            child,
            parent_harness=args.probe_parent_harness,
            parent_transport=args.probe_parent_transport,
            parent_sandbox=args.probe_parent_sandbox,
            launch_authority=args.launch_authority,
            worktree=args.probe_worktree or args.cwd,
        )
        for child in children
    ]
    native = json.loads(Path(args.native_evidence).read_text(encoding="utf-8")) if args.native_evidence else []
    return {"tuples": tuples, "native_subagent": native}


def run_compile(args, recipe, evidence) -> str:
    """Write recipe/evidence to a scratch dir and delegate to the route compiler."""
    with tempfile.TemporaryDirectory(prefix="compose-route-") as tmp:
        recipe_path = Path(tmp) / "recipe.json"
        evidence_path = Path(tmp) / "evidence.json"
        recipe_path.write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        evidence_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        command = [
            sys.executable, str(COMPILE), "compile",
            "--capability", args.capability,
            "--capability-mode", args.capability_mode,
            "--intensity", args.intensity,
            "--cwd", args.cwd,
            "--artifact-root", args.artifact_root,
            "--composed-recipe", str(recipe_path),
            "--dispatch-evidence", str(evidence_path),
            "--tracking", args.tracking,
            "--spec-read", args.spec_read,
            "--drift-verdict", args.drift_verdict,
            "--workflow-mode", args.workflow_mode,
            "--artifact-guard", args.artifact_guard,
            "--transport-evidence", args.transport_evidence,
        ]
        for signal in args.signal:
            command += ["--signal", signal]
        for predicate in args.predicate:
            command += ["--predicate", predicate]
        if args.output:
            command += ["--output", args.output]
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            sys.stderr.write(result.stderr)
            raise SystemExit(result.returncode)
        return result.stdout


def _parse_units(args) -> list:
    if bool(args.units) == bool(args.units_json):
        raise ValueError("provide exactly one of --units <file> or --units-json <json>")
    raw = Path(args.units).read_text(encoding="utf-8") if args.units else args.units_json
    parsed = json.loads(raw)
    units = parsed.get("units") if isinstance(parsed, dict) else parsed
    if not isinstance(units, list):
        raise ValueError("units must be a JSON list (or an object with a 'units' list)")
    return units


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capability", required=True)
    parser.add_argument("--capability-mode", required=True)
    parser.add_argument("--units", help="JSON file: a list of node specs (or {\"units\": [...]})")
    parser.add_argument("--units-json", help="inline JSON node-spec list (alternative to --units)")
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--intensity", default="standard")
    parser.add_argument("--topology-class", default="staged")
    parser.add_argument("--quick-write-scope", action="append", default=[])
    parser.add_argument("--signal", action="append", default=[])
    parser.add_argument("--predicate", action="append", default=[])
    parser.add_argument("--transport-evidence", default="caller-selected")
    parser.add_argument("--output", help="sealed route path (compiler write-once)")
    # Tracked gate evidence -- the caller states these; this tool never fabricates them.
    parser.add_argument("--tracking", required=True, choices=("tracked", "untracked"))
    parser.add_argument("--spec-read", required=True)
    parser.add_argument("--drift-verdict", required=True)
    parser.add_argument("--workflow-mode", required=True, choices=("tracked", "untracked"))
    parser.add_argument("--artifact-guard", required=True)
    # Dispatch evidence: caller-supplied file, or live probe of each child harness.
    parser.add_argument("--dispatch-evidence", help="checked dispatch evidence JSON (skips the live probe)")
    parser.add_argument("--native-evidence", help="native_subagent evidence JSON list (probe path only)")
    parser.add_argument("--probe-parent-harness", default="claude", choices=("claude", "codex", "opencode"))
    parser.add_argument("--probe-parent-transport", default="headless")
    parser.add_argument("--probe-parent-sandbox", default="workspace-write")
    parser.add_argument("--probe-child", action="append", default=[], choices=("claude", "codex", "opencode"))
    parser.add_argument("--probe-worktree")
    parser.add_argument("--launch-authority", default="conductor", choices=("conductor", "ancestor-broker"))
    args = parser.parse_args()

    topology = _load_topology()
    registry = topology.load_registry()
    unit_specs = _parse_units(args)
    recipe = build_recipe(
        args.capability, args.capability_mode, unit_specs,
        topology_class=args.topology_class,
        quick_write_scope=args.quick_write_scope,
        gate_index=unit_io_gate_index(registry),
    )
    evidence = assemble_dispatch_evidence(args)
    route_json = run_compile(args, recipe, evidence)

    route = json.loads(route_json)
    summary = (
        f"compose-route: sealed {route['route_id']} "
        f"({args.capability}/{args.capability_mode}, {len(recipe['standard_plus']['nodes'])} nodes, "
        f"effective={route['effective_intensity']})"
    )
    if args.output:
        summary += f" -> {args.output}"
    print(summary, file=sys.stderr)
    sys.stdout.write(route_json)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"compose-route: {exc}", file=sys.stderr)
        raise SystemExit(64)
