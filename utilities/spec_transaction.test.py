#!/usr/bin/env python3
import importlib.util, json, os, subprocess, sys, tempfile, time, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
R=load("route",ROOT/"utilities/capability-route.py")
DISPATCH={"tuples":[{"parent_harness":"codex","parent_transport":"headless","parent_sandbox":"fixture","child_harness":"codex","launch_authority":"conductor","status":"supported","probe_source":"fixture","probe_time":"2026-07-16T00:00:00Z","failure_class":""}],"native_subagent":[]}

class SpecTransactionTest(unittest.TestCase):
 def test_blocked_wait_reread_next_version(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); artifact=root/".agent_reports"; spec=artifact/"spec"; spec.mkdir(parents=True); (spec/"prd.md").write_text("v0\n")
   subprocess.run(["git","init","-q",str(root)],check=True); subprocess.run(["git","-C",str(root),"config","user.email","fixture@example.com"],check=True); subprocess.run(["git","-C",str(root),"config","user.name","Fixture"],check=True); (root/"README").write_text("x\n"); subprocess.run(["git","-C",str(root),"add","README"],check=True); subprocess.run(["git","-C",str(root),"commit","-qm","init"],check=True)
   gate={"spec_read":{"satisfied":True,"source":"fixture"},"drift_verdict":"within-spec","workflow_mode":"tracked","artifact_guard":{"satisfied":True,"source":"fixture"}}
   route=R.compile_route("autopilot-spec","update","strong",root,artifact,signals=["shared-contract"],transport="headless",tracking="tracked",tracked_gate_evidence=gate,dispatch_evidence=DISPATCH)
   route_path=root/"route.json"; route_path.write_text(json.dumps(route)); events=root/"events.jsonl"
   code="import os,time; from pathlib import Path; p=Path(os.environ['AGENT_ARTIFACT_ROOT'])/'spec/_internal/versions'/('v'+os.environ['AGENT_SPEC_NEXT_VERSION']); p.mkdir(parents=True); (p/'prd.md').write_text('snapshot'); time.sleep(float(os.environ.get('HOLD','0')))"
   base=[sys.executable,str(ROOT/"utilities/spec-transaction.py"),"run","--artifact-root",str(artifact),"--worktree",str(root),"--route",str(route_path),"--node","prd-transaction","--wait-timeout","3","--poll",".02","--events",str(events),"--require-snapshot","--",sys.executable,"-c",code]
   env={**os.environ,"AGENT_ARTIFACT_ROOT":str(artifact),"HOLD":".4"}; first=subprocess.Popen(base,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   deadline=time.time()+2
   while time.time()<deadline and (not events.exists() or '"status": "acquired"' not in events.read_text()): time.sleep(.02)
   env2={**os.environ,"AGENT_ARTIFACT_ROOT":str(artifact),"HOLD":"0"}; second=subprocess.Popen(base,env=env2,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   out1,err1=first.communicate(timeout=4); out2,err2=second.communicate(timeout=4)
   self.assertEqual(first.returncode,0,out1+err1); self.assertEqual(second.returncode,0,out2+err2)
   rows=[json.loads(line) for line in events.read_text().splitlines()]
   self.assertTrue(any(row["status"]=="BLOCKED" for row in rows)); self.assertTrue((spec/"_internal/versions/v1/prd.md").is_file()); self.assertTrue((spec/"_internal/versions/v2/prd.md").is_file()); self.assertEqual(len(list((spec/"_internal/versions").glob("v*/prd.md"))),2)
 def test_spec_touch_required(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); artifact=root/".agent_reports"; artifact.mkdir(); subprocess.run(["git","init","-q",str(root)],check=True)
   gate={"spec_read":{"satisfied":True,"source":"fixture"},"drift_verdict":"within-spec","workflow_mode":"tracked","artifact_guard":{"satisfied":True,"source":"fixture"}}
   route=R.compile_route("autopilot-code","dev","direct",root,artifact,predicates=["atomic-outcome","known-scope","no-shared-contract","no-resource-run","no-artifact-handoff","no-independent-verifier","focused-verification"],transport="inline-fallback",inline_reason="atomic-direct",tracking="tracked",tracked_gate_evidence=gate)
   path=root/"route.json"; path.write_text(json.dumps(route)); p=subprocess.run([sys.executable,str(ROOT/"utilities/spec-transaction.py"),"run","--artifact-root",str(artifact),"--worktree",str(root),"--route",str(path),"--node","inline","--",sys.executable,"-c","pass"],text=True,capture_output=True)
   self.assertEqual(p.returncode,65); self.assertIn("spec-touch-not-declared",p.stdout)
 def test_component_spec_root_owns_its_version_sequence(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); artifact=root/".agent_reports"; component=artifact/"spec/component"; component.mkdir(parents=True)
   subprocess.run(["git","init","-q",str(root)],check=True); subprocess.run(["git","-C",str(root),"config","user.email","fixture@example.com"],check=True); subprocess.run(["git","-C",str(root),"config","user.name","Fixture"],check=True); (root/"README").write_text("x\n"); subprocess.run(["git","-C",str(root),"add","README"],check=True); subprocess.run(["git","-C",str(root),"commit","-qm","init"],check=True)
   gate={"spec_read":{"satisfied":True,"source":"fixture"},"drift_verdict":"within-spec","workflow_mode":"tracked","artifact_guard":{"satisfied":True,"source":"fixture"}}
   route=R.compile_route("autopilot-spec","update","strong",root,artifact,signals=["shared-contract"],transport="headless",tracking="tracked",tracked_gate_evidence=gate,dispatch_evidence=DISPATCH)
   route_path=root/"route.json"; route_path.write_text(json.dumps(route))
   code="import os; from pathlib import Path; p=Path(os.environ['AGENT_SPEC_ROOT'])/'_internal/versions'/('v'+os.environ['AGENT_SPEC_NEXT_VERSION']); p.mkdir(parents=True); (p/'prd.md').write_text('snapshot')"
   command=[sys.executable,str(ROOT/"utilities/spec-transaction.py"),"run","--artifact-root",str(artifact),"--worktree",str(root),"--route",str(route_path),"--node","prd-transaction","--spec-root",str(component),"--require-snapshot","--",sys.executable,"-c",code]
   result=subprocess.run(command,text=True,capture_output=True)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   self.assertTrue((component/"_internal/versions/v1/prd.md").is_file())
   self.assertFalse((artifact/"spec/_internal/versions/v1").exists())

if __name__=="__main__": unittest.main()
