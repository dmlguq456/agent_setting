#!/usr/bin/env python3
"""Compile, verify, and complete immutable capability routes."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("capability_topology", ROOT/"tools/capability_topology.py")
TOPO = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(TOPO)
ORDER = {"direct":0,"quick":1,"standard":2,"strong":3,"thorough":4,"adversarial":5}
TRACKING = {"tracked", "untracked"}
GATE_FIELDS = {"spec_read", "drift_verdict", "workflow_mode", "artifact_guard"}

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

def compile_route(capability, capability_mode, requested_intensity, cwd, artifact_root,
                  predicates=(), signals=(), transport="inline-fallback",
                  transport_evidence="caller-selected", inline_reason=None,
                  tracking="tracked", tracked_gate_evidence=None):
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
        nodes=recipe["standard_plus"]["nodes"]; gates=recipe["completion_gates"]
        selection_basis=[{"axis":"promotion","signal":s,"source":"caller"} for s in signals]
    if transport=="inline-fallback":
        if inline_reason not in registry["inline_reasons"]: raise ValueError("structured inline_reason required")
    elif inline_reason is not None: raise ValueError("inline_reason only applies to inline-fallback")
    evidence=_validate_tracking_evidence(tracking, tracked_gate_evidence)
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
      "resume_retry_boundaries":recipe["resume_retry_boundaries"]}
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
    return route

def write_once(path, payload):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); data=json.dumps(payload,indent=2,ensure_ascii=False)+"\n"
    try:
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:
        if path.read_text(encoding="utf-8") != data: raise ValueError("immutable route already exists with different content")
        return
    with os.fdopen(fd,"w",encoding="utf-8") as fh: fh.write(data); fh.flush(); os.fsync(fh.fileno())

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="command",required=True)
    c=sub.add_parser("compile"); c.add_argument("--capability",required=True); c.add_argument("--capability-mode",default="default")
    c.add_argument("--intensity",default="auto"); c.add_argument("--cwd",required=True); c.add_argument("--artifact-root",required=True)
    c.add_argument("--predicate",action="append",default=[]); c.add_argument("--signal",action="append",default=[])
    c.add_argument("--transport",default="inline-fallback"); c.add_argument("--transport-evidence",default="caller-selected")
    c.add_argument("--inline-reason"); c.add_argument("--tracking",choices=sorted(TRACKING),required=True)
    c.add_argument("--spec-read",required=True); c.add_argument("--drift-verdict",required=True)
    c.add_argument("--workflow-mode",choices=sorted(TRACKING),required=True); c.add_argument("--artifact-guard",required=True)
    c.add_argument("--output")
    v=sub.add_parser("verify"); v.add_argument("--route",required=True); v.add_argument("--cwd")
    n=sub.add_parser("node"); n.add_argument("--route",required=True); n.add_argument("--node",required=True)
    d=sub.add_parser("complete"); d.add_argument("--route",required=True); d.add_argument("--node",required=True); d.add_argument("--evidence",required=True); d.add_argument("--output")
    a=p.parse_args()
    if a.command=="compile":
        gate={"spec_read":{"satisfied":a.spec_read.lower() not in ("0","false","no"),"source":a.spec_read},
              "drift_verdict":a.drift_verdict,"workflow_mode":a.workflow_mode,
              "artifact_guard":{"satisfied":a.artifact_guard.lower() not in ("0","false","no"),"source":a.artifact_guard}}
        route=compile_route(a.capability,a.capability_mode,a.intensity,a.cwd,a.artifact_root,a.predicate,a.signal,a.transport,a.transport_evidence,a.inline_reason,a.tracking,gate)
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
                marker={"route_id":route["route_id"],"route_hash":route["route_hash"],"registry_digest":route["registry_digest"],
                        "node_id":a.node,"completion_gate":node["completion_gate"],
                        "evidence":{"path":str(evidence),"sha256":hashlib.sha256(evidence.read_bytes()).hexdigest()}}
                write_once(a.output or evidence.with_suffix(evidence.suffix+".completion.json"),marker)
                print(json.dumps(marker,sort_keys=True))

if __name__=="__main__":
    try: main()
    except (ValueError,TOPO.TopologyError) as exc: print(f"capability-route: {exc}",file=sys.stderr); raise SystemExit(64)
