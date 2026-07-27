#!/usr/bin/env python3
"""Regression tests for model-free interactive Codex Stop parking."""

from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sessionend_lifecycle",
    ROOT / "adapters" / "codex" / "hooks" / "sessionend-lifecycle.py",
)
HOOK = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = HOOK
SPEC.loader.exec_module(HOOK)
JOIN = sys.modules["dispatch_completion_join"]

SESSION = "thread-stop-fixture"
ATTEMPT = "att-stop-child"


def row(status: str = "open") -> str:
    metadata = (
        "attempt_schema_version=2,dispatch_depth=1,transport=headless,"
        "execution_surface=registered-headless,registered_worker=1,"
        "launch_claimed=1,"
        "parent_completion_delivery=codex-stop-hook,"
        f"attempt_id={ATTEMPT},parent_sid={SESSION}"
    )
    if status == "done":
        metadata += ",launch_outcome=never-launched"
    return (
        f"2026-07-27T00:00:00Z\t{status}\t/repo\t/wt\tchild\t{metadata}\n"
    )


class CodexStopParentParkTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.jobs = Path(self.temp.name) / "jobs.log"
        self.env = mock.patch.dict(
            os.environ,
            {"AGENT_DISPATCH_JOBS": str(self.jobs), "AGENT_HOME": str(ROOT)},
            clear=False,
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def output(self, callback) -> str:
        stream = io.StringIO()
        with redirect_stdout(stream):
            callback()
        return stream.getvalue()

    def test_stop_hook_owns_bounded_long_wait_only(self) -> None:
        config = json.loads(
            (ROOT / "adapters" / "codex" / "hooks" / "hooks.json").read_text(
                encoding="utf-8"
            )
        )["hooks"]
        self.assertEqual(config["Stop"][0]["hooks"][0]["timeout"], 7200)
        self.assertEqual(HOOK.STOP_JOIN_TIMEOUT_MAX, 7140.0)
        self.assertEqual(
            config["Stop"][0]["hooks"][0]["timeout"]
            - HOOK.STOP_JOIN_TIMEOUT_MAX,
            60.0,
        )
        self.assertEqual(config["SessionStart"][0]["hooks"][0]["timeout"], 30)
        self.assertEqual(len(config["PreToolUse"]), 2)
        self.assertEqual(
            config["PreToolUse"][0]["matcher"],
            r"Write|Edit|MultiEdit|apply_patch|functions\.apply_patch|Bash|Shell|functions\.exec_command",
        )
        self.assertEqual(config["PreToolUse"][1]["matcher"], "*")
        self.assertIn(
            "AGENT_PARENT_PARK_ONLY=1",
            config["PreToolUse"][1]["hooks"][0]["command"],
        )

    def test_no_children_schedules_memory_lifecycle_silently(self) -> None:
        with mock.patch.object(HOOK, "spawn_preflight") as spawn:
            output = self.output(lambda: HOOK.handle_stop("/repo", SESSION))
        self.assertEqual(output, "")
        spawn.assert_called_once_with("session-end", "/repo", SESSION)

    def test_registered_only_native_row_does_not_enter_stop_wait(self) -> None:
        self.jobs.write_text(
            row().replace("launch_claimed=1", "launch_claimed=0"),
            encoding="utf-8",
        )
        with mock.patch.object(HOOK, "spawn_preflight") as spawn:
            output = self.output(lambda: HOOK.handle_stop("/repo", SESSION))
        self.assertEqual(output, "")
        spawn.assert_called_once_with("session-end", "/repo", SESSION)

    def test_harvested_open_row_does_not_reenter_stop_wait(self) -> None:
        self.jobs.write_text(
            row().rstrip("\n") + ",parent_completion_harvested=1\n",
            encoding="utf-8",
        )
        state = HOOK.parent_session_state_path(self.jobs, SESSION)
        HOOK.write_parent_session_state(state, SESSION, {ATTEMPT})
        self.assertTrue(
            JOIN.consume_parent_session_attempt(state, SESSION, ATTEMPT)
        )
        with mock.patch.object(HOOK, "spawn_preflight") as spawn:
            output = self.output(lambda: HOOK.handle_stop("/repo", SESSION))
        self.assertEqual(output, "")
        self.assertFalse(state.exists())
        spawn.assert_called_once_with("session-end", "/repo", SESSION)

    def test_worker_stop_owns_no_parent_lifecycle(self) -> None:
        with mock.patch.object(HOOK, "load_payload", return_value={}), \
             mock.patch.object(HOOK, "is_worker_session", return_value=True), \
             mock.patch.object(HOOK, "spawn_preflight") as spawn:
            self.assertEqual(HOOK.main(), 0)
        spawn.assert_not_called()

    def test_runtime_stop_continuation_never_blocks_or_joins_again(self) -> None:
        self.jobs.write_text(row(), encoding="utf-8")
        payload = {
            "hook_event_name": "Stop",
            "cwd": "/repo",
            "session_id": SESSION,
            "stop_hook_active": True,
        }
        with mock.patch.object(HOOK, "load_payload", return_value=payload), \
             mock.patch.object(HOOK, "is_worker_session", return_value=False), \
             mock.patch.object(HOOK, "handle_stop") as handle, \
             mock.patch.object(HOOK, "spawn_preflight") as spawn:
            output = self.output(HOOK.main)
        self.assertEqual(output, "")
        handle.assert_not_called()
        spawn.assert_not_called()

    def test_runtime_stop_continuation_runs_lifecycle_after_harvest(self) -> None:
        payload = {
            "hook_event_name": "Stop",
            "cwd": "/repo",
            "session_id": SESSION,
            "stop_hook_active": True,
        }
        with mock.patch.object(HOOK, "load_payload", return_value=payload), \
             mock.patch.object(HOOK, "is_worker_session", return_value=False), \
             mock.patch.object(HOOK, "handle_stop") as handle, \
             mock.patch.object(HOOK, "spawn_preflight") as spawn:
            output = self.output(HOOK.main)
        self.assertEqual(output, "")
        handle.assert_not_called()
        spawn.assert_called_once_with("session-end", "/repo", SESSION)

    def test_runtime_stop_continuation_leaves_invalid_state_for_recovery(self) -> None:
        state = HOOK.parent_session_state_path(self.jobs, SESSION)
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text("{}", encoding="utf-8")
        payload = {
            "hook_event_name": "Stop",
            "cwd": "/repo",
            "session_id": SESSION,
            "stop_hook_active": True,
        }
        with mock.patch.object(HOOK, "load_payload", return_value=payload), \
             mock.patch.object(HOOK, "is_worker_session", return_value=False), \
             mock.patch.object(HOOK, "handle_stop") as handle, \
             mock.patch.object(HOOK, "spawn_preflight") as spawn:
            output = self.output(HOOK.main)
        self.assertEqual(output, "")
        self.assertTrue(state.exists())
        handle.assert_not_called()
        spawn.assert_not_called()

    def test_ready_batch_publishes_state_and_one_continuation(self) -> None:
        self.jobs.write_text(row(), encoding="utf-8")
        receipt = {
            "schema_version": 1,
            "state": "ready",
            "parent_session_id": SESSION,
            "children": [
                {
                    "attempt_id": ATTEMPT,
                    "slug": "child",
                    "status": "open",
                    "readiness": "ready",
                    "reason": "terminal-observed",
                }
            ],
        }
        with mock.patch.object(
            HOOK, "join_session_batch", return_value=receipt
        ) as join, mock.patch.object(HOOK, "spawn_preflight") as spawn:
            output = self.output(lambda: HOOK.handle_stop("/repo", SESSION))
        value = json.loads(output)
        self.assertEqual(value["decision"], "block")
        self.assertIn("receipt state=ready", value["reason"])
        join.assert_called_once()
        spawn.assert_not_called()
        state = HOOK.parent_session_state_path(self.jobs, SESSION)
        self.assertEqual(
            JOIN.read_parent_session_state(state, SESSION), {ATTEMPT}
        )

    def test_child_closed_before_stop_is_retained_by_pending_session_state(self) -> None:
        self.jobs.write_text(row("done"), encoding="utf-8")
        state = HOOK.parent_session_state_path(self.jobs, SESSION)
        HOOK.write_parent_session_state(
            state,
            SESSION,
            set(),
            attempt_ids={ATTEMPT},
        )
        receipt = {
            "schema_version": 1,
            "state": "ready",
            "parent_session_id": SESSION,
            "children": [
                {
                    "attempt_id": ATTEMPT,
                    "slug": "child",
                    "status": "done",
                    "readiness": "ready",
                    "reason": "registry-closed",
                }
            ],
        }
        with mock.patch.object(HOOK, "join_session_batch", return_value=receipt):
            output = self.output(lambda: HOOK.handle_stop("/repo", SESSION))
        value = json.loads(output)
        self.assertEqual(value["decision"], "block")
        self.assertIn(f"{ATTEMPT}:all", value["reason"])
        self.assertEqual(JOIN.read_parent_session_state(state, SESSION), {ATTEMPT})

    def test_timeout_requests_immediate_end_turn_without_phase_delivery(self) -> None:
        self.jobs.write_text(row(), encoding="utf-8")
        receipt = {
            "schema_version": 1,
            "state": "timeout",
            "parent_session_id": SESSION,
            "children": [],
        }
        with mock.patch.object(
            HOOK, "join_session_batch", return_value=receipt
        ), mock.patch.object(HOOK, "spawn_preflight") as spawn:
            output = self.output(lambda: HOOK.handle_stop("/repo", SESSION))
        value = json.loads(output)
        self.assertEqual(value["decision"], "block")
        self.assertIn("bounded two-hour native wait", value["reason"])
        self.assertIn("operator re-entry is required", value["reason"])
        self.assertIn("Automatic completion delivery is no longer active", value["reason"])
        self.assertIsNone(
            JOIN.read_parent_session_state(
                HOOK.parent_session_state_path(self.jobs, SESSION), SESSION
            )
        )
        spawn.assert_not_called()

    def test_repeated_stop_does_not_join_delivered_open_attempt_again(self) -> None:
        self.jobs.write_text(row(), encoding="utf-8")
        state = HOOK.parent_session_state_path(self.jobs, SESSION)
        HOOK.write_parent_session_state(state, SESSION, {ATTEMPT})
        with mock.patch.object(
            HOOK, "join_session_batch"
        ) as join, mock.patch.object(HOOK, "spawn_preflight") as spawn:
            output = self.output(lambda: HOOK.handle_stop("/repo", SESSION))
        value = json.loads(output)
        self.assertEqual(value["decision"], "block")
        self.assertIn("already delivered", value["reason"])
        join.assert_not_called()
        spawn.assert_not_called()


if __name__ == "__main__":
    unittest.main()
