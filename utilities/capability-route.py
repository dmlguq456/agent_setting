#!/usr/bin/env python3
"""Compile, verify, and complete immutable capability routes."""
from __future__ import annotations
import argparse, contextlib, fcntl, hashlib, importlib.util, json, os, re, subprocess, sys, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("capability_topology", ROOT/"tools/capability_topology.py")
TOPO = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(TOPO)
DEFAULTS_SPEC = importlib.util.spec_from_file_location("dispatch_defaults", ROOT/"utilities/dispatch-defaults.py")
DEFAULTS = importlib.util.module_from_spec(DEFAULTS_SPEC); DEFAULTS_SPEC.loader.exec_module(DEFAULTS)
VALID_AFFINITY = DEFAULTS.AFFINITY_VALUES | {"unspecified"}
sys.path.insert(0, str(ROOT/"utilities"))
from dispatch_contract import (
    CANONICAL_PARENT_TRANSPORTS,
    DispatchContractError,
    EXECUTION_SURFACES,
    FALLBACK_HOPS,
    WRAPPER_TRANSPORTS,
    _atomic_registry_replace,
    ensure_global_registry_writable,
    parse_registry_metadata,
    resolve_agent_home,
    validate_attempt_metadata,
)
ORDER = {"direct":0,"quick":1,"standard":2,"strong":3,"thorough":4,"adversarial":5}
TRACKING = {"tracked", "untracked"}
GATE_FIELDS = {"spec_read", "drift_verdict", "workflow_mode", "artifact_guard"}
NESTED_STATUSES = {"supported", "unsupported", "unknown"}
NESTED_FIELDS = {
    "parent_harness", "parent_transport", "parent_sandbox", "child_harness",
    "launch_authority", "status", "probe_source", "probe_time", "failure_class",
}
BROKER_FIELDS = {"broker_root", "broker_instance"}  # historical v1
BROKER_FIELDS_V2 = {"broker_root"}                   # historical v2
DISPATCH_CONTRACT_VERSION = 3
FALLBACK_ORDER = ["same-harness-headless", "cross-harness-headless", "native-subagent", "inline"]
ROUTE_SCHEMA_VERSION = 2
REGISTERED_HEADLESS_EVIDENCE_FIELDS = {
    "harness", "transport", "surface", "status", "probe_source", "probe_time",
}
REGISTERED_HEADLESS_STATUSES = {"supported", "unsupported", "unknown"}
REGISTERED_HEADLESS_HARNESSES = {"claude", "codex", "opencode"}
NATIVE_SURFACES = {
    "codex": "codex-native-subagent",
    "claude": "claude-subagent",
}
NATIVE_EVIDENCE_FIELDS = {
    "harness",
    "transport",
    "execution_surface",
    "registered_worker",
    "status",
    "check_source",
}


def _validate_registered_headless_evidence(evidence):
    """Normalize quick eligibility; every invalid/empty case has one failure enum."""

    if not isinstance(evidence, dict):
        raise ValueError("quick-headless-unavailable")
    candidates = evidence.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("quick-headless-unavailable")
    normalized = []
    seen_harnesses = set()
    for row in candidates:
        if not isinstance(row, dict) or not REGISTERED_HEADLESS_EVIDENCE_FIELDS.issubset(row):
            raise ValueError("quick-headless-unavailable")
        if row["status"] not in REGISTERED_HEADLESS_STATUSES:
            raise ValueError("quick-headless-unavailable")
        if row["transport"] != "headless" or row["surface"] != "registered-headless":
            raise ValueError("quick-headless-unavailable")
        if row["harness"] not in REGISTERED_HEADLESS_HARNESSES:
            raise ValueError("quick-headless-unavailable")
        if row["harness"] in seen_harnesses:
            raise ValueError("quick-headless-unavailable")
        if not row["probe_source"] or not row["probe_time"]:
            raise ValueError("quick-headless-unavailable")
        seen_harnesses.add(row["harness"])
        normalized.append({key: row[key] for key in sorted(REGISTERED_HEADLESS_EVIDENCE_FIELDS)})
    if not any(row["status"] == "supported" for row in normalized):
        raise ValueError("quick-headless-unavailable")
    return sorted(normalized, key=lambda row: row["harness"])

def canonical(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",",":")).encode()

def route_hash(payload):
    bare={k:v for k,v in payload.items() if k not in ("route_hash","route_id")}
    return "sha256:"+hashlib.sha256(canonical(bare)).hexdigest()

def _git_commit(cwd):
    p=subprocess.run(["git","-C",str(cwd),"rev-parse","HEAD"],text=True,capture_output=True)
    return p.stdout.strip() if p.returncode == 0 else "unversioned"

def _validate_tracking_evidence(tracking, evidence):
    if tracking not in TRACKING: raise ValueError("invalid tracking value")
    if not isinstance(evidence, dict) or set(evidence) != GATE_FIELDS:
        raise ValueError("tracked gate evidence requires spec_read, drift_verdict, workflow_mode, artifact_guard")
    if evidence["workflow_mode"] != tracking:
        raise ValueError("tracked gate workflow_mode mismatch")
    if not isinstance(evidence["drift_verdict"], str) or not evidence["drift_verdict"]:
        raise ValueError("tracked gate drift_verdict required")
    for name in ("spec_read", "artifact_guard"):
        row=evidence[name]
        if not isinstance(row, dict) or not isinstance(row.get("satisfied"), bool) or not row.get("source"):
            raise ValueError(f"tracked gate {name} requires satisfied boolean and source")
        if tracking=="tracked" and not row["satisfied"]:
            raise ValueError(f"tracked gate {name} must be satisfied")
    return evidence

def _scope_touches_spec(scope):
    root=scope[:-3] if scope.endswith("/**") else scope
    return root=="spec" or root.startswith("spec/")

