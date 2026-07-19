#!/usr/bin/env python3
import os, subprocess, sys, tempfile, unittest
from unittest import mock
from pathlib import Path

P=Path(__file__).with_name("dispatch_contract.py")
sys.path.insert(0,str(P.parent))
import dispatch_contract as D

class DispatchContractTest(unittest.TestCase):
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
   D.validate_nested_eligibility(depth=2,action="start",parent_harness="codex",parent_transport="headless",parent_sandbox="workspace-write",child_harness="codex",launch_authority="conductor",status="unknown",source="fixture")
  self.assertEqual(caught.exception.reason,"nested-child-spawn-unknown")
 def test_launch_broker_is_retired(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); jobs=root/"jobs.log"
   with self.assertRaises(D.DispatchContractError) as caught:
    D.ensure_launch_broker(root,jobs,depth=1,action="start",intensity="strong")
   self.assertEqual(caught.exception.reason,"launch-broker-retired")
 def test_atomic_attempt_claim_is_exact_and_idempotent(self):
  with tempfile.TemporaryDirectory() as td:
   jobs=Path(td)/"jobs.log"; attempt="att-123456789abc"; prefix="att-123456789abc-extra"
   row=f"2026-07-16T00:00:00Z\topen\t/repo\t/wt\tstage\tcapability=code-plan,attempt_id={prefix}"
   self.assertTrue(D.claim_attempt_row(jobs,prefix,row))
   exact=f"2026-07-16T00:00:01Z\topen\t/repo\t/wt\tstage\tcapability=code-plan,attempt_id={attempt}"
   self.assertTrue(D.claim_attempt_row(jobs,attempt,exact))
   self.assertFalse(D.claim_attempt_row(jobs,attempt,exact))
   self.assertTrue(D.claim_attempt_row(jobs,attempt,exact,launch=True))
   self.assertFalse(D.claim_attempt_row(jobs,attempt,exact,launch=True))
   self.assertIn("launch_claimed=1",jobs.read_text())
   self.assertEqual(len(jobs.read_text().splitlines()),2)
 def test_concurrent_attempt_claim_has_one_winner(self):
  with tempfile.TemporaryDirectory() as td:
   jobs=Path(td)/"jobs.log"; attempt="att-concurrent1234"
   code=("import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);"
         "import dispatch_contract as D;"
         "print(int(D.claim_attempt_row(Path(sys.argv[2]),sys.argv[3],sys.argv[4],launch=True)))")
   row=f"2026-07-16T00:00:00Z\topen\t/repo\t/wt\tstage\tcapability=code-plan,attempt_id={attempt}"
   procs=[subprocess.Popen([sys.executable,"-c",code,str(P.parent),str(jobs),attempt,row],text=True,stdout=subprocess.PIPE) for _ in range(8)]
   winners=[p.communicate(timeout=10)[0].strip() for p in procs]
   self.assertEqual(winners.count("1"),1,winners)
   self.assertEqual(len(jobs.read_text().splitlines()),1)
 def test_register_to_start_transition_is_crash_atomic(self):
  with tempfile.TemporaryDirectory() as td:
   jobs=Path(td)/"jobs.log"; attempt="att-crashatomic123"
   row=f"2026-07-16T00:00:00Z\topen\t/repo\t/wt\tstage\tcapability=code-plan,attempt_id={attempt}"
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
         "row=f'2026-07-16T00:00:00Z\\topen\\t/r\\t/w\\ts\\troute_id=r,route_node=n,attempt_id={a},capacity_retry=1';"
         "print(int(D.claim_attempt_row(Path(sys.argv[2]),a,row,launch=True,exclusive_metadata={'route_id':'r','route_node':'n','capacity_retry':'1'})))")
   procs=[subprocess.Popen([sys.executable,"-c",code,str(P.parent),str(jobs),f"att-capacity{i:04d}"],text=True,stdout=subprocess.PIPE) for i in range(8)]
   winners=[p.communicate(timeout=10)[0].strip() for p in procs]
   self.assertEqual(winners.count("1"),1,winners)
   self.assertEqual(len(jobs.read_text().splitlines()),1)
 def test_conditional_close_revalidates_under_lock(self):
  with tempfile.TemporaryDirectory() as td:
   jobs=Path(td)/"jobs.log";attempt="att-revalidate001"
   row=f"2026-07-16T00:00:00Z\topen\t/r\t/w\ts\troute_id=r,route_node=n,attempt_id={attempt}"
   self.assertTrue(D.claim_attempt_row(jobs,attempt,row))
   self.assertFalse(D.close_attempt_row_if(jobs,attempt,"dead-test",lambda _fields:False))
   self.assertIn("\topen\t",jobs.read_text())
   self.assertTrue(D.close_attempt_row_if(jobs,attempt,"dead-test",lambda _fields:True))
   self.assertIn("note=dead-test",jobs.read_text())
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
 def test_legacy_reconcile_is_idempotent(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); local=root/"local.log"; global_jobs=root/"global.log"
   rows=[]
   for i in range(6):
    pipe=f"capability=code-plan,route_id=rt-1,route_node=plan,parent=owner,attempt_id=att-{i:012d},note=dead-network"
    rows.append(f"2026-07-15T00:00:0{i}Z\tdone\t/repo\t/wt\tstage-r{i}\t{pipe}\n")
   local.write_text("".join(rows),encoding="utf-8")
   self.assertEqual(D.reconcile_local_registry(global_jobs,local),(6,0))
   self.assertEqual(D.reconcile_local_registry(global_jobs,local),(0,0))
   copied=global_jobs.read_text(encoding="utf-8").splitlines()
   self.assertEqual(len(copied),6)
   self.assertTrue(all("reconciled_from=" in row and "note=dead-network" in row for row in copied))

if __name__=="__main__": unittest.main()
