#!/usr/bin/env python3
"""Exact-attempt harvest regression tests for Codex and OpenCode adapters."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "capability_route_harvest", ROOT / "utilities/capability-route.py"
)
ROUTE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ROUTE)


class HarvestTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "user.email", "fixture@example.com"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "user.name", "Fixture"],
            check=True,
        )
        (self.repo / "x").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "x"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "init"], check=True)
        self.artifact = self.base / ".agent_reports"
        self.artifact.mkdir()
        self.home = self.base / "agent-home"
        (self.home / "core").mkdir(parents=True)
        (self.home / "core/CORE.md").write_text("fixture\n", encoding="utf-8")
        gate = {
            "spec_read": {"satisfied": True, "source": "fixture"},
            "drift_verdict": "within-spec",
            "workflow_mode": "tracked",
            "artifact_guard": {"satisfied": True, "source": "fixture"},
        }
        dispatch = {
            "tuples": [{
                "parent_harness": "codex",
                "parent_transport": "headless",
                "parent_sandbox": "workspace-write",
                "child_harness": "codex",
                "launch_authority": "conductor",
                "status": "supported",
                "probe_source": "fixture",
                "probe_time": "2026-07-21T00:00:00Z",
                "failure_class": "",
            }],
            "native_subagent": [],
        }
        self.route = ROUTE.compile_route(
            "autopilot-code", "dev", "strong", self.repo, self.artifact,
            signals=["shared-contract"], transport="headless",
            tracking="tracked", tracked_gate_evidence=gate,
            dispatch_evidence=dispatch,
        )
        self.route_path = self.base / "route.json"
        self.route_path.write_text(json.dumps(self.route), encoding="utf-8")
        self.node = next(node for node in self.route["nodes"] if node["id"] == "plan")
        self.evidence = self.base / "plan.md"
        self.evidence.write_text("plan\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def env(self):
        return {
            **os.environ,
            "AGENT_HOME": str(self.home),
            "AGENT_ARTIFACT_ROOT": str(self.artifact),
        }

    def current_row(self, attempt, slug="worker"):
        pipe = (
            "attempt_schema_version=2,dispatch_depth=2,transport=headless,"
            "execution_surface=registered-headless,registered_worker=1,"
            "fallback_hop=same-harness-headless,"
            f"attempt_id={attempt},route_id={self.route['route_id']},"
            f"route_hash={self.route['route_hash']},route_node=plan,"
            f"route_file={self.route_path},completion_gate={self.node['completion_gate']}"
        )
        return (
            f"2026-07-21T00:00:00Z\topen\t{self.repo}\t{self.repo}\t{slug}\t{pipe}\n"
        )

    def test_routed_harvest_replays_shared_completion_for_one_exact_attempt(self):
        attempt = "att-harvest-exact"
        old = os.environ.get("AGENT_HOME")
        os.environ["AGENT_HOME"] = str(self.home)
        try:
            with self.assertRaisesRegex(ValueError, "attempt-row-absent"):
                ROUTE.complete_node(
                    self.route, self.node, "plan", self.evidence,
                    jobs=self.base / "missing.jobs.log", attempt_id=attempt,
                    explicit_attempt_metadata={
                        "attempt_schema_version": 2,
                        "dispatch_depth": 2,
                        "transport": "headless",
                        "execution_surface": "registered-headless",
                        "registered_worker": True,
                        "fallback_hop": "same-harness-headless",
                    },
                )
        finally:
            if old is None:
                os.environ.pop("AGENT_HOME", None)
            else:
                os.environ["AGENT_HOME"] = old
        completion = (
            self.home / ".dispatch/completion" / self.route["route_id"] / "plan.json"
        )
        self.assertTrue(completion.is_file())

        for adapter in ("codex", "opencode"):
            with self.subTest(adapter=adapter):
                jobs = self.base / f"{adapter}.jobs.log"
                jobs.write_text(self.current_row(attempt), encoding="utf-8")
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / f"adapters/{adapter}/bin/dispatch-harvest.py"),
                        "--jobs", str(jobs), "--slug", "worker", "--status", "open",
                        "--mark-done", "--completion", str(completion),
                    ],
                    text=True, capture_output=True, env=self.env(),
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                row = jobs.read_text(encoding="utf-8")
                self.assertIn("\tdone\t", row)
                self.assertIn("note=completed-marker", row)

    def test_ambiguous_or_legacy_selector_never_breadth_closes(self):
        for adapter in ("codex", "opencode"):
            with self.subTest(adapter=adapter, case="ambiguous"):
                jobs = self.base / f"{adapter}.ambiguous.log"
                jobs.write_text(
                    self.current_row("att-harvest-a", "same")
                    + self.current_row("att-harvest-b", "same"),
                    encoding="utf-8",
                )
                before = jobs.read_bytes()
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / f"adapters/{adapter}/bin/dispatch-harvest.py"),
                        "--jobs", str(jobs), "--slug", "same", "--status", "open",
                        "--mark-done",
                    ],
                    text=True, capture_output=True, env=self.env(),
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("reason=ambiguous-selector", result.stdout)
                self.assertEqual(jobs.read_bytes(), before)
            with self.subTest(adapter=adapter, case="legacy"):
                jobs = self.base / f"{adapter}.legacy.log"
                jobs.write_text(
                    f"2026-07-21T00:00:00Z\topen\t/r\t/w\tlegacy\t"
                    "capability=code,depth=2,attempt_id=att-legacy\n",
                    encoding="utf-8",
                )
                before = jobs.read_bytes()
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / f"adapters/{adapter}/bin/dispatch-harvest.py"),
                        "--jobs", str(jobs), "--slug", "legacy", "--status", "open",
                        "--mark-done",
                    ],
                    text=True, capture_output=True, env=self.env(),
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("legacy-attempt-row-read-only", result.stdout)
                self.assertEqual(jobs.read_bytes(), before)

    def test_codex_idempotent_mark_done_with_no_live_row_is_a_noop(self):
        jobs = self.base / "codex.done.log"
        jobs.write_text(
            self.current_row("att-harvest-done").replace(
                "\topen\t", "\tdone\t"
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "adapters/codex/bin/dispatch-harvest.py"),
                "--jobs", str(jobs), "--slug", "worker", "--status", "open",
                "--mark-done",
            ],
            text=True, capture_output=True, env=self.env(),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("marked_done=0", result.stdout)
        self.assertNotIn("UnboundLocalError", result.stderr)


if __name__ == "__main__":
    unittest.main()