def _validate_dispatch_evidence(evidence, contract_version=DISPATCH_CONTRACT_VERSION):
    contract_version = contract_version or 1
    if contract_version not in {1, 2, DISPATCH_CONTRACT_VERSION}:
        raise ValueError(f"unsupported dispatch contract version: {contract_version}")
    if not isinstance(evidence,dict): raise ValueError("checked dispatch evidence required")
    tuples=evidence.get("tuples")
    if not isinstance(tuples,list) or not tuples: raise ValueError("nested eligibility tuples required")
    normalized=[]
    for row in tuples:
        if not isinstance(row,dict) or not NESTED_FIELDS.issubset(row):
            raise ValueError("nested eligibility tuple fields missing")
        if row["status"] not in NESTED_STATUSES: raise ValueError("invalid nested eligibility status")
        if row["launch_authority"] not in ("conductor","ancestor-broker"):
            raise ValueError("invalid nested launch authority")
        if not row["probe_source"] or not row["probe_time"]:
            raise ValueError("nested eligibility checked source/time required")
        normalized_row={key:row[key] for key in sorted(NESTED_FIELDS)}
        if contract_version==DISPATCH_CONTRACT_VERSION:
            if row["launch_authority"] != "conductor":
                raise ValueError("v3 dispatch evidence requires conductor launch authority")
            if row["parent_transport"] not in CANONICAL_PARENT_TRANSPORTS:
                raise ValueError("v3 dispatch evidence requires canonical parent transport")
            if any(row.get(key) for key in BROKER_FIELDS):
                raise ValueError("v3 dispatch evidence must not carry broker fields")
        elif contract_version==2:
            if row.get("launch_authority")=="ancestor-broker" and row.get("status")=="supported" and not row.get("broker_root"):
                raise ValueError("v2 dispatch evidence requires broker_root")
            if row.get("broker_root"):
                normalized_row["broker_root"]=row["broker_root"]
            # broker_instance is mutable rollover identity -- v2 strips it
            # even if the caller's probe output still carries one.
        else:
            for key in BROKER_FIELDS:
                if key in row:
                    normalized_row[key]=row[key]
        normalized.append(normalized_row)
    native=evidence.get("native_subagent",[])
    if not isinstance(native,list): raise ValueError("native_subagent evidence must be a list")
    normalized_native=[]
    for row in native:
        if not isinstance(row,dict) or not NATIVE_EVIDENCE_FIELDS.issubset(row):
            raise ValueError("invalid native subagent evidence")
        harness=row.get("harness")
        if (
            row.get("status") not in NESTED_STATUSES
            or harness not in NATIVE_SURFACES
            or row.get("execution_surface") != NATIVE_SURFACES[harness]
            or row.get("transport") != "headless"
            or row.get("registered_worker") is not False
            or not row.get("check_source")
        ):
            raise ValueError("invalid native subagent evidence")
        normalized_native.append({key:row[key] for key in sorted(NATIVE_EVIDENCE_FIELDS)})
    return {"tuples":normalized,"native_subagent":normalized_native}

def _fallback_chain(evidence, contract_version=DISPATCH_CONTRACT_VERSION):
    contract_version = contract_version or 1
    evidence=_validate_dispatch_evidence(evidence, contract_version)
    tuples=evidence["tuples"]
    same=[row for row in tuples if row["child_harness"]==row["parent_harness"]]
    cross=[row for row in tuples if row["child_harness"]!=row["parent_harness"]]
    if contract_version==DISPATCH_CONTRACT_VERSION:
        same=[row for row in same if row["launch_authority"]=="conductor"]
        cross=[row for row in cross if row["launch_authority"]=="conductor"]
        has_direct=any(row["status"]=="supported" for row in same+cross)
        if not has_direct:
            raise ValueError("no supported direct headless tuple")
    elif contract_version==2:
        has_broker=any(
            row["status"]=="supported" and row["launch_authority"]=="ancestor-broker" and row.get("broker_root")
            for row in same+cross
        )
        if not has_broker:
            raise ValueError("no supported registered-headless launch tuple")
    else:
        has_broker=any(
            row["status"]=="supported" and row["launch_authority"]=="ancestor-broker"
            and row.get("broker_root") and row.get("broker_instance")
            for row in same+cross
        )
        if not has_broker:
            raise ValueError("no supported registered-headless launch tuple")
    return [
        {"ordinal":1,"fallback_hop":"same-harness-headless","candidates":same},
        {"ordinal":2,"fallback_hop":"cross-harness-headless","candidates":cross},
        {"ordinal":3,"fallback_hop":"native-subagent","candidates":evidence["native_subagent"],"fleet_visibility":"degraded"},
        {"ordinal":4,"fallback_hop":"inline","status":"eligible-after-prior-hop-exhaustion","reason_enum":"runtime-unavailable","fleet_visibility":"none"},
    ]

def _verify_fallback_chain(node, contract_version=None):
    contract_version = contract_version or 1
    chain=node.get("fallback_hops")
    if not isinstance(chain,list) or [row.get("fallback_hop") for row in chain] != FALLBACK_ORDER:
        raise ValueError(f"dispatch-depth-2 node {node.get('id')} missing ordered dispatch fallback")
    candidates=[candidate for row in chain[:2] for candidate in row.get("candidates",[])]
    if contract_version==DISPATCH_CONTRACT_VERSION:
        supported=[c for c in candidates if c.get("status")=="supported" and c.get("launch_authority")=="conductor"]
        if not supported:
            raise ValueError(f"dispatch-depth-2 node {node.get('id')} lacks supported direct headless tuple")
        if any(c.get("broker_root") or c.get("broker_instance") for c in candidates):
            raise ValueError(f"dispatch-depth-2 node {node.get('id')} v3 candidate carries retired broker fields")
    elif contract_version==1:
        supported=[c for c in candidates if c.get("status")=="supported" and c.get("launch_authority")=="ancestor-broker"]
        if not any(c.get("broker_root") and c.get("broker_instance") for c in supported):
            raise ValueError(f"dispatch-depth-2 node {node.get('id')} lacks supported dispatch-depth-0 broker tuple")
    elif contract_version==2:
        supported=[c for c in candidates if c.get("status")=="supported" and c.get("launch_authority")=="ancestor-broker"]
        if not any(c.get("broker_root") for c in supported):
            raise ValueError(f"dispatch-depth-2 node {node.get('id')} lacks supported dispatch-depth-0 broker tuple")
        if any(c.get("broker_instance") for c in supported):
            raise ValueError(f"dispatch-depth-2 node {node.get('id')} v2 candidate must not carry broker_instance")
    else:
        if not supported:
            raise ValueError(f"dispatch-depth-2 node {node.get('id')} lacks supported dispatch-depth-0 broker tuple")
    return chain

