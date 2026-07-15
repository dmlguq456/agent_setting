#!/usr/bin/env python3
"""Materialize a registry route node onto existing adapter dispatch wrappers."""
import argparse, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROLE_MODE={"deep maker":"dev/refactor","fast implementer":"dev/backend","deep reviewer":"qa/test","fast reviewer":"qa/review","fast writer":"docs/writing","deep orchestrator":"ops/orchestration","orchestrator":"ops/orchestration"}
def main():
 p=argparse.ArgumentParser(); p.add_argument("--route",required=True); p.add_argument("--node",required=True); p.add_argument("--adapter",choices=("claude","codex","opencode"),required=True); p.add_argument("--action",choices=("dry-run","register","start"),default="dry-run"); p.add_argument("--slug",required=True); p.add_argument("--qa",default="standard"); p.add_argument("--parent"); p.add_argument("--prompt-text",default="Execute the selected immutable route node and emit its completion evidence."); p.add_argument("adapter_args",nargs=argparse.REMAINDER)
 a=p.parse_args(); route=json.loads(Path(a.route).read_text()); subprocess.run([sys.executable,str(ROOT/"utilities/capability-route.py"),"verify","--route",a.route,"--cwd",route["cwd"]],check=True,stdout=subprocess.DEVNULL)
 node=next((x for x in route["nodes"] if x["id"]==a.node),None)
 if not node: raise SystemExit("unknown route node")
 if node["kind"]=="resource-runner": print("resource_runner="+str(ROOT/"utilities/resource-runner.py")+"\nroute_node="+a.node); return
 wrapper=ROOT/"adapters"/a.adapter/"bin"/"dispatch-headless.py"
 argv=[sys.executable,str(wrapper),"--"+a.action,"--worktree",route["cwd"],"--slug",a.slug,"--capability",route["capability"],"--mode",ROLE_MODE.get(node.get("role"),"ops/orchestration"),"--qa",a.qa,"--intensity",route["effective_intensity"],"--depth",str(node.get("depth",1)),"--worker-role",node["kind"],"--owner",route["capability"],"--route-id",route["route_id"],"--route-hash",route["route_hash"],"--route-node",node["id"],"--registry-digest",route["registry_digest"],"--write-scope",";".join(node["write_scope"]),"--completion-gate",node["completion_gate"],"--prompt-text",a.prompt_text]
 if node.get("depth")==2:
  if not a.parent: raise SystemExit("depth-2 route node requires --parent")
  argv += ["--parent",a.parent]
 argv += (a.adapter_args[1:] if a.adapter_args[:1]==["--"] else a.adapter_args); raise SystemExit(subprocess.run(argv).returncode)
if __name__=="__main__": main()
