#!/usr/bin/env python3
import json
from pathlib import Path
import tempfile
import unittest

from codex_dispatch_terminal import inspect_terminal_log


class CodexDispatchTerminalTest(unittest.TestCase):
    def write_log(self, root, verdict="BLOCKED", blocker="blocked", sandbox=True,
                  completed=True):
        path = Path(root) / "attempt.codex.jsonl"
        rows = [{"type": "turn.started"}]
        if sandbox:
            rows.append({
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "exit_code": 1,
                    "aggregated_output": (
                        "bwrap: Can't bind mount /bindfile123 on "
                        "/newroot/work/repo/.codex: Unable to mount source on "
                        "destination: No such file or directory\n"
                    ),
                },
            })
        rows.append({
            "type": "item.completed",
            "item": {
                "type": "agent_message",
                "text": f"artifact: -\nverdict: {verdict}\nblocker: {blocker}",
            },
        })
        if completed:
            rows.append({"type": "turn.completed"})
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
        return path

    def test_blocked_bwrap_mount_is_typed_sandbox_init(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = inspect_terminal_log(self.write_log(tmp))
        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertEqual(result["failure_note"], "dead-sandbox-init")
        self.assertEqual(result["failure_class"], "sandbox-init")

    def test_generic_blocked_is_not_mislabeled_sandbox_init(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = inspect_terminal_log(self.write_log(tmp, sandbox=False))
        self.assertEqual(result["failure_note"], "dead-worker-blocked")

    def test_fail_and_pass_have_distinct_outcomes(self):
        with tempfile.TemporaryDirectory() as tmp:
            failed = inspect_terminal_log(self.write_log(tmp, verdict="FAIL", sandbox=False))
            passed = inspect_terminal_log(self.write_log(tmp, verdict="PASS", sandbox=False))
        self.assertEqual(failed["failure_note"], "dead-worker-fail")
        self.assertEqual(passed["failure_note"], "")

    def test_handoff_without_turn_completed_is_not_terminal(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = inspect_terminal_log(self.write_log(tmp, completed=False))
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
