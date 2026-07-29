import os
import sys
from pathlib import Path
import unittest


TOOLS = Path(__file__).resolve().parents[2]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
from fleet import render  # noqa: E402


class DegradationAlertsTest(unittest.TestCase):
    def event(self, **extra):
        value = {"event_id": "e1", "route_id": "rt-r", "route_node": "execute",
                 "kind": "leg-failure", "dispatch_depth": 2, "ts": 1,
                 "parallel_leg_index": 0, "parallel_leg_count": 2, "harness": "codex",
                 "exit_code": 78, "reason": "network"}
        value.update(extra)
        return value

    def test_01_leg_row_has_syntax_and_coordinates(self):
        row = render._degradation_alert_rows({"rt-r": [self.event()]})[0]
        self.assertEqual(row, "⚠ execute leg 1/2 codex ✕ exit=78 network")

    def test_02_event_id_deduplicates(self):
        rows = render._degradation_alert_rows({"rt-r": [self.event(), self.event()]})
        self.assertEqual(len(rows), 1)

    def test_03_route_is_capped_at_three(self):
        rows = render._degradation_alert_rows({"rt-r": [self.event(event_id=str(i)) for i in range(5)]})
        self.assertEqual(sum("✕ exit" in row for row in rows), 3)

    def test_04_json_more_marker_is_explicit(self):
        rows = render._degradation_alert_rows({"rt-r": [self.event(event_id=str(i)) for i in range(5)]})
        self.assertIn("⚠ +2 more failed legs (--json)", rows)

    def test_05_show_all_toggle_exposes_every_event(self):
        rows = render._degradation_alert_rows({"rt-r": [self.event(event_id=str(i)) for i in range(5)]}, show_all=True)
        self.assertEqual(sum("✕ exit" in row for row in rows), 5)

    def test_06_chain_exhausted_uses_all_hops_phrase(self):
        row = render._degradation_alert_rows({"rt-r": [self.event(kind="chain-exhausted")]})[0]
        self.assertIn("fallback-chain-exhausted · all hops exhausted", row)

    def test_07_depth_one_is_contract_violation_alert(self):
        row = render._degradation_alert_rows({"rt-r": [self.event(kind="degradation", dispatch_depth=1,
                                                                    fallback_hop="inline")]})[0]
        self.assertEqual(row, "⚠ contract violation: quick degradation row · rt-r · execute · inline")

    def test_08_unattributed_event_is_standalone(self):
        row = render._degradation_alert_rows({"_unattributed": [self.event(route_id=None,
                                                                             _unattributed=True)]})[0]
        self.assertEqual(row, "⚠ unattributed degradation · network")


if __name__ == "__main__":
    unittest.main()
