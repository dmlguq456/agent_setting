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
 def test_namespace_local_attempt_state_uses_exact_heartbeat(self):
  heartbeat_dir=self.base/".dispatch/heartbeats";heartbeat_dir.mkdir(parents=True)
  attempt="att-namespace-state";route="r-namespace";node="test"
  heartbeat={"attempt_id":attempt,"route_id":route,"route_node":node,
             "phase":"tool","sequence":3,"updated_at":time.time()}
  (heartbeat_dir/f"{attempt}.json").write_text(json.dumps(heartbeat))
  args=("attempt-state","--pid","437","--pid-start","1","--pid-scope","namespace-local",
        "--attempt",attempt,"--route",route,"--node",node)
  live=self.invoke(*args);self.assertEqual(live.returncode,0,live.stdout+live.stderr);self.assertIn("state=working",live.stdout)
  heartbeat["phase"]="terminal";(heartbeat_dir/f"{attempt}.json").write_text(json.dumps(heartbeat))
  done=self.invoke(*args);self.assertEqual(done.returncode,0,done.stdout+done.stderr);self.assertIn("state=done",done.stdout)
  with self.jobs.open("a") as out:
   out.write(f"2026-07-16T00:00:05Z\topen\t/r\t/w\tnamespace\troute_id={route},route_node={node},attempt_id={attempt},pid=437,pid_start=1,pid_scope=namespace-local\n")
  applied=self.invoke("reconcile","--attempt",attempt,"--apply")
  record=json.loads(applied.stdout);self.assertEqual(record["closed"],1);self.assertEqual(record["decisions"][0]["category"],"terminal-heartbeat")
  self.assertIn("note=completed-terminal-heartbeat",self.jobs.read_text())


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
class OrphanReconcileTest(unittest.TestCase):
 """SD-64/71 post-exit orphan-conductor reconcile classification."""
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.home=self.base/"home";self.jobs=self.base/"jobs.log"
  self.route_id="rt-orphan-fixture"
  route={"route_id":self.route_id,"nodes":[
   {"id":"plan","depends_on":[]},{"id":"execute","depends_on":["plan"]},
   {"id":"test","depends_on":["execute"]},{"id":"report","depends_on":["test"]}]}
  self.route_file=self.base/"route.json";self.route_file.write_text(json.dumps(route))
  self.marker_dir=self.home/".dispatch/completion"/self.route_id;self.marker_dir.mkdir(parents=True)
 def tearDown(self): self.tmp.cleanup()
 def mark(self,node_id):
  (self.marker_dir/f"{node_id}.json").write_text(json.dumps({"node_id":node_id}))
 def owner_row(self,slug,attempt_id,pid,pid_start,extra="",include_route=True):
  route_meta=f"route_id={self.route_id},route_file={self.route_file}," if include_route else ""
  meta=f"{route_meta}worker_type=owner,attempt_id={attempt_id},pid={pid},pid_start={pid_start}"
  if extra: meta+=","+extra
  return f"2026-07-16T00:00:00Z\topen\t/r\t/w\t{slug}\t{meta}"
 def invoke(self,*args):
  return subprocess.run([sys.executable,str(SCRIPT),*args,"--jobs",str(self.jobs),"--agent-home",str(self.home)],capture_output=True,text=True)
 def test_dead_owner_with_open_child_is_orphaned(self):
  self.mark("plan")
  live=subprocess.Popen(["sleep","60"]);start=(Path("/proc")/str(live.pid)/"stat").read_text().split()[21]
  try:
   rows=[
    self.owner_row("owner","att-owner-dead",99999995,1),
    f"2026-07-16T00:00:01Z\topen\t/r\t/w\tchild\troute_id={self.route_id},route_node=execute,attempt_id=att-child-live,parent=owner,pid={live.pid},pid_start={start}",
   ]
   self.jobs.write_text("\n".join(rows)+"\n")
   dry=json.loads(self.invoke("reconcile","--attempt","att-owner-dead").stdout)
   self.assertEqual(dry["decisions"][0]["proposed_note"],"dead-parent-orphaned")
   applied=json.loads(self.invoke("reconcile","--attempt","att-owner-dead","--apply").stdout)
   self.assertEqual(applied["closed"],1)
   text=self.jobs.read_text()
   self.assertIn("note=dead-parent-orphaned",text)
   self.assertIn("\topen\t/r\t/w\tchild\t",text, "a live child must never be closed by the orphan repair")
  finally:
   live.kill();live.wait()
 def test_real_owner_without_route_derives_from_open_child_and_surfaces_boundary(self):
  self.mark("plan")
  rows=[
   self.owner_row("owner","att-owner-derived",99999990,1,include_route=False),
   f"2026-07-16T00:00:01Z\topen\t/r\t/w\tchild\t"
   f"route_id={self.route_id},route_file={self.route_file},route_node=execute,"
   "attempt_id=att-child-derived,parent=owner,pid=99999989,pid_start=1",
  ]
  self.jobs.write_text("\n".join(rows)+"\n")
  status=self.invoke("orphan-status","--attempt","att-owner-derived")
  self.assertEqual(status.returncode,0,status.stdout+status.stderr)
  self.assertIn("orphan=1",status.stdout);self.assertIn(f"route_id={self.route_id}",status.stdout)
  self.assertIn("resume_boundary=execute",status.stdout)
  scan=self.invoke("orphan-scan")
  self.assertEqual(scan.returncode,0,scan.stdout+scan.stderr)
  self.assertIn("orphaned_conductor_jobs=1",scan.stdout)
  applied=json.loads(self.invoke("reconcile","--attempt","att-owner-derived","--apply").stdout)
  self.assertEqual(applied["decisions"][0]["category"],"orphan")
  self.assertIn("\topen\t/r\t/w\tchild\t",self.jobs.read_text(),
                "even an exact-dead child remains open for depth-0 diagnosis")
 def test_terminal_child_route_context_detects_unstarted_successor(self):
  self.mark("plan");self.mark("execute")
  rows=[
   self.owner_row("owner","att-owner-terminal-child",99999988,1,include_route=False),
   f"2026-07-16T00:00:01Z\tdone\t/r\t/w\tchild\t"
   f"route_id={self.route_id},route_file={self.route_file},route_node=execute,"
   "attempt_id=att-child-terminal,parent=owner,note=completed-marker",
  ]
  self.jobs.write_text("\n".join(rows)+"\n")
  applied=json.loads(self.invoke("reconcile","--attempt","att-owner-terminal-child","--apply").stdout)
  self.assertEqual(applied["decisions"][0]["category"],"orphan")
 def test_conflicting_child_route_context_fails_closed(self):
  other_route=self.base/"other-route.json"
  other_route.write_text(json.dumps({"route_id":"rt-other","nodes":[{"id":"plan","depends_on":[]}]}))
  rows=[
   self.owner_row("owner","att-owner-conflict",99999987,1,include_route=False),
   f"2026-07-16T00:00:01Z\tdone\t/r\t/w\tchild-a\t"
   f"route_id={self.route_id},route_file={self.route_file},route_node=plan,"
   "attempt_id=att-child-a,parent=owner",
   "2026-07-16T00:00:02Z\topen\t/r\t/w\tchild-b\t"
   f"route_id=rt-other,route_file={other_route},route_node=plan,"
   "attempt_id=att-child-b,parent=owner,pid=99999986,pid_start=1",
  ]
  self.jobs.write_text("\n".join(rows)+"\n")
  result=json.loads(self.invoke("reconcile","--attempt","att-owner-conflict").stdout)
  self.assertNotEqual(result["decisions"][0]["category"],"orphan")
 def test_live_conductor_completed_route_live_child_is_never_orphaned(self):
  for node in ("plan","execute","test","report"): self.mark(node)
  live_owner=subprocess.Popen(["sleep","60"]);owner_start=(Path("/proc")/str(live_owner.pid)/"stat").read_text().split()[21]
  live_child=subprocess.Popen(["sleep","60"]);child_start=(Path("/proc")/str(live_child.pid)/"stat").read_text().split()[21]
  try:
   rows=[
    self.owner_row("owner","att-owner-live",live_owner.pid,owner_start),
    f"2026-07-16T00:00:01Z\topen\t/r\t/w\tchild\troute_id={self.route_id},route_node=report,attempt_id=att-child-live2,parent=owner,pid={live_child.pid},pid_start={child_start}",
   ]
   self.jobs.write_text("\n".join(rows)+"\n")
   result=json.loads(self.invoke("reconcile","--attempt","att-owner-live").stdout)
   self.assertEqual(result["decisions"][0]["category"],"active")
   self.assertIsNone(result["decisions"][0]["proposed_note"])
  finally:
   live_owner.kill();live_owner.wait();live_child.kill();live_child.wait()
 def test_unstarted_successor_with_no_open_child_is_orphaned(self):
  self.mark("plan");self.mark("execute")  # test/report incomplete; report depends on test (unmarked) so only test is a ready un-started successor
  rows=[self.owner_row("owner","att-owner-dead2",99999994,1)]
  self.jobs.write_text("\n".join(rows)+"\n")
  applied=json.loads(self.invoke("reconcile","--attempt","att-owner-dead2","--apply").stdout)
  self.assertEqual(applied["decisions"][0]["category"],"orphan")
  self.assertIn("note=dead-parent-orphaned",self.jobs.read_text())
 def test_dead_owner_with_completed_route_is_not_orphaned(self):
  for node in ("plan","execute","test","report"): self.mark(node)
  rows=[self.owner_row("owner","att-owner-dead3",99999993,1)]
  self.jobs.write_text("\n".join(rows)+"\n")
  applied=json.loads(self.invoke("reconcile","--attempt","att-owner-dead3","--apply").stdout)
  self.assertEqual(applied["decisions"][0]["category"],"exact-dead")
  self.assertNotEqual(applied["decisions"][0]["proposed_note"],"dead-parent-orphaned")
 def test_unreadable_route_record_fails_closed(self):
  rows=[self.owner_row("owner","att-owner-dead4",99999992,1,extra=f"route_file={self.base/'missing.json'}")]
  self.jobs.write_text("\n".join(rows)+"\n")
  applied=json.loads(self.invoke("reconcile","--attempt","att-owner-dead4","--apply").stdout)
  self.assertNotEqual(applied["decisions"][0]["category"],"orphan")


if __name__=="__main__":unittest.main()
