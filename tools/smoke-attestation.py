#!/usr/bin/env python3
"""Create and verify content-bound smoke attestations before expensive lab runs."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

def digest(path):
    path=Path(path)
    if path.is_file(): return hashlib.sha256(path.read_bytes()).hexdigest()
    rows=[]
    for item in sorted(x for x in path.rglob("*") if x.is_file()):
        rows.append((str(item.relative_to(path)),hashlib.sha256(item.read_bytes()).hexdigest()))
    return hashlib.sha256(json.dumps(rows,separators=(",",":")).encode()).hexdigest()

def payload(paths, command, cwd):
    return {"schema_version":1,"cwd":str(Path(cwd).resolve(strict=True)),"command":command,
            "inputs":[{"path":str(Path(p).resolve(strict=True)),"sha256":digest(p)} for p in sorted(paths)]}

def verify(data):
    claimed=data.get("attestation_hash")
    if claimed:
        bare={k:v for k,v in data.items() if k!="attestation_hash"}
        actual="sha256:"+hashlib.sha256(json.dumps(bare,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        if claimed!=actual: raise ValueError("attestation hash mismatch")
    for row in data["inputs"]:
        if not Path(row["path"]).exists() or digest(row["path"])!=row["sha256"]: raise ValueError("stale smoke input: "+row["path"])
    if data.get("status")!="passed" or data.get("exit_code")!=0: raise ValueError("smoke did not pass")
    return True

def main():
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest="cmd",required=True)
    a=s.add_parser("attest"); a.add_argument("--input",action="append",required=True); a.add_argument("--cwd",required=True); a.add_argument("--output",required=True); a.add_argument("command",nargs=argparse.REMAINDER)
    v=s.add_parser("verify"); v.add_argument("--attestation",required=True)
    x=p.parse_args()
    if x.cmd=="verify": verify(json.loads(Path(x.attestation).read_text())); print("smoke_attestation=valid"); return
    command=x.command[1:] if x.command[:1]==["--"] else x.command
    if not command: raise SystemExit("smoke command required")
    data=payload(x.input,command,x.cwd); result=subprocess.run(command,cwd=data["cwd"])
    data.update(exit_code=result.returncode,status="passed" if result.returncode==0 else "failed")
    data["attestation_hash"]="sha256:"+hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    Path(x.output).parent.mkdir(parents=True,exist_ok=True); Path(x.output).write_text(json.dumps(data,indent=2)+"\n")
    raise SystemExit(result.returncode)
if __name__=="__main__":
 try: main()
 except ValueError as e: print("smoke-attestation:",e,file=sys.stderr); raise SystemExit(65)
