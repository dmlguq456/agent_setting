#!/usr/bin/env python3
"""Detached process runner with PID reuse-safe reattachment."""
import argparse, contextlib, fcntl, importlib.util, json, os, re, signal, subprocess, sys, time
from pathlib import Path
from resource_run_registry import (
    classify_identity,
    is_alive,
    proc_identity,
    register_registry,
)

SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
RETRY = re.compile(r"^(?P<base>.+)__a(?P<n>[1-9][0-9]*)$")
TERMINAL_STATUSES = {"succeeded", "failed"}

# The payload runs under a tiny POSIX-sh sentinel wrapper so its exit status survives
# every observer. A detached run whose launcher, supervisor, and session are all gone
# must still be able to prove *how* it ended; without this, "the process is not there"
# is indistinguishable from "the process finished successfully" (2026-08-04 BC_ResNet_tf).
SENTINEL_SCRIPT = (
    '"$@"; ec=$?; '
    'printf %s "$ec" > "$AGENT_RESOURCE_SENTINEL.partial" 2>/dev/null && '
    'mv "$AGENT_RESOURCE_SENTINEL.partial" "$AGENT_RESOURCE_SENTINEL" 2>/dev/null; '
    'exit $ec'
)

def alive(run):
    return is_alive(run)
def fail(message):
    print("resource-runner:", message, file=sys.stderr)
    raise SystemExit(65)
def locked_update(path, fn):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with open(str(path)+".lock","a+") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX); data=json.loads(path.read_text()) if path.exists() else {"schema_version":1,"runs":{}}
        result=fn(data); tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(json.dumps(data,indent=2)+"\n"); os.replace(tmp,path); return result

def read_sentinel(path):
    """Return the payload's recorded exit code, or None when it left no proof."""
    if not path:
        return None
    try:
        raw=Path(path).read_text(encoding="utf-8",errors="replace").strip()
    except OSError:
        return None
    try:
        return int(raw)
    except ValueError:
        return None

def settle(registry, run_id, run):
    """Persist the terminal row once the process is verifiably gone.

    Any observer may call this — `reap`, `status`, `list`, a continuation supervisor, or
    a Fleet-adjacent status pass — and they converge on the same row. A stored
    `running` that outlives its process is a defect, not a state, so termination is
    recorded by whoever notices it first and is idempotent afterwards.
    """
    liveness,_current,reason=classify_identity(run)
    if liveness=="working":
        return run, False
    exit_code=read_sentinel(run.get("sentinel"))
    if exit_code==0:
        status,state,failure="succeeded","STAGE_SUCCEEDED",None
    elif exit_code is not None:
        status,state,failure="failed","FAILED_RETRYABLE",f"exit-{exit_code}"
    elif liveness=="stale":
        # PID reuse or an identity mismatch: the recorded process is gone, and it left
        # no exit proof. Absence of evidence is never success.
        status,state,failure="failed","FAILED_RETRYABLE",reason
    else:
        status,state,failure="failed","FAILED_RETRYABLE","no-exit-sentinel"
    def apply(data):
        row=data["runs"].get(run_id)
        if row is None: raise ValueError("unknown run id")
        if row.get("status") in TERMINAL_STATUSES:
            return row, False
        row.update({"status":status,"exit_code":exit_code,"ended_at":time.time(),
                    "workflow_state":state,"failure_class":failure,
                    "liveness_reason":reason})
        return row, True
    return locked_update(registry,apply)
