#!/usr/bin/env python3
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

P = Path(__file__).with_name("dispatch_lifecycle.py")
SPEC = importlib.util.spec_from_file_location(
    "dispatch_lifecycle", P
)
L = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = L
SPEC.loader.exec_module(L)


class LifecycleTest(unittest.TestCase):
    def test_namespace_detection_supports_host_and_remounted_proc(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            status = base / "status"
            comm = base / "comm"
            status.write_text("Name:\tpython\nNSpid:\t400\n", encoding="utf-8")
            comm.write_text("systemd\n", encoding="utf-8")
            self.assertFalse(L.pid_namespace_scoped(status, comm))
            status.write_text("Name:\tpython\nNSpid:\t400\t1\n", encoding="utf-8")
            self.assertTrue(L.pid_namespace_scoped(status, comm))
            status.write_text("Name:\tpython\nNSpid:\t1\n", encoding="utf-8")
            comm.write_text("bwrap\n", encoding="utf-8")
            self.assertTrue(L.pid_namespace_scoped(status, comm))

    def test_selection_preserves_detached_compatibility_and_override(self):
        self.assertEqual(
            L.select_launch_lifecycle({}, namespace_scoped=False), L.DETACHED
        )
        self.assertEqual(
            L.select_launch_lifecycle({}, namespace_scoped=True), L.FOREGROUND_SCOPED
        )
        self.assertEqual(
            L.select_launch_lifecycle(
                {"AGENT_DISPATCH_ALLOW_NAMESPACED_SPAWN": "1"},
                namespace_scoped=True,
            ),
            L.DETACHED,
        )

    def test_foreground_wait_reports_success_and_child_signal(self):
        success = subprocess.Popen(["sh", "-c", "exit 0"], start_new_session=True)
        self.assertEqual(L.wait_foreground(success, 2), L.ForegroundResult(0, ""))
        signaled = subprocess.Popen(
            ["sh", "-c", "kill -TERM $$"], start_new_session=True
        )
        outcome = L.wait_foreground(signaled, 2)
        self.assertEqual(outcome.failure, f"signal-{signal.SIGTERM}")

    def test_foreground_wait_forwards_wrapper_signal(self):
        proc = mock.Mock(pid=4312)

        def raise_term(timeout=None):
            signal.raise_signal(signal.SIGTERM)
            return 0

        proc.wait.side_effect = raise_term
        with mock.patch.object(os, "killpg") as killpg:
            outcome = L.wait_foreground(proc, 2)
        killpg.assert_called_once_with(4312, signal.SIGTERM)
        self.assertEqual(outcome.failure, f"signal-{signal.SIGTERM}")

    def test_foreground_timeout_terminates_group(self):
        proc = mock.Mock(pid=4313)
        proc.wait.side_effect = [subprocess.TimeoutExpired("child", 1), -signal.SIGTERM]
        with mock.patch.object(os, "killpg") as killpg:
            outcome = L.wait_foreground(proc, 1)
        killpg.assert_called_once_with(4313, signal.SIGTERM)
        self.assertEqual(outcome.failure, "timeout")


if __name__ == "__main__":
    unittest.main()
