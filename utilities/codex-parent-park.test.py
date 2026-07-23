#!/usr/bin/env python3
"""Regression tests for Codex registered-child parent parking."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "adapters" / "codex" / "hooks" / "pretooluse-write-guard.py"
SESSION = "019f89fa-fixture-parent"
ATTEMPT = "att-fixture-child"


class ParentParkGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.jobs = self.base / "jobs.log"
        self.write_row("open", ATTEMPT, parent_sid=SESSION)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_row(
        self,
        state: str,
        attempt: str,
        *,
        parent_sid: str = "",
        parent_attempt_id: str = "",
        append: bool = False,
    ) -> None:
        metadata = [
            "attempt_schema_version=2",
            "dispatch_depth=1",
            "transport=headless",
            "execution_surface=registered-headless",
            "registered_worker=1",
            "attempt_id=" + attempt,
        ]
        if parent_sid:
            metadata.append("parent_sid=" + parent_sid)
        if parent_attempt_id:
            metadata.append("parent_attempt_id=" + parent_attempt_id)
        row = "\t".join(
            ["2026-07-23T00:00:00Z", state, "/repo", "/repo-wt/child", "child", ",".join(metadata)]
        ) + "\n"
        if append:
            with self.jobs.open("a", encoding="utf-8") as handle:
                handle.write(row)
        else:
            self.jobs.write_text(row, encoding="utf-8")

    def invoke(
        self,
        name: str,
        command: str | None = None,
        *,
        session: str = SESSION,
        extra_env: dict[str, str] | None = None,
    ) -> dict[str, str] | None:
        payload: dict[str, object] = {
            "tool_name": name,
            "tool_input": {},
            "session_id": session,
            "cwd": str(ROOT),
        }
        if command is not None:
            payload["tool_input"] = {"command": command}
        env = {**os.environ, "AGENT_DISPATCH_JOBS": str(self.jobs), "AGENT_HOME": str(ROOT)}
        env.pop("AGENT_DISPATCH_ATTEMPT_ID", None)
        env.pop("AGENT_PARENT_PARK_BYPASS", None)
        if extra_env:
            env.update(extra_env)
        result = subprocess.run(
            ["python3", str(GUARD)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout else None

    def assert_parked(self, name: str, command: str | None = None, **kwargs: object) -> None:
        output = self.invoke(name, command, **kwargs)
        self.assertIsNotNone(output)
        self.assertEqual(output["decision"], "block")
        self.assertIn("parent-parked", output["reason"])
        self.assertIn(ATTEMPT, output["reason"])

    def test_actual_adjacent_session_activity_is_blocked(self) -> None:
        # Reduced forms of every waste class observed in the stopped adjacent
        # Codex parent: raw transcript reads, extraction, source search,
        # artifact census, git inspection, and redundant liveness calls.
        offender_commands = (
            "tail -n 120 /tmp/child.codex.jsonl",
            "python3 -c 'import json' /tmp/child.codex.jsonl",
            "rg -n parent-attempt-not-live adapters utilities",
            "find .agent_reports -maxdepth 4 -type f",
            "git status --short --branch",
            "git diff --stat",
            "adapters/codex/bin/preflight.sh liveness",
            "sed -n '1,200p' /tmp/child.codex.jsonl",
        )
        for command in offender_commands:
            with self.subTest(command=command):
                self.assert_parked("Bash", command)
        self.assert_parked("Read")
        self.assert_parked("update_plan")

    def test_only_exact_long_wait_and_typed_harvest_are_allowed(self) -> None:
        self.assertIsNone(
            self.invoke("Bash", f"utilities/dispatch-wait.sh --attempt-id {ATTEMPT} --max 600")
        )
        self.assertIsNone(
            self.invoke(
                "Bash",
                f"adapters/codex/bin/preflight.sh harvest --attempt-id {ATTEMPT} --status open",
            )
        )
        self.assertIsNone(self.invoke("functions.write_stdin"))
        self.assertIsNone(self.invoke("wait"))
        self.assert_parked("Bash", f"utilities/dispatch-wait.sh --attempt-id {ATTEMPT} --max 40")
        self.assert_parked("Bash", "utilities/dispatch-wait.sh --attempt-id att-other --max 600")
        self.assert_parked(
            "Bash",
            f"utilities/dispatch-wait.sh --attempt-id {ATTEMPT} --max 600; git status",
        )
        self.assert_parked(
            "Bash",
            f"adapters/codex/bin/preflight.sh harvest --attempt-id {ATTEMPT} --status done",
        )

    def test_foreign_and_terminal_rows_do_not_park(self) -> None:
        self.assertIsNone(self.invoke("Bash", "git status --short", session="different-session"))
        self.write_row("done", ATTEMPT, parent_sid=SESSION, append=True)
        self.assertIsNone(self.invoke("Bash", "git status --short"))

    def test_depth_one_owner_is_bound_by_exact_parent_attempt(self) -> None:
        owner_attempt = "att-owner-exact"
        self.write_row("open", ATTEMPT, parent_attempt_id=owner_attempt)
        self.assert_parked(
            "Bash",
            "tail -n 50 /tmp/child.codex.jsonl",
            session="worker-session",
            extra_env={"AGENT_DISPATCH_ATTEMPT_ID": owner_attempt},
        )
        self.assertIsNone(
            self.invoke(
                "Bash",
                f"utilities/dispatch-wait.sh --attempt-id {ATTEMPT} --max 300",
                session="worker-session",
                extra_env={"AGENT_DISPATCH_ATTEMPT_ID": owner_attempt},
            )
        )


if __name__ == "__main__":
    unittest.main()
