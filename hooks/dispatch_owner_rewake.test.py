#!/usr/bin/env python3
"""Tests for the one-shot Claude interactive owner completion bridge."""

from __future__ import annotations

import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).with_name("dispatch-owner-rewake.py")
SPEC = importlib.util.spec_from_file_location("dispatch_owner_rewake", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
rewake = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = rewake
SPEC.loader.exec_module(rewake)


class DispatchOwnerRewakeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.jobs = self.root / "jobs.log"
        self.jobs.write_text("fixture\n", encoding="utf-8")

    def payload(self, **replacements):
        output = "\n".join(
            (
                "status=eligible",
                "check=ok",
                "status=start",
                "dispatch_depth=1",
                "worker_type=owner",
                "parent_completion_delivery=claude-parent-runtime",
                "parent_session_id=session-1",
                f"job_registry={self.jobs}",
                "attempt_id=att-owner-1",
                "registered=1",
                "started=1",
            )
        )
        payload = {
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "session_id": "session-1",
            "tool_input": {
                "command": "python3 utilities/dispatch-owner.py --start --slug owner"
            },
            "tool_response": {"stdout": output, "stderr": ""},
        }
        payload.update(replacements)
        return payload

    def test_exact_successful_owner_start_is_armed(self) -> None:
        launch = rewake.parse_launch(self.payload())
        self.assertIsNotNone(launch)
        assert launch is not None
        self.assertEqual(launch.attempt_id, "att-owner-1")
        self.assertEqual(launch.jobs, self.jobs)
        self.assertEqual(launch.session_id, "session-1")

    def test_foreign_or_incomplete_output_is_ignored(self) -> None:
        foreign = self.payload(session_id="session-2")
        self.assertIsNone(rewake.parse_launch(foreign))
        ordinary = self.payload(tool_input={"command": "git status"})
        self.assertIsNone(rewake.parse_launch(ordinary))
        incomplete = self.payload()
        incomplete["tool_response"]["stdout"] = incomplete["tool_response"]["stdout"].replace(
            "started=1", "started=0"
        )
        self.assertIsNone(rewake.parse_launch(incomplete))

    def test_symlink_registry_is_rejected(self) -> None:
        link = self.root / "jobs-link.log"
        link.symlink_to(self.jobs)
        payload = self.payload()
        payload["tool_response"]["stdout"] = payload["tool_response"]["stdout"].replace(
            str(self.jobs), str(link)
        )
        self.assertIsNone(rewake.parse_launch(payload))

    def test_wait_is_one_process_until_exact_attempt_is_ready(self) -> None:
        launch = rewake.parse_launch(self.payload())
        assert launch is not None
        pending = subprocess.CompletedProcess([], 2, stdout="pending")
        ready = subprocess.CompletedProcess([], 0, stdout="ready")
        with mock.patch.object(
            rewake.subprocess, "run", side_effect=[pending, ready]
        ) as run, mock.patch.object(rewake.time, "sleep") as sleep, mock.patch.object(
            rewake.time, "monotonic", side_effect=[0.0, 1.0]
        ), mock.patch.dict(
                os.environ,
                {
                    "AGENT_CLAUDE_REWAKE_INTERVAL_SECONDS": "3",
                    "AGENT_CLAUDE_REWAKE_MAX_SECONDS": "60",
                },
            ):
            state, reason = rewake.wait_for_attempt(launch, self.root / "ready.py")
        self.assertEqual((state, reason), ("ready", "terminal-quiescent"))
        self.assertEqual(run.call_count, 2)
        sleep.assert_called_once_with(3)
        command = run.call_args_list[0].args[0]
        self.assertEqual(command[-2:], ["--attempt-id", "att-owner-1"])
        self.assertIn(str(self.jobs), command)

    def test_receipt_forbids_visible_monitor_rearming(self) -> None:
        launch = rewake.parse_launch(self.payload())
        assert launch is not None
        message = rewake.receipt(launch, "ready", "terminal-quiescent", self.root)
        self.assertIn("attempt_id=att-owner-1", message)
        self.assertIn("Do not start or re-arm Background Bash", message)
        self.assertIn("harvest --attempt-id att-owner-1 --mark-done", message)

    def test_unrelated_hook_payload_is_a_silent_noop(self) -> None:
        payload = self.payload(tool_name="Read")
        with mock.patch.object(rewake.sys, "stdin", io.StringIO(__import__("json").dumps(payload))):
            self.assertEqual(rewake.main(), 0)


if __name__ == "__main__":
    unittest.main()
