#!/usr/bin/env python3
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
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
        proc = subprocess.Popen(["sleep", "60"], start_new_session=True)
        timer = threading.Timer(0.05, lambda: os.kill(os.getpid(), signal.SIGTERM))
        timer.start()
        try:
            outcome = L.wait_foreground(proc, 2, poll_interval=0.01)
            self.assertEqual(outcome.failure, f"signal-{signal.SIGTERM}")
            self.assertTrue(outcome.group_empty)
            self.assertIsNotNone(proc.poll())
        finally:
            timer.cancel()
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()

    def test_foreground_timeout_terminates_group(self):
        proc = subprocess.Popen(["sleep", "60"], start_new_session=True)
        outcome = L.wait_foreground(proc, 0.05, poll_interval=0.01)
        self.assertEqual(outcome.failure, "timeout")
        self.assertTrue(outcome.group_empty)
        self.assertIsNotNone(proc.poll())

    def test_foreground_parent_identity_loss_terminates_child_group(self):
        parent = subprocess.Popen(["sleep", "60"])
        child = subprocess.Popen(["sleep", "60"], start_new_session=True)
        parent_start = L.process_start_ticks(parent.pid)
        timer = threading.Timer(0.05, parent.kill)
        timer.start()
        try:
            outcome = L.wait_foreground(
                child,
                3,
                parent_pid=parent.pid,
                parent_pid_start=parent_start,
                poll_interval=0.01,
            )
            self.assertEqual(outcome.failure, "parent-terminated")
            self.assertIsNotNone(child.poll())
        finally:
            timer.cancel()
            if parent.poll() is None:
                parent.kill()
            parent.wait()
            if child.poll() is None:
                child.kill()
            child.wait()

    def test_unverifiable_group_is_never_reported_empty(self):
        observation = type("Observation", (), {"state": "unverifiable"})()
        with mock.patch.object(L, "process_group_observation", return_value=observation):
            self.assertIsNone(L._group_empty(123))

    def test_missing_leader_has_no_numeric_group_signal_authority(self):
        proc = mock.Mock(pid=437)
        with mock.patch.object(
            L, "signal_exact_process_group", return_value="leader-gone"
        ) as exact, mock.patch.object(L.os, "killpg") as killpg:
            result = L._terminate_group(proc, signal.SIGTERM, "42")
        self.assertEqual(result, "leader-gone")
        exact.assert_called_once_with(437, "42", signal.SIGTERM)
        killpg.assert_not_called()

    def test_identity_unavailable_still_reaps_direct_child(self):
        proc = subprocess.Popen(["sleep", "60"], start_new_session=True)
        with mock.patch.object(L, "process_start_ticks", return_value=None):
            outcome = L.wait_foreground(proc, 2)
        self.assertEqual(outcome.failure, "process-identity-unavailable")
        self.assertFalse(outcome.group_empty)
        self.assertIsNotNone(proc.poll())

    def test_exceptional_observation_path_does_not_leave_direct_child(self):
        proc = subprocess.Popen(["sleep", "60"], start_new_session=True)
        with mock.patch.object(L, "_group_empty", side_effect=RuntimeError("fixture")):
            with self.assertRaisesRegex(RuntimeError, "fixture"):
                L.wait_foreground(proc, 2, poll_interval=0.01)
        self.assertIsNotNone(proc.poll())

    @unittest.skipUnless(hasattr(signal, "SIGHUP"), "SIGHUP unavailable")
    def test_foreground_installs_and_restores_sighup_forwarding(self):
        proc = subprocess.Popen(["sh", "-c", "exit 0"], start_new_session=True)
        with mock.patch.object(L.signal, "getsignal", return_value=signal.SIG_DFL), \
             mock.patch.object(L.signal, "signal") as install:
            outcome = L.wait_foreground(proc, 2)
        self.assertEqual(outcome.exit_code, 0)
        sighup_calls = [call for call in install.call_args_list if call.args[0] == signal.SIGHUP]
        self.assertEqual(len(sighup_calls), 2)


if __name__ == "__main__":
    unittest.main()
