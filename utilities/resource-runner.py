#!/usr/bin/env python3
"""Detached process runner with PID reuse-safe reattachment."""
import argparse, fcntl, hashlib, json, os, signal, subprocess, sys, time
from pathlib import Path

def proc_identity(pid):
    stat=Path(f"/proc/{pid}/stat"); cmd=Path(f"/proc/{pid}/cmdline")
    if not stat.exists() or not cmd.exists(): return None
    fields=stat.read_text().split(); return {"pid":pid,"starttime":fields[21],"command_hash":hashlib.sha256(cmd.read_bytes()).hexdigest()}
def alive(run):
    cur=proc_identity(run["pid"]); return bool(cur and all(str(cur[k])==str(run[k]) for k in ("pid","starttime","command_hash")))
def locked_update(path, fn):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with open(str(path)+".lock","a+") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX); data=json.loads(path.read_text()) if path.exists() else {"schema_version":1,"runs":{}}
        result=fn(data); tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(json.dumps(data,indent=2)+"\n"); os.replace(tmp,path); return result
def main():
    p=argparse.ArgumentParser(); p.add_argument("--registry",required=True); s=p.add_subparsers(dest="cmd",required=True)
    a=s.add_parser("start"); a.add_argument("--run-id",required=True); a.add_argument("--cwd",required=True); a.add_argument("--log",required=True); a.add_argument("--route"); a.add_argument("--node"); a.add_argument("--smoke-attestation"); a.add_argument("command",nargs=argparse.REMAINDER)
    for name in ("status","stop","tail"):
        x=s.add_parser(name); x.add_argument("--run-id",required=True)
    args=p.parse_args(); registry=Path(args.registry).resolve()
    if args.cmd=="start":
        cwd=Path(args.cwd).resolve(strict=True); log=Path(args.log).resolve(); log.parent.mkdir(parents=True,exist_ok=True)
        command=args.command[1:] if args.command[:1]==["--"] else args.command
        if not command: raise SystemExit("command required")
        if args.route:
            route=json.loads(Path(args.route).read_text()); node=next((n for n in route["nodes"] if n["id"]==args.node),None)
            if not node or node["kind"]!="resource-runner": raise SystemExit("route node is not resource-runner")
            if route["cwd"]!=str(cwd): raise SystemExit("route cwd mismatch")
        if not args.smoke_attestation: raise SystemExit("hash-bound smoke attestation required")
        subprocess.run([sys.executable,str(Path(__file__).parents[1]/"tools/smoke-attestation.py"),"verify","--attestation",args.smoke_attestation],check=True)
        out=open(log,"ab",buffering=0); proc=subprocess.Popen(command,cwd=cwd,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
        ident=None
        for _ in range(20):
            ident=proc_identity(proc.pid)
            if ident: break
            time.sleep(.01)
        if not ident: proc.kill(); raise SystemExit("could not establish process identity")
        run={**ident,"run_id":args.run_id,"process_group":os.getpgid(proc.pid),"cwd":str(cwd),"log":str(log),"command":command,
             "route":args.route,"node":args.node,"status":"running"}
        def add(data):
            if args.run_id in data["runs"]: raise ValueError("run id already exists")
            data["runs"][args.run_id]=run
        locked_update(registry,add); print(json.dumps(run)); return
    data=json.loads(registry.read_text()); run=data["runs"].get(args.run_id)
    if not run: raise SystemExit("unknown run id")
    if args.cmd=="tail": print(Path(run["log"]).read_text(errors="replace"),end=""); return
    is_alive=alive(run)
    if args.cmd=="stop":
        if not is_alive: raise SystemExit("process identity is stale")
        os.killpg(run["process_group"],signal.SIGTERM)
    print(json.dumps({**run,"status":"running" if is_alive else "exited"},sort_keys=True))
if __name__=="__main__":
 try: main()
 except ValueError as e: print("resource-runner:",e,file=sys.stderr); raise SystemExit(65)
