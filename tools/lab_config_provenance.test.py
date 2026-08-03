import hashlib, importlib.util, io, json, os, subprocess, tarfile, tempfile, unittest, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("provenance", ROOT / "tools/lab-config-provenance.py")
M = importlib.util.module_from_spec(SPEC); assert SPEC and SPEC.loader; SPEC.loader.exec_module(M)
CLEAN_ENV = {k: v for k, v in os.environ.items() if k != "AGENT_ARTIFACT_ROOT"}
TOOL = str(ROOT / "tools/lab-config-provenance.py")

def run_cli(*args, env=None):
    return subprocess.run(["python3", TOOL, *args], env=env or CLEAN_ENV, capture_output=True, text=True)

def seal_cli(repo, config, slug, artifact_root, run_id=None, config_ref=None, env=None):
    args = ["seal", "--repo", str(repo), "--config", config, "--slug", slug, "--artifact-root", str(artifact_root)]
    if run_id is not None: args += ["--run-id", run_id]
    if config_ref is not None: args += ["--config-ref", config_ref]
    return run_cli(*args, env=env)

def manifest_dir(artifact_root, slug):
    return Path(artifact_root) / "experiments" / slug / "_internal" / "configs"


class TestProvenance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"; self.repo.mkdir()
        (self.repo / "configs").mkdir(); (self.repo / "configs_exp/demo").mkdir(parents=True); (self.repo / "configs_legacy").mkdir()
        (self.repo / "configs/a.yaml").write_text("adopted")
        (self.repo / "configs_exp/demo/b.yaml").write_text("experiment")
        (self.repo / "configs_legacy/c.yaml").write_text("legacy")

    def _dir(self):
        return Path(tempfile.mkdtemp(dir=self.temp.name))

    def _custom_repo(self, roots, layout_name="bcresnet", extra_top=None):
        repo = self._dir()
        payload = {"schema_version": 1, "layout": layout_name, "roots": roots}
        if extra_top: payload.update(extra_top)
        (repo / ".lab-config-layout.json").write_text(json.dumps(payload))
        for rel in roots.values() if isinstance(roots, dict) else []:
            if isinstance(rel, str) and not rel.startswith("/") and ".." not in Path(rel).parts:
                (repo / rel).mkdir(parents=True, exist_ok=True)
        return repo

    def _git_repo(self):
        repo = self._dir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
        (repo / "configs").mkdir()
        (repo / "configs/a.yaml").write_text("v1\n")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "init"], check=True)
        return repo

    # ---- T1/base regression (unchanged behavior) ----

    def test_resolution_is_explicit_and_traversal_safe(self):
        self.assertEqual(M.resolve_ref(self.repo, "a.yaml")["namespace"], "default")
        self.assertEqual(M.resolve_ref(self.repo, "exp:demo/b.yaml")["namespace"], "exp")
        self.assertEqual(M.resolve_ref(self.repo, "legacy:c.yaml")["namespace"], "legacy")
        with self.assertRaises(SystemExit): M.resolve_ref(self.repo, "b.yaml")
        with self.assertRaises(SystemExit): M.resolve_ref(self.repo, "c.yaml")
        with self.assertRaises(SystemExit): M.resolve_ref(self.repo, "exp:../x")

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

    def test_unstructured_does_not_move_files(self):
        repo = Path(self.temp.name) / "unstructured"; repo.mkdir(); cfg = repo / "model.yaml"; cfg.write_text("x")
        before = sorted(p.relative_to(repo) for p in repo.rglob("*"))
        self.assertEqual(M.resolve_ref(repo, "./model.yaml")["layout"], "legacy/unstructured")
        with self.assertRaises(SystemExit): M.resolve_ref(repo, "model.yaml")
        after = sorted(p.relative_to(repo) for p in repo.rglob("*"))
        self.assertEqual(before, after)

    def test_checkpoint_directory_name_inference_is_rejected(self):
        repo = Path(self.temp.name) / "ckpt-repo"; repo.mkdir()
        (repo / "checkpoints/run_2026-01-01_epoch12").mkdir(parents=True)
        with self.assertRaises(SystemExit):
            M.resolve_ref(repo, "run_2026-01-01_epoch12")
        with self.assertRaises(SystemExit):
            M.resolve_ref(repo, "checkpoints/run_2026-01-01_epoch12")

    # ---- T-old-1/2/3, T-F5-2: --out/--run-id -> --artifact-root/optional --run-id ----

    def test_seal_is_idempotent_and_verify_is_fail_closed(self):
        artifact_root = self._dir()
        result = seal_cli(self.repo, "a.yaml", "demo", artifact_root)
        self.assertEqual(result.returncode, 0, result.stderr)
        run_id_value = json.loads(result.stdout)["run_id"]
        manifest = manifest_dir(artifact_root, "demo") / f"{run_id_value}.manifest.json"
        first = manifest.read_bytes()
        result2 = seal_cli(self.repo, "a.yaml", "demo", artifact_root, run_id=run_id_value)
        self.assertEqual(result2.returncode, 0, result2.stderr)
        self.assertEqual(first, manifest.read_bytes())
        snapshot = next(manifest_dir(artifact_root, "demo").glob("*.yaml")); snapshot.write_text("tampered")
        result3 = run_cli("verify", "--manifest", str(manifest))
        self.assertEqual(result3.returncode, 65)

    def test_seal_rerun_does_not_touch_existing_manifest_or_snapshot_bytes(self):
        artifact_root = self._dir()
        result = seal_cli(self.repo, "a.yaml", "demo", artifact_root)
        self.assertEqual(result.returncode, 0, result.stderr)
        run_id_value = json.loads(result.stdout)["run_id"]
        out = manifest_dir(artifact_root, "demo")
        manifest = out / f"{run_id_value}.manifest.json"; snapshot = next(out.glob("*.yaml"))
        manifest_before = manifest.read_bytes(); snapshot_before = snapshot.read_bytes()
        manifest_mtime = manifest.stat().st_mtime_ns; snapshot_mtime = snapshot.stat().st_mtime_ns
        result2 = seal_cli(self.repo, "a.yaml", "demo", artifact_root, run_id=run_id_value)
        self.assertEqual(result2.returncode, 0, result2.stderr)
        self.assertEqual(manifest_before, manifest.read_bytes())
        self.assertEqual(snapshot_before, snapshot.read_bytes())
        self.assertEqual(manifest_mtime, manifest.stat().st_mtime_ns)
        self.assertEqual(snapshot_mtime, snapshot.stat().st_mtime_ns)

    def test_promotion_recommendation_path_does_not_mutate_canonical_source(self):
        source = self.repo / "configs/a.yaml"
        before_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        before_mtime = source.stat().st_mtime_ns
        artifact_root = self._dir()
        result = seal_cli(self.repo, "a.yaml", "demo", artifact_root)
        self.assertEqual(result.returncode, 0, result.stderr)
        after_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        after_mtime = source.stat().st_mtime_ns
        self.assertEqual(before_sha, after_sha)
        self.assertEqual(before_mtime, after_mtime)

    # T-F5-2 -- a bogus AGENT_ARTIFACT_ROOT must not redirect output; every
    # path is explicit (--artifact-root is required).
    def test_tool_does_not_infer_artifact_root(self):
        artifact_root = self._dir()
        env = dict(CLEAN_ENV); env["AGENT_ARTIFACT_ROOT"] = "/nonexistent/bogus-root"
        result = seal_cli(self.repo, "a.yaml", "demo", artifact_root, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        run_id_value = json.loads(result.stdout)["run_id"]
        self.assertTrue((manifest_dir(artifact_root, "demo") / f"{run_id_value}.manifest.json").is_file())
        self.assertFalse(Path("/nonexistent/bogus-root").exists())

    def test_package_data(self):
        repo = self._dir(); (repo / "pyproject.toml").write_text("include = ['configs', 'configs_exp', 'configs_legacy']")
        self.assertEqual(run_cli("package-data", "--repo", str(repo)).returncode, 0)

    def test_package_data_three_variants(self):
        all_included = self._dir()
        (all_included / "pyproject.toml").write_text("include = ['configs', 'configs_exp', 'configs_legacy']")
        result = run_cli("package-data", "--repo", str(all_included))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["missing"], [])

        configs_missing = self._dir()
        (configs_missing / "pyproject.toml").write_text("include = ['configs_exp', 'configs_legacy']")
        result = run_cli("package-data", "--repo", str(configs_missing))
        self.assertEqual(result.returncode, 65)
        self.assertEqual(json.loads(result.stdout)["missing"], ["configs"])

        no_file = self._dir()
        result = run_cli("package-data", "--repo", str(no_file))
        self.assertEqual(result.returncode, 65)
        self.assertEqual(sorted(json.loads(result.stdout)["missing"]), ["configs", "configs_exp", "configs_legacy"])

    # ================= F1: declared physical roots =================

    def test_T_F1_1_declared_roots_resolve_bare_and_prefixed(self):
        repo = self._custom_repo({"default": "conf", "exp": "conf/experiments", "legacy": "conf/archive"})
        (repo / "conf/a.yaml").write_text("a")
        (repo / "conf/experiments/demo").mkdir(parents=True, exist_ok=True)
        (repo / "conf/experiments/demo/b.yaml").write_text("b")
        (repo / "conf/archive/c.yaml").write_text("c")
        self.assertEqual(M.resolve_ref(repo, "a.yaml")["path"], str((repo / "conf/a.yaml").resolve()))
        self.assertEqual(M.resolve_ref(repo, "config:a.yaml")["path"], str((repo / "conf/a.yaml").resolve()))
        self.assertEqual(M.resolve_ref(repo, "legacy:c.yaml")["path"], str((repo / "conf/archive/c.yaml").resolve()))

    def test_T_F1_2_default_names_do_not_resolve_under_custom_layout(self):
        repo = self._custom_repo({"default": "conf", "exp": "conf_exp", "legacy": "conf_legacy"})
        (repo / "conf/a.yaml").write_text("a")
        with self.assertRaises(SystemExit):
            M.resolve_ref(repo, "configs/a.yaml")

    def test_T_F1_3_declared_roots_still_traversal_safe(self):
        repo = self._custom_repo({"default": "conf", "exp": "conf_exp", "legacy": "conf_legacy"})
        (repo / "conf_exp/demo").mkdir(parents=True); (repo / "conf_exp/demo/b.yaml").write_text("b")
        (repo / "secret.yaml").write_text("s")
        with self.assertRaises(SystemExit):
            M.resolve_ref(repo, "exp:../secret.yaml")
        outside = Path(self.temp.name) / "outside.yaml"; outside.write_text("o")
        (repo / "conf_exp/link.yaml").symlink_to(outside)
        with self.assertRaises(SystemExit):
            M.resolve_ref(repo, "exp:link.yaml")

    def test_T_F1_4_malformed_declaration_fails_closed(self):
        cases = []

        bad_json = self._dir(); (bad_json / ".lab-config-layout.json").write_text("{not json")
        cases.append(bad_json)

        missing_roots = self._dir(); (missing_roots / ".lab-config-layout.json").write_text(json.dumps({"schema_version": 1}))
        cases.append(missing_roots)

        extra_key = self._dir()
        (extra_key / ".lab-config-layout.json").write_text(json.dumps({
            "schema_version": 1, "roots": {"default": "c", "exp": "e", "legacy": "l", "extra": "x"}}))
        cases.append(extra_key)

        absolute_root = self._dir()
        (absolute_root / ".lab-config-layout.json").write_text(json.dumps({
            "schema_version": 1, "roots": {"default": "/etc", "exp": "e", "legacy": "l"}}))
        cases.append(absolute_root)

        traversal_root = self._dir()
        (traversal_root / ".lab-config-layout.json").write_text(json.dumps({
            "schema_version": 1, "roots": {"default": "c/../x", "exp": "e", "legacy": "l"}}))
        cases.append(traversal_root)

        for repo in cases:
            with self.subTest(repo=repo):
                with self.assertRaises(SystemExit):
                    M.layout_spec(repo.resolve())

    def test_T_F1_5_nested_roots_use_longest_match(self):
        repo = self._custom_repo({"default": "conf", "exp": "conf/experiments", "legacy": "conf/archive"})
        (repo / "conf/experiments/demo").mkdir(parents=True, exist_ok=True)
        (repo / "conf/experiments/demo/b.yaml").write_text("b")
        resolved = M.resolve_ref(repo, "conf/experiments/demo/b.yaml")
        self.assertEqual(resolved["namespace"], "exp")
        self.assertEqual(resolved["config_ref"], "exp:demo/b.yaml")

    def test_T_F1_6_lexically_duplicate_roots_fail_closed(self):
        repo = self._dir()
        (repo / ".lab-config-layout.json").write_text(json.dumps({
            "schema_version": 1, "roots": {"default": "conf", "exp": "conf", "legacy": "conf_legacy"}}))
        with self.assertRaises(SystemExit):
            M.layout_spec(repo.resolve())

    def test_T_F1_7_segment_boundary_prefix_is_not_a_match(self):
        repo = self._custom_repo({"default": "conf", "exp": "conf_exp", "legacy": "conf_legacy"})
        (repo / "conference").mkdir(); (repo / "conference/x.yaml").write_text("x")
        resolved = M.resolve_ref(repo, "conference/x.yaml")
        self.assertEqual(resolved["namespace"], "path")
        self.assertEqual(resolved["config_ref"], "path:conference/x.yaml")

    def test_T_F1_8_label_only_declaration_is_honest_about_roots(self):
        repo = self._dir()
        (repo / ".lab-config-layout").write_text("bcresnet\n")
        label, roots, kind = M.layout_spec(repo.resolve())
        self.assertEqual(kind, "label-only")
        self.assertEqual(label, "declared/bcresnet")
        self.assertEqual(roots, M.DEFAULT_ROOTS)

    def test_T_F1_9_bad_json_reports_declaration_path_in_stderr(self):
        repo = self._dir(); decl = repo / ".lab-config-layout.json"; decl.write_text("{not json")
        result = run_cli("resolve", "--repo", str(repo), "--ref", "a.yaml")
        self.assertEqual(result.returncode, 65)
        self.assertIn(str(decl), result.stderr)

    def test_T_F1_10_symlinked_root_collapse_fails_closed(self):
        repo = self._dir()
        (repo / "conf").mkdir(); (repo / "conf_legacy").mkdir()
        (repo / "conf_link").symlink_to(repo / "conf", target_is_directory=True)
        (repo / ".lab-config-layout.json").write_text(json.dumps({
            "schema_version": 1, "roots": {"default": "conf", "exp": "conf_link", "legacy": "conf_legacy"}}))
        with self.assertRaises(SystemExit):
            M.layout_spec(repo.resolve())

    # ================= F2: canonical config_ref =================

    def test_T_F2_1_five_forms_normalize_to_the_same_config_ref(self):
        forms = ["a.yaml", "config:a.yaml", "configs/a.yaml", "./configs/a.yaml", str((self.repo / "configs/a.yaml").resolve())]
        for ref in forms:
            with self.subTest(ref=ref):
                self.assertEqual(M.resolve_ref(self.repo, ref)["config_ref"], "config:a.yaml")

    def test_T_F2_2_exp_forms_normalize(self):
        for ref in ("exp:demo/b.yaml", "configs_exp/demo/b.yaml"):
            with self.subTest(ref=ref):
                self.assertEqual(M.resolve_ref(self.repo, ref)["config_ref"], "exp:demo/b.yaml")

    def test_T_F2_3_custom_layout_normalizes(self):
        repo = self._custom_repo({"default": "conf", "exp": "conf_exp", "legacy": "conf_legacy"})
        (repo / "conf/a.yaml").write_text("a")
        self.assertEqual(M.resolve_ref(repo, "conf/a.yaml")["config_ref"], "config:a.yaml")

    def test_T_F2_4_seal_rejects_forged_config_ref(self):
        artifact_root = self._dir()
        result = seal_cli(self.repo, "a.yaml", "demo", artifact_root, config_ref="config:forged.yaml")
        self.assertEqual(result.returncode, 65)

    def test_T_F2_5_run_id_config_ref_grammar_is_validated(self):
        for bad in ("config:../x", "not-a-ref", "config:\x01bad", "config:trailing/"):
            with self.subTest(ref=bad):
                result = run_cli("run-id", "--slug", "demo", "--config-ref", bad)
                self.assertEqual(result.returncode, 65)

    def test_T_F2_6_symlinked_declared_root_still_attributes_correctly(self):
        repo = self._dir()
        (repo / "conf").mkdir(); (repo / "conf_legacy").mkdir()
        (repo / "actual_exp").mkdir(); (repo / "actual_exp/demo").mkdir()
        (repo / "actual_exp/demo/b.yaml").write_text("b")
        (repo / "conf_exp").symlink_to(repo / "actual_exp", target_is_directory=True)
        (repo / ".lab-config-layout.json").write_text(json.dumps({
            "schema_version": 1, "roots": {"default": "conf", "exp": "conf_exp", "legacy": "conf_legacy"}}))
        resolved = M.resolve_ref(repo, "exp:demo/b.yaml")
        self.assertEqual(resolved["namespace"], "exp")
        self.assertEqual(resolved["config_ref"], "exp:demo/b.yaml")

    # ================= F3: slug/run-id safety =================

    def test_T_F3_1_slug_is_required_and_validated(self):
        artifact_root = self._dir()
        for bad_slug in ("../x", ".", "..", "a" * 65, "bad\x01slug"):
            with self.subTest(slug=bad_slug):
                result = seal_cli(self.repo, "a.yaml", bad_slug, artifact_root)
                self.assertEqual(result.returncode, 65)

    def test_T_F3_2_run_id_stem_excludes_namespace_prefix(self):
        rid = M.run_id("demo", "config:a.yaml", "a" * 64)
        self.assertIn("__a__", rid)
        self.assertNotIn("config-a", rid)
        self.assertNotIn("config:a", rid)

    def test_T_F3_3_run_id_is_optional_and_verified(self):
        artifact_root = self._dir()
        result = seal_cli(self.repo, "a.yaml", "demo", artifact_root)
        self.assertEqual(result.returncode, 0, result.stderr)
        computed = json.loads(result.stdout)["run_id"]
        mismatched = seal_cli(self.repo, "a.yaml", "demo", artifact_root, run_id="not-the-computed-value")
        self.assertEqual(mismatched.returncode, 65)
        traversal = seal_cli(self.repo, "a.yaml", "demo", artifact_root, run_id="../../evil")
        self.assertEqual(traversal.returncode, 65)
        matching = seal_cli(self.repo, "a.yaml", "demo", artifact_root, run_id=computed)
        self.assertEqual(matching.returncode, 0, matching.stderr)

    def test_T_F3_4_manifest_path_matches_derived_output_directory(self):
        artifact_root = self._dir()
        result = seal_cli(self.repo, "a.yaml", "demo", artifact_root)
        self.assertEqual(result.returncode, 0, result.stderr)
        run_id_value = json.loads(result.stdout)["run_id"]
        manifest = manifest_dir(artifact_root, "demo") / f"{run_id_value}.manifest.json"
        snapshot = next(manifest_dir(artifact_root, "demo").glob("*.yaml"))
        self.assertEqual(manifest.resolve().parent, snapshot.resolve().parent)

    # ================= F4: source-scoped git state =================

    def test_T_F4_1_clean(self):
        repo = self._git_repo()
        state, commit = M.git_state(repo, Path("configs/a.yaml"))
        self.assertEqual(state, "clean"); self.assertRegex(commit, r"^[0-9a-f]{40}$")

    def test_T_F4_2_staged(self):
        repo = self._git_repo()
        (repo / "configs/a.yaml").write_text("v2\n")
        subprocess.run(["git", "-C", str(repo), "add", "configs/a.yaml"], check=True)
        state, _ = M.git_state(repo, Path("configs/a.yaml"))
        self.assertEqual(state, "staged")

    def test_T_F4_3_staged_and_unstaged(self):
        repo = self._git_repo()
        (repo / "configs/a.yaml").write_text("v2\n")
        subprocess.run(["git", "-C", str(repo), "add", "configs/a.yaml"], check=True)
        (repo / "configs/a.yaml").write_text("v3\n")
        state, _ = M.git_state(repo, Path("configs/a.yaml"))
        self.assertEqual(state, "staged+unstaged")

    def test_T_F4_4_untracked(self):
        repo = self._git_repo()
        (repo / "configs/new.yaml").write_text("new\n")
        state, _ = M.git_state(repo, Path("configs/new.yaml"))
        self.assertEqual(state, "untracked")

    def test_T_F4_5_non_git_directory(self):
        repo = self._dir(); (repo / "configs").mkdir(); (repo / "configs/a.yaml").write_text("x")
        state, commit = M.git_state(repo, Path("configs/a.yaml"))
        self.assertEqual(state, "unknown-no-git"); self.assertEqual(commit, "unknown")

    # Must never come back "clean" for a probe that is actually source-scoped.
    def test_T_F4_6_dirty_sibling_does_not_taint_clean_config(self):
        repo = self._git_repo()
        (repo / "configs/sibling.yaml").write_text("dirty\n")
        state, _ = M.git_state(repo, Path("configs/a.yaml"))
        self.assertEqual(state, "clean")

    def test_T_F4_7_gitignored_config_is_ignored_and_dirty(self):
        repo = self._git_repo()
        (repo / ".gitignore").write_text("configs/ignored.yaml\n")
        subprocess.run(["git", "-C", str(repo), "add", ".gitignore"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "ignore"], check=True)
        (repo / "configs/ignored.yaml").write_text("secret\n")
        state, _ = M.git_state(repo, Path("configs/ignored.yaml"))
        self.assertEqual(state, "ignored")

    def test_T_F4_8_rename_record_does_not_misparse_next_record(self):
        repo = self._git_repo()
        subprocess.run(["git", "-C", str(repo), "mv", "configs/a.yaml", "configs/renamed.yaml"], check=True)
        state, _ = M.git_state(repo, Path("configs/renamed.yaml"))
        self.assertIn(state, ("staged", "staged+unstaged"))

    # ================= F5: artifact-root derivation =================

    def test_T_F5_1_linked_worktree_writes_to_primary_artifact_root(self):
        primary = self._git_repo()
        (primary / ".agent_reports").mkdir()
        linked = Path(self.temp.name) / "linked-worktree"
        subprocess.run(["git", "-C", str(primary), "worktree", "add", str(linked)], check=True, capture_output=True, text=True)
        env = dict(CLEAN_ENV); env.pop("AGENT_ARTIFACT_ROOT", None)
        artifact_root_probe = subprocess.run(
            ["sh", str(ROOT / "utilities/artifact-root.sh"), str(linked)],
            env=env, capture_output=True, text=True,
        )
        self.assertEqual(artifact_root_probe.returncode, 0, artifact_root_probe.stderr)
        artifact_root = Path(artifact_root_probe.stdout.strip())
        before = sorted(p.relative_to(linked) for p in linked.rglob("*") if ".git" not in p.parts)
        result = seal_cli(linked, "configs/a.yaml", "demo", artifact_root, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        run_id_value = json.loads(result.stdout)["run_id"]
        self.assertTrue((manifest_dir(artifact_root, "demo") / f"{run_id_value}.manifest.json").is_file())
        after = sorted(p.relative_to(linked) for p in linked.rglob("*") if ".git" not in p.parts)
        self.assertEqual(before, after)

    def test_T_F5_3_artifact_root_must_be_absolute_and_exist(self):
        for bad in ("relative-dir", str(Path(self.temp.name) / "does-not-exist")):
            with self.subTest(bad=bad):
                result = seal_cli(self.repo, "a.yaml", "demo", bad)
                self.assertEqual(result.returncode, 65)

    # ================= F6: fail-closed verify + schema v2 =================

    def _sealed_manifest(self):
        artifact_root = self._dir()
        result = seal_cli(self.repo, "a.yaml", "demo", artifact_root)
        self.assertEqual(result.returncode, 0, result.stderr)
        run_id_value = json.loads(result.stdout)["run_id"]
        manifest = manifest_dir(artifact_root, "demo") / f"{run_id_value}.manifest.json"
        return artifact_root, manifest, json.loads(manifest.read_text())

    def test_T_F6_1_key_set_mismatch_is_rejected(self):
        _, manifest, data = self._sealed_manifest()
        missing_key = dict(data); del missing_key["source_git_state"]
        manifest.write_text(json.dumps(missing_key))
        self.assertEqual(run_cli("verify", "--manifest", str(manifest)).returncode, 65)
        extra_key = dict(data); extra_key["extra"] = "x"
        manifest.write_text(json.dumps(extra_key))
        self.assertEqual(run_cli("verify", "--manifest", str(manifest)).returncode, 65)

    def test_T_F6_2_schema_version_1_is_rejected(self):
        _, manifest, data = self._sealed_manifest()
        v1 = dict(data); v1["schema_version"] = 1
        manifest.write_text(json.dumps(v1))
        self.assertEqual(run_cli("verify", "--manifest", str(manifest)).returncode, 65)

    def test_T_F6_3_type_and_pattern_violations_are_rejected(self):
        _, manifest, data = self._sealed_manifest()
        cases = [
            {"source_dirty": "false"},
            {"source_sha256": "a" * 63},
            {"source_git_state": "not-a-state"},
            {"config_ref": "not-a-ref"},
        ]
        for change in cases:
            with self.subTest(change=change):
                bad = dict(data); bad.update(change)
                manifest.write_text(json.dumps(bad))
                self.assertEqual(run_cli("verify", "--manifest", str(manifest)).returncode, 65)

    def test_T_F6_4_unsafe_run_id_is_rejected(self):
        _, manifest, data = self._sealed_manifest()
        bad = dict(data); bad["run_id"] = "../evil"
        manifest.write_text(json.dumps(bad))
        self.assertEqual(run_cli("verify", "--manifest", str(manifest)).returncode, 65)

    def test_T_F6_5_source_and_snapshot_digest_must_agree(self):
        _, manifest, data = self._sealed_manifest()
        bad = dict(data); bad["source_sha256"] = "0" * 64
        manifest.write_text(json.dumps(bad))
        self.assertEqual(run_cli("verify", "--manifest", str(manifest)).returncode, 65)

    def test_T_F6_6_snapshot_filename_and_digest_are_checked(self):
        artifact_root, manifest, data = self._sealed_manifest()
        snapshot = Path(data["snapshot_path"])
        original = snapshot.read_bytes()
        snapshot.write_text("tampered")
        self.assertEqual(run_cli("verify", "--manifest", str(manifest)).returncode, 65)
        snapshot.write_bytes(original)
        renamed = snapshot.with_name("not-the-hash.yaml"); snapshot.rename(renamed)
        bad = dict(data); bad["snapshot_path"] = str(renamed)
        manifest.write_text(json.dumps(bad))
        self.assertEqual(run_cli("verify", "--manifest", str(manifest)).returncode, 65)

    def test_T_F6_7_manifest_must_stay_in_situ(self):
        artifact_root, manifest, data = self._sealed_manifest()
        outside = self._dir()
        moved_manifest = outside / manifest.name; moved_snapshot = outside / Path(data["snapshot_path"]).name
        moved_manifest.write_bytes(manifest.read_bytes())
        moved_snapshot.write_bytes(Path(data["snapshot_path"]).read_bytes())
        rewritten = dict(data); rewritten["snapshot_path"] = str(moved_snapshot)
        moved_manifest.write_text(json.dumps(rewritten))
        self.assertEqual(run_cli("verify", "--manifest", str(moved_manifest)).returncode, 65)

    def test_T_F6_8_source_absence_passes_but_source_tamper_fails(self):
        artifact_root, manifest, data = self._sealed_manifest()
        source = Path(data["source_path"])
        backup = source.read_bytes()
        source.unlink()
        result = run_cli("verify", "--manifest", str(manifest))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("source_present=false", result.stdout)
        source.write_text("tampered")
        result2 = run_cli("verify", "--manifest", str(manifest))
        self.assertEqual(result2.returncode, 65)
        source.write_bytes(backup)

    def test_T_F6_9_required_keys_are_a_three_way_anchor(self):
        schema = json.loads((ROOT / "capabilities/lab-config-manifest.schema.json").read_text())
        self.assertEqual(set(schema["required"]), M.MANIFEST_KEYS)
        _, _, data = self._sealed_manifest()
        self.assertEqual(set(data.keys()), M.MANIFEST_KEYS)

    # ================= F8: archive-verified packaging =================

    def _make_zip(self, path, members):
        with zipfile.ZipFile(path, "w") as zf:
            for name, content in members.items():
                zf.writestr(name, content)

    def _make_tar(self, path, mode, plain=(), symlinks=(), dirs=()):
        with tarfile.open(path, mode) as tf:
            for name in dirs:
                info = tarfile.TarInfo(name=name); info.type = tarfile.DIRTYPE
                tf.addfile(info)
            for name, content in plain:
                data = content.encode()
                info = tarfile.TarInfo(name=name); info.size = len(data)
                tf.addfile(info, io.BytesIO(data))
            for name, target in symlinks:
                info = tarfile.TarInfo(name=name); info.type = tarfile.SYMTYPE; info.linkname = target
                tf.addfile(info)

    def test_T_F8_1_zip_archive_with_all_roots_verifies(self):
        archive = Path(self.temp.name) / "pkg.whl"
        self._make_zip(archive, {
            "pkg/configs/a.yaml": "x", "pkg/configs_exp/demo/b.yaml": "x", "pkg/configs_legacy/c.yaml": "x",
        })
        result = run_cli("package-data", "--repo", str(self.repo), "--archive", str(archive))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["check"], "archive"); self.assertTrue(data["verified"]); self.assertEqual(data["missing"], [])

    def test_T_F8_2_missing_root_fails_closed(self):
        archive = Path(self.temp.name) / "pkg-partial.whl"
        self._make_zip(archive, {"pkg/configs_exp/demo/b.yaml": "x", "pkg/configs_legacy/c.yaml": "x"})
        result = run_cli("package-data", "--repo", str(self.repo), "--archive", str(archive))
        self.assertEqual(result.returncode, 65)
        self.assertEqual(json.loads(result.stdout)["missing"], ["configs"])

    def test_T_F8_3_tar_gz_archive_works(self):
        archive = Path(self.temp.name) / "pkg.tar.gz"
        self._make_tar(archive, "w:gz", plain=[
            ("pkg/configs/a.yaml", "x"), ("pkg/configs_exp/demo/b.yaml", "x"), ("pkg/configs_legacy/c.yaml", "x"),
        ])
        result = run_cli("package-data", "--repo", str(self.repo), "--archive", str(archive))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["verified"])

    def test_T_F8_4_unsupported_archive_format_fails_closed(self):
        archive = Path(self.temp.name) / "pkg.rar"; archive.write_bytes(b"not-an-archive")
        result = run_cli("package-data", "--repo", str(self.repo), "--archive", str(archive))
        self.assertEqual(result.returncode, 65)

    def test_T_F8_5_static_mode_does_not_claim_verification(self):
        repo = self._dir(); (repo / "pyproject.toml").write_text("include = ['configs', 'configs_exp', 'configs_legacy']")
        result = run_cli("package-data", "--repo", str(repo))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["check"], "static-declaration")

    def test_T_F8_6_symlink_and_hardlink_members_count_as_present(self):
        archive = Path(self.temp.name) / "pkg-links.tar"
        self._make_tar(archive, "w", plain=[
            ("pkg/_real/a.yaml", "x"), ("pkg/configs_exp/demo/b.yaml", "x"), ("pkg/configs_legacy/c.yaml", "x"),
        ], symlinks=[("pkg/configs/a.yaml", "../_real/a.yaml")])
        result = run_cli("package-data", "--repo", str(self.repo), "--archive", str(archive))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["verified"])

    def test_T_F8_7_leading_dot_slash_is_normalized(self):
        archive = Path(self.temp.name) / "pkg-dotslash.tar"
        self._make_tar(archive, "w", plain=[
            ("./pkg/configs/a.yaml", "x"), ("./pkg/configs_exp/demo/b.yaml", "x"), ("./pkg/configs_legacy/c.yaml", "x"),
        ])
        result = run_cli("package-data", "--repo", str(self.repo), "--archive", str(archive))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["verified"])

    def test_T_F8_8_unrelated_nested_same_name_dir_is_a_visible_false_positive(self):
        archive = Path(self.temp.name) / "pkg-nested.tar"
        self._make_tar(archive, "w", plain=[
            ("pkg/tests/fixtures/configs/x.yaml", "x"),
            ("pkg/configs_exp/demo/b.yaml", "x"), ("pkg/configs_legacy/c.yaml", "x"),
        ])
        result = run_cli("package-data", "--repo", str(self.repo), "--archive", str(archive))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["verified"])
        self.assertEqual(data["matched"]["default"], "pkg/tests/fixtures/configs/x.yaml")

    def test_T_F8_9_directory_only_entry_is_missing(self):
        archive = Path(self.temp.name) / "pkg-dironly.tar"
        self._make_tar(archive, "w", dirs=["pkg/configs/"], plain=[
            ("pkg/configs_exp/demo/b.yaml", "x"), ("pkg/configs_legacy/c.yaml", "x"),
        ])
        result = run_cli("package-data", "--repo", str(self.repo), "--archive", str(archive))
        self.assertEqual(result.returncode, 65)
        self.assertEqual(json.loads(result.stdout)["missing"], ["configs"])

    def test_T_F8_10_custom_declared_roots_via_archive(self):
        repo = self._custom_repo({"default": "conf", "exp": "conf_exp", "legacy": "conf_legacy"})
        archive = Path(self.temp.name) / "pkg-custom.whl"
        self._make_zip(archive, {"pkg/conf/a.yaml": "x", "pkg/conf_exp/demo/b.yaml": "x", "pkg/conf_legacy/c.yaml": "x"})
        result = run_cli("package-data", "--repo", str(repo), "--archive", str(archive))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["verified"])


if __name__ == "__main__": unittest.main()