def main():
    p=argparse.ArgumentParser(); p.add_argument("--registry"); s=p.add_subparsers(dest="cmd",required=True)
    a=s.add_parser("start"); a.add_argument("--run-id",required=True); a.add_argument("--cwd",required=True); a.add_argument("--log",required=True); a.add_argument("--route",required=True); a.add_argument("--node",required=True); a.add_argument("--smoke-attestation"); a.add_argument("--config-manifest")
    a.add_argument("--parent-attempt-id",help="registered headless attempt that owns this resource child")
    a.add_argument("command",nargs=argparse.REMAINDER)
    for name in ("status","stop","tail","reap"):
        x=s.add_parser(name); x.add_argument("--run-id",required=True)
    s.add_parser("list")
    index_cmd=s.add_parser("index"); index_cmd.add_argument("--registry",required=True)
    args=p.parse_args()
    if args.cmd=="index":
        registry=Path(args.registry).resolve(strict=True)
        indexed=register_registry(registry)
        print(json.dumps({"registry":str(registry),**indexed},sort_keys=True))
        return
    if not args.registry: fail("--registry is required")
    registry=Path(args.registry).resolve()
    if args.cmd=="start":
        cwd=Path(args.cwd).resolve(strict=True)
        command=args.command[1:] if args.command[:1]==["--"] else args.command
        if not command: fail("command required")
        guard_path=Path(__file__).parents[1]/"hooks"/"material-route-guard.py"
        spec=importlib.util.spec_from_file_location("material_route_guard", guard_path)
        guard=importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(guard)
        route=guard.verify_route(
            Path(args.route), cwd, guard.resolve_agent_home(), expected_node=args.node,
            accepted_capabilities={"autopilot-code", "autopilot-lab"},
        )
        node=next((n for n in route["nodes"] if isinstance(n,dict) and n.get("id")==args.node),None)
        if not node or node.get("kind")!="resource-runner" or node.get("resource_transport")!="detached-process":
            fail("route node is not detached resource-runner")
        if not args.smoke_attestation: fail("hash-bound smoke attestation required")
        subprocess.run([sys.executable,str(Path(__file__).parents[1]/"tools/smoke-attestation.py"),"verify","--attestation",args.smoke_attestation],check=True)
        provenance = {}
        if args.config_manifest:
            manifest = json.loads(Path(args.config_manifest).read_text())
            verify_tool = Path(__file__).parents[1] / "tools" / "lab-config-provenance.py"
            subprocess.run([sys.executable, str(verify_tool), "verify", "--manifest", args.config_manifest], check=True)
            if not SAFE_RUN_ID.match(args.run_id):
                fail("invalid --run-id")
            # --attempt suffix policy: "<manifest_run_id>__a<N>" retries the same
            # sealed manifest under a distinct registry key; anything else must
            # match the manifest's run_id exactly. The registry row's run_id is
            # always args.run_id (the registry key), never the manifest's.
            # Order is load-bearing (A9): the exact match must be checked before
            # the regex, since a computed run id's 12-hex hash tail can
            # coincidentally read as "a" + digits and get mis-split otherwise.
            manifest_run_id = manifest["run_id"]
            if args.run_id != manifest_run_id:
                m = RETRY.fullmatch(args.run_id)
                if not (m and m["base"] == manifest_run_id):
                    fail("run id does not match sealed manifest")
            attestation = json.loads(Path(args.smoke_attestation).read_text())
            if attestation.get("config_sha256") != manifest.get("snapshot_sha256"):
                fail("config provenance does not match smoke attestation")
            if attestation.get("config_source_sha256") != manifest.get("source_sha256"):
                fail("config source provenance does not match smoke attestation")
            try:
                attested_source = Path(attestation.get("config_source_path", "")).resolve(strict=False)
            except (OSError, ValueError):
                attested_source = None
            if attested_source != Path(manifest["source_path"]).resolve(strict=False):
                fail("config source path does not match smoke attestation")
            provenance = {"config_ref": manifest["config_ref"], "config_sha256": manifest["snapshot_sha256"],
                          "source_commit": manifest["source_commit"], "source_dirty": manifest["source_dirty"],
                          "source_git_state": manifest.get("source_git_state", "unknown-no-git"),
                          "config_layout": manifest.get("config_layout", "unknown")}
        log=Path(args.log).resolve()
        sentinel=Path(str(log)+".exit")
        placeholder={"run_id":args.run_id,"cwd":str(cwd),"log":str(log),"command":command,
                     **provenance,"route":args.route,"node":args.node,"status":"launching",
                     "sentinel":str(sentinel),
                     "parent_attempt_id":args.parent_attempt_id,
                     "workflow_state":"READY","started_at":time.time()}
        def reserve(data):
            if args.run_id in data["runs"]: raise ValueError("run id already exists")
            data["runs"][args.run_id]=placeholder
        locked_update(registry,reserve)
        try:
            register_registry(registry)
        except Exception:
            locked_update(registry,lambda data:data["runs"].pop(args.run_id,None))
            raise
        log.parent.mkdir(parents=True,exist_ok=True)
        with contextlib.suppress(OSError):
            sentinel.unlink()
        with contextlib.suppress(OSError):
            Path(str(sentinel)+".partial").unlink()
        launch_argv=["/bin/sh","-c",SENTINEL_SCRIPT,"resource-runner",*command]
        environment={**os.environ,"AGENT_RESOURCE_SENTINEL":str(sentinel)}
        out=open(log,"ab",buffering=0)
        try:
            proc=subprocess.Popen(launch_argv,cwd=cwd,env=environment,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
        except Exception:
            out.close()
            locked_update(registry,lambda data:data["runs"].pop(args.run_id,None))
            raise
        ident=None
        for _ in range(20):
            ident=proc_identity(proc.pid)
            if ident: break
            time.sleep(.01)
        if not ident:
            proc.kill()
            locked_update(registry,lambda data:data["runs"].pop(args.run_id,None))
            fail("could not establish process identity")
        run={**ident,"run_id":args.run_id,"process_group":os.getpgid(proc.pid),"cwd":str(cwd),"log":str(log),"command":command,
             "launch_argv":launch_argv,"sentinel":str(sentinel),
             "parent_attempt_id":args.parent_attempt_id,**provenance,
             "route":args.route,"node":args.node,"status":"running","workflow_state":"RUNNING",
             "started_at":placeholder["started_at"]}
        def add(data):
            data["runs"][args.run_id]=run
        locked_update(registry,add); print(json.dumps(run)); return
    data=json.loads(registry.read_text())
    if args.cmd=="list":
        rows=[]
        for run_id,row in sorted(data.get("runs",{}).items()):
            if isinstance(row,dict):
                row,_settled=settle(registry,run_id,row)
                liveness=classify_identity(row)[0]
                rows.append({**row,"liveness":liveness})
        print(json.dumps(rows,sort_keys=True)); return
    run=data["runs"].get(args.run_id)
    if not run: fail("unknown run id")
    if args.cmd=="tail": print(Path(run["log"]).read_text(errors="replace"),end=""); return
    if args.cmd in ("status","reap"):
        run,settled=settle(registry,args.run_id,run)
        if args.cmd=="reap":
            liveness=classify_identity(run)[0]
            print(json.dumps({**run,"liveness":liveness,"settled":settled},sort_keys=True)); return
    liveness,_,_=classify_identity(run)
    if args.cmd=="stop":
        if liveness!="working": fail("process identity is stale")
        try:
            pid=int(run["pid"]); group=int(run["process_group"])
            if os.getpgid(pid)!=group or group!=pid: fail("process group identity is stale")
        except (OSError,TypeError,ValueError,KeyError):
            fail("process group identity is stale")
        # Close the TOCTOU window as far as userspace allows: identity is
        # re-read immediately before signalling the exact group leader.
        if classify_identity(run)[0]!="working": fail("process identity changed before signal")
        try:
            if os.getpgid(pid)!=group: fail("process group changed before signal")
        except OSError:
            fail("process group changed before signal")
        os.killpg(group,signal.SIGTERM)
    status=run.get("status") if run.get("status") in TERMINAL_STATUSES else \
        {"working":"running","exited":"exited","stale":"stale"}[liveness]
    print(json.dumps({**run,"status":status,"liveness":liveness},sort_keys=True))
if __name__=="__main__":
 try: main()
 except ValueError as e: print("resource-runner:",e,file=sys.stderr); raise SystemExit(65)
