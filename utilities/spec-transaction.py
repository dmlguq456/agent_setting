#!/usr/bin/env python3
"""Hold the canonical spec lock across one route-declared transaction."""
from __future__ import annotations

import argparse
import fcntl
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("worker_route_guard",ROOT/"utilities/worker-route-guard.py")
GUARD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(GUARD)


def emit(event, events=None):
    line=json.dumps(event,sort_keys=True)
    print(line,flush=True)
    if events:
        with open(events,"a",encoding="utf-8") as fh: fh.write(line+"\n")


def next_version(spec_root: Path) -> int:
    versions=spec_root/"_internal"/"versions"
    found=[]
    if versions.is_dir():
        for row in versions.iterdir():
            match=re.fullmatch(r"v([0-9]+)",row.name)
            if match and row.is_dir(): found.append(int(match.group(1)))
    return max(found,default=0)+1


def main():
    parser=argparse.ArgumentParser(); sub=parser.add_subparsers(dest="command",required=True); run=sub.add_parser("run")
    run.add_argument("--artifact-root",required=True); run.add_argument("--worktree",required=True)
    run.add_argument("--route",required=True); run.add_argument("--node",required=True)
    run.add_argument("--wait-timeout",type=float,default=600); run.add_argument("--poll",type=float,default=.05)
    run.add_argument("--events"); run.add_argument("--require-snapshot",action="store_true")
    run.add_argument("transaction",nargs=argparse.REMAINDER)
    args=parser.parse_args()
    command=args.transaction[1:] if args.transaction[:1]==["--"] else args.transaction
    if not command: parser.error("transaction command required after --")
    artifact=Path(args.artifact_root); worktree=Path(args.worktree)
    try: route,node,_=GUARD.validate_route_contract(args.route,args.node,worktree,artifact)
    except GUARD.WorkerRouteError as exc:
        emit({"status":"blocked","reason":exc.reason,"detail":str(exc),"route_id":exc.route_id,"route_file":args.route},args.events); return 65
    if not route.get("spec_touch"):
        emit({"status":"blocked","reason":"spec-touch-not-declared","route_id":route["route_id"],"route_file":args.route},args.events); return 65
    if not any((scope[:-3] if scope.endswith("/**") else scope)=="spec" or (scope[:-3] if scope.endswith("/**") else scope).startswith("spec/") for scope in node["write_scope"]):
        emit({"status":"blocked","reason":"route-node-scope-mismatch","route_id":route["route_id"],"node_id":node["id"]},args.events); return 65
    lock_path=artifact/".pipeline-lock"; lock_path.parent.mkdir(parents=True,exist_ok=True)
    with lock_path.open("a+",encoding="utf-8") as lock:
        blocked=False
        waited=False
        try: fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            blocked=True; waited=True; lock.seek(0); owner=lock.read().strip()
            emit({"status":"BLOCKED","action":"wait","route_id":route["route_id"],"owner":owner},args.events)
        deadline=time.monotonic()+max(0,args.wait_timeout)
        while blocked:
            try: fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB); blocked=False
            except BlockingIOError:
                if time.monotonic()>=deadline:
                    emit({"status":"blocked","reason":"spec-lock-timeout","route_id":route["route_id"]},args.events); return 3
                time.sleep(max(.01,args.poll))
        spec_root=artifact/"spec"; version=next_version(spec_root)
        owner={"route_id":route["route_id"],"node_id":node["id"],"worktree":str(worktree.resolve()),"pid":os.getpid(),"next_version":version}
        lock.seek(0); lock.truncate(); lock.write(json.dumps(owner,sort_keys=True)+"\n"); lock.flush(); os.fsync(lock.fileno())
        emit({"status":"acquired","action":"latest-reread","route_id":route["route_id"],"next_version":version,"waited":waited},args.events)
        env={**os.environ,"AGENT_SPEC_LOCK_HELD":"1","AGENT_SPEC_NEXT_VERSION":str(version),"AGENT_ROUTE_FILE":str(Path(args.route).resolve()),"AGENT_ROUTE_ID":route["route_id"],"AGENT_ROUTE_NODE":node["id"]}
        result=subprocess.run(command,cwd=str(worktree),env=env)
        version_dir=spec_root/"_internal"/"versions"/f"v{version}"
        if result.returncode==0 and args.require_snapshot and not version_dir.is_dir():
            emit({"status":"blocked","reason":"version-snapshot-missing","route_id":route["route_id"],"version":version},args.events); result=subprocess.CompletedProcess(command,65)
        emit({"status":"released","route_id":route["route_id"],"version":version,"result":result.returncode},args.events)
        lock.seek(0); lock.truncate(); lock.flush(); os.fsync(lock.fileno())
        return result.returncode


if __name__=="__main__": raise SystemExit(main())
