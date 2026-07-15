#!/usr/bin/env python3
import importlib.util, json, subprocess, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
R=load("route",ROOT/"utilities/capability-route.py"); G=load("guard",ROOT/"utilities/worker-route-guard.py")
ALL=["atomic-outcome","known-scope","no-shared-contract","no-resource-run","no-artifact-handoff","no-independent-verifier","focused-verification"]
DISPATCH={"tuples":[{"parent_harness":"codex","parent_transport":"headless","parent_sandbox":"fixture","child_harness":"codex","launch_authority":"conductor","status":"supported","probe_source":"fixture","probe_time":"2026-07-15T00:00:00Z","failure_class":""}],"native_subagent":[]}

class WorkerRouteGuardTest(unittest.TestCase):
 def route(self):
  gate={"spec_read":{"satisfied":True,"source":"prd-sha256"},"drift_verdict":"within-spec","workflow_mode":"tracked","artifact_guard":{"satisfied":True,"source":"conductor"}}
  return R.compile_route("autopilot-code","dev","strong",ROOT,ROOT,predicates=ALL,signals=["shared-contract"],transport="headless",tracking="tracked",tracked_gate_evidence=gate,dispatch_evidence=DISPATCH)
 def test_valid_and_scope_bound(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"route.json"; route=self.route(); path.write_text(json.dumps(route))
   _,node,_=G.validate_route_contract(path,"execute",ROOT,ROOT,"autopilot-code","strong",";".join(next(x for x in route["nodes"] if x["id"]=="execute")["write_scope"]),route["route_id"],route["route_hash"],route["registry_digest"])
   self.assertEqual(node["id"],"execute")
   self.assertRaisesRegex(G.WorkerRouteError,"expected=",G.validate_route_contract,path,"execute",ROOT,ROOT,"autopilot-code","strong","spec/**")
 def test_hash_and_reselection_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"route.json"; route=self.route(); route["cwd"]="/tmp"; path.write_text(json.dumps(route))
   self.assertRaisesRegex(G.WorkerRouteError,"stale or modified",G.validate_route_contract,path,"execute",ROOT,ROOT)
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"route.json"; route=self.route(); path.write_text(json.dumps(route))
   self.assertRaisesRegex(G.WorkerRouteError,"expected=autopilot-code",G.validate_route_contract,path,"execute",ROOT,ROOT,"code-execute")
 def test_source_commit_mismatch_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   repo=Path(td)/"repo"; repo.mkdir(); subprocess.run(["git","init","-q",str(repo)],check=True)
   subprocess.run(["git","-C",str(repo),"config","user.email","fixture@example.com"],check=True); subprocess.run(["git","-C",str(repo),"config","user.name","Fixture"],check=True)
   (repo/"x").write_text("a"); subprocess.run(["git","-C",str(repo),"add","x"],check=True); subprocess.run(["git","-C",str(repo),"commit","-qm","a"],check=True)
   gate={"spec_read":{"satisfied":True,"source":"prd"},"drift_verdict":"within-spec","workflow_mode":"tracked","artifact_guard":{"satisfied":True,"source":"conductor"}}
   route=R.compile_route("autopilot-code","dev","strong",repo,repo,signals=["shared-contract"],transport="headless",tracking="tracked",tracked_gate_evidence=gate,dispatch_evidence=DISPATCH); path=Path(td)/"route.json"; path.write_text(json.dumps(route))
   (repo/"x").write_text("b"); subprocess.run(["git","-C",str(repo),"commit","-am","b","-q"],check=True)
   with self.assertRaisesRegex(G.WorkerRouteError,"expected=.* observed=") as ctx: G.validate_route_contract(path,"execute",repo,repo)
   self.assertEqual(ctx.exception.reason,"route-source-commit-mismatch")

if __name__=="__main__": unittest.main()
