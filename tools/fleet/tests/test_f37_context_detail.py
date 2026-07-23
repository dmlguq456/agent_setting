"""Focused F-37 context/NOW subordinate-row and child-association checks."""
import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet import collectors as fleet_collectors  # noqa: E402
from fleet import projection, render, route  # noqa: E402
from fleet.model import ContextEvidence, ContextProjection, Session, DispatchJob, SubAgent  # noqa: E402


FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "route")
REAL = os.path.join(FIXTURES, "real_claude_staged.json")
COMPOSED = os.path.join(FIXTURES, "synth_composed_survey.json")


def text(lines):
    return "\n".join("".join(part for part, _ in line) for line in lines if line)


class ContextDetailTruthTableTest(unittest.TestCase):
    def _session(self, **kwargs):
        base = dict(harness="claude", pid=1, cwd="/x", liveness="working")
        base.update(kwargs)
        return Session(**base)

    def test_context_now_truth_table(self):
        cases = [
            (ContextProjection(63, "normal", "claude"), "Doing work",
             "context ━━━━━━━━━━────── 63%  Doing work"),
            (ContextProjection(63, "normal", "claude"), None,
             "context ━━━━━━━━━━────── 63%"),
            (ContextProjection(None, "unknown", "claude"), "Doing work",
             "context ────────────────   —  Doing work"),
            (None, None, "context ────────────────   —"),
            (ContextProjection(0, "normal", "claude"), None,
             "context ────────────────  0%"),
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

    def test_malformed_legacy_percentage_is_unavailable_not_clamped(self):
        for malformed in (-1, 101, True, "63"):
            with self.subTest(malformed=malformed):
                row = render._context_detail_row(
                    self._session(ctx_pct=malformed), term_width=168)
                self.assertEqual(text(row), render._SUBAGENT_IND +
                                 "context ────────────────   —")

    def test_context_alert_uses_the_full_visible_label(self):
        session = self._session(slug="hot", ctx_pct=85)
        visible = text(render._build_lines([session], [], "fleet", False, 0,
                                           layout="wide", term_width=168))
        self.assertIn("⚠ context 85% hot", visible)
        self.assertNotIn("⚠ ctx ", visible)

    def test_context_row_is_cell_safe_at_all_required_widths(self):
        for width in (168, 120, 100, 60):
            row = render._context_detail_row(
                self._session(context=ContextProjection(63, "normal", "x"),
                              summary="한글 상태 설명이 아주 길게 이어지는 중"), term_width=width)
            self.assertLessEqual(render._dw(text(row)), width)
            track = re.search(r"[━─]+", text(row)).group(0)
            self.assertEqual(len(track), render._HW)
            self.assertIn("context ", text(row))
            self.assertLess(text(row).index("context "), text(row).index("한글"))
            self.assertNotIn(": ", text(row))
            self.assertIn("  한글", text(row))
            self.assertEqual(text(row).index("한글"), render._NAME_COL)

    def test_description_column_is_stable_for_value_width_and_depth(self):
        for pct in (None, 0, 63, 100):
            context = ContextProjection(pct, "unknown", "x")
            for depth in (0, 1, 2):
                with self.subTest(pct=pct, depth=depth):
                    row = render._context_detail_row(
                        self._session(context=context, summary="Doing work"),
                        depth=depth, term_width=168)
                    visible = text(row)
                    self.assertEqual(visible.index("Doing work"), render._NAME_COL)
                    track = re.search(r"[━─]+", visible).group(0)
                    self.assertEqual(len(track), render._HW - 2 * depth)

    def test_context_band_is_not_rendered(self):
        for band in ("normal", "tight", "critical"):
            with self.subTest(band=band):
                row = render._context_detail_row(
                    self._session(context=ContextProjection(85, band, "x"),
                                  summary="Doing work"), term_width=168)
                visible = text(row)
                self.assertNotIn(band, visible)
                self.assertIn("85%  Doing work", visible)
                self.assertNotIn(": ", visible)

    def test_percentage_is_dim_while_gauge_keeps_level_color(self):
        row = render._context_detail_row(
            self._session(context=ContextProjection(85, "critical", "x")),
            term_width=168)[0]
        self.assertEqual([key for value, key in row if value == " 85%"], ["dim"])
        self.assertIn("lvl_r", [key for value, key in row if "━" in value])

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
            for node_id in ("plan", "execute", "test", "report"):
                self.assertEqual(len(re.findall(r"\b%s [✓●○✕]" % re.escape(node_id), visible)), 1)
            self.assertIn("execute ● ←{plan}", visible)
            self.assertIn("test ○ ←{execute}", visible)
            self.assertIn("report ○ ←{test}", visible)

    def test_inline_main_session_uses_artifact_stage_without_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = os.path.join(tmp, "plans", "2026-07-22_inline-main")
            os.makedirs(plan)
            with open(os.path.join(plan, "execute.md"), "w", encoding="utf-8") as stream:
                stream.write("inline implementation evidence\n")
            session = Session(harness="codex", pid=205, proc_start="inline", cwd=tmp,
                              session_id="sid-inline", slug="inline-main",
                              liveness="working")
            projection.attach_projections([session], [], artifact_root=tmp, now=100.0)
            self.assertEqual(session.work_projection.source, "artifact-inferred")
            self.assertEqual(session.work_projection.stage_label, "exec")
            for width in (168, 120, 100, 60):
                lines = render._build_lines([session], [], "fleet", width < 70, 0,
                                            layout=render._layout_mode(width),
                                            term_width=width)
                visible = text(lines)
                with self.subTest(width=width):
                    self.assertIn("context ", visible)
                    for primary in ("plan ✓", "exec ●", "test ○", "report ○"):
                        self.assertEqual(visible.count(primary), 1)
                    self.assertIn("exec ● ←{plan}", visible)
                    stage_rows = render._projection_stage_detail_rows(
                        session, term_width=width)
                    self.assertTrue(all(render._dw(text([line])) <= width
                                        for line in stage_rows))

    def test_composed_pipeline_keeps_parallel_and_fanin_at_all_widths(self):
        rid = route.load(COMPOSED)["route_id"]
        owner = Session(harness="claude", pid=210, proc_start="root", cwd="/root",
                        session_id="sid-composed", slug="root", liveness="working")
        jobs = [
            DispatchJob(key="claim", slug="claim-b", parent_sid="sid-composed", depth=2,
                        route_id=rid, route_file=COMPOSED, route_node="claim-b",
                        liveness="working"),
            DispatchJob(key="claim", slug="claim-a", parent_sid="sid-composed", depth=2,
                        route_id=rid, route_file=COMPOSED, route_node="claim-a",
                        liveness="working"),
        ]
        projection.attach_projections([owner], jobs, now=100.0)
        view = owner.work_projection._route_view["view"]
        for width in (168, 120, 100, 60):
            stage_rows = render._stage_detail_rows(view["nodes"], term_width=width)
            rendered = text(stage_rows)
            with self.subTest(width=width):
                self.assertTrue(all(render._dw(text([row])) <= width for row in stage_rows))
                for node_id in ("survey", "claim-a", "claim-b", "synth"):
                    self.assertEqual(
                        len(re.findall(r"\b%s [✓●○✕]" % re.escape(node_id), rendered)), 1)
                self.assertIn("claim-a ● ←{survey}", rendered)
                self.assertIn("claim-b ● ←{survey}", rendered)
                self.assertIn("synth ○ ←{claim-a,claim-b}", rendered)
                self.assertIn("| claim-b", rendered)

    def test_arbitrary_dag_keeps_multiple_roots_partial_join_and_exact_edges(self):
        nodes = [
            {"id": "root-a", "state": "done", "level": 0, "depends_on": []},
            {"id": "root-b", "state": "done", "level": 0, "depends_on": []},
            {"id": "a1", "state": "active", "level": 1, "depends_on": ["root-a"]},
            {"id": "a2", "state": "pending", "level": 2, "depends_on": ["a1"]},
            {"id": "partial", "state": "pending", "level": 2,
             "depends_on": ["a1", "root-b"]},
            {"id": "final", "state": "pending", "level": 3,
             "depends_on": ["a2", "partial"]},
        ]
        for width in (168, 120, 100, 60):
            rows = render._stage_detail_rows(nodes, term_width=width)
            rendered = text(rows)
            with self.subTest(width=width):
                self.assertTrue(all(render._dw(text([row])) <= width for row in rows))
                for node in nodes:
                    primary = r"\b%s [✓●○✕]" % re.escape(node["id"])
                    self.assertEqual(len(re.findall(primary, rendered)), 1)
                for relation in ("a1 ● ←{root-a}", "a2 ○ ←{a1}",
                                 "partial ○ ←{a1,root-b}",
                                 "final ○ ←{a2,partial}"):
                    self.assertIn(relation, rendered)
                self.assertIn("| root-b", rendered)
                self.assertIn("| partial", rendered)


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
        self.assertLess(visible.index("└▸🚀"), visible.index("context "))
        self.assertLess(visible.index("context "), visible.index("⚡tool"))


if __name__ == "__main__":
    unittest.main()
