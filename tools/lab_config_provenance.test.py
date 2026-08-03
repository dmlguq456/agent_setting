import hashlib, importlib.util, json, os, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("provenance", ROOT / "tools/lab-config-provenance.py")
M = importlib.util.module_from_spec(SPEC); assert SPEC and SPEC.loader; SPEC.loader.exec_module(M)
CLEAN_ENV = {k: v for k, v in os.environ.items() if k != "AGENT_ARTIFACT_ROOT"}

def run_cli(*args):
    return subprocess.run(
        ["python3", str(ROOT / "tools/lab-config-provenance.py"), *args],
        env=CLEAN_ENV, capture_output=True, text=True,
    )

class TestProvenance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"; self.repo.mkdir()
        (self.repo / "configs").mkdir(); (self.repo / "configs_exp/demo").mkdir(parents=True); (self.repo / "configs_legacy").mkdir()
        (self.repo / "configs/a.yaml").write_text("adopted")
        (self.repo / "configs_exp/demo/b.yaml").write_text("experiment")
        (self.repo / "configs_legacy/c.yaml").write_text("legacy")

    # T1 -- bare names never fall back into exp/ or legacy/, either direction.
    def test_resolution_is_explicit_and_traversal_safe(self):
        self.assertEqual(M.resolve_ref(self.repo, "a.yaml")["namespace"], "default")
        self.assertEqual(M.resolve_ref(self.repo, "exp:demo/b.yaml")["namespace"], "exp")
        self.assertEqual(M.resolve_ref(self.repo, "legacy:c.yaml")["namespace"], "legacy")
        with self.assertRaises(SystemExit): M.resolve_ref(self.repo, "b.yaml")
        with self.assertRaises(SystemExit): M.resolve_ref(self.repo, "c.yaml")
        with self.assertRaises(SystemExit): M.resolve_ref(self.repo, "exp:../x")

    # T2 -- B1 regression: prefixed refs that escape their own lifecycle root
    # must be rejected even when the escaped-to file really exists, plus the
    # traversal/control-character edge cases the original review reproduced.
    def test_prefixed_refs_cannot_escape_their_lifecycle_root(self):
        (self.repo / "secret").mkdir()
        (self.repo / "secret/s.yaml").write_text("secret")
        escapes = [
            "exp:../configs/a.yaml",
            "legacy:../configs/a.yaml",
            "exp:../secret/s.yaml",
            "../../etc/passwd",
        ]
        for ref in escapes:
            with self.subTest(ref=ref):
                with self.assertRaises(SystemExit):
                    M.resolve_ref(self.repo, ref)

    def test_symlink_escape_from_lifecycle_root_is_rejected(self):
        outside = Path(self.temp.name) / "outside.yaml"; outside.write_text("outside")
        (self.repo / "configs_exp/demo/link.yaml").symlink_to(outside)
        with self.assertRaises(SystemExit):
            M.resolve_ref(self.repo, "exp:demo/link.yaml")

    def test_control_characters_in_ref_are_rejected(self):
        for bad in ("configs/a.yaml\n", "configs/a.yaml\r", "configs/a.yaml\x00", "exp:demo/b.yaml\n"):
            with self.subTest(ref=bad):
                with self.assertRaises(SystemExit):
                    M.resolve_ref(self.repo, bad)

    def test_run_id_binds_slug_and_hash(self):
        one = M.run_id("s1", "exp:s1/config.yaml", "a" * 64)
        self.assertNotEqual(one, M.run_id("s2", "exp:s2/config.yaml", "a" * 64))
        self.assertEqual(one, M.run_id("s1", "exp:s1/config.yaml", "a" * 64))
        self.assertNotEqual(one, M.run_id("s1", "exp:s1/config.yaml", "b" * 64))

    def test_seal_is_idempotent_and_verify_is_fail_closed(self):
        source = self.repo / "configs/a.yaml"; out = Path(self.temp.name) / "artifacts"
        args = ["seal", "--repo", str(self.repo), "--config", "a.yaml", "--slug", "demo", "--run-id", "run", "--out", str(out)]
        subprocess.run(["python3", str(ROOT / "tools/lab-config-provenance.py"), *args], check=True, env=CLEAN_ENV)
        manifest = out / "run.manifest.json"; first = manifest.read_bytes()
        subprocess.run(["python3", str(ROOT / "tools/lab-config-provenance.py"), *args], check=True, env=CLEAN_ENV)
        self.assertEqual(first, manifest.read_bytes())
        snapshot = next(out.glob("*.yaml")); snapshot.write_text("tampered")
        result = subprocess.run(["python3", str(ROOT / "tools/lab-config-provenance.py"), "verify", "--manifest", str(manifest)], env=CLEAN_ENV)
        self.assertEqual(result.returncode, 65)

    # T12 -- append-only: re-running seal against an out directory that already
    # holds the correct manifest/snapshot must not rewrite those bytes at all.
    def test_seal_rerun_does_not_touch_existing_manifest_or_snapshot_bytes(self):
        out = Path(self.temp.name) / "artifacts"
        args = ["seal", "--repo", str(self.repo), "--config", "a.yaml", "--slug", "demo", "--run-id", "run", "--out", str(out)]
        subprocess.run(["python3", str(ROOT / "tools/lab-config-provenance.py"), *args], check=True, env=CLEAN_ENV)
        manifest = out / "run.manifest.json"; snapshot = next(out.glob("*.yaml"))
        manifest_before = manifest.read_bytes(); snapshot_before = snapshot.read_bytes()
        manifest_mtime = manifest.stat().st_mtime_ns; snapshot_mtime = snapshot.stat().st_mtime_ns
        subprocess.run(["python3", str(ROOT / "tools/lab-config-provenance.py"), *args], check=True, env=CLEAN_ENV)
        self.assertEqual(manifest_before, manifest.read_bytes())
        self.assertEqual(snapshot_before, snapshot.read_bytes())
        self.assertEqual(manifest_mtime, manifest.stat().st_mtime_ns)
        self.assertEqual(snapshot_mtime, snapshot.stat().st_mtime_ns)

    def test_unstructured_does_not_move_files(self):
        repo = Path(self.temp.name) / "unstructured"; repo.mkdir(); cfg = repo / "model.yaml"; cfg.write_text("x")
        before = sorted(p.relative_to(repo) for p in repo.rglob("*"))
        self.assertEqual(M.resolve_ref(repo, "./model.yaml")["layout"], "legacy/unstructured")
        with self.assertRaises(SystemExit): M.resolve_ref(repo, "model.yaml")
        after = sorted(p.relative_to(repo) for p in repo.rglob("*"))
        self.assertEqual(before, after)

    # T15 -- historical compatibility is only through an explicit migration map
    # or provenance manifest; a checkpoint-directory-derived bare name must not
    # resolve without one.
    def test_checkpoint_directory_name_inference_is_rejected(self):
        repo = Path(self.temp.name) / "ckpt-repo"; repo.mkdir()
        (repo / "checkpoints/run_2026-01-01_epoch12").mkdir(parents=True)
        with self.assertRaises(SystemExit):
            M.resolve_ref(repo, "run_2026-01-01_epoch12")
        with self.assertRaises(SystemExit):
            M.resolve_ref(repo, "checkpoints/run_2026-01-01_epoch12")

    # T8 -- promotion is a recommendation only; resolving/sealing must never
    # mutate the canonical configs/ source.
    def test_promotion_recommendation_path_does_not_mutate_canonical_source(self):
        source = self.repo / "configs/a.yaml"
        before_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        before_mtime = source.stat().st_mtime_ns
        out = Path(self.temp.name) / "artifacts"
        subprocess.run(["python3", str(ROOT / "tools/lab-config-provenance.py"), "seal",
                         "--repo", str(self.repo), "--config", "a.yaml", "--slug", "demo",
                         "--run-id", "run", "--out", str(out)], check=True, env=CLEAN_ENV)
        after_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        after_mtime = source.stat().st_mtime_ns
        self.assertEqual(before_sha, after_sha)
        self.assertEqual(before_mtime, after_mtime)

    # T6 -- the tool never infers the artifact root itself; every path is a
    # required argument, so a bogus AGENT_ARTIFACT_ROOT cannot redirect output.
    def test_tool_does_not_infer_artifact_root(self):
        out = Path(self.temp.name) / "explicit-out"
        env = dict(CLEAN_ENV); env["AGENT_ARTIFACT_ROOT"] = "/nonexistent/bogus-root"
        result = subprocess.run(
            ["python3", str(ROOT / "tools/lab-config-provenance.py"), "seal",
             "--repo", str(self.repo), "--config", "a.yaml", "--slug", "demo",
             "--run-id", "run", "--out", str(out)],
            env=env, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((out / "run.manifest.json").is_file())
        self.assertFalse(Path("/nonexistent/bogus-root").exists())

    def test_package_data(self):
        repo = Path(self.temp.name) / "package"; repo.mkdir(); (repo / "pyproject.toml").write_text("include = ['configs', 'configs_exp', 'configs_legacy']")
        self.assertEqual(subprocess.run(["python3", str(ROOT / "tools/lab-config-provenance.py"), "package-data", "--repo", str(repo)], env=CLEAN_ENV).returncode, 0)

    # T10 -- three variants: everything included, only "configs" missing
    # (B4 regression, previously masked by substring matching on
    # "configs_exp"), and no manifest file present at all.
    def test_package_data_three_variants(self):
        all_included = Path(self.temp.name) / "pkg-all"; all_included.mkdir()
        (all_included / "pyproject.toml").write_text("include = ['configs', 'configs_exp', 'configs_legacy']")
        result = run_cli("package-data", "--repo", str(all_included))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["missing"], [])

        configs_missing = Path(self.temp.name) / "pkg-partial"; configs_missing.mkdir()
        (configs_missing / "pyproject.toml").write_text("include = ['configs_exp', 'configs_legacy']")
        result = run_cli("package-data", "--repo", str(configs_missing))
        self.assertEqual(result.returncode, 65)
        self.assertEqual(json.loads(result.stdout)["missing"], ["configs"])

        no_file = Path(self.temp.name) / "pkg-none"; no_file.mkdir()
        result = run_cli("package-data", "--repo", str(no_file))
        self.assertEqual(result.returncode, 65)
        self.assertEqual(sorted(json.loads(result.stdout)["missing"]), ["configs", "configs_exp", "configs_legacy"])

if __name__ == "__main__": unittest.main()