def _seal_dispatch_defaults(nodes, capability):
    """Return dispatch_defaults_digest and stamp each dispatch-depth-2 node's
    harness_affinity, BEFORE route_hash is computed. Absent config -> all
    'unspecified' + digest None. Corrupt config -> fail-loud (reused loader
    validator), surfaced as ValueError so main() exits 64. registry_digest is
    a separate field and is never touched here."""
    config_path = DEFAULTS.default_config_path()
    if not os.path.exists(config_path):
        for node in nodes:
            if node.get("dispatch_depth") == 2:
                node["harness_affinity"] = "unspecified"
        return None
    try:
        cfg = DEFAULTS.load_and_validate(config_path, DEFAULTS.default_topology_path())
    except DEFAULTS.DefaultsConfigError as exc:
        raise ValueError(f"corrupt dispatch-defaults config: {exc}")
    for node in nodes:
        if node.get("dispatch_depth") == 2:
            node["harness_affinity"] = DEFAULTS.query_stage_affinity(cfg, capability, node["id"])
    return "sha256:" + hashlib.sha256(canonical(cfg)).hexdigest()

def unit_catalog_digest(units_root=None):
    """Digest of unit frontmatter blocks (machine contracts); unit BODY prose stays un-hashed."""
    units_root=Path(units_root) if units_root else ROOT/"roles"/"units"
    blocks=[]
    for path in sorted(units_root.glob("*/*.md")):
        if path.name.startswith("_"): continue
        match=re.match(r"\A---\n.*?\n---\n", path.read_text(encoding="utf-8"), re.DOTALL)
        if match: blocks.append(f"{path.relative_to(units_root)}\n{match.group(0)}")
    return "sha256:"+hashlib.sha256("\n".join(blocks).encode()).hexdigest()

def compile_route(capability, capability_mode, requested_intensity, cwd, artifact_root,
                  predicates=(), signals=(), transport=None,
                  transport_evidence="caller-selected", inline_reason=None,
                  tracking="tracked", tracked_gate_evidence=None, dispatch_evidence=None,
                  registered_headless_evidence=None):
    registry=TOPO.load_registry(); TOPO.validate_registry(registry)
    recipe=TOPO.resolve_recipe(registry, capability, capability_mode)
    return _compile_from_recipe(
        registry, recipe, capability, capability_mode, requested_intensity, cwd, artifact_root,
        predicates=predicates, signals=signals, transport=transport,
        transport_evidence=transport_evidence, inline_reason=inline_reason,
        tracking=tracking, tracked_gate_evidence=tracked_gate_evidence,
        dispatch_evidence=dispatch_evidence,
        registered_headless_evidence=registered_headless_evidence)

def compile_composed_route(composed_recipe, capability_mode, requested_intensity, cwd, artifact_root,
                           **kwargs):
    """Compile a compose-on-demand recipe through the SAME validate/seal path (composed: true)."""
    registry=TOPO.load_registry(); TOPO.validate_registry(registry)
    if not isinstance(composed_recipe, dict): raise ValueError("composed recipe must be an object")
    TOPO._validate_recipe(composed_recipe, registry)
    # SAME validator means gates too: without this, a composed recipe could carry a
    # forged completion gate that no registry contract backs (2026-07-22 verify finding).
    TOPO._validate_gate_contracts(composed_recipe, registry)
    if capability_mode not in composed_recipe.get("modes", []):
        raise ValueError("composed recipe does not declare the requested capability mode")
    return _compile_from_recipe(
        registry, composed_recipe, composed_recipe["capability"], capability_mode,
        requested_intensity, cwd, artifact_root, composed=True, **kwargs)

