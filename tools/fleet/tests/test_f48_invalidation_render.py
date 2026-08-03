"""F-48 blocked precedence, process safety, render badges and public JSON."""

import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet import fleet as fleetmod  # noqa: E402
from fleet import model, render  # noqa: E402
from fleet.model import Session  # noqa: E402


WAIT = {"kind": "decision", "source": "codex-rollout", "waiting_since": 100.0}


class InvalidationRenderTest(unittest.TestCase):
    def setUp(self):
        model.reset_state_tracker()

    def evidence(self, **overrides):
        value = {
            "harness": "codex", "pid": 10, "pid_alive": True,
            "proc_start": "100", "proc_start_match": True, "orphan": False,
            "status": "busy", "mtime": 199.0, "transcript": True,
            "interaction_wait": dict(WAIT),
        }
        value.update(overrides)
        return value

    def test_blocked_precedes_activity_without_dwell(self):
        key = ("s", "codex", 10, "100")
        state, evidence = model.classify_session(self.evidence(), 200.0, key=key)
        self.assertEqual(state, "blocked")
        self.assertEqual(evidence["tier"], 2)
        self.assertEqual(evidence["source"], "interaction:codex-rollout")
        self.assertIsNone(evidence["hysteresis"])
        state, evidence = model.classify_session(self.evidence(status=None), 201.0, key=key)
        self.assertEqual(state, "blocked")
        self.assertIsNone(evidence["hysteresis"])

    def test_existence_and_identity_are_stronger(self):
        cases = [
            (dict(pid_alive=False), "dead"),
            (dict(proc_start_match=False), "dead"),
            (dict(orphan=True), "stale"),
        ]
        for overrides, expected in cases:
            state, _evidence = model.classify_session(self.evidence(**overrides), 200.0)
            self.assertEqual(state, expected)

    def session(self, kind="decision"):
        return Session(
            harness="codex", pid=10, cwd="/work/project", session_id="sid",
            slug="project", liveness="blocked", elapsed_min=3,
            interaction_state={"kind": kind, "source": "codex-rollout", "waiting_since": 100.0},
            state_evidence={"source": "interaction:codex-rollout",
                            "inputs": {"interaction_wait": dict(WAIT)}},
        )

    def test_wide_narrow_stack_and_plain_show_kind(self):
        session = self.session()
        wide = render._session_row(session, narrow=False, name_width=40)
        narrow = render._session_row_2line(session, term_width=100)[0]
        stack = render._session_row_stack(session, term_width=60)[0]
        for segments in (wide, narrow, stack):
            text = render._plain(segments)
            self.assertIn("decision", text)
            self.assertIn("◑", text)
            self.assertNotIn("실제 질문", text)

    def test_compact_kind_labels(self):
        expected = {"decision": "decision", "approval": "approval",
                    "permission": "perm", "elicitation": "elicit"}
        for kind, label in expected.items():
            self.assertEqual(render._interaction_badge(self.session(kind)).strip(), label)

    def test_working_spinners_use_dedicated_light_yellow_keys(self):
        with mock.patch.object(render.time, "time", return_value=0.0):
            _main_glyph, main_key = render._glyph("working")
            _job_glyph, job_key = render._glyph("working", dim=True)
            pulse = render._pulse_segs(
                [Session(harness="codex", pid=1, liveness="working")], []
            )
        self.assertEqual(main_key, "g_spin")
        self.assertEqual(job_key, "g_spin_dim")
        self.assertEqual(render._HUE_OF[main_key], ("y", render._A_BOLD))
        self.assertEqual(render._HUE_OF[job_key], ("y", 0))
        self.assertEqual(pulse[1][1], "g_spin")
        self.assertEqual(render._GLYPH_KEY["blocked"], "g_idle")

    def test_public_json_contains_only_interaction_metadata(self):
        with mock.patch.object(fleetmod, "_collect_memory", return_value=None), \
             mock.patch.object(fleetmod, "_collect_route", return_value=[]), \
             mock.patch.object(fleetmod, "_collect_governor", return_value=None):
            output = json.loads(fleetmod._snapshot_json([self.session()], []))
        public = output["sessions"][0]
        self.assertEqual(public["interaction_state"]["kind"], "decision")
        self.assertEqual(public["state_evidence"]["inputs"]["interaction_wait"]["kind"],
                         "decision")
        self.assertNotIn("_interaction_activity", public)
        self.assertNotIn("prompt", json.dumps(public))


if __name__ == "__main__":
    unittest.main()
