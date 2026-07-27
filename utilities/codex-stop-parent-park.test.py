#!/usr/bin/env python3
"""Regression tests for the silent no-op Codex Stop bridge."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STOP_PATH = ROOT / "adapters" / "codex" / "hooks" / "stop-lifecycle.py"
SESSIONEND_PATH = ROOT / "adapters" / "codex" / "hooks" / "sessionend-lifecycle.py"
HOOKS_PATH = ROOT / "adapters" / "codex" / "hooks" / "hooks.json"


def load_stop():
    spec = importlib.util.spec_from_file_location("codex_stop_lifecycle", STOP_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StopLifecycleTest(unittest.TestCase):
    def test_manifest_uses_short_dedicated_stop_bridge(self):
        config = json.loads(HOOKS_PATH.read_text(encoding="utf-8"))
        definition = config["hooks"]["Stop"][0]["hooks"][0]
        self.assertEqual(definition["timeout"], 30)
        self.assertIn("stop-lifecycle.py", definition["command"])
        self.assertNotIn("sessionend-lifecycle.py", definition["command"])

    def test_stop_is_a_silent_noop(self):
        module = load_stop()
        self.assertEqual(module.main(), 0)
        source = STOP_PATH.read_text(encoding="utf-8")
        for retired in (
            "subprocess",
            "session-end",
            "join_session_batch",
            "decision",
            "parent_session_state",
        ):
            self.assertNotIn(retired, source)

    def test_stop_source_has_no_payload_or_environment_branch(self):
        source = STOP_PATH.read_text(encoding="utf-8")
        self.assertNotIn("sys.stdin", source)
        self.assertNotIn("os.environ", source)

    def test_sessionend_has_no_stop_branch(self):
        source = SESSIONEND_PATH.read_text(encoding="utf-8")
        self.assertIn('run_preflight("session-end"', source)
        self.assertNotIn("join_session_batch", source)
        self.assertNotIn('event == "stop"', source)


if __name__ == "__main__":
    unittest.main()
