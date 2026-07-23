#!/usr/bin/env python3
import os, subprocess, sys, tempfile, unittest
from unittest import mock
from pathlib import Path

P=Path(__file__).with_name("dispatch_contract.py")
sys.path.insert(0,str(P.parent))
import dispatch_contract as D

CURRENT="attempt_schema_version=2,dispatch_depth=2,transport=headless,execution_surface=registered-headless,registered_worker=1,fallback_hop=same-harness-headless"

class DispatchContractTest(unittest.TestCase):
 def owner_row(self,attempt,pid,start,slug="owner"):
  return (f"2026-07-23T00:00:00Z\topen\t/repo\t/wt\t{slug}\t"
          "attempt_schema_version=2,dispatch_depth=1,transport=headless,"
          "execution_surface=registered-headless,registered_worker=1,"
          "fallback_hop=same-harness-headless,worker_type=owner,"
          f"attempt_id={attempt},pid={pid},pid_start={start}")

 def test_live_parent_binding_is_attempt_exact_and_same_slug_safe(self):
  with tempfile.TemporaryDirectory() as td:
   jobs=Path(td)/"jobs.log"
   first=subprocess.Popen(["sleep","60"])
   second=subprocess.Popen(["sleep","60"])
   try:
    first_start=D.process_start_ticks(first.pid);second_start=D.process_start_ticks(second.pid)
    jobs.write_text(self.owner_row("att-parent-first",first.pid,first_start)+"\n"+
                    self.owner_row("att-parent-second",second.pid,second_start)+"\n")
    with self.assertRaises(D.DispatchContractError) as caught:
     D.resolve_live_parent_attempt(jobs,parent_slug="owner",repo="/repo",worktree="/wt")
    self.assertEqual(caught.exception.reason,"parent-attempt-ambiguous")
    binding=D.resolve_live_parent_attempt(
     jobs,parent_slug="owner",repo="/repo",worktree="/wt",
     expected_attempt_id="att-parent-second")
    self.assertEqual(binding.attempt_id,"att-parent-second")
    self.assertEqual((binding.observed_pid,binding.observed_pid_start),(second.pid,second_start))
   finally:
    for proc in (first,second):
     if proc.poll() is None:proc.kill()
     proc.wait()

 def test_dead_or_identity_missing_parent_prevents_claim(self):
  with tempfile.TemporaryDirectory() as td:
   jobs=Path(td)/"jobs.log"
   jobs.write_text(self.owner_row("att-parent-dead",99999971,"1")+"\n")
   with self.assertRaises(D.DispatchContractError) as caught:
    D.resolve_live_parent_attempt(
     jobs,parent_slug="owner",repo="/repo",worktree="/wt",
     expected_attempt_id="att-parent-dead")
   self.assertEqual(caught.exception.reason,"parent-attempt-not-live")

 def test_launch_identity_records_outer_pid_start_and_group(self):
  proc=subprocess.Popen(["sleep","60"],start_new_session=True)
  try:
   identity=D.process_launch_identity(proc.pid)
   self.assertEqual(identity["pid"],str(proc.pid))
   self.assertEqual(identity["pid_start"],D.process_start_ticks(proc.pid))
   self.assertEqual(identity.get("pid_host"),str(proc.pid))
   self.assertEqual(identity.get("pid_host_start"),identity["pid_start"])
   self.assertEqual(identity.get("pgid"),str(proc.pid))
  finally:
   proc.kill();proc.wait()

 def test_claimed_spawn_rechecks_parent_and_publishes_identity_under_lock(self):
  with tempfile.TemporaryDirectory() as td:
   jobs=Path(td)/"jobs.log"
   parent=subprocess.Popen(["sleep","60"])
   child=None
   try:
    start=D.process_start_ticks(parent.pid)
    owner=self.owner_row("att-parent-atomic",parent.pid,start)
    child_row=("2026-07-23T00:00:01Z\topen\t/repo\t/wt\tchild\t"
               f"{CURRENT},worker_type=stage,parent=owner,"
               "parent_attempt_id=att-parent-atomic,attempt_id=att-child-atomic")
    jobs.write_text(owner+"\n")
    binding=D.resolve_live_parent_attempt(
     jobs,parent_slug="owner",repo="/repo",worktree="/wt",
     expected_attempt_id="att-parent-atomic")
    self.assertTrue(D.claim_attempt_row(jobs,"att-child-atomic",child_row,launch=True))
    child,identity=D.spawn_claimed_attempt(
     jobs,"att-child-atomic",parent_binding=binding,
     spawn=lambda: subprocess.Popen(["sleep","60"],start_new_session=True),
     launch_metadata={"launch_lifecycle":"detached"})
    meta=D.parse_registry_metadata(jobs.read_text().splitlines()[1].split("\t")[5])
    self.assertEqual(meta["pid"],str(child.pid))
    self.assertEqual(meta["pid_start"],identity["pid_start"])
    self.assertEqual(meta["pgid"],str(child.pid))
    self.assertEqual(meta["launch_lifecycle"],"detached")
   finally:
    for proc in (child,parent):
     if proc is not None and proc.poll() is None:proc.kill()
     if proc is not None:proc.wait()

 def test_claimed_spawn_starts_zero_children_when_parent_dies_before_final_check(self):
  with tempfile.TemporaryDirectory() as td:
   jobs=Path(td)/"jobs.log"
   parent=subprocess.Popen(["sleep","60"])
   start=D.process_start_ticks(parent.pid)
   jobs.write_text(self.owner_row("att-parent-race",parent.pid,start)+"\n")
   binding=D.resolve_live_parent_attempt(
    jobs,parent_slug="owner",repo="/repo",worktree="/wt",
    expected_attempt_id="att-parent-race")
   child_row=("2026-07-23T00:00:01Z\topen\t/repo\t/wt\tchild\t"
              f"{CURRENT},worker_type=stage,parent=owner,"
              "parent_attempt_id=att-parent-race,attempt_id=att-child-race")
   self.assertTrue(D.claim_attempt_row(jobs,"att-child-race",child_row,launch=True))
   parent.kill();parent.wait()
   spawned=[]
   with self.assertRaises(D.DispatchContractError) as caught:
    D.spawn_claimed_attempt(
     jobs,"att-child-race",parent_binding=binding,
     spawn=lambda: spawned.append(True))
   self.assertEqual(caught.exception.reason,"parent-attempt-not-live")
   self.assertEqual(spawned,[])

 def test_nested_registry_is_inherited_and_immutable(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); global_jobs=(root/"global/jobs.log").resolve(); local=(root/"cycle/jobs.log").resolve()
   selected=D.resolve_global_registry(root,str(global_jobs),1,"start",{})
   self.assertEqual(selected.path,global_jobs)
   inherited=D.resolve_global_registry(root,str(global_jobs),2,"start",{"AGENT_DISPATCH_JOBS":str(global_jobs)})
   self.assertTrue(inherited.inherited)
   with self.assertRaisesRegex(D.DispatchContractError,"explicit=.*inherited"):
    D.resolve_global_registry(root,str(local),2,"start",{"AGENT_DISPATCH_JOBS":str(global_jobs)})
   with self.assertRaises(D.DispatchContractError) as caught:
    D.resolve_global_registry(root,str(local),2,"start",{})
   self.assertEqual(caught.exception.reason,"global-registry-unset")
 def test_unwritable_registry_is_structured(self):
  with self.assertRaises(D.DispatchContractError) as caught:
   D.ensure_global_registry_writable(Path("/proc/1/stage-dispatch-v11/jobs.log"))
  self.assertEqual(caught.exception.reason,"global-registry-unwritable")
 def test_attempt_id_and_nested_unknown(self):
  self.assertTrue(D.new_attempt_id().startswith("att-"))
  with self.assertRaises(D.DispatchContractError) as caught:
   D.validate_nested_eligibility(dispatch_depth=2,action="start",parent_harness="codex",parent_transport="headless",parent_sandbox="workspace-write",child_harness="codex",launch_authority="conductor",status="unknown",source="fixture")
  self.assertEqual(caught.exception.reason,"nested-child-spawn-unknown")
 def test_runtime_surface_label_is_rejected_as_parent_transport(self):
  with self.assertRaises(D.DispatchContractError) as caught:
   D.validate_nested_eligibility(dispatch_depth=2,action="start",parent_harness="codex",parent_transport="codex-exec-headless",parent_sandbox="workspace-write",child_harness="codex",launch_authority="conductor",status="supported",source="fixture")
  self.assertEqual(caught.exception.reason,"invalid-parent-transport")
 def test_attempt_namespaces_reject_unknowns_before_claim(self):
  base=dict(attempt_schema_version=2,dispatch_depth=1,transport="headless",
            execution_surface="registered-headless",registered_worker=True,
            fallback_hop="same-harness-headless")
  for field,value,reason in (
      ("transport","detached-process","invalid-transport"),
      ("execution_surface","mystery","invalid-execution-surface"),
      ("fallback_hop","mystery","invalid-fallback-hop"),
      ("registered_worker","maybe","invalid-registered-worker")):
   metadata=dict(base);metadata[field]=value
   with self.subTest(field=field),self.assertRaises(D.DispatchContractError) as caught:
    D.validate_attempt_metadata(metadata)
   self.assertEqual(caught.exception.reason,reason)
 def test_current_attempt_rejects_every_bare_depth_alias(self):
  base=dict(attempt_schema_version=2,dispatch_depth=1,transport="headless",
            execution_surface="registered-headless",registered_worker=True,
            fallback_hop="same-harness-headless")
  for field in ("depth","owner_depth","max_depth"):
   metadata=dict(base);metadata[field]=1
   with self.subTest(field=field),self.assertRaises(D.DispatchContractError) as caught:
    D.validate_attempt_metadata(metadata)
   self.assertEqual(caught.exception.reason,"bare-dispatch-depth-field")
 def test_direct_and_runtime_native_attempt_axes_are_independent(self):
  D.validate_attempt_metadata(dict(
   attempt_schema_version=2,dispatch_depth=0,transport="interactive",
   execution_surface="inline",registered_worker=False,fallback_hop=""))
  for surface in ("codex-native-subagent","claude-subagent"):
   with self.subTest(surface=surface):
    D.validate_attempt_metadata(dict(
     attempt_schema_version=2,dispatch_depth=2,transport="headless",
     execution_surface=surface,registered_worker=False,fallback_hop="native-subagent"))
  with self.assertRaises(D.DispatchContractError) as caught:
   D.validate_attempt_metadata(dict(
    attempt_schema_version=2,dispatch_depth=2,transport="interactive",
    execution_surface="claude-agent-team-teammate",registered_worker=False,
    fallback_hop="native-subagent"))
  self.assertEqual(caught.exception.reason,"teammate-not-dispatch-attempt")
 def test_launch_broker_is_retired(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); jobs=root/"jobs.log"
   with self.assertRaises(D.DispatchContractError) as caught:
    D.ensure_launch_broker(root,jobs,dispatch_depth=1,action="start",intensity="strong")
   self.assertEqual(caught.exception.reason,"launch-broker-retired")
 def test_atomic_attempt_claim_is_exact_and_idempotent(self):
  with tempfile.TemporaryDirectory() as td:
   jobs=Path(td)/"jobs.log"; attempt="att-123456789abc"; prefix="att-123456789abc-extra"
   row=f"2026-07-16T00:00:00Z\topen\t/repo\t/wt\tstage\t{CURRENT},capability=code-plan,attempt_id={prefix}"
   self.assertTrue(D.claim_attempt_row(jobs,prefix,row))
   exact=f"2026-07-16T00:00:01Z\topen\t/repo\t/wt\tstage\t{CURRENT},capability=code-plan,attempt_id={attempt}"
   self.assertTrue(D.claim_attempt_row(jobs,attempt,exact))
   self.assertFalse(D.claim_attempt_row(jobs,attempt,exact))
   self.assertTrue(D.claim_attempt_row(jobs,attempt,exact,launch=True))
   self.assertFalse(D.claim_attempt_row(jobs,attempt,exact,launch=True))
   self.assertIn("launch_claimed=1",jobs.read_text())
   self.assertEqual(len(jobs.read_text().splitlines()),2)
 def test_existing_attempt_id_rejects_conflicting_immutable_identity_without_mutation(self):
  with tempfile.TemporaryDirectory() as td:
   jobs=Path(td)/"jobs.log"; attempt="att-conflict00001"
   row=f"2026-07-16T00:00:00Z\topen\t/repo\t/wt-a\tstage\t{CURRENT},route_id=rt-a,route_node=plan,attempt_id={attempt}"
   self.assertTrue(D.claim_attempt_row(jobs,attempt,row))
   before=jobs.read_bytes()
   conflict=f"2026-07-16T00:00:01Z\topen\t/repo\t/wt-b\tstage\t{CURRENT},route_id=rt-b,route_node=execute,attempt_id={attempt}"
   with self.assertRaises(D.DispatchContractError) as caught:
    D.claim_attempt_row(jobs,attempt,conflict,launch=True)
   self.assertEqual(caught.exception.reason,"attempt-identity-conflict")
   self.assertEqual(jobs.read_bytes(),before)
 def test_standard_route_candidate_requires_exact_checked_launch_tuple(self):
  with tempfile.TemporaryDirectory() as td:
   route_path=Path(td)/"route.json"
   candidate={
    "parent_harness":"claude","parent_transport":"headless",
    "parent_sandbox":"workspace-write","child_harness":"codex",
    "launch_authority":"conductor","status":"supported"}
   route={
    "schema_version":2,"effective_intensity":"standard",
    "nodes":[{"id":"execute","dispatch_depth":2,"fallback_hops":[
     {"ordinal":1,"fallback_hop":"same-harness-headless","candidates":[]},
     {"ordinal":2,"fallback_hop":"cross-harness-headless","candidates":[candidate]},
     {"ordinal":3,"fallback_hop":"native-subagent","candidates":[]},
     {"ordinal":4,"fallback_hop":"inline","candidates":[]}]}]}
   route_path.write_text(__import__("json").dumps(route))
   with self.assertRaises(D.DispatchContractError) as caught:
    D.headless_attempt_policy(
     route_file=str(route_path),route_node="execute",intensity="standard",
     harness="codex",dispatch_depth=2,parent_slug="owner",
     execution_surface="registered-headless",registered_worker=True,
     fallback_hop="cross-harness-headless",fallback_ordinal=2,
     parent_harness="codex",parent_transport="headless",
     parent_sandbox="workspace-write",launch_authority="conductor")
   self.assertEqual(caught.exception.reason,"route-fallback-candidate-mismatch")
 def test_concurrent_attempt_claim_has_one_winner(self):
  with tempfile.TemporaryDirectory() as td:
   jobs=Path(td)/"jobs.log"; attempt="att-concurrent1234"
   code=("import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);"
         "import dispatch_contract as D;"
         "print(int(D.claim_attempt_row(Path(sys.argv[2]),sys.argv[3],sys.argv[4],launch=True)))")
   row=f"2026-07-16T00:00:00Z\topen\t/repo\t/wt\tstage\t{CURRENT},capability=code-plan,attempt_id={attempt}"
   procs=[subprocess.Popen([sys.executable,"-c",code,str(P.parent),str(jobs),attempt,row],text=True,stdout=subprocess.PIPE) for _ in range(8)]
   winners=[p.communicate(timeout=10)[0].strip() for p in procs]
   self.assertEqual(winners.count("1"),1,winners)
   self.assertEqual(len(jobs.read_text().splitlines()),1)
 def test_register_to_start_transition_is_crash_atomic(self):
  with tempfile.TemporaryDirectory() as td:
   jobs=Path(td)/"jobs.log"; attempt="att-crashatomic123"
   row=f"2026-07-16T00:00:00Z\topen\t/repo\t/wt\tstage\t{CURRENT},capability=code-plan,attempt_id={attempt}"
   self.assertTrue(D.claim_attempt_row(jobs,attempt,row))
   before=jobs.read_text()
   with mock.patch.object(D.os,"replace",side_effect=OSError("fixture-crash")):
    with self.assertRaises(OSError): D.claim_attempt_row(jobs,attempt,row,launch=True)
   self.assertEqual(jobs.read_text(),before)
   self.assertFalse(list(Path(td).glob(".jobs.log.claim-*")))
 def test_capacity_retry_claim_is_exclusive_per_route_node(self):
  with tempfile.TemporaryDirectory() as td:
   jobs=Path(td)/"jobs.log"
   code=("import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);"
         "import dispatch_contract as D;a=sys.argv[3];"
         "row=f'2026-07-16T00:00:00Z\\topen\\t/r\\t/w\\ts\\tattempt_schema_version=2,dispatch_depth=2,transport=headless,execution_surface=registered-headless,registered_worker=1,fallback_hop=same-harness-headless,route_id=r,route_node=n,attempt_id={a},capacity_retry=1';"
         "print(int(D.claim_attempt_row(Path(sys.argv[2]),a,row,launch=True,exclusive_metadata={'route_id':'r','route_node':'n','capacity_retry':'1'})))")
   procs=[subprocess.Popen([sys.executable,"-c",code,str(P.parent),str(jobs),f"att-capacity{i:04d}"],text=True,stdout=subprocess.PIPE) for i in range(8)]
   winners=[p.communicate(timeout=10)[0].strip() for p in procs]
   self.assertEqual(winners.count("1"),1,winners)
   self.assertEqual(len(jobs.read_text().splitlines()),1)
 def test_conditional_close_revalidates_under_lock(self):
  with tempfile.TemporaryDirectory() as td:
   jobs=Path(td)/"jobs.log";attempt="att-revalidate001"
   row=f"2026-07-16T00:00:00Z\topen\t/r\t/w\ts\t{CURRENT},route_id=r,route_node=n,attempt_id={attempt}"
   self.assertTrue(D.claim_attempt_row(jobs,attempt,row))
   self.assertFalse(D.close_attempt_row_if(jobs,attempt,"dead-test",lambda _fields:False))
   self.assertIn("\topen\t",jobs.read_text())
   self.assertTrue(D.close_attempt_row_if(jobs,attempt,"dead-test",lambda _fields:True))
   self.assertIn("note=dead-test",jobs.read_text())
 def test_quick_attempts_are_serial_and_exhaust_exactly(self):
  with tempfile.TemporaryDirectory() as td:
   jobs=Path(td)/"jobs.log"
   def row(attempt,stamp):
    return (f"{stamp}\topen\t/r\t/w\tquick\t{CURRENT},route_id=rt-q,"
            f"route_node=one-shot,attempt_id={attempt}")
   exclusive={"route_id":"rt-q","route_node":"one-shot"}
   first="att-quick000001"; second="att-quick000002"; third="att-quick000003"
   self.assertTrue(D.claim_attempt_row(jobs,first,row(first,"2026-07-20T00:00:00Z"),
                                       launch=True,exclusive_live_metadata=exclusive,
                                       terminal_attempt_limit=2))
   self.assertFalse(D.claim_attempt_row(jobs,second,row(second,"2026-07-20T00:00:01Z"),
                                        launch=True,exclusive_live_metadata=exclusive,
                                        terminal_attempt_limit=2))
   self.assertTrue(D.close_attempt_row(jobs,first,"dead-fixture"))
   self.assertTrue(D.claim_attempt_row(jobs,second,row(second,"2026-07-20T00:00:02Z"),
                                       launch=True,exclusive_live_metadata=exclusive,
                                       terminal_attempt_limit=2))
   self.assertTrue(D.close_attempt_row(jobs,second,"dead-fixture"))
   with self.assertRaises(D.DispatchContractError) as caught:
    D.claim_attempt_row(jobs,third,row(third,"2026-07-20T00:00:03Z"),
                        launch=True,exclusive_live_metadata=exclusive,
                        terminal_attempt_limit=2)
   self.assertEqual(caught.exception.reason,"quick-registered-headless-exhausted")
   self.assertEqual(len(jobs.read_text().splitlines()),2)
 def test_orphan_watch_launch_is_exact_and_detached(self):
  fake=mock.Mock(pid=4321)
  with mock.patch.object(D.subprocess,"Popen",return_value=fake) as popen:
   watcher=D.launch_orphan_watch(
    Path("/tmp/jobs.log"),Path("/tmp/agent-home"),"att-watch-contract",1234,"5678")
  self.assertEqual(watcher,4321)
  argv=popen.call_args.args[0]
  self.assertIn("dispatch-orphan-watch.py",argv[1])
  self.assertIn("att-watch-contract",argv)
  self.assertEqual(popen.call_args.kwargs["cwd"],"/")
  self.assertTrue(popen.call_args.kwargs["start_new_session"])
  with self.assertRaises(D.DispatchContractError) as caught:
   D.launch_orphan_watch(Path("/tmp/jobs.log"),Path("/tmp/home"),"",0,"")
  self.assertEqual(caught.exception.reason,"orphan-watch-identity-invalid")
 def test_legacy_reconcile_is_read_only(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); local=root/"local.log"; global_jobs=root/"global.log"
   rows=[]
   for i in range(6):
    pipe=f"capability=code-plan,route_id=rt-1,route_node=plan,parent=owner,attempt_id=att-{i:012d},note=dead-network"
    rows.append(f"2026-07-15T00:00:0{i}Z\tdone\t/repo\t/wt\tstage-r{i}\t{pipe}\n")
   local.write_text("".join(rows),encoding="utf-8")
   self.assertEqual(D.reconcile_local_registry(global_jobs,local),(0,6))
   self.assertEqual(global_jobs.read_text(encoding="utf-8"),"")
 def test_current_reconcile_is_idempotent(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); local=root/"local.log"; global_jobs=root/"global.log"
   rows=[]
   for i in range(2):
    attempt=f"att-current{i:05d}"
    pipe=f"{CURRENT},route_id=rt-1,route_node=plan,parent=owner,attempt_id={attempt},note=dead-network"
    rows.append(f"2026-07-15T00:00:0{i}Z\tdone\t/repo\t/wt\tstage-r{i}\t{pipe}\n")
   local.write_text("".join(rows),encoding="utf-8")
   self.assertEqual(D.reconcile_local_registry(global_jobs,local),(2,0))
   self.assertEqual(D.reconcile_local_registry(global_jobs,local),(0,0))
   copied=global_jobs.read_text(encoding="utf-8").splitlines()
   self.assertEqual(len(copied),2)
   self.assertTrue(all("reconciled_from=" in row for row in copied))

if __name__=="__main__": unittest.main()
