#!/usr/bin/env python3
import os, subprocess, sys, tempfile, unittest
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
 def test_depth0_prepares_broker_and_worker_cannot_replace_it(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); jobs=root/"jobs.log"; broker=root/"broker"
   selection=D.ensure_launch_broker(root,jobs,depth=1,action="start",intensity="strong",environ={"AGENT_DISPATCH_BROKER_ROOT":str(broker)})
   self.assertIsNotNone(selection); self.assertEqual(selection.jobs,jobs.resolve()); self.assertTrue(selection.instance_id.startswith("brk-"))
   with self.assertRaises(D.DispatchContractError) as caught:
    D.ensure_launch_broker(root,jobs,depth=1,action="start",intensity="strong",environ={"AGENT_SESSION_ROLE":"worker","AGENT_DISPATCH_BROKER_ROOT":str(root/"other")})
   self.assertEqual(caught.exception.reason,"broker-ensure-worker-forbidden")
   subprocess.run([sys.executable,str(P.with_name("dispatch-broker.py")),"stop","--root",str(broker),"--jobs",str(jobs)],env={**os.environ,"AGENT_HOME":str(root)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
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
