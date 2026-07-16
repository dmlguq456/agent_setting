#!/usr/bin/env python3
import hashlib, json, os, subprocess, sys, tempfile, time, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; SCRIPT=ROOT/"utilities/dispatch-registry.py"
class RegistryTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.base=Path(self.tmp.name); self.jobs=self.base/"jobs.log"
  self.proc=subprocess.Popen(["sleep","60"]); start=(Path("/proc")/str(self.proc.pid)/"stat").read_text().split()[21]
  rows=[
   f"2026-07-16T00:00:00Z\topen\t/r\t/w\tactive\troute_id=r1,route_node=test,attempt_id=att-active0001,parent_sid=s1,pid={self.proc.pid},pid_start={start}",
   "2026-07-16T00:00:01Z\topen\t/r\t/w\tdead\troute_id=r1,route_node=report,attempt_id=att-dead000001,parent_sid=s1,pid=99999999,pid_start=1",
   "2026-07-16T00:00:02Z\topen\t/r\t/w\tother\troute_id=r2,route_node=test,attempt_id=att-other00001,parent_sid=s2,pid=99999998,pid_start=1"]
  self.jobs.write_text("\n".join(rows)+"\n")
 def tearDown(self):
  if self.proc.poll() is None:self.proc.kill()
  self.proc.wait();self.tmp.cleanup()
 def invoke(self,*args):
  return subprocess.run([sys.executable,str(SCRIPT),*args,"--jobs",str(self.jobs),"--agent-home",str(self.base)],capture_output=True,text=True)
 def test_current_filters_before_totals(self):
  r=self.invoke("current","--route","r1");self.assertEqual(r.returncode,0,r.stdout+r.stderr);data=json.loads(r.stdout)
  self.assertEqual(data["total"],2);self.assertEqual({x["slug"] for x in data["rows"]},{"active","dead"})
 def test_reconcile_closes_only_selected_exact_dead(self):
  before=self.jobs.read_text();dry=self.invoke("reconcile","--attempt","att-dead000001");self.assertEqual(json.loads(dry.stdout)["closed"],0);self.assertEqual(self.jobs.read_text(),before)
  applied=self.invoke("reconcile","--attempt","att-dead000001","--apply");self.assertEqual(json.loads(applied.stdout)["closed"],1)
  text=self.jobs.read_text();self.assertIn("note=dead-exact-pid",text);self.assertIn("\topen\t/r\t/w\tactive\t",text);self.assertIn("\topen\t/r\t/w\tother\t",text)
  again=self.invoke("reconcile","--attempt","att-dead000001","--apply");self.assertEqual(json.loads(again.stdout)["closed"],0)
 def test_codex_preflight_projects_current_and_dry_reconcile(self):
  pre=ROOT/"adapters/codex/bin/preflight.sh"
  current=subprocess.run([str(pre),"dispatch-current","--jobs",str(self.jobs),"--route","r1","--agent-home",str(self.base)],capture_output=True,text=True,env={**os.environ,"AGENT_HOME":str(ROOT)})
  self.assertEqual(current.returncode,0,current.stdout+current.stderr);self.assertEqual(json.loads(current.stdout)["total"],2)
  before=self.jobs.read_text();dry=subprocess.run([str(pre),"dispatch-reconcile","--jobs",str(self.jobs),"--route","r1","--agent-home",str(self.base)],capture_output=True,text=True,env={**os.environ,"AGENT_HOME":str(ROOT)})
  self.assertEqual(dry.returncode,0,dry.stdout+dry.stderr);self.assertEqual(self.jobs.read_text(),before)
 def test_current_hides_older_attempt_and_all_preserves_history(self):
  with self.jobs.open("a") as out:
   out.write("2026-07-16T00:00:03Z\tdone\t/r\t/w\told\troute_id=r3,route_node=test,attempt_id=att-old-history\n")
   out.write("2026-07-16T00:00:04Z\topen\t/r\t/w\tnew\troute_id=r3,route_node=test,attempt_id=att-new-history\n")
  current=json.loads(self.invoke("current","--route","r3").stdout);history=json.loads(self.invoke("current","--route","r3","--all").stdout)
  self.assertEqual([row["slug"] for row in current["rows"]],["new"])
  self.assertEqual([row["slug"] for row in history["rows"]],["old","new"])
 def test_preflight_liveness_ignores_superseded_open_attempt(self):
  start=(Path("/proc")/str(self.proc.pid)/"stat").read_text().split()[21]
  with self.jobs.open("a") as out:
   out.write("2026-07-16T00:00:03Z\topen\t/r\t/w\told-dead\troute_id=r4,route_node=test,attempt_id=att-old-dead,pid=99999997,pid_start=1,harness=codex\n")
   out.write(f"2026-07-16T00:00:04Z\topen\t/r\t/w\tnew-live\troute_id=r4,route_node=test,attempt_id=att-new-live,pid={self.proc.pid},pid_start={start},harness=codex\n")
  pre=ROOT/"adapters/codex/bin/preflight.sh"
  result=subprocess.run([str(pre),"liveness",str(self.jobs),"--route","r4"],capture_output=True,text=True,env={**os.environ,"AGENT_HOME":str(ROOT)})
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
  self.assertIn("new-live",result.stdout);self.assertNotIn("old-dead",result.stdout)


class MixedRegistryTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.home=self.base/"home";self.jobs=self.base/"jobs.log"
  bare=self.base/"remote.git";subprocess.run(["git","init","--bare","-q",str(bare)],check=True)
  self.primary=self.base/"primary";subprocess.run(["git","clone","-q",str(bare),str(self.primary)],check=True)
  subprocess.run(["git","-C",str(self.primary),"config","user.email","fixture@example.com"],check=True)
  subprocess.run(["git","-C",str(self.primary),"config","user.name","Fixture"],check=True)
  (self.primary/"base.txt").write_text("base")
  subprocess.run(["git","-C",str(self.primary),"add","base.txt"],check=True)
  subprocess.run(["git","-C",str(self.primary),"commit","-qm","base"],check=True)
  subprocess.run(["git","-C",str(self.primary),"branch","-M","main"],check=True)
  subprocess.run(["git","-C",str(self.primary),"push","-qu","origin","main"],check=True)
  self.merged=self.base/"merged";self.unsafe=self.base/"unsafe"
  subprocess.run(["git","-C",str(self.primary),"worktree","add","-q","-b","merged-fixture",str(self.merged),"main"],check=True)
  subprocess.run(["git","-C",str(self.primary),"worktree","add","-q","-b","unsafe-fixture",str(self.unsafe),"main"],check=True)
  (self.unsafe/"unsafe.txt").write_text("unmerged")
  subprocess.run(["git","-C",str(self.unsafe),"add","unsafe.txt"],check=True)
  subprocess.run(["git","-C",str(self.unsafe),"-c","user.email=fixture@example.com","-c","user.name=Fixture","commit","-qm","unsafe"],check=True)
  self.proc=subprocess.Popen(["sleep","60"]);start=(Path("/proc")/str(self.proc.pid)/"stat").read_text().split()[21]
  old="2020-01-01T00:00:00Z";repo=str(self.primary)
  rows=[
   f"{old}\topen\t{repo}\t/x\tactive\tparent_sid=s1,route_id=r1,route_node=active,route_hash=h1,attempt_id=att-active-mixed,pid={self.proc.pid},pid_start={start}",
   f"{old}\topen\t{repo}\t/x\tdead\tparent_sid=s1,route_id=r1,route_node=dead,route_hash=h1,attempt_id=att-dead-mixed,pid=99999991,pid_start=1",
   f"{old}\topen\t{repo}\t{self.merged}\tmerged\tparent_sid=s1,route_id=r1,route_node=merged,route_hash=h1,attempt_id=att-merged-mixed",
   f"{old}\topen\t{repo}\t/x\tstale\tparent_sid=s1,route_id=r1,route_node=stale,route_hash=h-stale,attempt_id=att-stale-mixed,completion_gate=code-test",
   f"{old}\topen\t{repo}\t{self.unsafe}\tunsafe\tparent_sid=s1,route_id=r1,route_node=unsafe,route_hash=h1,attempt_id=att-unsafe-mixed",
   f"{old}\topen\t{repo}\t/x\tunrelated\tparent_sid=s2,route_id=r2,route_node=other,route_hash=h2,attempt_id=att-other-mixed,pid=99999992,pid_start=1",
  ]
  self.jobs.write_text("\n".join(rows)+"\n")
  evidence=self.base/"stale-evidence.md";evidence.write_text("complete")
  marker_dir=self.home/".dispatch/completion/r1";marker_dir.mkdir(parents=True)
  marker={"route_id":"r1","route_hash":"h-stale","node_id":"stale","completion_gate":"code-test",
   "evidence":{"path":str(evidence),"sha256":hashlib.sha256(evidence.read_bytes()).hexdigest()},
   "completed_at":"2026-07-16T00:00:00Z"}
  (marker_dir/"stale.json").write_text(json.dumps(marker))
  wd=self.home/".dispatch/watchdog";wd.mkdir(parents=True)
  (wd/"att-stale-mixed.json").write_text(json.dumps({"quiet_windows":2,"observed_at":time.time()+10,"last_progress_at":0}))
 def tearDown(self):
  if self.proc.poll() is None:self.proc.kill()
  self.proc.wait();subprocess.run(["git","-C",str(self.primary),"worktree","remove","--force",str(self.merged)],capture_output=True)
  subprocess.run(["git","-C",str(self.primary),"worktree","remove","--force",str(self.unsafe)],capture_output=True)
  self.tmp.cleanup()
 def invoke(self,*args):
  return subprocess.run([sys.executable,str(SCRIPT),*args,"--jobs",str(self.jobs),"--agent-home",str(self.home)],capture_output=True,text=True)
 def test_mixed_current_and_guarded_reconcile(self):
  current=json.loads(self.invoke("current","--session","s1").stdout)
  self.assertEqual(current["total"],5);self.assertTrue(all(row["meta"].get("parent_sid")=="s1" for row in current["rows"]))
  self.assertEqual(json.loads(self.invoke("current","--job","dead").stdout)["total"],1)
  before=self.jobs.read_text();dry=json.loads(self.invoke("reconcile","--route","r1").stdout)
  self.assertEqual(dry["closed"],0);self.assertEqual(self.jobs.read_text(),before)
  applied=json.loads(self.invoke("reconcile","--route","r1","--apply").stdout)
  categories={item["slug"]:item["category"] for item in applied["decisions"]}
  self.assertEqual(categories,{"active":"active","dead":"exact-dead","merged":"merged","stale":"stale-terminal","unsafe":"unsafe"})
  text=self.jobs.read_text();self.assertIn("note=dead-exact-pid",text);self.assertIn("note=cleanup-merged",text);self.assertIn("note=dead-stale-terminal",text)
  self.assertIn("\topen\t"+str(self.primary)+"\t"+str(self.unsafe)+"\tunsafe\t",text)
  self.assertIn("\topen\t"+str(self.primary)+"\t/x\tunrelated\t",text)
  again=json.loads(self.invoke("reconcile","--route","r1","--apply").stdout);self.assertEqual(again["closed"],0)
 def test_concurrent_reconcile_adds_one_terminal_note(self):
  row="2020-01-01T00:00:00Z\topen\t/r\t/x\trace\tparent_sid=s3,route_id=rc,route_node=n,attempt_id=att-race-mixed,pid=99999990,pid_start=1\n"
  with self.jobs.open("a") as out:out.write(row)
  cmd=[sys.executable,str(SCRIPT),"reconcile","--attempt","att-race-mixed","--apply","--jobs",str(self.jobs),"--agent-home",str(self.home)]
  procs=[subprocess.Popen(cmd,stdout=subprocess.PIPE,text=True) for _ in range(4)]
  results=[json.loads(p.communicate(timeout=10)[0]) for p in procs]
  self.assertEqual(sum(result["closed"] for result in results),1)
  self.assertEqual(self.jobs.read_text().count("att-race-mixed"),1)
  self.assertEqual(self.jobs.read_text().count("note=dead-exact-pid"),1)
if __name__=="__main__":unittest.main()