def _compile_from_recipe(registry, recipe, capability, capability_mode, requested_intensity,
                         cwd, artifact_root, predicates=(), signals=(), transport=None,
                         transport_evidence="caller-selected", inline_reason=None,
                         tracking="tracked", tracked_gate_evidence=None, dispatch_evidence=None,
                         registered_headless_evidence=None, composed=False):
    cwd=Path(cwd).resolve(strict=True); artifact=Path(artifact_root).resolve()
    if not cwd.is_absolute() or not artifact.is_absolute(): raise ValueError("cwd and artifact root must be absolute")
    known_pred=set(recipe["direct_predicates"]); predicates=sorted(set(predicates))
    unknown=set(predicates)-known_pred
    if unknown: raise ValueError("unknown predicates: "+",".join(sorted(unknown)))
    signals=sorted(set(signals))
    if set(signals) & TRACKING: raise ValueError("tracking cannot be an escalation signal")
    unknown=set(signals)-set(recipe["promotion_signals"])
    if unknown: raise ValueError("unknown promotion signals: "+",".join(sorted(unknown)))
    requested="standard" if requested_intensity=="auto" else requested_intensity
    if requested not in ORDER: raise ValueError("invalid intensity")
    if transport is not None and transport not in WRAPPER_TRANSPORTS:
        raise ValueError(f"invalid transport: {transport!r}")
    inferred="standard" if signals else ("direct" if set(predicates)==known_pred else "quick")
    effective=max((requested,inferred),key=ORDER.get)
    if composed and effective in ("direct","quick"):
        raise ValueError("composed routes require a standard+ effective intensity")
    registered_headless_candidates=None
    if effective=="direct":
        transport="interactive"
        if inline_reason is None: inline_reason="atomic-direct"
        nodes=[{"id":"inline","kind":"capability-owner","dispatch_depth":0,"role":"orchestrator",
                "write_scope":recipe["quick"]["write_scope"],"resource_class":"normal",
                "execution_surface":"inline","registered_worker":False,
                "completion_gate":"inline-complete"}]
        gates=["inline-complete"]
        selection_basis=[{"axis":"direct-predicate","signal":p,"source":"caller"} for p in predicates]
    elif effective=="quick":
        if transport not in (None, "headless"):
            raise ValueError(f"invalid quick transport: {transport!r}")
        registered_headless_candidates=_validate_registered_headless_evidence(
            registered_headless_evidence
        )
        transport="headless"
        nodes=[{"id":"one-shot","kind":recipe["quick"]["worker_kind"],"dispatch_depth":1,"role":"orchestrator",
                "write_scope":recipe["quick"]["write_scope"],"resource_class":"normal",
                "execution_surface":"registered-headless","registered_worker":True,
                "completion_gate":"quick-complete"}]
        gates=["quick-complete"]
        selection_basis=[{"axis":"direct-predicate-gap","signal":p,"source":"compiler"} for p in sorted(known_pred-set(predicates))]
    else:
        if transport not in (None, "headless"):
            raise ValueError(f"invalid standard+ transport: {transport!r}")
        transport="headless"
        nodes=json.loads(json.dumps(recipe["standard_plus"]["nodes"])); gates=recipe["completion_gates"]
        for node in nodes:
            node.pop("fallback_hops", None)
        selection_basis=[{"axis":"promotion","signal":s,"source":"caller"} for s in signals]
    if effective != "direct" and inline_reason is not None:
        raise ValueError("inline_reason only applies to direct")
    if effective=="direct" and inline_reason not in registry["inline_reasons"]:
        raise ValueError("structured inline_reason required")
    evidence=_validate_tracking_evidence(tracking, tracked_gate_evidence)
    checked_dispatch=None
    if effective not in ("direct","quick"):
        checked_dispatch=_validate_dispatch_evidence(dispatch_evidence, DISPATCH_CONTRACT_VERSION)
        chain=_fallback_chain(checked_dispatch, DISPATCH_CONTRACT_VERSION)
        for node in nodes:
            if node.get("dispatch_depth")==2:
                node["fallback_hops"]=json.loads(json.dumps(chain))
    dispatch_defaults_digest=_seal_dispatch_defaults(nodes, capability)
    spec_touch=any(_scope_touches_spec(scope) for node in nodes for scope in node["write_scope"])
    payload={
      "schema_version":ROUTE_SCHEMA_VERSION,"capability":capability,"capability_mode":capability_mode,
      "requested_intensity":requested_intensity,"effective_intensity":effective,
      "execution_topology":("inline" if effective=="direct" else recipe["quick"]["topology"] if effective=="quick" else recipe["topology_class"]),
      "owner_dispatch_depth":0 if effective=="direct" else (recipe["quick"]["owner_dispatch_depth"] if effective=="quick" else recipe["standard_plus"]["owner_dispatch_depth"]),
      "max_dispatch_depth":recipe["quick"]["max_dispatch_depth"] if effective=="quick" else (0 if effective=="direct" else recipe["standard_plus"]["max_dispatch_depth"]),
      "tracking":tracking,"tracked_gate_evidence":evidence,"spec_touch":spec_touch,
      "cwd":str(cwd),"artifact_root":str(artifact),"source_commit":_git_commit(cwd),
      "registry_digest":TOPO.registry_digest(registry),
      "dispatch_defaults_digest":dispatch_defaults_digest,
      "selection":{"direct_predicates":predicates,"promotion_signals":[{"signal":s,"source":"caller"} for s in signals],
                   "selection_basis":selection_basis,
                   "escalation_basis":[{"signal":s,"source":"caller"} for s in signals],
                   "transport":transport,"transport_evidence":transport_evidence,"inline_reason":inline_reason},
      "nodes":nodes,"completion_gates":gates,"human_gates":recipe["human_gates"],
      "resume_retry_boundaries":recipe["resume_retry_boundaries"],
      "dispatch_evidence":checked_dispatch,
      "dispatch_contract_version":DISPATCH_CONTRACT_VERSION,
      "registered_headless_candidates":registered_headless_candidates,
      "registered_headless_policy":"serial-attempt" if effective=="quick" else None,
      "unit_catalog_digest":unit_catalog_digest()}
    if composed:
        payload["composed"]=True
        payload["composed_recipe"]=json.loads(json.dumps(recipe))
    digest=route_hash(payload); payload["route_hash"]=digest; payload["route_id"]="rt-"+digest.split(":",1)[1][:16]
    return payload

