#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "claude_dispatch_headless",
    ROOT / "adapters" / "claude" / "bin" / "dispatch-headless.py",
)
WRAPPER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(WRAPPER)


def selection(**values):
    return SimpleNamespace(
        inherit_model_settings=values.get("inherit", False),
        model_role=values.get("role"),
        model=values.get("model"),
        effort=values.get("effort"),
    )


class ClaudeDispatchModelEligibilityTest(unittest.TestCase):
    def test_deep_role_resolves_to_opus_and_not_main_only(self):
        result = WRAPPER.resolve_model_settings(selection(role="deep orchestrator"))
        self.assertEqual(result["model"], "opus")
        self.assertEqual(result["effort"], "xhigh")

    def test_explicit_and_role_override_fable_are_rejected(self):
        with self.assertRaises(WRAPPER.ModelSelectionError) as explicit:
            WRAPPER.resolve_model_settings(selection(model="claude-fable-5", effort="xhigh"))
        self.assertEqual(explicit.exception.reason, "headless-main-session-only-model")
        with mock.patch.dict(os.environ, {"CLAUDE_MODEL_DEEP": "fable"}):
            with self.assertRaises(WRAPPER.ModelSelectionError) as mapped:
                WRAPPER.resolve_model_settings(selection(role="deep maker"))
        self.assertEqual(mapped.exception.reason, "headless-main-session-only-model")

    def test_inherited_headless_model_is_rejected_before_launch(self):
        with self.assertRaises(WRAPPER.ModelSelectionError) as inherited:
            WRAPPER.resolve_model_settings(selection(inherit=True))
        self.assertEqual(
            inherited.exception.reason,
            "headless-model-inheritance-ineligible",
        )

    def test_missing_main_only_policy_fails_closed(self):
        with mock.patch.object(WRAPPER, "_model_policy", return_value={}):
            with self.assertRaises(WRAPPER.ModelSelectionError) as unavailable:
                WRAPPER.resolve_model_settings(
                    selection(model="sonnet", effort="high")
                )
        self.assertEqual(
            unavailable.exception.reason,
            "dispatch-model-policy-unavailable",
        )

    def test_explicit_eligible_model_remains_explicit(self):
        result = WRAPPER.resolve_model_settings(
            selection(model="sonnet", effort="high")
        )
        self.assertEqual(
            result,
            {"source": "explicit", "role": "-", "model": "sonnet", "effort": "high"},
        )

    def test_cli_rejects_fable_before_registry_prompt_log_or_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worktree = root / "repo"
            worktree.mkdir()
            subprocess.run(
                ["git", "init", "-q", str(worktree)], check=True
            )
            jobs = root / "jobs.log"
            logs = root / "logs"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "adapters" / "claude" / "bin" / "dispatch-headless.py"),
                    "--register",
                    "--worktree", str(worktree),
                    "--jobs", str(jobs),
                    "--log-dir", str(logs),
                    "--slug", "main-only-rejected",
                    "--capability", "autopilot-code",
                    "--mode", "dev/backend",
                    "--qa", "standard",
                    "--model", "claude-fable-5",
                    "--effort", "xhigh",
                    "--prompt-text", "must not launch",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 64)
            self.assertIn("reason=headless-main-session-only-model", result.stdout)
            self.assertIn("child_spawned=0", result.stdout)
            self.assertFalse(jobs.exists())
            self.assertFalse(logs.exists())


if __name__ == "__main__":
    unittest.main()
