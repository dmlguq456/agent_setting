#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "dispatch_attempt_ready", ROOT / "utilities" / "dispatch-attempt-ready.py"
)
READY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(READY)


class DispatchAttemptReadyTest(unittest.TestCase):
    def test_open_quiescent_attempt_is_terminal_unclosed_not_pending(self):
        fields = [
            "2026-07-24T00:00:00Z", "open", "/r", "/w", "owner", "",
        ]
        metadata = {
            "attempt_schema_version": "2",
            "dispatch_depth": "1",
            "transport": "headless",
            "execution_surface": "registered-headless",
            "registered_worker": "1",
            "fallback_hop": "same-harness-headless",
            "attempt_id": "att-ready-stale",
            "launch_outcome": "reaped-before-publish",
        }
        receipt = READY.classify([(fields, metadata)])
        self.assertEqual(receipt["state"], "terminal")
        self.assertEqual(receipt["children"][0]["readiness"], "terminal-unclosed")
        self.assertEqual(
            receipt["children"][0]["observed_liveness"], "reconcile-needed"
        )

    def test_exact_terminal_envelope_is_reported_without_registry_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "attempt.claude.jsonl"
            log.write_text(
                '{"type":"result","is_error":true,"api_error_status":429}\n',
                encoding="utf-8",
            )
            fields = [
                "2026-07-24T00:00:00Z", "open", "/r", "/w", "owner", "",
            ]
            metadata = {
                "attempt_schema_version": "2",
                "dispatch_depth": "1",
                "transport": "headless",
                "execution_surface": "registered-headless",
                "registered_worker": "1",
                "fallback_hop": "same-harness-headless",
                "attempt_id": "att-ready-envelope",
                "launch_outcome": "reaped-before-publish",
                "log_file": str(log),
            }
            receipt = READY.classify([(fields, metadata)])
        child = receipt["children"][0]
        self.assertEqual(receipt["state"], "terminal")
        self.assertEqual(child["observed_reason"], "terminal-observed")


if __name__ == "__main__":
    unittest.main()

