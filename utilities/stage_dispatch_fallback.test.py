#!/usr/bin/env python3
import importlib.util, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
S=importlib.util.spec_from_file_location("route",ROOT/"utilities/capability-route.py"); R=importlib.util.module_from_spec(S); S.loader.exec_module(R)

class FallbackTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); base=Path(self.tmp.name); self.repo=base/"repo"; self.repo.mkdir()
  subprocess.run(["git","init","-q",str(self.repo)],check=True); subprocess.run(["git","-C",str(self.repo),"config","user.email","fixture@example.com"],check=True); subprocess.run(["git","-C",str(self.repo),"config","user.name","Fixture"],check=True)
  (self.repo/"x").write_text("x"); subprocess.run(["git","-C",str(self.repo),"add","x"],check=True); subprocess.run(["git","-C",str(self.repo),"commit","-qm","init"],check=True)
  self.art=base/".agent_reports"; self.art.mkdir(); self.jobs=base/"jobs.log"
 def tearDown(self): self.tmp.cleanup()
 def tuple(self,child,status,authority="conductor"):
  return {"parent_harness":"codex","parent_transport":"headless","parent_sandbox":"workspace-write","child_harness":child,"launch_authority":authority,"status":status,"probe_source":"fixture","probe_time":"2026-07-15T00:00:00Z","failure_class":"network-operation-not-permitted" if status!="supported" else ""}
 def route(self,native="unsupported",same_status="unsupported"):
  gate={"spec_read":{"satisfied":True,"source":"fixture"},"drift_verdict":"within-spec","workflow_mode":"tracked","artifact_guard":{"satisfied":True,"source":"fixture"}}
  evidence={"tuples":[self.tuple("codex",same_status),self.tuple("claude","supported","ancestor-broker")],"native_subagent":[{"harness":"codex","status":native,"check_source":"fixture"}]}
  route=R.compile_route("autopilot-code","dev","strong",self.repo,self.art,signals=["shared-contract"],transport="headless",tracking="tracked",tracked_gate_evidence=gate,dispatch_evidence=evidence)
  path=Path(self.tmp.name)/"route.json"; path.write_text(json.dumps(route),encoding="utf-8"); return path
 def run_chain(self,path,*extra):
  cmd=[sys.executable,str(ROOT/"utilities/stage-dispatch-fallback.py"),"--route",str(path),"--node","plan","--slug","fallback-plan","--parent","owner","--mode","dev/backend","--model-role","deep maker","--jobs",str(self.jobs),"--dry-run",*extra]
  env={**os.environ,"AGENT_HOME":str(ROOT),"AGENT_ARTIFACT_ROOT":str(self.art)}
  return subprocess.run(cmd,text=True,capture_output=True,env=env)
 def test_cross_harness_precedes_inline(self):
  result=self.run_chain(self.route())
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
  self.assertIn("selected_hop=cross-harness-headless",result.stdout)
  self.assertIn("child_harness=claude",result.stdout)
  self.assertIn("depth=2",result.stdout); self.assertIn("parent=owner",result.stdout)
  self.assertIn("launch_authority=ancestor-broker",result.stdout)
 def test_failed_same_and_cross_degrade_in_order(self):
  path=self.route(native="supported")
  same="codex/headless/workspace-write/codex/conductor"; cross="codex/headless/workspace-write/claude/ancestor-broker"
  result=self.run_chain(path,"--failed-tuple",same,"--failed-tuple",cross)
  self.assertEqual(result.returncode,78,result.stdout+result.stderr); self.assertIn("selected_hop=native-subagent",result.stdout)
  route=json.loads(path.read_text()); route["dispatch_evidence"]["native_subagent"][0]["status"]="unsupported"
  for node in route["nodes"]: node["dispatch_fallback"][2]["candidates"][0]["status"]="unsupported"
  route["route_hash"]=R.route_hash(route); route["route_id"]="rt-"+route["route_hash"].split(":",1)[1][:16]; path.write_text(json.dumps(route))
  result=self.run_chain(path,"--failed-tuple",same,"--failed-tuple",cross)
  self.assertEqual(result.returncode,79,result.stdout+result.stderr); self.assertIn("selected_hop=inline",result.stdout)
 def test_registry_prevents_unchanged_same_harness_retry(self):
  path=self.route(same_status="supported"); route=json.loads(path.read_text())
  pipe=f"capability=autopilot-code,route_id={route['route_id']},route_node=plan,parent=owner,attempt_id=att-prior000000,parent_harness=codex,parent_transport=headless,parent_sandbox=workspace-write,child_harness=codex,launch_authority=conductor,note=dead-network-operation-not-permitted"
  self.jobs.write_text(f"2026-07-15T00:00:00Z\tdone\t/repo\t{self.repo}\tfallback-plan\t{pipe}\n")
  result=self.run_chain(path)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
  self.assertIn("selected_hop=cross-harness-headless",result.stdout)
  self.assertIn("skipped-prior-unchanged-failure",result.stdout)
  self.assertIn("prior_attempt_ids=att-prior000000",result.stdout)

if __name__=="__main__": unittest.main()
