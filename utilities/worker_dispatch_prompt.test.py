#!/usr/bin/env python3

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTERS = {
    "codex": (
        ROOT / "adapters/codex/bin/dispatch-headless.py",
        ["--model", "gpt-test", "--reasoning", "low"],
        "codex.prompt.txt",
    ),
    "claude": (
        ROOT / "adapters/claude/bin/dispatch-headless.py",
        ["--model", "claude-test", "--effort", "low"],
        "claude.prompt.txt",
    ),
    "opencode": (
        ROOT / "adapters/opencode/bin/dispatch-headless.py",
        ["--model", "provider/test", "--variant", "low"],
        "opencode.prompt.txt",
    ),
}


class WorkerDispatchPromptTest(unittest.TestCase):
    def test_custom_assignment_is_wrapped_for_every_adapter(self):
        for harness, (wrapper, model, suffix) in ADAPTERS.items():
            with self.subTest(harness=harness), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo = root / "repo"
                repo.mkdir()
                subprocess.run(["git", "init", "-q", str(repo)], check=True)
                subprocess.run(
                    ["git", "-C", str(repo), "config", "user.email", "fixture@example.com"],
                    check=True,
                )
                subprocess.run(
                    ["git", "-C", str(repo), "config", "user.name", "Fixture"],
                    check=True,
                )
                (repo / "x").write_text("x", encoding="utf-8")
                subprocess.run(["git", "-C", str(repo), "add", "x"], check=True)
                subprocess.run(["git", "-C", str(repo), "commit", "-qm", "init"], check=True)
                artifact_root = root / ".agent_reports"
                artifact_root.mkdir()
                logs = root / "logs"
                slug = f"{harness}-typed"
                command = [
                    sys.executable,
                    str(wrapper),
                    "--register",
                    "--worktree",
                    str(repo),
                    "--slug",
                    slug,
                    "--capability",
                    "autopilot-code",
                    "--mode",
                    "dev/backend",
                    "--intensity",
                    "standard",
                    "--depth",
                    "2",
                    "--parent",
                    "owner",
                    "--worker-role",
                    "code-test",
                    "--prompt-text",
                    "CUSTOM ASSIGNMENT",
                    "--jobs",
                    str(root / "jobs.log"),
                    "--log-dir",
                    str(logs),
                    *model,
                ]
                env = {
                    **os.environ,
                    "AGENT_HOME": str(ROOT),
                    "AGENT_ARTIFACT_ROOT": str(artifact_root),
                    "OPENCODE_CONFIG_CONTENT": "{}",
                }
                result = subprocess.run(command, text=True, capture_output=True, env=env)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                prompt = (logs / f"{slug}.{suffix}").read_text(encoding="utf-8")
                self.assertEqual(prompt.count("# Portable Worker Kernel"), 1)
                self.assertEqual(prompt.count("# Worker Type:"), 1)
                self.assertIn("# Worker Type: Stage", prompt)
                self.assertIn("CUSTOM ASSIGNMENT", prompt)
                self.assertIn("artifact: <canonical path | ->", prompt)
                self.assertIn("verdict: PASS | FAIL | BLOCKED", prompt)
                self.assertIn("blocker: none | <one line>", prompt)
                self.assertNotIn("Read $AGENT_HOME/adapters/codex/AGENTS.md first", prompt)
                self.assertNotIn("Return a concise report with changed files", prompt)


if __name__ == "__main__":
    unittest.main()
