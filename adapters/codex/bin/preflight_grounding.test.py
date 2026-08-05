#!/usr/bin/env python3
"""Codex capability router -> Fleet inline grounding bridge (F-43)."""

from pathlib import Path
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
PREFLIGHT = ROOT / "adapters" / "codex" / "bin" / "preflight.sh"


class PreflightGroundingTest(unittest.TestCase):
    def run_route(self, worker=False):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        agent_home = base / "agent-home"
        (agent_home / "core").mkdir(parents=True)
        (agent_home / "core" / "CORE.md").write_text("fixture\n", encoding="utf-8")
        cwd = base / "repo"
        cwd.mkdir()
        env = {**os.environ, "AGENT_HOME": str(agent_home), "HOME": str(base)}
        if worker:
            env["AGENT_SESSION_ROLE"] = "worker"
        result = subprocess.run(
            [str(PREFLIGHT), "route", "autopilot-code", str(cwd), "sid-f43",
             "debug", "direct"],
            text=True, capture_output=True, env=env, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return agent_home / ".capability-grounding" / "sid-f43"

    def test_main_route_records_exact_capability_mode_and_intensity(self):
        marker = self.run_route()
        self.assertEqual(
            marker.read_text(encoding="utf-8").splitlines(),
            ["capability=autopilot-code", "mode=debug", "intensity=direct",
             "cwd=" + str(marker.parents[2] / "repo")],
        )

    def test_worker_route_does_not_create_inline_main_marker(self):
        self.assertFalse(self.run_route(worker=True).exists())


class GuardIdentityTest(unittest.TestCase):
    """SD-45 deterministic guard identity (plan.md Phase 2, round_1 finding 4)."""

    def _fixture(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        agent_home = base / "agent-home"
        (agent_home / "core").mkdir(parents=True)
        (agent_home / "core" / "CORE.md").write_text("fixture\n", encoding="utf-8")
        # core-read-marker.sh only fires under `$repo/core/*.md`; make
        # agent_home its own repo root so the marker actually writes.
        subprocess.run(["git", "init", "-q", str(agent_home)], check=True)
        subprocess.run(
            ["git", "-C", str(agent_home), "config", "user.email", "fixture@example.com"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(agent_home), "config", "user.name", "Fixture"], check=True
        )
        prd = agent_home / "core" / "CORE.md"  # any readable file works for `read`
        return base, agent_home, prd

    def _base_env(self, base, agent_home):
        return {
            "AGENT_HOME": str(agent_home),
            "HOME": str(base),
            "PATH": os.environ.get("PATH", ""),
        }

    def test_attempt_id_default_marker_filename_starts_with_attempt_prefix(self):
        # (a) with AGENT_DISPATCH_ATTEMPT_ID and no positional session-id,
        # `read` writes a marker whose filename begins with the attempt id —
        # assert on the filename itself, not a later gate verdict.
        base, agent_home, prd = self._fixture()
        env = self._base_env(base, agent_home)
        env["AGENT_DISPATCH_ATTEMPT_ID"] = "att-x"
        result = subprocess.run(
            [str(PREFLIGHT), "read", str(prd)],
            text=True, capture_output=True, env=env, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        markers = list((agent_home / ".core-grounding").glob("att-x__*"))
        self.assertEqual(len(markers), 1, list((agent_home / ".core-grounding").iterdir()))

    def test_empty_attempt_id_in_worker_hard_fails(self):
        # (b) AGENT_DISPATCH_ATTEMPT_ID explicitly set to the empty string,
        # inside a worker (AGENT_DISPATCH_CHILD=1) — must hard-fail, never
        # silently collapse onto the shared `codex` namespace.
        base, agent_home, prd = self._fixture()
        env = self._base_env(base, agent_home)
        env["AGENT_DISPATCH_ATTEMPT_ID"] = ""
        env["AGENT_DISPATCH_CHILD"] = "1"
        result = subprocess.run(
            [str(PREFLIGHT), "write", str(prd)],
            text=True, capture_output=True, env=env, timeout=20,
        )
        self.assertEqual(result.returncode, 65, result.stdout + result.stderr)
        self.assertIn("reason=guard-identity-unavailable", result.stderr)

    def test_unset_attempt_id_in_worker_hard_fails(self):
        # (b-2) the SEPARATE unset case (variable never exported at all),
        # not merely empty — both must hard-fail identically inside a worker.
        base, agent_home, prd = self._fixture()
        env = self._base_env(base, agent_home)
        env.pop("AGENT_DISPATCH_ATTEMPT_ID", None)
        self.assertNotIn("AGENT_DISPATCH_ATTEMPT_ID", env)
        env["AGENT_DISPATCH_CHILD"] = "1"
        result = subprocess.run(
            [str(PREFLIGHT), "write", str(prd)],
            text=True, capture_output=True, env=env, timeout=20,
        )
        self.assertEqual(result.returncode, 65, result.stdout + result.stderr)
        self.assertIn("reason=guard-identity-unavailable", result.stderr)

    def test_interactive_session_keeps_legacy_codex_default(self):
        # (c) neither AGENT_DISPATCH_ATTEMPT_ID nor any worker-session signal
        # set (interactive) — the legacy `codex` default still applies and
        # the command succeeds exactly as before this cycle.
        base, agent_home, prd = self._fixture()
        env = self._base_env(base, agent_home)
        for key in (
            "AGENT_DISPATCH_ATTEMPT_ID", "AGENT_SESSION_ROLE", "AGENT_DISPATCH_CHILD",
            "AGENT_DISPATCH_DEPTH", "OPENCODE_DISPATCH_SLUG", "FLEET_TITLE_REFRESH",
            "MEM_DISTILL",
        ):
            env.pop(key, None)
        result = subprocess.run(
            [str(PREFLIGHT), "read", str(prd)],
            text=True, capture_output=True, env=env, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        markers = list((agent_home / ".core-grounding").glob("codex__*"))
        self.assertEqual(len(markers), 1, list((agent_home / ".core-grounding").iterdir()))

    def test_explicit_positional_session_id_wins_over_attempt_id(self):
        # prompt/env equality: an explicit positional session id (as a human
        # CLI caller would pass) still takes precedence over the env default.
        base, agent_home, prd = self._fixture()
        env = self._base_env(base, agent_home)
        env["AGENT_DISPATCH_ATTEMPT_ID"] = "att-env-should-not-win"
        result = subprocess.run(
            [str(PREFLIGHT), "read", str(prd), "explicit-sid"],
            text=True, capture_output=True, env=env, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        markers = list((agent_home / ".core-grounding").glob("explicit-sid__*"))
        self.assertEqual(len(markers), 1, list((agent_home / ".core-grounding").iterdir()))


if __name__ == "__main__":
    unittest.main()
