#!/usr/bin/env python3
import importlib.util,os,tempfile,unittest
from pathlib import Path
P=Path(__file__).with_name("resource-runner.py"); S=importlib.util.spec_from_file_location("runner",P); R=importlib.util.module_from_spec(S); S.loader.exec_module(R)
class TestRunner(unittest.TestCase):
 def test_pid_identity_and_registry(self):
  i=R.proc_identity(os.getpid()); self.assertTrue(i); self.assertTrue(R.alive(i)); i["starttime"]="0"; self.assertFalse(R.alive(i))
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"runs.json"; R.locked_update(p,lambda d:d["runs"].update(x={"pid":1})); self.assertIn("x",__import__("json").loads(p.read_text())["runs"])
if __name__=="__main__": unittest.main()
