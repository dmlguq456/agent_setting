#!/usr/bin/env python3
import importlib.util, json, tempfile, unittest
from pathlib import Path
P=Path(__file__).with_name("capability-route.py"); S=importlib.util.spec_from_file_location("route",P); R=importlib.util.module_from_spec(S); S.loader.exec_module(R)
ALL=["atomic-outcome","known-scope","no-shared-contract","no-resource-run","no-artifact-handoff","no-independent-verifier","focused-verification"]
class TestRoute(unittest.TestCase):
 def args(self,**kw):
  d=dict(capability="autopilot-code",capability_mode="dev",requested_intensity="direct",cwd=R.ROOT,artifact_root=R.ROOT,predicates=ALL,transport="inline-fallback",inline_reason="atomic-direct"); d.update(kw); return d
 def test_direct_all_and_stable(self):
  a=R.compile_route(**self.args()); b=R.compile_route(**self.args()); self.assertEqual(a,b); self.assertEqual(a["effective_intensity"],"direct"); R.verify_route(a,R.ROOT)
 def test_ambiguous_quick(self):
  a=R.compile_route(**self.args(predicates=[],inline_reason="runtime-unavailable")); self.assertEqual(a["effective_intensity"],"quick")
 def test_promotion_standard(self):
  a=R.compile_route(**self.args(signals=["public-api"],inline_reason="dispatch-infra-self-modification")); self.assertEqual(a["effective_intensity"],"standard"); self.assertEqual([x["id"] for x in a["nodes"]],["plan","execute","test","report"])
 def test_hash_detects_mutation(self):
  a=R.compile_route(**self.args()); a["cwd"]="/tmp"; self.assertRaises(ValueError,R.verify_route,a)
 def test_write_once_and_completion(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"route.json"; a=R.compile_route(**self.args()); R.write_once(p,a); R.write_once(p,a)
   a["effective_intensity"]="quick"; self.assertRaises(ValueError,R.write_once,p,a)
if __name__=="__main__": unittest.main()
