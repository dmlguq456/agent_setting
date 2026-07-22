"""Focused F-37 context/NOW subordinate-row and child-association checks."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet import collectors as fleet_collectors  # noqa: E402
from fleet import projection, render, route  # noqa: E402
from fleet.model import ContextEvidence, ContextProjection, Session, DispatchJob, SubAgent  # noqa: E402


FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "route")
REAL = os.path.join(FIXTURES, "real_claude_staged.json")


def text(lines):
    return "\n".join("".join(part for part, _ in line) for line in lines if line)


class ContextDetailTruthTableTest(unittest.TestCase):
    def _session(self, **kwargs):
        base = dict(harness="claude", pid=1, cwd="/x", liveness="working")
        base.update(kwargs)
        return Session(**base)

    def test_context_now_truth_table(self):
        cases = [
            (ContextProjection(63, "normal", "claude"), "Doing work", "ctx 63% normal · Doing work"),
            (ContextProjection(63, "normal", "claude"), None, "ctx 63% normal"),
            (ContextProjection(None, "unknown", "claude"), "Doing work", "ctx — · Doing work"),
            (None, None, "ctx —"),
        ]
        for context, now, expected in cases:
            row = render._context_detail_row(self._session(context=context, summary=now), term_width=168)
            self.assertEqual(text(row), render._SUBAGENT_IND + expected)

    def test_stale_and_dead_rows_suppress_cached_detail(self):
        for state in ("stale", "dead"):
            row = render._context_detail_row(
                self._session(liveness=state, context=ContextProjection(85, "critical", "x"),
                              summary="cached now"), term_width=168)
            self.assertEqual(row, [])

    def test_context_row_is_cell_safe_at_all_required_widths(self):
        for width in (168, 120, 100, 60):
            row = render._context_detail_row(
                self._session(context=ContextProjection(63, "normal", "x"),
                              summary="한글 상태 설명이 아주 길게 이어지는 중"), term_width=width)
            self.assertLessEqual(render._dw(text(row)), width)

    def test_main_session_projection_stage_and_progress_is_visible_at_all_widths(self):
        rid = route.load(REAL)["route_id"]
        session = Session(harness="claude", pid=200, proc_start="root", cwd="/root",
                          session_id="sid-root", slug="root", liveness="working")
        owner = DispatchJob(key="code", slug="owner", parent_sid="sid-root", depth=1,
                            liveness="working")
        leaf = DispatchJob(key="code-execute", slug="leaf", parent_slug="owner", depth=2,
                           pid=201, proc_start="leaf", route_id=rid, route_file=REAL,
                           route_node="execute", liveness="working")
        projection.attach_projections([session], [owner, leaf], now=100.0)
        for width, layout in ((168, "wide"), (120, "wide"), (100, "narrow"), (60, "stack")):
            lines = render._build_lines([session], [owner, leaf], "both", False, 0,
                                        layout=layout, term_width=width)
            visible = "\n".join("".join(part for part, _ in line) for line in lines if line)
            self.assertIn("stage execute", visible)
            self.assertIn("0/4", visible)


class ChildAssociationTest(unittest.TestCase):
    def _child(self, pid, start, cwd, harness="claude"):
        return Session(harness=harness, pid=pid, proc_start=start, cwd=cwd,
                       session_id="sid-%s" % pid, is_child=True, liveness="working",
                       title="Child title", summary="Child now",
                       context=ContextProjection(70, "tight", "child"))

    def test_exact_identity_copies_title_now_and_context_atomically(self):
        child = self._child(7, "new", "/child")
        job = DispatchJob(key="code", slug="job", pid=7, proc_start="new", cwd="/other",
                          harness="claude", liveness="working", is_child=True)
        fleet_collectors._adopt_child_titles([child], [job])
        self.assertEqual((job.title, job.summary, job.context.used_pct), ("Child title", "Child now", 70))

    def test_pid_reuse_cwd_ambiguity_and_cross_harness_are_fail_closed(self):
        old = self._child(7, "old", "/shared")
        new = self._child(7, "new", "/shared")
        reused = DispatchJob(key="code", slug="reuse", pid=7, proc_start="missing",
                             cwd="/shared", harness="claude", is_child=True)
        fleet_collectors._adopt_child_titles([old, new], [reused])
        self.assertIsNone(reused.title)
        self.assertIsNone(reused.association_ambiguity)  # exact identity mismatch never falls through
        cwd_ambiguous = DispatchJob(key="code", slug="cwd", cwd="/shared", harness="claude",
                                    is_child=True)
        fleet_collectors._adopt_child_titles([old, new], [cwd_ambiguous])
        self.assertEqual(cwd_ambiguous.association_ambiguity, "multiple-child-cwd-candidates")
        foreign = self._child(8, "x", "/other", harness="codex")
        cross = DispatchJob(key="code", slug="cross", pid=8, proc_start="x", cwd="/other",
                            harness="claude", is_child=True)
        fleet_collectors._adopt_child_titles([foreign], [cross])
        self.assertIsNone(cross.title)

    def test_parent_context_is_not_inherited(self):
        parent = Session(harness="claude", pid=1, cwd="/x", context=ContextProjection(85, "critical", "parent"))
        child = self._child(2, "x", "/child")
        job = DispatchJob(key="code", slug="job", pid=99, proc_start="wrong", cwd="/job",
                          harness="claude", is_child=True)
        fleet_collectors._adopt_child_titles([parent, child], [job])
        self.assertIsNone(job.context)

    def test_process_route_chunk_orders_job_context_then_exact_session_subagents(self):
        rid = route.load(REAL)["route_id"]
        job = DispatchJob(key="code", slug="process-leaf", pid=301, proc_start="leaf",
                          route_id=rid, route_file=REAL, route_node="execute",
                          harness="claude", liveness="working", summary="NOW")
        job._context_evidence = ContextEvidence(used_pct=50, source="claude")
        session = Session(harness="claude", pid=301, proc_start="leaf", cwd="/x",
                          is_child=True, liveness="working",
                          subagents=[SubAgent(agent_type="tool", active=True)])
        projection.attach_projections([session], [job], now=100.0)
        render.set_process_view(True)
        try:
            lines = render._build_lines([session], [job], "both", False, 0,
                                        layout="wide", term_width=168)
        finally:
            render.set_process_view(False)
        visible = "\n".join("".join(part for part, _ in line) for line in lines if line)
        self.assertLess(visible.index("└▸🚀"), visible.index("ctx 50%"))
        self.assertLess(visible.index("ctx 50%"), visible.index("⚡tool"))


if __name__ == "__main__":
    unittest.main()
