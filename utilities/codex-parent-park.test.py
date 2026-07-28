#!/usr/bin/env python3
"""Regression tests for the retired Codex all-tool parent park."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "adapters" / "codex" / "hooks" / "pretooluse-write-guard.py"
HOOKS = ROOT / "adapters" / "codex" / "hooks" / "hooks.json"


class ParentParkRetirementTest(unittest.TestCase):
    def invoke(self, payload: dict[str, object], *, env: dict[str, str] | None = None):
        return subprocess.run(
            ["python3", str(GUARD)],
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, **(env or {})},
            check=False,
        )

    def test_hook_manifest_has_no_wildcard_parent_park(self):
        config = json.loads(HOOKS.read_text(encoding="utf-8"))
        entries = config["hooks"]["PreToolUse"]
        self.assertEqual(len(entries), 1)
        self.assertNotEqual(entries[0].get("matcher"), "*")
        rendered = json.dumps(entries)
        self.assertNotIn("AGENT_PARENT_PARK_ONLY", rendered)

    def test_open_legacy_child_does_not_block_unrelated_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            jobs = Path(tmp) / "jobs.log"
            jobs.write_text(
                "2026-07-27T00:00:00Z\topen\trepo\t/tmp/wt\tchild\t"
                "attempt_id=att-old,parent_sid=thread-a,launch_claimed=1,"
                "registered_worker=1,parent_completion_delivery=codex-stop-hook\n",
                encoding="utf-8",
            )
            result = self.invoke(
                {"tool_name": "wait", "session_id": "thread-a", "tool_input": {}},
                env={
                    "AGENT_DISPATCH_JOBS": str(jobs),
                    "AGENT_DISPATCH_COMPLETION_MODE": "poll",
                },
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("parent-parked", result.stderr)

    def test_supervisor_metadata_does_not_turn_guard_into_scheduler(self):
        result = self.invoke(
            {"tool_name": "wait", "session_id": "thread-b", "tool_input": {}},
            env={"AGENT_DISPATCH_COMPLETION_MODE": "supervised"},
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_guard_source_has_only_material_write_responsibility(self):
        source = GUARD.read_text(encoding="utf-8")
        for retired in (
            "parent_park_rows",
            "native_stop_delivered",
            "exact_park_control",
            "AGENT_PARENT_PARK_ONLY",
            "runtime-supervised-parent",
        ):
            self.assertNotIn(retired, source)
        self.assertIn('"material-route", "check"', source)
        self.assertIn('[str(PREFLIGHT), "write", file, session_id]', source)


if __name__ == "__main__":
    unittest.main()
