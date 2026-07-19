#!/usr/bin/env python3
"""Compile, verify, and complete immutable capability routes."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, subprocess, sys, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("capability_topology", ROOT/"tools/capability_topology.py")
TOPO = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(TOPO)
sys.path.insert(0, str(ROOT/"utilities"))
from dispatch_contract import resolve_agent_home, close_attempt_row, DispatchContractError
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
    for row in native:
        if not isinstance(row,dict) or row.get("status") not in NESTED_STATUSES or not row.get("harness") or not row.get("check_source"):
            raise ValueError("invalid native subagent evidence")
    return {"tuples":normalized,"native_subagent":native}

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
            raise ValueError("no supported depth-0 launch broker tuple")
    else:
        has_broker=any(
            row["status"]=="supported" and row["launch_authority"]=="ancestor-broker"
            and row.get("broker_root") and row.get("broker_instance")
            for row in same+cross
        )
        if not has_broker:
            raise ValueError("no supported depth-0 launch broker tuple")
    return [
        {"ordinal":1,"hop":"same-harness-headless","candidates":same},
        {"ordinal":2,"hop":"cross-harness-headless","candidates":cross},
        {"ordinal":3,"hop":"native-subagent","candidates":evidence["native_subagent"],"fleet_visibility":"degraded"},
        {"ordinal":4,"hop":"inline","status":"eligible-after-prior-hop-exhaustion","reason_enum":"runtime-unavailable","fleet_visibility":"none"},
    ]

def _verify_fallback_chain(node, contract_version=None):
    contract_version = contract_version or 1
    chain=node.get("dispatch_fallback")
    if not isinstance(chain,list) or [row.get("hop") for row in chain] != FALLBACK_ORDER:
        raise ValueError(f"depth-2 node {node.get('id')} missing ordered dispatch fallback")
    candidates=[candidate for row in chain[:2] for candidate in row.get("candidates",[])]
    if contract_version==DISPATCH_CONTRACT_VERSION:
        supported=[c for c in candidates if c.get("status")=="supported" and c.get("launch_authority")=="conductor"]
        if not supported:
            raise ValueError(f"depth-2 node {node.get('id')} lacks supported direct headless tuple")
        if any(c.get("broker_root") or c.get("broker_instance") for c in candidates):
            raise ValueError(f"depth-2 node {node.get('id')} v3 candidate carries retired broker fields")
    elif contract_version==1:
        supported=[c for c in candidates if c.get("status")=="supported" and c.get("launch_authority")=="ancestor-broker"]
        if not any(c.get("broker_root") and c.get("broker_instance") for c in supported):
            raise ValueError(f"depth-2 node {node.get('id')} lacks supported depth-0 broker tuple")
    elif contract_version==2:
        supported=[c for c in candidates if c.get("status")=="supported" and c.get("launch_authority")=="ancestor-broker"]
        if not any(c.get("broker_root") for c in supported):
            raise ValueError(f"depth-2 node {node.get('id')} lacks supported depth-0 broker tuple")
        if any(c.get("broker_instance") for c in supported):
            raise ValueError(f"depth-2 node {node.get('id')} v2 candidate must not carry broker_instance")
    else:
        if not supported:
            raise ValueError(f"depth-2 node {node.get('id')} lacks supported depth-0 broker tuple")
    return chain

def compile_route(capability, capability_mode, requested_intensity, cwd, artifact_root,
                  predicates=(), signals=(), transport="inline-fallback",
                  transport_evidence="caller-selected", inline_reason=None,
                  tracking="tracked", tracked_gate_evidence=None, dispatch_evidence=None):
    cwd=Path(cwd).resolve(strict=True); artifact=Path(artifact_root).resolve()
    if not cwd.is_absolute() or not artifact.is_absolute(): raise ValueError("cwd and artifact root must be absolute")
    registry=TOPO.load_registry(); TOPO.validate_registry(registry)
    recipe=TOPO.resolve_recipe(registry, capability, capability_mode)
    known_pred=set(recipe["direct_predicates"]); predicates=sorted(set(predicates))
    unknown=set(predicates)-known_pred
    if unknown: raise ValueError("unknown predicates: "+",".join(sorted(unknown)))
    signals=sorted(set(signals))
    if set(signals) & TRACKING: raise ValueError("tracking cannot be an escalation signal")
    unknown=set(signals)-set(recipe["promotion_signals"])
    if unknown: raise ValueError("unknown promotion signals: "+",".join(sorted(unknown)))
    requested="standard" if requested_intensity=="auto" else requested_intensity
    if requested not in ORDER: raise ValueError("invalid intensity")
    inferred="standard" if signals else ("direct" if set(predicates)==known_pred else "quick")
    effective=max((requested,inferred),key=ORDER.get)
    if effective=="direct":
        if inline_reason is None: inline_reason="atomic-direct"
        nodes=[{"id":"inline","kind":"capability-owner","depth":1,"role":"orchestrator",
                "write_scope":recipe["quick"]["write_scope"],"resource_class":"normal",
                "transport":[transport],"completion_gate":"inline-complete"}]
        gates=["inline-complete"]
        selection_basis=[{"axis":"direct-predicate","signal":p,"source":"caller"} for p in predicates]
    elif effective=="quick":
        nodes=[{"id":"one-shot","kind":recipe["quick"]["worker_kind"],"depth":1,"role":"orchestrator",
                "write_scope":recipe["quick"]["write_scope"],"resource_class":"normal",
                "transport":[transport],"completion_gate":"quick-complete"}]
        gates=["quick-complete"]
        selection_basis=[{"axis":"direct-predicate-gap","signal":p,"source":"compiler"} for p in sorted(known_pred-set(predicates))]
    else:
        nodes=json.loads(json.dumps(recipe["standard_plus"]["nodes"])); gates=recipe["completion_gates"]
        selection_basis=[{"axis":"promotion","signal":s,"source":"caller"} for s in signals]
    if transport=="inline-fallback":
        if inline_reason not in registry["inline_reasons"]: raise ValueError("structured inline_reason required")
    elif inline_reason is not None: raise ValueError("inline_reason only applies to inline-fallback")
    evidence=_validate_tracking_evidence(tracking, tracked_gate_evidence)
    checked_dispatch=None
    if effective not in ("direct","quick") and transport=="headless":
        checked_dispatch=_validate_dispatch_evidence(dispatch_evidence, DISPATCH_CONTRACT_VERSION)
        chain=_fallback_chain(checked_dispatch, DISPATCH_CONTRACT_VERSION)
        for node in nodes:
            if node.get("depth")==2:
                node["dispatch_fallback"]=json.loads(json.dumps(chain))
    spec_touch=any(_scope_touches_spec(scope) for node in nodes for scope in node["write_scope"])
    payload={
      "schema_version":1,"capability":capability,"capability_mode":capability_mode,
      "requested_intensity":requested_intensity,"effective_intensity":effective,
      "execution_topology":("inline" if effective=="direct" else recipe["quick"]["topology"] if effective=="quick" else recipe["topology_class"]),
      "owner_depth":recipe["quick"]["owner_depth"] if effective in ("direct","quick") else recipe["standard_plus"]["owner_depth"],
      "tracking":tracking,"tracked_gate_evidence":evidence,"spec_touch":spec_touch,
      "cwd":str(cwd),"artifact_root":str(artifact),"source_commit":_git_commit(cwd),
      "registry_digest":TOPO.registry_digest(registry),
      "selection":{"direct_predicates":predicates,"promotion_signals":[{"signal":s,"source":"caller"} for s in signals],
                   "selection_basis":selection_basis,
                   "escalation_basis":[{"signal":s,"source":"caller"} for s in signals],
                   "transport":transport,"transport_evidence":transport_evidence,"inline_reason":inline_reason},
      "nodes":nodes,"completion_gates":gates,"human_gates":recipe["human_gates"],
      "resume_retry_boundaries":recipe["resume_retry_boundaries"],
      "dispatch_evidence":checked_dispatch,
      "dispatch_contract_version":DISPATCH_CONTRACT_VERSION if checked_dispatch is not None else None}
    digest=route_hash(payload); payload["route_hash"]=digest; payload["route_id"]="rt-"+digest.split(":",1)[1][:16]
    return payload

def verify_route(route, expected_cwd=None):
    if route.get("route_hash") != route_hash(route): raise ValueError("stale or modified route hash")
    if route.get("route_id") != "rt-"+route["route_hash"].split(":",1)[1][:16]: raise ValueError("invalid route id")
    if expected_cwd and Path(expected_cwd).resolve()!=Path(route["cwd"]): raise ValueError("route cwd mismatch")
    registry=TOPO.load_registry()
    if route["registry_digest"] != TOPO.registry_digest(registry): raise ValueError("stale registry digest")
    _validate_tracking_evidence(route.get("tracking"), route.get("tracked_gate_evidence"))
    escalation=route.get("selection",{}).get("escalation_basis")
    if not isinstance(escalation,list): raise ValueError("escalation_basis missing")
    if any(row.get("signal") in TRACKING for row in escalation if isinstance(row,dict)):
        raise ValueError("tracking cannot be an escalation basis")
    spec_touch=any(_scope_touches_spec(scope) for node in route.get("nodes",[]) for scope in node.get("write_scope",[]))
    if bool(route.get("spec_touch")) != spec_touch: raise ValueError("spec_touch declaration mismatch")
    if route.get("effective_intensity") not in ("direct","quick") and route.get("selection",{}).get("transport")=="headless":
        contract_version=route.get("dispatch_contract_version") or route.get("broker_contract_version") or 1
        checked_dispatch=_validate_dispatch_evidence(route.get("dispatch_evidence"), contract_version)
        expected_chain=_fallback_chain(checked_dispatch, contract_version)
        for node in route.get("nodes",[]):
            if node.get("depth")==2:
                chain=_verify_fallback_chain(node, contract_version)
                if chain != expected_chain:
                    raise ValueError(f"depth-2 node {node.get('id')} dispatch fallback differs from checked evidence")
    return route

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

def write_completion_marker(route, node, node_id, evidence):
    directory=completion_dir(route["route_id"])
    canonical_path=directory/f"{node_id}.json"
    sha=hashlib.sha256(evidence.read_bytes()).hexdigest()
    if canonical_path.is_file():
        existing=json.loads(canonical_path.read_text(encoding="utf-8"))
        if existing.get("evidence",{}).get("sha256")==sha:
            return existing
    history=sorted(directory.glob(f"{node_id}.*.json")) if directory.is_dir() else []
    sequence=len(history)+1
    marker={
        "route_id":route["route_id"],"route_hash":route["route_hash"],
        "registry_digest":route["registry_digest"],"node_id":node_id,
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

def complete_node(route, node, node_id, evidence, jobs=None, attempt_id=None):
    """Write the completion marker, then (SD-70) idempotently close only the exact attempt row.

    ``jobs``/``attempt_id`` are optional-but-paired: supplying one without the
    other is a structured error so legacy marker-only callers (unpaired) keep
    today's behavior. The marker is always written first and is never deleted
    or rewritten if the row-close step fails afterward.
    """
    marker=write_completion_marker(route, node, node_id, evidence)
    if not jobs and not attempt_id:
        return marker, None
    if not jobs or not attempt_id:
        raise ValueError("complete requires --jobs and --attempt-id together, or neither")
    jobs_path=Path(jobs)
    canonical_marker_path=completion_dir(route["route_id"])/f"{node_id}.json"
    row_evidence={
        "completion_marker":str(canonical_marker_path),
        "route_node":node_id,"route_id":route["route_id"],
    }
    # SD-70 reconcile repair: written before the row-close attempt so a later
    # dead row can still be matched to this exact attempt even if the close
    # below fails (e.g. jobs registry unwritable at complete-time).
    atomic_write(
        completion_dir(route["route_id"])/f"{node_id}.attempt.json",
        {"route_id":route["route_id"],"node_id":node_id,"attempt_id":attempt_id,
         "completion_marker":str(canonical_marker_path)},
    )
    try:
        closed=close_attempt_row(jobs_path, attempt_id, "completed-marker", evidence=row_evidence)
    except DispatchContractError as exc:
        raise ValueError(f"row-close-failed:{exc}") from exc
    if closed:
        return marker, {"attempt_id":attempt_id,"status":"closed"}
    status=_find_attempt_row_status(jobs_path, attempt_id)
    if status=="done":
        return marker, {"attempt_id":attempt_id,"status":"already-closed"}
    raise ValueError(f"attempt-row-absent:{attempt_id}")

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="command",required=True)
    c=sub.add_parser("compile"); c.add_argument("--capability",required=True); c.add_argument("--capability-mode",default="default")
    c.add_argument("--intensity",default="auto"); c.add_argument("--cwd",required=True); c.add_argument("--artifact-root",required=True)
    c.add_argument("--predicate",action="append",default=[]); c.add_argument("--signal",action="append",default=[])
    c.add_argument("--transport",default="inline-fallback"); c.add_argument("--transport-evidence",default="caller-selected")
    c.add_argument("--inline-reason"); c.add_argument("--tracking",choices=sorted(TRACKING),required=True)
    c.add_argument("--dispatch-evidence",help="JSON file with checked nested tuples/native evidence")
    c.add_argument("--spec-read",required=True); c.add_argument("--drift-verdict",required=True)
    c.add_argument("--workflow-mode",choices=sorted(TRACKING),required=True); c.add_argument("--artifact-guard",required=True)
    c.add_argument("--output")
    v=sub.add_parser("verify"); v.add_argument("--route",required=True); v.add_argument("--cwd")
    n=sub.add_parser("node"); n.add_argument("--route",required=True); n.add_argument("--node",required=True)
    d=sub.add_parser("complete"); d.add_argument("--route",required=True); d.add_argument("--node",required=True); d.add_argument("--evidence",required=True); d.add_argument("--output")
    d.add_argument("--jobs",help="canonical registry path (SD-70); pairs with --attempt-id")
    d.add_argument("--attempt-id",help="exact current attempt id (SD-70); pairs with --jobs")
    a=p.parse_args()
    if a.command=="compile":
        gate={"spec_read":{"satisfied":a.spec_read.lower() not in ("0","false","no"),"source":a.spec_read},
              "drift_verdict":a.drift_verdict,"workflow_mode":a.workflow_mode,
              "artifact_guard":{"satisfied":a.artifact_guard.lower() not in ("0","false","no"),"source":a.artifact_guard}}
        dispatch_evidence=json.loads(Path(a.dispatch_evidence).read_text()) if a.dispatch_evidence else None
        route=compile_route(a.capability,a.capability_mode,a.intensity,a.cwd,a.artifact_root,a.predicate,a.signal,a.transport,a.transport_evidence,a.inline_reason,a.tracking,gate,dispatch_evidence)
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
                marker,row=complete_node(route, node, a.node, evidence, jobs=a.jobs, attempt_id=a.attempt_id)
                if a.output: atomic_write(a.output, marker)
                print(json.dumps(marker,sort_keys=True))
                if row: print(json.dumps(row,sort_keys=True))

if __name__=="__main__":
    try: main()
    except (ValueError,TOPO.TopologyError) as exc: print(f"capability-route: {exc}",file=sys.stderr); raise SystemExit(64)
