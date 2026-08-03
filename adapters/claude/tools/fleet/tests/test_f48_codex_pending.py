"""F-48 structured Codex request_user_input call/output pairing."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet.collectors import codex  # noqa: E402


def record(payload, timestamp="2026-08-03T00:00:00Z"):
    return {"timestamp": timestamp, "type": "response_item", "payload": payload}


class CodexPendingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "rollout.jsonl")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, *rows):
        with open(self.path, "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(row if isinstance(row, str) else json.dumps(row))
                handle.write("\n")

    def call(self, call_id="c1", name="request_user_input", timestamp="2026-08-03T00:00:00Z"):
        return record({"type": "function_call", "name": name, "call_id": call_id}, timestamp)

    def output(self, call_id="c1"):
        return record({"type": "function_call_output", "call_id": call_id})

    def test_open_and_closed_call(self):
        self.write(self.call())
        pending = codex._tail_pending_request_user_input(self.path)
        self.assertEqual(pending["call_id"], "c1")
        self.assertIsInstance(pending["waiting_since"], float)
        self.write(self.call(), self.output())
        self.assertIsNone(codex._tail_pending_request_user_input(self.path))

    def test_prose_and_other_function_are_not_evidence(self):
        prose = record({"type": "message", "content": "request_user_input should be used"})
        self.write(prose, self.call(name="exec_command"))
        self.assertIsNone(codex._tail_pending_request_user_input(self.path))

    def test_call_id_reuse_reopens_after_output(self):
        self.write(
            self.call("same", timestamp="2026-08-03T00:00:00Z"),
            self.output("same"),
            self.call("same", timestamp="2026-08-03T00:00:10Z"),
        )
        pending = codex._tail_pending_request_user_input(self.path)
        self.assertEqual(pending["call_id"], "same")
        self.assertGreater(pending["waiting_since"], 0)

    def test_latest_open_call_wins_and_malformed_is_skipped(self):
        self.write("{broken", self.call("old"), self.call("new"), "not json")
        self.assertEqual(codex._tail_pending_request_user_input(self.path)["call_id"], "new")

    def test_absent_file_is_silent(self):
        self.assertIsNone(codex._tail_pending_request_user_input(self.path + ".missing"))


if __name__ == "__main__":
    unittest.main()
