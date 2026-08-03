#!/usr/bin/env python3
import importlib.util,tempfile,unittest
import hashlib,json
from pathlib import Path
P=Path(__file__).with_name("smoke-attestation.py"); S=importlib.util.spec_from_file_location("smoke",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)
class TestSmoke(unittest.TestCase):
 def test_hash_binding(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"config"; p.write_text("a"); data=M.payload([p],["true"],td); data.update(status="passed",exit_code=0); self.assertTrue(M.verify(data)); p.write_text("b"); self.assertRaises(ValueError,M.verify,data)
 def test_attestation_hash(self):
   with tempfile.TemporaryDirectory() as td:
    p=Path(td)/"config"; p.write_text("a"); data=M.payload([p],["true"],td); data.update(status="passed",exit_code=0); data["attestation_hash"]="sha256:"+hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest(); self.assertTrue(M.verify(data)); data["command"]=["false"]; self.assertRaises(ValueError,M.verify,data)
 def test_config_manifest_binds_exact_snapshot(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); snapshot=root/"snapshot"; snapshot.write_text("config")
   digest=hashlib.sha256(snapshot.read_bytes()).hexdigest()
   manifest=root/"manifest.json"; manifest.write_text(json.dumps({"snapshot_path":str(snapshot),"snapshot_sha256":digest}))
   data=M.payload([], ["true"], td, manifest); data.update(status="passed",exit_code=0)
   self.assertEqual(data["config_sha256"], digest); self.assertTrue(M.verify(data))
   data["inputs"]=[]; self.assertRaises(ValueError,M.verify,data)
 def test_stale_config_manifest_is_rejected_before_running_the_command(self):
  # N9: payload() must catch a stale manifest itself, before main() would
  # spend a subprocess run on it, instead of only surfacing the mismatch on
  # a later `verify` of the saved attestation.
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); snapshot=root/"snapshot"; snapshot.write_text("config")
   manifest=root/"manifest.json"
   manifest.write_text(json.dumps({"snapshot_path":str(snapshot),"snapshot_sha256":"0"*64}))
   self.assertRaises(ValueError, M.payload, [], ["true"], td, manifest)
 def test_case_3_is_not_enforced_by_smoke_attestation_verify_alone(self):
  # Truth-table case 3 (manifest provided, attestation missing config_sha256)
  # is enforced by utilities/resource-runner.py, not by
  # `smoke-attestation verify` in isolation: verify() has no way to learn a
  # manifest was ever expected, so an attestation built without
  # --config-manifest passes standalone verification even when a config
  # manifest exists elsewhere. See utilities/resource_runner.test.py for the
  # actual enforcement point (start rejects the mismatch before Popen).
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"config"; p.write_text("a")
   data=M.payload([p],["true"],td); data.update(status="passed",exit_code=0)
   self.assertNotIn("config_sha256", data)
   self.assertTrue(M.verify(data))
if __name__=="__main__": unittest.main()