def verify_route(route, expected_cwd=None):
    if route.get("schema_version") != ROUTE_SCHEMA_VERSION:
        raise ValueError(
            f"legacy route schema_version={route.get('schema_version')!r} rejected for mutating/resume use"
        )
    if route.get("dispatch_contract_version") != DISPATCH_CONTRACT_VERSION:
        raise ValueError("legacy dispatch contract is read-only")
    if route.get("route_hash") != route_hash(route): raise ValueError("stale or modified route hash")
    if route.get("route_id") != "rt-"+route["route_hash"].split(":",1)[1][:16]: raise ValueError("invalid route id")
    if expected_cwd and Path(expected_cwd).resolve()!=Path(route["cwd"]): raise ValueError("route cwd mismatch")
    registry=TOPO.load_registry()
    if route["registry_digest"] != TOPO.registry_digest(registry): raise ValueError("stale registry digest")
    if route.get("unit_catalog_digest") is not None and route["unit_catalog_digest"] != unit_catalog_digest():
        raise ValueError("stale unit catalog digest")
    if route.get("composed"):
        if route.get("effective_intensity") in ("direct","quick"):
            raise ValueError("composed routes require a standard+ effective intensity")
        composed_recipe=route.get("composed_recipe")
        if not isinstance(composed_recipe, dict):
            raise ValueError("composed route lacks embedded composed_recipe")
        TOPO._validate_recipe(composed_recipe, registry)
        def _node_identity(node):
            return {k:v for k,v in node.items() if k not in ("fallback_hops","harness_affinity")}
        if ([_node_identity(n) for n in route.get("nodes",[])]
                != [_node_identity(n) for n in composed_recipe["standard_plus"]["nodes"]]):
            raise ValueError("composed route nodes differ from embedded composed recipe")
    if route.get("owner_dispatch_depth") not in {0, 1} or route.get("max_dispatch_depth") not in {0, 1, 2}:
        raise ValueError("invalid qualified dispatch depth")
    if any(key in route for key in ("depth", "owner_depth", "max_depth")):
        raise ValueError("bare route dispatch-depth fields are forbidden")
    observed_dispatch_depths = [route["owner_dispatch_depth"]]
    for node in route.get("nodes", []):
        if node.get("kind") == "resource-runner":
            if any(
                key in node
                for key in (
                    "depth", "owner_depth", "max_depth", "dispatch_depth",
                    "transport", "fallback_hops",
                )
            ):
                raise ValueError(f"resource node {node.get('id')} has dispatch attempt fields")
            if node.get("resource_transport") != "detached-process":
                raise ValueError(f"resource node {node.get('id')} lacks detached lifecycle")
            continue
        if any(key in node for key in ("depth", "owner_depth", "max_depth")) or node.get("dispatch_depth") not in {0, 1, 2}:
            raise ValueError(f"node {node.get('id')} has invalid dispatch_depth")
        observed_dispatch_depths.append(node["dispatch_depth"])
        if "harness_affinity" in node and node["harness_affinity"] not in VALID_AFFINITY:
            raise ValueError(f"invalid harness_affinity vocabulary: {node['harness_affinity']!r}")
        if "execution_surface" in node and node["execution_surface"] not in EXECUTION_SURFACES:
            raise ValueError(f"invalid execution_surface vocabulary: {node['execution_surface']!r}")
        if "registered_worker" in node and not isinstance(node["registered_worker"], bool):
            raise ValueError("registered_worker must be boolean")
        if "dispatch_fallback" in node:
            raise ValueError("legacy dispatch_fallback is read-only")
        for hop in node.get("fallback_hops", []):
            if not isinstance(hop, dict) or hop.get("fallback_hop") not in FALLBACK_HOPS:
                raise ValueError(f"invalid fallback_hop vocabulary: {hop!r}")
    if route["max_dispatch_depth"] != max(observed_dispatch_depths):
        raise ValueError("max_dispatch_depth does not match the realized route")
    effective=route.get("effective_intensity")
    selection=route.get("selection",{})
    if effective=="direct":
        if (
            route.get("owner_dispatch_depth") != 0
            or route.get("max_dispatch_depth") != 0
            or selection.get("transport") != "interactive"
            or route.get("registered_headless_candidates") is not None
            or route.get("registered_headless_policy") is not None
            or len(route.get("nodes",[])) != 1
        ):
            raise ValueError("direct route shape mismatch")
        node=route["nodes"][0]
        if (
            node.get("id") != "inline"
            or node.get("dispatch_depth") != 0
            or node.get("execution_surface") != "inline"
            or node.get("registered_worker") is not False
            or node.get("fallback_hops")
        ):
            raise ValueError("direct node axes mismatch")
    elif effective=="quick":
        if (
            route.get("owner_dispatch_depth") != 1
            or route.get("max_dispatch_depth") != 1
            or selection.get("transport") != "headless"
            or selection.get("inline_reason") is not None
            or route.get("registered_headless_policy") != "serial-attempt"
            or len(route.get("nodes",[])) != 1
        ):
            raise ValueError("quick route shape mismatch")
        candidates=_validate_registered_headless_evidence({
            "candidates":route.get("registered_headless_candidates")
        })
        if candidates != route.get("registered_headless_candidates"):
            raise ValueError("quick registered-headless evidence is not canonical")
        node=route["nodes"][0]
        if (
            node.get("id") != "one-shot"
            or node.get("dispatch_depth") != 1
            or node.get("execution_surface") != "registered-headless"
            or node.get("registered_worker") is not True
            or node.get("fallback_hops")
        ):
            raise ValueError("quick node axes mismatch")
    dd_digest=route.get("dispatch_defaults_digest")
    if dd_digest is not None and (not isinstance(dd_digest, str) or not dd_digest.startswith("sha256:")):
        raise ValueError("invalid dispatch_defaults_digest format")
    _validate_tracking_evidence(route.get("tracking"), route.get("tracked_gate_evidence"))
    escalation=route.get("selection",{}).get("escalation_basis")
    if not isinstance(escalation,list): raise ValueError("escalation_basis missing")
    if any(row.get("signal") in TRACKING for row in escalation if isinstance(row,dict)):
        raise ValueError("tracking cannot be an escalation basis")
    spec_touch=any(_scope_touches_spec(scope) for node in route.get("nodes",[]) for scope in node.get("write_scope",[]))
    if bool(route.get("spec_touch")) != spec_touch: raise ValueError("spec_touch declaration mismatch")
    if route.get("effective_intensity") not in ("direct","quick"):
        if route.get("selection",{}).get("transport") != "headless":
            raise ValueError("standard+ routes require checked headless transport")
        contract_version=route.get("dispatch_contract_version") or route.get("broker_contract_version") or 1
        checked_dispatch=_validate_dispatch_evidence(route.get("dispatch_evidence"), contract_version)
        expected_chain=_fallback_chain(checked_dispatch, contract_version)
        for node in route.get("nodes",[]):
            if node.get("dispatch_depth")==2:
                chain=_verify_fallback_chain(node, contract_version)
                if chain != expected_chain:
                    raise ValueError(f"dispatch-depth-2 node {node.get('id')} fallback differs from checked evidence")
    return route

def legacy_route_diagnostic(route):
    """Return read-only classification for historical Fleet display."""
    version=route.get("schema_version",1)
    return {
        "route_id":route.get("route_id"),
        "schema_version":version,
        "legacy":version != ROUTE_SCHEMA_VERSION,
        "classification":"version-tagged-read-only-bootstrap" if version != ROUTE_SCHEMA_VERSION else "current",
    }

def write_once(path, payload):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); data=json.dumps(payload,indent=2,ensure_ascii=False)+"\n"
    try:
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:
        if path.read_text(encoding="utf-8") != data: raise ValueError("immutable route already exists with different content")
        return
    with os.fdopen(fd,"w",encoding="utf-8") as fh: fh.write(data); fh.flush(); os.fsync(fh.fileno())

def completion_dir(route_id):
    return resolve_agent_home()/".dispatch"/"completion"/route_id

def atomic_write(path, payload):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(payload,indent=2,ensure_ascii=False)+"\n"
    temp=path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"w",encoding="utf-8") as fh: fh.write(data); fh.flush(); os.fsync(fh.fileno())
    os.replace(temp,path)

