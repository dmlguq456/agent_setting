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
if __name__=="__main__": unittest.main()
