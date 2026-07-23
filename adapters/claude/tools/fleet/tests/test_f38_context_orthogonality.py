"""Focused F-38 display-only pressure and compaction-sequence checks."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet import projection  # noqa: E402
from fleet.model import ContextEvidence, DispatchJob, Session  # noqa: E402


class ContextOrthogonalityTest(unittest.TestCase):
    def test_interactive_threshold_truth_table_is_display_only(self):
        projections = []
        for pct in (69, 70, 85):
            entity = Session(harness="codex", pid=pct, slug="s-%d" % pct)
            entity._context_evidence = ContextEvidence(used_pct=pct, source="codex",
                                                       sequence=(2,), source_head_sequence=(2,))
            projection.attach_projections([entity], [], now=100.0)
            projections.append((entity.work_projection.to_dict(), entity.context.to_dict()))
        self.assertEqual(projections[0][0], projections[1][0])
        self.assertEqual(projections[1][0], projections[2][0])
        self.assertEqual([row[1]["band"] for row in projections], ["normal", "tight", "critical"])

    def test_dispatch_drops_legacy_context_instead_of_projecting_unknown(self):
        job = DispatchJob(key="code", slug="worker")
        job._context_evidence = ContextEvidence(used_pct=85, source="legacy")
        projection.attach_projections([], [job], now=100.0)
        self.assertIsNone(job.context)
        self.assertIsNone(job._context_evidence)

    def test_newer_compaction_decrease_is_valid_but_sequence_regression_is_unknown(self):
        valid = ContextEvidence(used_pct=40, source="claude", sequence=(11,),
                                source_head_sequence=(11,))
        public, _ = projection.normalize_context(valid, now=100.0)
        self.assertEqual((public.used_pct, public.band), (40, "normal"))
        invalid = ContextEvidence(used_pct=40, source="claude", sequence=(9,),
                                  source_head_sequence=(11,))
        public, evidence = projection.normalize_context(invalid, now=100.0)
        self.assertEqual(public.band, "unknown")
        self.assertEqual(evidence.invalid_reason, "selected-sequence-before-source-head")

    def test_missing_stale_and_malformed_telemetry_are_unknown(self):
        for evidence in (
            ContextEvidence(),
            ContextEvidence(used_pct=101, source="codex"),
            ContextEvidence(used_pct=50, source="codex", observed_at=0, fresh_until=1),
        ):
            public, _ = projection.normalize_context(evidence, now=100)
            self.assertEqual(public.band, "unknown")
            self.assertIsNone(public.used_pct)


if __name__ == "__main__":
    unittest.main()