def _marker_attempt_axes(node, attempt_id, attempt_metadata):
    if node.get("kind") == "resource-runner":
        if attempt_id or attempt_metadata:
            raise ValueError("resource completion cannot carry agent attempt axes")
        return {
            "attempt_id":None,
            "dispatch_depth":None,
            "transport":None,
            "execution_surface":None,
            "registered_worker":False,
            "fallback_hop":None,
        }
    if attempt_metadata is None:
        if node.get("dispatch_depth") != 0 or node.get("execution_surface") != "inline":
            raise ValueError("current dispatched completion requires exact attempt metadata")
        attempt_metadata={
            "attempt_schema_version":2,
            "dispatch_depth":0,
            "transport":"interactive",
            "execution_surface":"inline",
            "registered_worker":False,
            "fallback_hop":"",
        }
    validate_attempt_metadata(attempt_metadata)
    dispatch_depth=int(attempt_metadata["dispatch_depth"])
    if dispatch_depth != node.get("dispatch_depth"):
        raise ValueError("completion attempt dispatch_depth does not match route node")
    registered=str(attempt_metadata["registered_worker"]).lower() in {"1","true"}
    return {
        "attempt_id":attempt_id,
        "dispatch_depth":dispatch_depth,
        "transport":str(attempt_metadata["transport"]),
        "execution_surface":str(attempt_metadata["execution_surface"]),
        "registered_worker":registered,
        "fallback_hop":str(attempt_metadata.get("fallback_hop") or "") or None,
    }

def _next_marker_sequence(directory, node_id):
    maximum=0
    if directory.is_dir():
        prefix=f"{node_id}."
        for path in directory.glob(f"{node_id}.*.json"):
            middle=path.name[len(prefix):-5]
            if middle.isdigit():
                maximum=max(maximum,int(middle))
    return maximum+1

def write_completion_marker(route, node, node_id, evidence, *, attempt_id=None, attempt_metadata=None):
    directory=completion_dir(route["route_id"])
    canonical_path=directory/f"{node_id}.json"
    sha=hashlib.sha256(evidence.read_bytes()).hexdigest()
    axes=_marker_attempt_axes(node, attempt_id, attempt_metadata)
    identity={
        "evidence_sha256":sha,
        **axes,
    }
    if canonical_path.is_file():
        existing=json.loads(canonical_path.read_text(encoding="utf-8"))
        existing_identity={
            "evidence_sha256":existing.get("evidence",{}).get("sha256"),
            **{key:existing.get(key) for key in axes},
        }
        if existing_identity==identity:
            static_identity={
                "schema_version":2,
                "route_id":route["route_id"],
                "route_hash":route["route_hash"],
                "registry_digest":route["registry_digest"],
                "node_id":node_id,
                "completion_gate":node["completion_gate"],
            }
            if any(existing.get(key)!=value for key,value in static_identity.items()):
                raise ValueError("canonical completion marker identity conflict")
            history_path=directory/f"{node_id}.{existing.get('sequence')}.json"
            if (
                not history_path.is_file()
                or json.loads(history_path.read_text(encoding="utf-8"))!=existing
            ):
                raise ValueError("canonical completion marker history conflict")
            return existing
    sequence=_next_marker_sequence(directory,node_id)
    marker={
        "schema_version":2,
        "route_id":route["route_id"],"route_hash":route["route_hash"],
        "registry_digest":route["registry_digest"],"node_id":node_id,
        **axes,
        "completion_gate":node["completion_gate"],
        "evidence":{"path":str(evidence),"sha256":sha},
        "sequence":sequence,
    }
    from datetime import datetime, timezone
    marker["completed_at"]=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    while True:
        history_path=directory/f"{node_id}.{sequence}.json"
        try:
            write_once(history_path, marker)
        except ValueError:
            sequence+=1; marker["sequence"]=sequence; continue
        break
    atomic_write(canonical_path, marker)
    return marker

def _find_attempt_row_status(jobs, attempt_id):
    """Return the row status ('open'|'running'|'done') for attempt_id, or None if absent."""
    if not jobs.is_file(): return None
    for line in jobs.read_text(encoding="utf-8", errors="replace").splitlines():
        fields=line.split("\t")
        if len(fields)!=6: continue
        metadata=dict(part.split("=",1) for part in fields[5].split(",") if "=" in part)
        if metadata.get("attempt_id")==attempt_id: return fields[1]
    return None

def _find_attempt_row_metadata(jobs, attempt_id):
    if not jobs.is_file(): return None
    for line in jobs.read_text(encoding="utf-8",errors="replace").splitlines():
        fields=line.split("\t")
        if len(fields)!=6: continue
        metadata=parse_registry_metadata(fields[5])
        if metadata.get("attempt_id")==attempt_id:
            metadata["_status"]=fields[1]
            return metadata
    return None

@contextlib.contextmanager
def _exclusive_lock(path):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(),fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(),fcntl.LOCK_UN)

def _attempt_completion_path(route, node_id, attempt_id):
    safe_attempt="".join(
        character if character.isalnum() or character in "._-" else "_"
        for character in attempt_id
    )
    return completion_dir(route["route_id"])/f"{node_id}.{safe_attempt}.attempt.json"

