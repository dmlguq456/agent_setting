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

def _with_hash(data):
    # G4 hardening made attestation_hash required; this recomputes it the
    # same way the CLI does so hand-built fixtures still verify.
    data = dict(data); data.pop("attestation_hash", None)
    data["attestation_hash"] = "sha256:" + hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return data

class TestSmoke(unittest.TestCase):
 def _sealed_repo(self, td):
  root=Path(td); repo=root/"repo"; (repo/"configs").mkdir(parents=True)
  (repo/"configs/a.yaml").write_text("config")
  artifact_root=root/"artifacts"; artifact_root.mkdir()
  return repo, seal(repo, "a.yaml", "demo", artifact_root)

 def test_hash_binding(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"config"; p.write_text("a"); data=M.payload([p],["true"],td); data.update(status="passed",exit_code=0)
   data=_with_hash(data)
   self.assertTrue(M.verify(data)); p.write_text("b"); self.assertRaises(ValueError,M.verify,data)
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
   self.assertEqual(data["config_sha256"], m["snapshot_sha256"])
   data=_with_hash(data)
   self.assertTrue(M.verify(data))
   # Clearing `inputs` after the hash was computed over the full dict makes
   # the *hash* mismatch fire first (rather than the missing-snapshot-row
   # check) -- still a ValueError, and the original claim (empty inputs is
   # rejected) still holds.
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
   data=_with_hash(data)
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
   data = _with_hash(data)
   self.assertTrue(M.verify(data))
   Path(m["source_path"]).write_text("tampered-source")
   self.assertRaises(ValueError, M.verify, data)

 # T-F7-3 (A4): hand-assembling config_sha256/config_source_sha256/
 # config_source_path onto an attestation that never went through
 # --config-manifest must still fail verify -- a snapshot-only input row
 # cannot satisfy the new path-bound requirement.
 #
 # round 5 (plan §1.5): this test was already vacuous under 407b5e66 -- the
 # `--input` here was a file unrelated to the config hash, so it never
 # satisfied even the *hash*-binding check (":56-57"), and the test's
 # assertRaises passed for that reason, never reaching the path-binding code
 # path (":58-63") the name and docstring claim to exercise. The fix below
 # includes the snapshot itself as a plain `--input` so hash-binding is
 # satisfied first, then omits any row at `config_source_path` so the
 # path-binding check is the one that actually fires, asserted on its
 # message.
 def test_T_F7_3_config_source_path_binding_is_not_vacuous(self):
  with tempfile.TemporaryDirectory() as td:
   repo, manifest = self._sealed_repo(td)
   m = json.loads(manifest.read_text())
   snapshot = Path(m["snapshot_path"])
   data = M.payload([snapshot], ["true"], td); data.update(status="passed", exit_code=0)
   data["config_sha256"] = m["snapshot_sha256"]
   data["config_source_sha256"] = m["source_sha256"]
   data["config_source_path"] = str(Path(m["source_path"]).resolve())
   data = _with_hash(data)
   with self.assertRaises(ValueError) as ctx:
       M.verify(data)
   self.assertIn("config source is not bound to an input", str(ctx.exception))

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

 # ================= G4: hash-bound smoke verification =================

 def _full_attestation(self, td, manifest):
  data = M.payload([], ["true"], td, manifest); data.update(status="passed", exit_code=0)
  return _with_hash(data)

 def test_T_G4_1_missing_hash_is_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   repo, manifest = self._sealed_repo(td)
   data = self._full_attestation(td, manifest)
   del data["attestation_hash"]
   with self.assertRaises(ValueError) as ctx:
       M.verify(data)
   self.assertIn("attestation hash is required", str(ctx.exception))

 def _assert_missing_config_key_rejected(self, key):
  with tempfile.TemporaryDirectory() as td:
   repo, manifest = self._sealed_repo(td)
   data = M.payload([], ["true"], td, manifest); data.update(status="passed", exit_code=0)
   del data[key]
   data = _with_hash(data)
   with self.assertRaises(ValueError) as ctx:
       M.verify(data)
   self.assertIn("missing: " + key, str(ctx.exception))

 def test_T_G4_2_missing_config_sha256_is_rejected(self):
  self._assert_missing_config_key_rejected("config_sha256")

 def test_T_G4_3_missing_config_source_sha256_is_rejected(self):
  self._assert_missing_config_key_rejected("config_source_sha256")

 def test_T_G4_4_missing_config_source_path_is_rejected(self):
  self._assert_missing_config_key_rejected("config_source_path")

 def test_T_G4_5_absent_snapshot_row_is_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   snapshot_bytes = b"real-snapshot-bytes"
   source_bytes = b"different-source-content"
   snapshot_sha = hashlib.sha256(snapshot_bytes).hexdigest()
   source_path = Path(td) / "source.yaml"; source_path.write_bytes(source_bytes)
   source_sha = hashlib.sha256(source_bytes).hexdigest()
   # A real file carrying the snapshot hash satisfies hash-binding (step 1)
   # without being byte-identical to the source -- so no *second* row with
   # the config hash exists, and the source is not degenerately the
   # snapshot (config_source_sha256 != config_sha256).
   hash_carrier = Path(td) / "snapshot.bin"; hash_carrier.write_bytes(snapshot_bytes)
   data = M.payload([hash_carrier, source_path], ["true"], td)
   data.update(status="passed", exit_code=0)
   data["config_sha256"] = snapshot_sha
   data["config_source_sha256"] = source_sha
   data["config_source_path"] = str(source_path.resolve())
   data = _with_hash(data)
   with self.assertRaises(ValueError) as ctx:
       M.verify(data)
   self.assertIn("config snapshot row is not bound to an input", str(ctx.exception))

 def test_T_G4_6_degenerate_source_equals_snapshot_passes_with_one_row(self):
  with tempfile.TemporaryDirectory() as td:
   content = b"identical-bytes"
   digest_hex = hashlib.sha256(content).hexdigest()
   source_path = Path(td) / f"{digest_hex}.yaml"; source_path.write_bytes(content)
   data = M.payload([source_path], ["true"], td)
   data.update(status="passed", exit_code=0)
   data["config_sha256"] = digest_hex
   data["config_source_sha256"] = digest_hex
   data["config_source_path"] = str(source_path.resolve())
   data = _with_hash(data)
   self.assertTrue(M.verify(data))

 # T-G4-9 (round 5 plan-check blocking finding, lock-in): a filename/stem
 # carve-out (`Path(config_source_path).stem == config_sha256`) is forgeable
 # -- a source file literally *named* `<config_sha256><suffix>` whose real
 # bytes hash to something else entirely would satisfy it. The corrected
 # carve-out condition is real-digest equality
 # (`config_source_sha256 == config_sha256`), which this forged input must
 # NOT satisfy; if the carve-out ever regresses to a stem check, this test
 # must fail.
 def test_T_G4_9_forged_carve_out_via_deceptive_filename_is_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   snapshot_bytes = b"real-snapshot-bytes"
   snapshot_sha = hashlib.sha256(snapshot_bytes).hexdigest()
   hash_carrier = Path(td) / "snapshot.bin"; hash_carrier.write_bytes(snapshot_bytes)
   forged_source = Path(td) / f"{snapshot_sha}.yaml"
   forged_source.write_text("totally unrelated content")
   forged_sha = hashlib.sha256(forged_source.read_bytes()).hexdigest()
   self.assertNotEqual(forged_sha, snapshot_sha)
   data = M.payload([hash_carrier, forged_source], ["true"], td)
   data.update(status="passed", exit_code=0)
   data["config_sha256"] = snapshot_sha
   data["config_source_sha256"] = forged_sha
   data["config_source_path"] = str(forged_source.resolve())
   data = _with_hash(data)
   with self.assertRaises(ValueError) as ctx:
       M.verify(data)
   self.assertIn("config snapshot row is not bound to an input", str(ctx.exception))

if __name__=="__main__": unittest.main()
