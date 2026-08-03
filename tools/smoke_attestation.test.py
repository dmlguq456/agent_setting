#!/usr/bin/env python3
import importlib.util,os,subprocess,sys,tempfile,unittest
import hashlib,json
from pathlib import Path
P=Path(__file__).with_name("smoke-attestation.py"); S=importlib.util.spec_from_file_location("smoke",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)
ROOT=Path(__file__).resolve().parents[1]
PROV=ROOT/"tools"/"lab-config-provenance.py"
CLEAN_ENV={k:v for k,v in os.environ.items() if k!="AGENT_ARTIFACT_ROOT"}

def seal(repo, config, slug, artifact_root):
    result=subprocess.run([sys.executable,str(PROV),"seal","--repo",str(repo),"--config",config,
                            "--slug",slug,"--artifact-root",str(artifact_root)],
                           check=True,capture_output=True,text=True,env=CLEAN_ENV)
    run_id=json.loads(result.stdout)["run_id"]
    return artifact_root/"experiments"/slug/"_internal"/"configs"/f"{run_id}.manifest.json"

class TestSmoke(unittest.TestCase):
 def _sealed_repo(self, td):
  root=Path(td); repo=root/"repo"; (repo/"configs").mkdir(parents=True)
  (repo/"configs/a.yaml").write_text("config")
  artifact_root=root/"artifacts"; artifact_root.mkdir()
  return repo, seal(repo, "a.yaml", "demo", artifact_root)

 def test_hash_binding(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"config"; p.write_text("a"); data=M.payload([p],["true"],td); data.update(status="passed",exit_code=0); self.assertTrue(M.verify(data)); p.write_text("b"); self.assertRaises(ValueError,M.verify,data)
 def test_attestation_hash(self):
   with tempfile.TemporaryDirectory() as td:
    p=Path(td)/"config"; p.write_text("a"); data=M.payload([p],["true"],td); data.update(status="passed",exit_code=0); data["attestation_hash"]="sha256:"+hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest(); self.assertTrue(M.verify(data)); data["command"]=["false"]; self.assertRaises(ValueError,M.verify,data)

 # T-sm-1: fixture replaced with a real `seal` manifest, since payload() now
 # enforces the full §4.7 contract before it will bind a config manifest.
 def test_config_manifest_binds_exact_snapshot(self):
  with tempfile.TemporaryDirectory() as td:
   repo, manifest = self._sealed_repo(td)
   data=M.payload([], ["true"], td, manifest); data.update(status="passed",exit_code=0)
   m=json.loads(manifest.read_text())
   self.assertEqual(data["config_sha256"], m["snapshot_sha256"]); self.assertTrue(M.verify(data))
   data["inputs"]=[]; self.assertRaises(ValueError,M.verify,data)

 # T-sm-2: stale is now a byte tamper on the real snapshot rather than a
 # hand-authored sha256 mismatch, since the manifest itself must verify.
 def test_stale_config_manifest_is_rejected_before_running_the_command(self):
  with tempfile.TemporaryDirectory() as td:
   repo, manifest = self._sealed_repo(td)
   m = json.loads(manifest.read_text())
   Path(m["snapshot_path"]).write_text("tampered-snapshot")
   self.assertRaises(ValueError, M.payload, [], ["true"], td, manifest)

 # T-sm-3: with A4 landed, the "gap" this documents is narrower -- a caller
 # that omits --config-manifest at attest time simply never gets the new
 # top-level fields; the actual attempt-suffix/source-binding enforcement
 # lives in utilities/resource_runner.test.py (start rejects before Popen).
 def test_case_3_is_not_enforced_by_smoke_attestation_verify_alone(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"config"; p.write_text("a")
   data=M.payload([p],["true"],td); data.update(status="passed",exit_code=0)
   self.assertNotIn("config_sha256", data)
   self.assertNotIn("config_source_path", data)
   self.assertTrue(M.verify(data))

 # T-F7-1: both a snapshot row and a source row land in `inputs`; a caller
 # `--input` that duplicates the source path collapses to one row; and the
 # list is sorted by resolved path.
 def test_T_F7_1_both_snapshot_and_source_rows_are_present_and_deduped(self):
  with tempfile.TemporaryDirectory() as td:
   repo, manifest = self._sealed_repo(td)
   m = json.loads(manifest.read_text())
   source = Path(m["source_path"]); snapshot = Path(m["snapshot_path"])
   data = M.payload([source], ["true"], td, manifest)
   paths = [row["path"] for row in data["inputs"]]
   self.assertEqual(paths, sorted(paths))
   self.assertIn(str(source), paths); self.assertIn(str(snapshot), paths)
   self.assertEqual(paths.count(str(source)), 1)

 # T-F7-2: tampering the *source* alone (snapshot untouched) must still fail
 # a standalone `smoke-attestation verify`.
 def test_T_F7_2_source_tamper_alone_fails_verify(self):
  with tempfile.TemporaryDirectory() as td:
   repo, manifest = self._sealed_repo(td)
   m = json.loads(manifest.read_text())
   data = M.payload([], ["true"], td, manifest); data.update(status="passed", exit_code=0)
   self.assertTrue(M.verify(data))
   Path(m["source_path"]).write_text("tampered-source")
   self.assertRaises(ValueError, M.verify, data)

 # T-F7-3 (A4): hand-assembling config_sha256/config_source_sha256/
 # config_source_path onto an attestation that never went through
 # --config-manifest must still fail verify -- a snapshot-only input row
 # cannot satisfy the new path-bound requirement. The attested --input here
 # is a separate file from the manifest's source, so no input row can
 # accidentally satisfy the new config_source_path check by coincidence.
 def test_T_F7_3_config_source_path_binding_is_not_vacuous(self):
  with tempfile.TemporaryDirectory() as td:
   repo, manifest = self._sealed_repo(td)
   m = json.loads(manifest.read_text())
   unrelated = Path(td) / "unrelated-input"; unrelated.write_text("unrelated")
   data = M.payload([unrelated], ["true"], td); data.update(status="passed", exit_code=0)
   data["config_sha256"] = m["snapshot_sha256"]
   data["config_source_sha256"] = m["source_sha256"]
   data["config_source_path"] = str(Path(m["source_path"]).resolve())
   data["attestation_hash"] = "sha256:" + hashlib.sha256(
       json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
   self.assertRaises(ValueError, M.verify, data)

 # T-F7-4 (A5): attest-time source absence is fail closed, even though a
 # standalone `verify` of an already-sealed manifest tolerates it.
 def test_T_F7_4_attest_time_source_absence_is_fail_closed(self):
  with tempfile.TemporaryDirectory() as td:
   repo, manifest = self._sealed_repo(td)
   m = json.loads(manifest.read_text())
   Path(m["source_path"]).unlink()
   self.assertRaises(ValueError, M.payload, [], ["true"], td, manifest)

 # T-F7-5: a manifest that violates the §4.7 contract (extra key, wrong
 # schema_version) must raise before the smoke command would ever run.
 def test_T_F7_5_contract_violations_raise_before_running(self):
  with tempfile.TemporaryDirectory() as td:
   repo, manifest = self._sealed_repo(td)
   m = json.loads(manifest.read_text())
   extra = dict(m); extra["extra"] = "x"
   manifest.write_text(json.dumps(extra))
   self.assertRaises(ValueError, M.payload, [], ["true"], td, manifest)
   v1 = dict(m); v1["schema_version"] = 1
   manifest.write_text(json.dumps(v1))
   self.assertRaises(ValueError, M.payload, [], ["true"], td, manifest)

if __name__=="__main__": unittest.main()