def _publish_completion_locked(
    route,
    node,
    node_id,
    evidence,
    *,
    attempt_id,
    attempt_metadata,
    require_existing_link=False,
):
    """Publish marker history, exact-attempt link, and canonical marker under one node lock."""

    axes=_marker_attempt_axes(node,attempt_id,attempt_metadata)
    evidence_sha=hashlib.sha256(evidence.read_bytes()).hexdigest()
    attempt_path=(
        _attempt_completion_path(route,node_id,attempt_id)
        if attempt_id else None
    )
    marker=None
    if attempt_path and attempt_path.is_file():
        existing_link=json.loads(attempt_path.read_text(encoding="utf-8"))
        expected_link_identity={
            "schema_version":2,
            "route_id":route["route_id"],
            "node_id":node_id,
            "attempt_id":attempt_id,
            **axes,
            "evidence_sha256":evidence_sha,
        }
        actual_link_identity={
            key:existing_link.get(key) for key in expected_link_identity
        }
        if actual_link_identity != expected_link_identity:
            raise ValueError("immutable attempt completion differs from existing link")
        history_path=Path(existing_link.get("completion_marker_history",""))
        if not history_path.is_file():
            raise ValueError("immutable attempt completion history is missing")
        marker=json.loads(history_path.read_text(encoding="utf-8"))
        marker_identity={
            "schema_version":marker.get("schema_version"),
            "route_id":marker.get("route_id"),
            "node_id":marker.get("node_id"),
            "attempt_id":marker.get("attempt_id"),
            **{key:marker.get(key) for key in axes if key!="attempt_id"},
            "evidence_sha256":marker.get("evidence",{}).get("sha256"),
        }
        if marker_identity != expected_link_identity:
            raise ValueError("immutable attempt completion history differs from link")
        expected_history_path=completion_dir(route["route_id"])/f"{node_id}.{marker.get('sequence')}.json"
        if history_path!=expected_history_path:
            raise ValueError("immutable attempt completion history path differs from link")
        marker_static={
            "route_hash":route["route_hash"],
            "registry_digest":route["registry_digest"],
            "completion_gate":node["completion_gate"],
            "evidence_path":str(evidence),
        }
        actual_static={
            "route_hash":marker.get("route_hash"),
            "registry_digest":marker.get("registry_digest"),
            "completion_gate":marker.get("completion_gate"),
            "evidence_path":marker.get("evidence",{}).get("path"),
        }
        if actual_static!=marker_static:
            raise ValueError("immutable attempt completion route identity differs from link")
    elif require_existing_link:
        raise ValueError("completed attempt row lacks immutable completion link")

    if marker is None:
        marker=write_completion_marker(
            route,node,node_id,evidence,
            attempt_id=attempt_id,
            attempt_metadata=attempt_metadata,
        )
    if not attempt_id:
        return marker

    canonical_marker_path=completion_dir(route["route_id"])/f"{node_id}.json"
    history_marker_path=completion_dir(route["route_id"])/f"{node_id}.{marker['sequence']}.json"
    attempt_link={
        "schema_version":2,
        "route_id":route["route_id"],"node_id":node_id,"attempt_id":attempt_id,
        "dispatch_depth":marker["dispatch_depth"],
        "transport":marker["transport"],
        "execution_surface":marker["execution_surface"],
        "registered_worker":marker["registered_worker"],
        "fallback_hop":marker["fallback_hop"],
        "evidence_sha256":marker["evidence"]["sha256"],
        "completion_marker":str(canonical_marker_path),
        "completion_marker_history":str(history_marker_path),
    }
    write_once(attempt_path,attempt_link)
    current_marker=json.loads(canonical_marker_path.read_text(encoding="utf-8"))
    if current_marker==marker:
        atomic_write(
            completion_dir(route["route_id"])/f"{node_id}.attempt.json",
            attempt_link,
        )
    return marker

