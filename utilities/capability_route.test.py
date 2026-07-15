#!/usr/bin/env python3
import importlib.util, json, tempfile, unittest
from pathlib import Path
P=Path(__file__).with_name("capability-route.py"); S=importlib.util.spec_from_file_location("route",P); R=importlib.util.module_from_spec(S); S.loader.exec_module(R)
ALL=["atomic-outcome","known-scope","no-shared-contract","no-resource-run","no-artifact-handoff","no-independent-verifier","focused-verification"]
class TestRoute(unittest.TestCase):
 def dispatch(self,*rows):
  return {"tuples":list(rows),"native_subagent":[{"harness":"codex","status":"supported","check_source":"fixture-native-check"}]}
 def nested(self,parent="codex",child="codex",authority="conductor",status="supported",failure=""):
  return {"parent_harness":parent,"parent_transport":"headless","parent_sandbox":"workspace-write","child_harness":child,"launch_authority":authority,"status":status,"probe_source":"fixture-probe","probe_time":"2026-07-15T00:00:00Z","failure_class":failure}
 def args(self,**kw):
  gate={"spec_read":{"satisfied":True,"source":"canonical-prd-sha256"},"drift_verdict":"within-spec","workflow_mode":"tracked","artifact_guard":{"satisfied":True,"source":"conductor-prechecked"}}
  d=dict(capability="autopilot-code",capability_mode="dev",requested_intensity="direct",cwd=R.ROOT,artifact_root=R.ROOT,predicates=ALL,transport="inline-fallback",inline_reason="atomic-direct",tracking="tracked",tracked_gate_evidence=gate); d.update(kw); return d
 def test_direct_all_and_stable(self):
  a=R.compile_route(**self.args()); b=R.compile_route(**self.args()); self.assertEqual(a,b); self.assertEqual(a["effective_intensity"],"direct"); self.assertEqual(a["tracking"],"tracked"); self.assertEqual(a["selection"]["escalation_basis"],[]); R.verify_route(a,R.ROOT)
 def test_ambiguous_quick(self):
  a=R.compile_route(**self.args(predicates=[],inline_reason="runtime-unavailable")); self.assertEqual(a["effective_intensity"],"quick")
 def test_promotion_standard(self):
  a=R.compile_route(**self.args(signals=["public-api"],inline_reason="dispatch-infra-self-modification")); self.assertEqual(a["effective_intensity"],"standard"); self.assertEqual([x["id"] for x in a["nodes"]],["plan","execute","test","report"])
 def test_tracking_is_independent_and_never_escalates(self):
  tracked=R.compile_route(**self.args(predicates=[])); untracked_gate={"spec_read":{"satisfied":False,"source":"untracked-bypass"},"drift_verdict":"within-spec","workflow_mode":"untracked","artifact_guard":{"satisfied":False,"source":"untracked-bypass"}}
  untracked=R.compile_route(**self.args(predicates=[],tracking="untracked",tracked_gate_evidence=untracked_gate))
  self.assertEqual(tracked["effective_intensity"],untracked["effective_intensity"]); self.assertEqual(tracked["nodes"],untracked["nodes"])
  self.assertRaises(ValueError,R.compile_route,**self.args(signals=["tracked"]))
 def test_tracked_gate_evidence_is_required(self):
  self.assertRaisesRegex(ValueError,"tracked gate evidence",R.compile_route,**self.args(tracked_gate_evidence={}))
  bad=self.args(); bad["tracked_gate_evidence"]["spec_read"]={"satisfied":False,"source":"missing"}
  self.assertRaisesRegex(ValueError,"spec_read must be satisfied",R.compile_route,**bad)
 def test_hash_detects_mutation(self):
  a=R.compile_route(**self.args()); a["cwd"]="/tmp"; self.assertRaises(ValueError,R.verify_route,a)
 def test_write_once_and_completion(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"route.json"; a=R.compile_route(**self.args()); R.write_once(p,a); R.write_once(p,a)
   a["effective_intensity"]="quick"; self.assertRaises(ValueError,R.write_once,p,a)
 def test_nested_surface_and_fallback_order(self):
  evidence=self.dispatch(
   self.nested(status="unsupported",failure="network-operation-not-permitted"),
   self.nested(child="claude",authority="ancestor-broker",status="supported"),
  )
  route=R.compile_route(**self.args(requested_intensity="strong",predicates=[],signals=["shared-contract"],transport="headless",inline_reason=None,dispatch_evidence=evidence))
  chain=route["nodes"][0]["dispatch_fallback"]
  self.assertEqual([row["hop"] for row in chain],R.FALLBACK_ORDER)
  self.assertEqual(chain[0]["candidates"][0]["status"],"unsupported")
  self.assertEqual(chain[1]["candidates"][0]["child_harness"],"claude")
  R.verify_route(route,R.ROOT)
 def test_unknown_nested_tuple_fails_closed(self):
  evidence=self.dispatch(self.nested(status="unknown",failure="unprobed-tuple"))
  with self.assertRaisesRegex(ValueError,"no supported nested headless"):
   R.compile_route(**self.args(requested_intensity="standard",predicates=[],signals=["shared-contract"],transport="headless",inline_reason=None,dispatch_evidence=evidence))
if __name__=="__main__": unittest.main()
