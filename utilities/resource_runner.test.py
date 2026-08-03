#!/usr/bin/env python3
"""CLI regression tests for the detached resource authorization boundary."""
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ENV = {k: v for k, v in os.environ.items() if k != "AGENT_ARTIFACT_ROOT"}
RUNNER = ROOT / "utilities" / "resource-runner.py"
ROUTER = ROOT / "utilities" / "capability-route.py"
SMOKE = ROOT / "tools" / "smoke-attestation.py"
spec = importlib.util.spec_from_file_location("runner", RUNNER)
R = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(R)


class TestRunner(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Test"], check=True)
        (self.repo / "config").write_text("ok\n")
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "initial"], check=True)
        self.artifacts = self.base / "artifacts"
        self.artifacts.mkdir()
        self.home = self.base / "agent-home"
        (self.home / "core").mkdir(parents=True)
        (self.home / "core" / "CORE.md").write_text("core\n")
        (self.home / "utilities").symlink_to(ROOT / "utilities", target_is_directory=True)
        self.route = self.artifacts / "route.json"
        evidence = self.base / "dispatch-evidence.json"
        evidence.write_text(json.dumps({"tuples": [{
            "harness": "codex", "parent_harness": "codex", "parent_transport": "headless",
            "parent_sandbox": "workspace-write", "child_harness": "codex",
            "launch_authority": "conductor", "status": "supported", "probe_source": "test",
            "probe_time": "2026-07-27T00:00:00Z", "failure_class": "none",
        }], "native_subagent": []}))
        result = subprocess.run([
            sys.executable, str(ROUTER), "compile", "--capability", "autopilot-lab",
            "--capability-mode", "setup", "--intensity", "auto", "--signal", "resource-run",
            "--cwd", str(self.repo), "--artifact-root", str(self.artifacts),
            "--dispatch-evidence", str(evidence), "--tracking", "untracked",
            "--spec-read", "not-applicable", "--drift-verdict", "no-project-spec",
            "--workflow-mode", "untracked", "--artifact-guard", "preflight-passed",
            "--output", str(self.route),
        ], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.registry = self.base / "registry.json"
        self.log = self.base / "logs" / "run.log"
        self.launch = self.base / "launched"
        self.attestation = self.base / "smoke.json"
        subprocess.run([
            sys.executable, str(SMOKE), "attest", "--input", str(self.repo / "config"),
            "--cwd", str(self.repo), "--output", str(self.attestation), "--", sys.executable, "-c", "pass",
        ], check=True, stdout=subprocess.DEVNULL)

    def cli(self, *args, cwd=None):
        return subprocess.run([
            sys.executable, str(RUNNER), "--registry", str(self.registry), *args,
        ], cwd=cwd, text=True, capture_output=True)

    def start_args(self, route=None, node="full-run", smoke=None, run_id="case", config_manifest=None):
        return ("start", "--run-id", run_id, "--cwd", str(self.repo), "--log", str(self.log),
                "--route", str(route or self.route), "--node", node,
                *(('--smoke-attestation', str(smoke)) if smoke is not None else ()),
                *(('--config-manifest', str(config_manifest)) if config_manifest is not None else ()),
                "--", sys.executable, "-c", f"from pathlib import Path; import time; Path({str(self.launch)!r}).write_text('launched'); time.sleep(30)")

    def seal_config_manifest(self, run_id):
        PROV = ROOT / "tools" / "lab-config-provenance.py"
        out = self.base / f"configs-out-{run_id}"
        subprocess.run([
            sys.executable, str(PROV), "seal", "--repo", str(self.repo), "--config", "./config",
            "--slug", "demo", "--run-id", run_id, "--out", str(out),
        ], check=True, capture_output=True, text=True, env=CLEAN_ENV)
        return out / f"{run_id}.manifest.json"

    def attest_with_config_manifest(self, manifest_path, name):
        attestation = self.base / f"{name}.json"
        subprocess.run([
            sys.executable, str(SMOKE), "attest", "--input", str(self.repo / "config"),
            "--config-manifest", str(manifest_path), "--cwd", str(self.repo),
            "--output", str(attestation), "--", sys.executable, "-c", "pass",
        ], check=True, stdout=subprocess.DEVNULL, env=CLEAN_ENV)
        return attestation

    def assert_rejected_before_side_effects(self, *args, cli_cwd=None):
        result = self.cli(*args, cwd=cli_cwd)
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.log.exists(), result.stderr)
        self.assertFalse(self.registry.exists(), result.stderr)
        self.assertFalse(self.launch.exists(), result.stderr)

    def test_pid_identity_and_registry(self):
        identity = R.proc_identity(os.getpid())
        self.assertTrue(identity)
        self.assertTrue(R.alive(identity))
        identity["starttime"] = "0"
        self.assertFalse(R.alive(identity))
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "runs.json"
            R.locked_update(path, lambda data: data["runs"].update(x={"pid": 1}))
            self.assertIn("x", json.loads(path.read_text())["runs"])

    def test_actual_cli_rejects_every_invalid_launch_proof_before_side_effects(self):
        cases = [
            ("omitted route", tuple(x for x in self.start_args() if x not in ("--route", str(self.route)))),
            ("omitted node", tuple(x for x in self.start_args() if x not in ("--node", "full-run"))),
            ("unknown node", self.start_args(node="missing")),
            ("missing smoke", self.start_args(smoke=None)),
            ("invalid smoke", self.start_args(smoke=self.base / "missing-smoke.json")),
        ]
        # Omitted flags are represented explicitly to ensure argparse rejects them.
        for name, args in cases:
            with self.subTest(name=name):
                self.assert_rejected_before_side_effects(*args)

        linked = self.base / "linked-route.json"
        linked.symlink_to(self.route)
        self.assert_rejected_before_side_effects(*self.start_args(route=linked, smoke=self.attestation))

        for name, mutate in (
            ("tampered route", lambda row: row.update(route_id="rt-tampered")),
            ("stale source commit", lambda row: row.update(source_commit="0" * 40)),
            ("wrong kind", lambda row: next(n for n in row["nodes"] if n["id"] == "full-run").update(kind="pipeline-stage")),
            ("wrong resource transport", lambda row: next(n for n in row["nodes"] if n["id"] == "full-run").update(resource_transport="inline")),
        ):
            row = json.loads(self.route.read_text())
            mutate(row)
            row.pop("route_hash", None)
            row.pop("route_id", None)
            bare = json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
            row["route_hash"] = "sha256:" + hashlib.sha256(bare).hexdigest()
            row["route_id"] = "rt-" + row["route_hash"].split(":", 1)[1][:16]
            candidate = self.base / f"{name.replace(' ', '-')}.json"
            candidate.write_text(json.dumps(row))
            with self.subTest(name=name):
                self.assert_rejected_before_side_effects(*self.start_args(route=candidate, smoke=self.attestation))

        other = self.base / "other-cwd"
        other.mkdir()
        wrong_cwd_args = list(self.start_args(smoke=self.attestation))
        wrong_cwd_args[wrong_cwd_args.index("--cwd") + 1] = str(other)
        self.assert_rejected_before_side_effects(*wrong_cwd_args)

    def test_valid_detached_start_status_stop_cleans_process_group(self):
        result = self.cli(*self.start_args(smoke=self.attestation))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.strip(), repr(result))
        run = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertTrue(self.log.exists())
        status = self.cli("status", "--run-id", "case")
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(json.loads(status.stdout)["run_id"], "case")
        stop = self.cli("stop", "--run-id", "case")
        self.assertEqual(stop.returncode, 0, stop.stderr)
        for _ in range(50):
            if not R.proc_identity(run["pid"]):
                break
            time.sleep(0.02)
        self.assertFalse(R.proc_identity(run["pid"]))
        self.assertEqual(os.getpgid(run["pid"]) if Path(f"/proc/{run['pid']}").exists() else None, None)

    def _legacy_row(self, run_id):
        identity = R.proc_identity(os.getpid())
        return {**identity, "run_id": run_id, "process_group": os.getpgid(os.getpid()),
                "cwd": str(self.repo), "log": str(self.log), "command": ["true"],
                "route": str(self.route), "node": "full-run", "status": "running"}

    # T7 -- a running legacy process (registry row predating the config
    # fields) must keep the same status/alive() judgment under the new code.
    def test_legacy_run_row_without_config_fields_is_unaffected(self):
        legacy_run = self._legacy_row("legacy")
        R.locked_update(self.registry, lambda data: data["runs"].update(legacy=legacy_run))
        self.assertTrue(R.alive(legacy_run))
        result = self.cli("status", "--run-id", "legacy")
        self.assertEqual(result.returncode, 0, result.stderr)
        row = json.loads(result.stdout)
        self.assertEqual(row["run_id"], "legacy")
        self.assertEqual(row["status"], "running")
        self.assertNotIn("config_ref", row)
        self.assertNotIn("config_sha256", row)

    # T13 -- an existing_run_exception recorded in run.json (a surface the
    # harness never writes) must not cause the registry row to be rewritten,
    # and the original worktree/command/config path/run ID stay intact.
    def test_existing_run_exception_in_run_json_does_not_trigger_a_registry_rewrite(self):
        legacy_run = self._legacy_row("legacy")
        R.locked_update(self.registry, lambda data: data["runs"].update(legacy=legacy_run))
        registry_before = self.registry.read_bytes()
        run_json = self.base / "run.json"
        run_json.write_text(json.dumps({
            "worktree": str(self.repo), "command": ["true"], "config_path": "config",
            "run_id": "legacy",
            "existing_run_exception": {
                "reason": "policy predates this run", "policy_version": "2026-08-03",
                "applies_from": "2026-08-04",
            },
        }, indent=2))
        run_json_before = run_json.read_bytes()
        status = self.cli("status", "--run-id", "legacy")
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(self.registry.read_bytes(), registry_before)
        self.assertEqual(run_json.read_bytes(), run_json_before)
        row = json.loads(status.stdout)
        self.assertEqual(row["cwd"], str(self.repo))
        self.assertEqual(row["command"], ["true"])
        self.assertEqual(row["run_id"], "legacy")

    # T14 -- adding the new provenance fields must not make Fleet mistake an
    # ordinary process for a separate training run: the registry gains
    # exactly one row per start, never a phantom second one.
    def test_ordinary_start_creates_exactly_one_registry_row(self):
        result = self.cli(*self.start_args(smoke=self.attestation))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(self.registry.read_text())
        self.assertEqual(len(data["runs"]), 1)
        self.assertNotIn("config_ref", data["runs"]["case"])

    # B3 regression -- a config manifest whose run_id disagrees with --run-id
    # (and isn't a valid --attempt suffix of it) is rejected before Popen.
    def test_config_manifest_run_id_mismatch_is_rejected_before_side_effects(self):
        manifest = self.seal_config_manifest("sealed-run")
        attestation = self.attest_with_config_manifest(manifest, "config-smoke-mismatch")
        self.assert_rejected_before_side_effects(
            *self.start_args(smoke=attestation, run_id="mismatched-run-id", config_manifest=manifest))

    # B3 regression -- on a match, the registry key and the row's run_id
    # field are always identical (never split by the manifest's own run_id).
    def test_config_manifest_matching_run_id_binds_registry_key_to_row_field(self):
        manifest = self.seal_config_manifest("sealed-run")
        attestation = self.attest_with_config_manifest(manifest, "config-smoke-match")
        result = self.cli(*self.start_args(smoke=attestation, run_id="sealed-run", config_manifest=manifest))
        self.assertEqual(result.returncode, 0, result.stderr)
        run = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(run["run_id"], "sealed-run")
        data = json.loads(self.registry.read_text())
        self.assertIn("sealed-run", data["runs"])
        self.assertEqual(data["runs"]["sealed-run"]["run_id"], "sealed-run")
        self.assertEqual(data["runs"]["sealed-run"]["config_ref"], "./config")

    # B3 regression -- the documented "__aN" attempt-suffix policy: a
    # registry key that retries the same sealed manifest under a distinct
    # key is accepted, and the row still carries the registry key, not the
    # manifest's run_id.
    def test_config_manifest_attempt_suffix_is_accepted(self):
        manifest = self.seal_config_manifest("sealed-run")
        attestation = self.attest_with_config_manifest(manifest, "config-smoke-attempt")
        result = self.cli(*self.start_args(smoke=attestation, run_id="sealed-run__a2", config_manifest=manifest))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(self.registry.read_text())
        self.assertIn("sealed-run__a2", data["runs"])
        self.assertEqual(data["runs"]["sealed-run__a2"]["run_id"], "sealed-run__a2")


if __name__ == "__main__":
    unittest.main()
