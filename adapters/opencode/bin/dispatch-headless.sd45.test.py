#!/usr/bin/env python3
import importlib.util,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=importlib.util.spec_from_file_location("route",ROOT/"utilities/capability-route.py"); R=importlib.util.module_from_spec(S); S.loader.exec_module(R)
class OpenCodeSD45(unittest.TestCase):
 def test_route_consumer_and_capability_reselection_refusal(self):
  with tempfile.TemporaryDirectory() as td:
   base=Path(td); repo=base/"repo"; repo.mkdir(); subprocess.run(["git","init","-q",str(repo)],check=True); subprocess.run(["git","-C",str(repo),"config","user.email","fixture@example.com"],check=True); subprocess.run(["git","-C",str(repo),"config","user.name","Fixture"],check=True); (repo/"x").write_text("x"); subprocess.run(["git","-C",str(repo),"add","x"],check=True); subprocess.run(["git","-C",str(repo),"commit","-qm","init"],check=True)
   art=base/".agent_reports"; art.mkdir(); gate={"spec_read":{"satisfied":True,"source":"opencode-fixture"},"drift_verdict":"within-spec","workflow_mode":"tracked","artifact_guard":{"satisfied":True,"source":"opencode-fixture"}}
   route=R.compile_route("autopilot-code","dev","strong",repo,art,signals=["shared-contract"],transport="headless",tracking="tracked",tracked_gate_evidence=gate); path=base/"route.json"; path.write_text(json.dumps(route)); node=next(x for x in route["nodes"] if x["id"]=="execute"); jobs=base/"jobs.log"; logs=base/"logs"
   args=[sys.executable,str(ROOT/"adapters/opencode/bin/dispatch-headless.py"),"--register","--worktree",str(repo),"--slug","opencode-sd45","--capability","autopilot-code","--mode","dev/backend","--qa","standard","--intensity","strong","--depth","2","--parent","owner","--route-file",str(path),"--route-id",route["route_id"],"--route-hash",route["route_hash"],"--route-node","execute","--registry-digest",route["registry_digest"],"--write-scope",";".join(node["write_scope"]),"--completion-gate",node["completion_gate"],"--model","provider/test","--variant","low","--jobs",str(jobs),"--log-dir",str(logs)]
   env={**os.environ,"AGENT_HOME":str(ROOT),"AGENT_ARTIFACT_ROOT":str(art),"OPENCODE_CONFIG_CONTENT":"{}"}; ok=subprocess.run(args,text=True,capture_output=True,env=env); self.assertEqual(ok.returncode,0,ok.stderr); prompt=(logs/"opencode-sd45.opencode.prompt.txt").read_text(); self.assertIn("consume the immutable record",prompt); self.assertNotIn("status -> prompt-signal -> mode -> route\n",prompt)
   bad=args.copy(); bad[bad.index("autopilot-code")]="audit"; denied=subprocess.run(bad,text=True,capture_output=True,env=env); self.assertEqual(denied.returncode,65); self.assertIn("capability-reselection",denied.stderr)
   legacy=[sys.executable,str(ROOT/"adapters/opencode/bin/dispatch-headless.py"),"--dry-run","--worktree",str(repo),"--slug","opencode-legacy-scope","--capability","autopilot-code","--mode","dev/backend","--qa","standard","--write-scope","source/**","--model","provider/test","--variant","low"]
   compatible=subprocess.run(legacy,text=True,capture_output=True,env=env); self.assertEqual(compatible.returncode,0,compatible.stderr); self.assertIn("status=dry-run",compatible.stdout)
if __name__=="__main__": unittest.main()
