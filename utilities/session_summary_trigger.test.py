#!/usr/bin/env python3
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path[:0] = [str(ROOT / "utilities"), str(ROOT / "tools")]

import session_summary_trigger as T  # noqa: E402


class SessionSummaryTriggerTest(unittest.TestCase):
    def test_codex_resolves_only_exact_rollout_suffix(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            sessions = home / "sessions" / "2026" / "08" / "04"
            sessions.mkdir(parents=True)
            exact = sessions / "rollout-2026-08-04T00-00-00-exact-sid.jsonl"
            foreign = sessions / "rollout-2026-08-04T00-00-01-not-exact-sid-extra.jsonl"
            exact.write_text("{}\n")
            foreign.write_text("{}\n")
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(home)}):
                self.assertEqual(T._codex_transcript("exact-sid"), exact)

    def test_trigger_maps_phase_to_ticket_and_priority(self):
        with tempfile.TemporaryDirectory() as td:
            transcript = Path(td) / "session.jsonl"
            transcript.write_text("{}\n")
            with mock.patch("fleet.refresh_title.maybe_spawn", return_value=True) as spawn:
                self.assertTrue(T.trigger(
                    "claude", "sid", "final", str(transcript)))
            kwargs = spawn.call_args.kwargs
            self.assertEqual(kwargs["quota_class"], "final")
            self.assertEqual(kwargs["debounce"], 0)
            self.assertTrue(kwargs["priority"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
