#!/usr/bin/env python3
"""SD-56 fixtures: completion marker canonical write + start-time gate."""
import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("route", ROOT / "utilities/capability-route.py")
ROUTE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ROUTE)

ADAPTERS = {
    "codex": ([sys.executable, str(ROOT / "adapters/codex/bin/dispatch-headless.py")], ["--model", "gpt-test", "--reasoning", "low"]),
    "claude": ([sys.executable, str(ROOT / "adapters/claude/bin/dispatch-headless.py")], ["--model", "claude-test", "--effort", "low"]),
    "opencode": ([sys.executable, str(ROOT / "adapters/opencode/bin/dispatch-headless.py")], ["--model", "provider/test", "--variant", "low"]),
}


class CompletionMarkerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "fixture@example.com"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Fixture"], check=True)
        (self.repo / "x").write_text("x", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "x"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "init"], check=True)
        self.artifact = self.base / ".agent_reports"
        self.artifact.mkdir()
        self.agent_home = self.base / "agent-home"
        (self.agent_home / "core").mkdir(parents=True)
        (self.agent_home / "core" / "CORE.md").write_text("fixture\n", encoding="utf-8")
        self.jobs = self.base / "jobs.log"
        self.logs = self.base / "logs"

    def tearDown(self):
        self.temp.cleanup()

    def compile_route(self):
        rows = [
            {
                "parent_harness": "claude",
                "parent_transport": "headless",
                "parent_sandbox": "fixture",
                "child_harness": "claude",
                "launch_authority": "ancestor-broker",
                "status": "supported",
                "probe_source": "fixture-broker",
                "probe_time": "2026-07-15T00:00:00Z",
                "failure_class": "",
                "broker_root": str(self.base / "broker"),
                "broker_instance": "brk-" + "f" * 32,
            }
        ]
        evidence = {"tuples": rows, "native_subagent": []}
        gate = {
            "spec_read": {"satisfied": True, "source": "fixture"},
            "drift_verdict": "within-spec",
            "workflow_mode": "tracked",
            "artifact_guard": {"satisfied": True, "source": "fixture"},
        }
        return ROUTE.compile_route(
            "autopilot-code", "dev", "strong", self.repo, self.artifact,
            signals=["shared-contract"], transport="headless", tracking="tracked",
            tracked_gate_evidence=gate, dispatch_evidence=evidence,
        )

    def as_v2(self, route):
        # Hand-forced v2 shape: strip mutable broker_instance from the
        # evidence and every candidate (mirrors what SD-55's compile_route
        # will do natively), then re-hash. completion_marker_gate only reads
        # `broker_contract_version`, so this exercises the gate independent
        # of SD-55's own compile-time behavior.
        forced = copy.deepcopy(route)
        forced["broker_contract_version"] = 2
        for row in forced.get("dispatch_evidence", {}).get("tuples", []):
            row.pop("broker_instance", None)
        for node in forced.get("nodes", []):
            for hop in node.get("dispatch_fallback", []):
                for candidate in hop.get("candidates", []):
                    candidate.pop("broker_instance", None)
        forced["route_hash"] = ROUTE.route_hash(forced)
        forced["route_id"] = "rt-" + forced["route_hash"].split(":", 1)[1][:16]
        return forced

    def as_v1(self, route):
        # Hand-forced v1 shape (compile_route defaults to v2 as of SD-55) --
        # needed by the negative fixture that documents v1 records are not
        # subject to the completion-marker gate (§13.5.3 acceptance 5).
        forced = copy.deepcopy(route)
        forced["broker_contract_version"] = 1
        for row in forced.get("dispatch_evidence", {}).get("tuples", []):
            if row.get("launch_authority") == "ancestor-broker":
                row["broker_instance"] = "brk-" + "f" * 32
        for node in forced.get("nodes", []):
            for hop in node.get("dispatch_fallback", []):
                for candidate in hop.get("candidates", []):
                    if candidate.get("launch_authority") == "ancestor-broker":
                        candidate["broker_instance"] = "brk-" + "f" * 32
        forced["route_hash"] = ROUTE.route_hash(forced)
        forced["route_id"] = "rt-" + forced["route_hash"].split(":", 1)[1][:16]
        return forced

    def write_route(self, route, name="route.json"):
        path = self.base / name
        path.write_text(json.dumps(route), encoding="utf-8")
        return path

    def base_env(self):
        return {
            **os.environ,
            "AGENT_HOME": str(self.agent_home),
            "AGENT_ARTIFACT_ROOT": str(self.artifact),
            "OPENCODE_CONFIG_CONTENT": "{}",
        }

    def wrapper_command(self, harness, action, route_path, route, node_id):
        wrapper, model = ADAPTERS[harness]
        node = next(n for n in route["nodes"] if n["id"] == node_id)
        return wrapper + [
            f"--{action}", "--worktree", str(self.repo), "--slug", f"{harness}-{node_id}",
            "--capability", "autopilot-code", "--mode", "dev/backend",
            "--intensity", route["effective_intensity"], "--depth", "2", "--parent", "owner",
            "--worker-role", "code-" + node_id, "--owner", "autopilot-code",
            "--jobs", str(self.jobs), "--log-dir", str(self.logs),
            "--parent-harness", harness, "--parent-transport", "headless", "--parent-sandbox", "fixture",
            "--launch-authority", "conductor", "--nested-eligibility", "supported",
            "--eligibility-source", f"{harness}-fixture", "--fallback-ordinal", "1",
            "--route-file", str(route_path), "--route-id", route["route_id"],
            "--route-hash", route["route_hash"], "--route-node", node_id,
            "--registry-digest", route["registry_digest"],
            "--write-scope", ";".join(node["write_scope"]),
        ] + model

    def complete(self, route_path, node_id, evidence_path):
        return subprocess.run(
            [sys.executable, str(ROOT / "utilities/capability-route.py"), "complete",
             "--route", str(route_path), "--node", node_id, "--evidence", str(evidence_path)],
            text=True, capture_output=True, env=self.base_env(),
        )

    # fixture 6 -----------------------------------------------------------
    def test_complete_writes_canonical_marker(self):
        route = self.compile_route()
        route_path = self.write_route(route)
        evidence = self.base / "plan.md"
        evidence.write_text("plan body\n", encoding="utf-8")
        result = self.complete(route_path, "plan", evidence)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        canonical = self.agent_home / ".dispatch" / "completion" / route["route_id"] / "plan.json"
        self.assertTrue(canonical.is_file())
        marker = json.loads(canonical.read_text(encoding="utf-8"))
        self.assertEqual(marker["route_id"], route["route_id"])
        self.assertEqual(marker["route_hash"], route["route_hash"])
        self.assertEqual(marker["registry_digest"], route["registry_digest"])
        self.assertEqual(marker["node_id"], "plan")
        self.assertEqual(marker["completion_gate"], "code-plan")
        import hashlib
        self.assertEqual(marker["evidence"]["sha256"], hashlib.sha256(evidence.read_bytes()).hexdigest())

    # fixture 7 -------------------------------------------------------------
    def test_start_without_dependency_marker_fails_closed(self):
        route = self.as_v2(self.compile_route())
        route_path = self.write_route(route, "route-v2.json")
        for harness in ADAPTERS:
            with self.subTest(harness=harness):
                command = self.wrapper_command(harness, "start", route_path, route, "execute")
                result = subprocess.run(command, text=True, capture_output=True, env=self.base_env())
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("reason=completion-marker-missing", result.stdout)
                self.assertIn("child_spawned=0", result.stdout)
                self.assertFalse(self.jobs.exists())

        # Write the "plan" marker this route depends on, then re-run: the
        # gate itself must no longer be the blocker (other reasons -- e.g.
        # missing real claude/codex/opencode binaries -- are acceptable).
        evidence = self.base / "plan.md"
        evidence.write_text("plan body\n", encoding="utf-8")
        completed = self.complete(route_path, "plan", evidence)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        for harness in ADAPTERS:
            with self.subTest(harness=harness, phase="after-marker"):
                command = self.wrapper_command(harness, "start", route_path, route, "execute")
                result = subprocess.run(command, text=True, capture_output=True, env=self.base_env())
                self.assertNotIn("reason=completion-marker-missing", result.stdout)

    # fixture 8 -------------------------------------------------------------
    def test_marker_absence_is_not_a_failure(self):
        # (a) v1 record + --start, no marker anywhere -> gate must not fire.
        v1_route = self.as_v1(self.compile_route())
        self.assertEqual(v1_route.get("broker_contract_version"), 1)
        v1_path = self.write_route(v1_route, "route-v1.json")
        for harness in ADAPTERS:
            with self.subTest(harness=harness, phase="v1"):
                command = self.wrapper_command(harness, "start", v1_path, v1_route, "execute")
                result = subprocess.run(command, text=True, capture_output=True, env=self.base_env())
                self.assertNotIn("reason=completion-marker-missing", result.stdout)

        # (b) record-unbound --start (no --route-file at all) -> gate must
        # not fire either (no route to evaluate depends_on against).
        for harness in ADAPTERS:
            with self.subTest(harness=harness, phase="unbound"):
                wrapper, model = ADAPTERS[harness]
                command = wrapper + [
                    "--start", "--worktree", str(self.repo), "--slug", f"{harness}-unbound",
                    "--capability", "autopilot-code", "--mode", "dev/backend",
                    "--intensity", "standard", "--depth", "2", "--parent", "owner",
                    "--worker-role", "code-execute", "--owner", "autopilot-code",
                    "--jobs", str(self.jobs), "--log-dir", str(self.logs),
                    "--parent-harness", harness, "--parent-transport", "headless", "--parent-sandbox", "fixture",
                    "--launch-authority", "conductor", "--nested-eligibility", "supported",
                    "--eligibility-source", f"{harness}-fixture", "--fallback-ordinal", "1",
                ] + model
                result = subprocess.run(command, text=True, capture_output=True, env=self.base_env())
                self.assertNotIn("reason=completion-marker-missing", result.stdout)

        # (c) static guardian: nothing outside the gate helper itself and the
        # adapters' generic `fail(e.reason, ...)` relay maps marker absence
        # to a failure string.
        offenders = []
        search_roots = [ROOT / "utilities", ROOT / "adapters", ROOT / "tools" / "fleet"]
        allow = {
            (ROOT / "utilities" / "dispatch_contract.py").resolve(),
            (ROOT / "utilities" / "dispatch_completion_marker.test.py").resolve(),
        }
        for adapter in ("claude", "codex", "opencode"):
            allow.add((ROOT / "adapters" / adapter / "bin" / "dispatch-headless.py").resolve())
        for search_root in search_roots:
            if not search_root.is_dir():
                continue
            for path in search_root.rglob("*.py"):
                if path.resolve() in allow:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
                if "completion-marker-missing" in text:
                    offenders.append(str(path))
        self.assertEqual(offenders, [])

    # fixture 9 ---------------------------------------------------------
    def test_reharvest_preserves_history_and_latest_is_authoritative(self):
        route = self.compile_route()
        route_path = self.write_route(route)
        evidence = self.base / "plan.md"
        evidence.write_text("v1\n", encoding="utf-8")
        first = self.complete(route_path, "plan", evidence)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        directory = self.agent_home / ".dispatch" / "completion" / route["route_id"]
        history_1 = directory / "plan.1.json"
        canonical = directory / "plan.json"
        self.assertTrue(history_1.is_file())
        first_marker = json.loads(canonical.read_text(encoding="utf-8"))
        self.assertEqual(first_marker["sequence"], 1)

        # same evidence again -> no-op (no new history file).
        second = self.complete(route_path, "plan", evidence)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        history_2 = directory / "plan.2.json"
        self.assertFalse(history_2.is_file())

        # changed evidence -> new history entry, old one untouched, canonical
        # points at the latest.
        evidence.write_text("v2\n", encoding="utf-8")
        third = self.complete(route_path, "plan", evidence)
        self.assertEqual(third.returncode, 0, third.stdout + third.stderr)
        self.assertTrue(history_2.is_file())
        self.assertEqual(json.loads(history_1.read_text(encoding="utf-8")), first_marker)
        latest = json.loads(canonical.read_text(encoding="utf-8"))
        self.assertEqual(latest["sequence"], 2)
        import hashlib
        self.assertEqual(latest["evidence"]["sha256"], hashlib.sha256(evidence.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