def complete_node(
    route,
    node,
    node_id,
    evidence,
    jobs=None,
    attempt_id=None,
    explicit_attempt_metadata=None,
):
    """Atomically publish one exact-attempt completion and close only its row."""
    if jobs and not attempt_id:
        raise ValueError("registered completion requires --attempt-id")
    if not jobs and attempt_id and explicit_attempt_metadata is None:
        raise ValueError("unregistered completion requires explicit attempt metadata")
    if not jobs and explicit_attempt_metadata is not None and not attempt_id:
        raise ValueError("explicit attempt metadata requires --attempt-id")

    jobs_path=Path(jobs) if jobs else None
    directory=completion_dir(route["route_id"])
    node_lock=directory/f".{node_id}.completion.lock"
    with _exclusive_lock(node_lock):
        if not jobs_path:
            marker=_publish_completion_locked(
                route,node,node_id,evidence,
                attempt_id=attempt_id,
                attempt_metadata=explicit_attempt_metadata,
            )
            status="unregistered-complete" if attempt_id else None
            return marker, ({"attempt_id":attempt_id,"status":status} if status else None)

        try:
            ensure_global_registry_writable(jobs_path)
        except DispatchContractError as exc:
            if explicit_attempt_metadata is not None:
                _publish_completion_locked(
                    route,node,node_id,evidence,
                    attempt_id=attempt_id,
                    attempt_metadata=explicit_attempt_metadata,
                )
            raise ValueError(f"row-close-failed:{exc.reason}") from exc
        with _exclusive_lock(Path(f"{jobs_path}.lock")):
            lines=jobs_path.read_text(encoding="utf-8",errors="replace").splitlines()
            row_index=None
            row_fields=None
            row_metadata=None
            for index,line in enumerate(lines):
                fields=line.split("\t")
                if len(fields)!=6:
                    continue
                metadata=parse_registry_metadata(fields[5])
                if metadata.get("attempt_id")==attempt_id:
                    row_index=index; row_fields=fields; row_metadata=metadata
                    break
            if row_fields is None or row_metadata is None:
                if explicit_attempt_metadata is not None:
                    _publish_completion_locked(
                        route,node,node_id,evidence,
                        attempt_id=attempt_id,
                        attempt_metadata=explicit_attempt_metadata,
                    )
                raise ValueError(
                    f"attempt-row-absent:{attempt_id}; exact fallback attempt metadata required"
                )
            try:
                validate_attempt_metadata(row_metadata)
            except DispatchContractError as exc:
                raise ValueError(f"row-contract-invalid:{exc.reason}") from exc
            if (
                row_metadata.get("route_id") != route["route_id"]
                or row_metadata.get("route_hash") != route["route_hash"]
                or row_metadata.get("route_node") != node_id
            ):
                raise ValueError("attempt row route identity mismatch")
            if explicit_attempt_metadata is not None:
                axis_keys=(
                    "attempt_schema_version","dispatch_depth","transport",
                    "execution_surface","registered_worker","fallback_hop",
                )
                row_axes={key:str(row_metadata.get(key,"")).lower() for key in axis_keys}
                explicit_axes={key:str(explicit_attempt_metadata.get(key,"")).lower() for key in axis_keys}
                if row_axes != explicit_axes:
                    raise ValueError("explicit attempt metadata differs from canonical row")
            if row_fields[1] not in {"open","running","done"}:
                raise ValueError(f"attempt-row-terminal:{row_fields[1]}")
            already_closed=row_fields[1]=="done"
            if already_closed and row_metadata.get("note")!="completed-marker":
                raise ValueError(
                    f"attempt-row-terminal-without-completion:{row_metadata.get('note','unknown')}"
                )
            attempt_metadata={
                key:value for key,value in row_metadata.items()
                if not key.startswith("_")
            }
            marker=_publish_completion_locked(
                route,node,node_id,evidence,
                attempt_id=attempt_id,
                attempt_metadata=attempt_metadata,
                require_existing_link=already_closed,
            )
            if already_closed:
                return marker, {"attempt_id":attempt_id,"status":"already-closed"}

            canonical_marker_path=directory/f"{node_id}.json"
            history_marker_path=directory/f"{node_id}.{marker['sequence']}.json"
            row_fields[1]="done"
            row_fields[5] += (
                f",note=completed-marker,completion_marker={canonical_marker_path}"
                f",completion_marker_history={history_marker_path}"
            )
            lines[row_index]="\t".join(row_fields)
            _atomic_registry_replace(jobs_path,lines)
            return marker, {"attempt_id":attempt_id,"status":"closed"}

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="command",required=True)
    c=sub.add_parser("compile"); c.add_argument("--capability",required=True); c.add_argument("--capability-mode",default="default")
    c.add_argument("--intensity",default="auto"); c.add_argument("--cwd",required=True); c.add_argument("--artifact-root",required=True)
    c.add_argument("--predicate",action="append",default=[]); c.add_argument("--signal",action="append",default=[])
    c.add_argument("--transport",default=None); c.add_argument("--transport-evidence",default="caller-selected")
    c.add_argument("--inline-reason"); c.add_argument("--tracking",choices=sorted(TRACKING),required=True)
    c.add_argument("--dispatch-evidence",help="JSON file with checked nested tuples/native evidence")
    c.add_argument("--registered-headless-evidence",help="JSON file with checked quick candidates")
    c.add_argument("--composed-recipe",help="JSON file with a compose-on-demand recipe (sealed composed: true)")
    c.add_argument("--spec-read",required=True); c.add_argument("--drift-verdict",required=True)
    c.add_argument("--workflow-mode",choices=sorted(TRACKING),required=True); c.add_argument("--artifact-guard",required=True)
    c.add_argument("--output")
    v=sub.add_parser("verify"); v.add_argument("--route",required=True); v.add_argument("--cwd")
    n=sub.add_parser("node"); n.add_argument("--route",required=True); n.add_argument("--node",required=True)
    d=sub.add_parser("complete"); d.add_argument("--route",required=True); d.add_argument("--node",required=True); d.add_argument("--evidence",required=True); d.add_argument("--output")
    d.add_argument("--jobs",help="canonical registry path for a registered attempt")
    d.add_argument("--attempt-id",help="exact current attempt id")
    d.add_argument("--dispatch-depth",type=int)
    d.add_argument("--transport")
    d.add_argument("--execution-surface")
    d.add_argument("--registered-worker",choices=("0","1","false","true"))
    d.add_argument("--fallback-hop")
    a=p.parse_args()
    if a.command=="compile":
        gate={"spec_read":{"satisfied":a.spec_read.lower() not in ("0","false","no"),"source":a.spec_read},
              "drift_verdict":a.drift_verdict,"workflow_mode":a.workflow_mode,
              "artifact_guard":{"satisfied":a.artifact_guard.lower() not in ("0","false","no"),"source":a.artifact_guard}}
        dispatch_evidence=json.loads(Path(a.dispatch_evidence).read_text()) if a.dispatch_evidence else None
        registered_headless_evidence=(
            json.loads(Path(a.registered_headless_evidence).read_text())
            if a.registered_headless_evidence else None
        )
        if a.composed_recipe:
            composed_recipe=json.loads(Path(a.composed_recipe).read_text())
            if composed_recipe.get("capability") != a.capability:
                raise ValueError("composed recipe capability differs from --capability")
            route=compile_composed_route(
                composed_recipe,a.capability_mode,a.intensity,a.cwd,a.artifact_root,
                predicates=a.predicate,signals=a.signal,transport=a.transport,
                transport_evidence=a.transport_evidence,inline_reason=a.inline_reason,
                tracking=a.tracking,tracked_gate_evidence=gate,
                dispatch_evidence=dispatch_evidence,
                registered_headless_evidence=registered_headless_evidence,
            )
        else:
            route=compile_route(
                a.capability,a.capability_mode,a.intensity,a.cwd,a.artifact_root,
                a.predicate,a.signal,a.transport,a.transport_evidence,a.inline_reason,
                a.tracking,gate,dispatch_evidence,registered_headless_evidence,
            )
        if a.output: write_once(a.output,route)
        print(json.dumps(route,sort_keys=True))
    else:
        route=verify_route(json.loads(Path(a.route).read_text()), getattr(a,"cwd",None))
        if a.command=="verify": print(f"route_id={route['route_id']}\nroute_hash={route['route_hash']}")
        else:
            node=next((x for x in route["nodes"] if x["id"]==a.node),None)
            if not node: raise SystemExit("unknown route node")
            if a.command=="node": print(json.dumps(node,sort_keys=True))
            else:
                evidence=Path(a.evidence).resolve()
                if not evidence.is_file(): raise SystemExit("completion evidence missing")
                raw_axes=(a.dispatch_depth,a.transport,a.execution_surface,a.registered_worker,a.fallback_hop)
                explicit_attempt_metadata=None
                if any(value is not None for value in raw_axes):
                    explicit_attempt_metadata={
                        "attempt_schema_version":2,
                        "dispatch_depth":a.dispatch_depth,
                        "transport":a.transport,
                        "execution_surface":a.execution_surface,
                        "registered_worker":a.registered_worker,
                        "fallback_hop":a.fallback_hop,
                    }
                marker,row=complete_node(
                    route,node,a.node,evidence,
                    jobs=a.jobs,
                    attempt_id=a.attempt_id,
                    explicit_attempt_metadata=explicit_attempt_metadata,
                )
                if a.output: atomic_write(a.output, marker)
                print(json.dumps(marker,sort_keys=True))
                if row: print(json.dumps(row,sort_keys=True))

if __name__=="__main__":
    try: main()
    except (ValueError,TOPO.TopologyError) as exc: print(f"capability-route: {exc}",file=sys.stderr); raise SystemExit(64)
