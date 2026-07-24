"""Focused F-37 context/NOW subordinate-row and child-association checks."""
import json
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet import collectors as fleet_collectors  # noqa: E402
from fleet import projection, render, route  # noqa: E402
from fleet.collectors import dispatch as dispatch_collector  # noqa: E402
from fleet.model import (  # noqa: E402
    ContextProjection, DispatchJob, ProgressProjection, Session,
    SubAgent, WorkProjection,
)


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
             "💬 ━━━━━━━━━━────── 63%   Doing work"),
            (ContextProjection(63, "normal", "claude"), None,
             "💬 ━━━━━━━━━━────── 63%"),
            (ContextProjection(None, "unknown", "claude"), "Doing work",
             "💬 ────────────────   —   Doing work"),
            (None, None, "💬 ────────────────   —"),
            (ContextProjection(0, "normal", "claude"), None,
             "💬 ────────────────  0%"),
        ]
        for context, now, expected in cases:
            row = render._context_detail_row(self._session(context=context, summary=now), term_width=168)
            # The row is left-aligned to the NAME column (2026-07-24).
            self.assertEqual(text(row), " " * render._NAME_COL + expected)

    def test_stale_and_dead_rows_suppress_cached_detail(self):
        for state in ("stale", "dead"):
            row = render._context_detail_row(
                self._session(liveness=state, context=ContextProjection(85, "critical", "x"),
                              summary="cached now"), term_width=168)
            self.assertEqual(row, [])

    def test_dispatch_omits_context_and_keeps_only_fresh_now(self):
        job = DispatchJob(
            key="code", slug="worker", harness="claude", depth=1,
            liveness="working", summary="NOW",
            context=ContextProjection(85, "critical", "legacy"),
        )
        for width, layout in ((168, "wide"), (120, "wide"),
                              (100, "narrow"), (60, "stack")):
            with self.subTest(width=width):
                row = render._dispatch_summary_detail_row(
                    job, depth=1, term_width=width)
                visible = text(row)
                self.assertNotIn("💬", visible)
                self.assertEqual(visible.index("NOW"), render._NAME_COL)
                self.assertLessEqual(render._dw(visible), width)

                rendered = text(render._build_lines(
                    [], [job], "both", False, 0,
                    layout=layout, term_width=width))
                self.assertNotIn("💬", rendered)
                self.assertIn("NOW", rendered)

        job.summary = None
        self.assertEqual(render._dispatch_summary_detail_row(job), [])

    def test_malformed_legacy_percentage_is_unavailable_not_clamped(self):
        for malformed in (-1, 101, True, "63"):
            with self.subTest(malformed=malformed):
                row = render._context_detail_row(
                    self._session(ctx_pct=malformed), term_width=168)
                self.assertEqual(text(row), " " * render._NAME_COL +
                                 "💬 ────────────────   —")

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
            self.assertIn("💬 ", text(row))
            self.assertLess(text(row).index("💬 "), text(row).index("한글"))
            self.assertNotIn(": ", text(row))
            self.assertIn("   한글", text(row))
            row_text = text(row)
            # The context row starts at the NAME column on wide terminals, at the compact strip
            # inset on narrow ones (2026-07-24 left-align gated to wide layout).
            expected_col = render._NAME_COL if width >= render._TWO_LINE_CUTOFF else len(render._SUBAGENT_IND)
            self.assertEqual(render._dw(row_text[:row_text.index("💬")]), expected_col)

    def test_description_column_is_stable_for_value_width_and_depth(self):
        for pct in (None, 0, 63, 100):
            context = ContextProjection(pct, "unknown", "x")
            for depth in (0, 1, 2):
                with self.subTest(pct=pct, depth=depth):
                    row = render._context_detail_row(
                        self._session(context=context, summary="Doing work"),
                        depth=depth, term_width=168)
                    visible = text(row)
                    self.assertEqual(
                        render._dw(visible[:visible.index("Doing work")]),
                        render._NAME_COL + render._CTX_LABEL_W + render._HW
                        + render._CONTEXT_VALUE_W + render._CONTEXT_NOW_GAP)
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
                self.assertIn("85%   Doing work", visible)
                self.assertNotIn(": ", visible)

    def test_percentage_is_dim_while_gauge_keeps_level_color(self):
        row = render._context_detail_row(
            self._session(context=ContextProjection(85, "critical", "x")),
            term_width=168)[0]
        self.assertEqual([key for value, key in row if value == " 85%"], ["dim"])
        self.assertIn("lvl_r", [key for value, key in row if "━" in value])

    def test_linear_dispatch_owner_owns_projection_stage_once_at_all_widths(self):
        rid = route.load(REAL)["route_id"]
        session = Session(harness="claude", pid=200, proc_start="root", cwd="/root",
                          session_id="sid-root", slug="root", liveness="working")
        owner = DispatchJob(key="code", slug="owner", parent_sid="sid-root", depth=1,
                            cwd="/root", harness="claude", is_child=True,
                            liveness="working")
        leaf = DispatchJob(key="code-execute", slug="leaf", parent_slug="owner", depth=2,
                           pid=201, proc_start="leaf", route_id=rid, route_file=REAL,
                           route_node="execute", liveness="working")
        projection.attach_projections([session], [owner, leaf], now=100.0)
        for width, layout in ((168, "wide"), (120, "wide"), (100, "narrow"), (60, "stack")):
            lines = render._build_lines([session], [owner, leaf], "both", False, 0,
                                        layout=layout, term_width=width)
            visible = "\n".join("".join(part for part, _ in line) for line in lines if line)
            self.assertNotIn("stage execute", visible)
            self.assertNotIn("←{", visible)
            self.assertIn("plan › execute › test › report", visible)

    def test_replica_route_collapses_and_second_line_stays_log_summary(self):
        # 2026-07-24: the conductor breadcrumb names a replica group ONCE
        # (`impl-review(2-way)`), never leg-by-leg, and a dispatch card's second
        # line is its live log summary — no dedicated stage row even for a
        # non-linear (replica-branched) route.
        nodes = [
            {"id": "plan", "state": "done", "level": 0, "depends_on": []},
            {"id": "execute", "state": "done", "level": 1, "depends_on": ["plan"]},
            {"id": "impl-review", "state": "active", "level": 2,
             "depends_on": ["execute"], "replica_group": "impl-review"},
            {"id": "impl-review-replica", "state": "active", "level": 2,
             "depends_on": ["execute"], "replica_group": "impl-review"},
            {"id": "test", "state": "pending", "level": 3,
             "depends_on": ["impl-review", "impl-review-replica"]},
        ]
        work = WorkProjection(
            source="route-exact", route_id="rt-replica",
            stage_label="impl-review(2-way)", node_state="active",
            progress=ProgressProjection(2, 5),
            _route_view={"view": {"nodes": nodes}},
        )
        session = Session(harness="claude", pid=230, proc_start="root", cwd="/root",
                          session_id="sid-rep", slug="root", liveness="working")
        owner = DispatchJob(key="code", slug="conductor", parent_sid="sid-rep",
                            depth=1, cwd="/root", harness="claude", is_child=True,
                            liveness="working", work_projection=work,
                            summary="review merge")
        for width, layout in ((256, "wide"), (168, "wide"), (100, "narrow"),
                              (60, "stack")):
            visible = text(render._build_lines([session], [owner], "both", False, 0,
                                               layout=layout, term_width=width))
            with self.subTest(width=width):
                self.assertIn("impl-review(2-way)", visible)
                self.assertNotIn("impl-review-replica", visible)
                self.assertNotIn("←{", visible)
                self.assertIn("review merge", visible)
        # A genuinely wide terminal lends its slack to the breadcrumb: the whole
        # collapsed route stays visible instead of folding its early stages.
        wide = text(render._build_lines([session], [owner], "both", False, 0,
                                        layout="wide", term_width=256))
        self.assertIn("plan✓ › execute✓ › impl-review(2-way) › test", wide)

    def test_quick_one_shot_is_rendered_once_on_owner_not_parent_or_detail(self):
        node = {"id": "one-shot", "state": "active", "level": 0, "depends_on": []}
        work = WorkProjection(
            source="route-exact", route_id="rt-one", route_node="one-shot",
            stage_label="one-shot", node_state="active",
            progress=ProgressProjection(0, 1),
            _route_view={"view": {"nodes": [node]}},
        )
        session = Session(
            harness="claude", pid=220, proc_start="root", cwd="/tmp/fleet-one",
            session_id="sid-one", slug="parent", liveness="working",
            work_projection=work,
        )
        owner = DispatchJob(
            key="code", slug="quick-worker", parent_sid="sid-one", is_child=True,
            cwd="/tmp/fleet-one", harness="claude", depth=1, intensity="quick",
            liveness="working", work_projection=work,
        )
        for width, layout in ((168, "wide"), (120, "wide"), (100, "narrow"), (60, "stack")):
            visible = text(render._build_lines(
                [session], [owner], "both", False, 0, layout=layout, term_width=width))
            with self.subTest(width=width):
                self.assertEqual(visible.count("one-shot"), 1)
                self.assertNotIn("quick/exec", visible)
                self.assertNotIn("stage one-shot", visible)

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
                    self.assertIn("💬 ", visible)             # context icon
                    self.assertIn("stage exec", visible)      # stage rides the row's own column
                    # An INFERRED inline stage carries NO dedicated detail row (2026-07-24): a
                    # main session must not show the `plan › exec › test` breadcrumb line.
                    self.assertNotIn("exec ● ←{plan}", visible)
                    self.assertEqual(
                        render._projection_stage_detail_rows(session, term_width=width), [])

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

    def test_completed_route_suppresses_session_detail_row(self):
        # 2026-07-24 (user "stage 설명 여전히 뜨는데 이거 없앴다매?"): a fully-done route draws
        # no stage detail row on the owning session — a finished (often dead-conductor) pipeline's
        # whole DAG lingering under the live dispatcher session is noise. Any non-done node still
        # renders so a real failure stays visible.
        def _session(nodes):
            return Session(harness="claude", pid=1, proc_start="p", cwd="/x",
                           session_id="sid-x", slug="root", liveness="working",
                           work_projection=WorkProjection(
                               source="route-exact", route_id="rt-done",
                               _route_view={"view": {"nodes": nodes}}))
        done_nodes = [
            {"id": "plan", "state": "done", "level": 0, "depends_on": []},
            {"id": "execute", "state": "done", "level": 1, "depends_on": ["plan"]},
        ]
        for width in (168, 120, 100, 60):
            with self.subTest(width=width):
                self.assertEqual(
                    render._projection_stage_detail_rows(_session(done_nodes), term_width=width),
                    [])
        live_nodes = [
            {"id": "plan", "state": "done", "level": 0, "depends_on": []},
            {"id": "execute", "state": "active", "level": 1, "depends_on": ["plan"]},
        ]
        rows = render._projection_stage_detail_rows(_session(live_nodes), term_width=168)
        self.assertTrue(rows)
        self.assertIn("execute", text(rows))

    def test_replica_completed_route_collapses_and_suppresses(self):
        # The replica legs collapse to `impl-review(2-way)`; when the whole (collapsed) route
        # is done, still no detail row.
        nodes = [
            {"id": "execute", "state": "done", "level": 0, "depends_on": []},
            {"id": "impl-review", "state": "done", "level": 1, "depends_on": ["execute"],
             "replica_group": "impl-review"},
            {"id": "impl-review-replica", "state": "done", "level": 1,
             "depends_on": ["execute"], "replica_group": "impl-review"},
            {"id": "test", "state": "done", "level": 2,
             "depends_on": ["impl-review", "impl-review-replica"]},
        ]
        session = Session(harness="claude", pid=2, proc_start="p", cwd="/y",
                          session_id="sid-y", slug="root", liveness="working",
                          work_projection=WorkProjection(
                              source="route-exact", route_id="rt-rep-done",
                              _route_view={"view": {"nodes": nodes}}))
        self.assertEqual(render._projection_stage_detail_rows(session, term_width=168), [])


class ClaudeStreamSessionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.logs = os.path.join(self.tmp.name, ".dispatch", "logs")
        os.makedirs(self.logs)
        self.env = mock.patch.dict(os.environ, {"AGENT_HOME": self.tmp.name})
        self.env.start()
        dispatch_collector._CLAUDE_STREAM_CACHE.clear()

    def tearDown(self):
        dispatch_collector._CLAUDE_STREAM_CACHE.clear()
        self.env.stop()
        self.tmp.cleanup()

    def _job(self, attempt="att-stream-exact"):
        job = DispatchJob(
            key="code", slug="owner", pid=91, proc_start="wrapper", harness="claude",
            attempt_id=attempt, is_child=True, liveness="working",
        )
        job._log_file = os.path.join(self.logs, "owner.%s.claude.jsonl" % attempt)
        return job

    def _write_log(self, job, rows):
        with open(job._log_file, "w", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row) + "\n")

    @staticmethod
    def _assistant(sid, model_id, active):
        return {
            "type": "assistant", "session_id": sid,
            "message": {"model": model_id, "usage": {
                "input_tokens": 10,
                "cache_creation_input_tokens": 20,
                "cache_read_input_tokens": active - 30,
            }},
        }

    @staticmethod
    def _agent_use(sid, agent_type="explore"):
        return {
            "type": "assistant", "session_id": sid,
            "timestamp": "2026-07-23T05:00:00Z",
            "message": {"content": [{
                "type": "tool_use", "name": "Agent", "id": "toolu-agent-1",
                "input": {"subagent_type": agent_type},
            }]},
        }

    def test_attempt_stream_recovers_exact_session_without_context(self):
        job = self._job()
        self._write_log(job, [
            {"type": "system", "session_id": "sid-child"},
            self._assistant("sid-child", "claude-fable-5", 100),
            self._assistant("sid-child", "claude-fable-5", 160),
        ])
        dispatch_collector._enrich_claude_stream_session(job)
        self.assertEqual(job._runtime_session_id, "sid-child")
        self.assertIsNone(job.context)
        self.assertIsNone(job._context_evidence)

    def test_stream_usage_does_not_create_context_or_model(self):
        job = self._job()
        self._write_log(job, [self._assistant("sid-child", "claude-fable-5", 160)])
        dispatch_collector._enrich_claude_stream_session(job)
        self.assertEqual(job._runtime_session_id, "sid-child")
        self.assertIsNone(job.model)
        self.assertIsNone(job.context)
        self.assertIsNone(job._context_evidence)

    def test_attempt_stream_attaches_native_subagents_without_context(self):
        job = self._job()
        self._write_log(job, [
            {"type": "system", "session_id": "sid-child"},
            self._agent_use("sid-child", "fact-check"),
        ])
        dispatch_collector._enrich_claude_stream_session(job)
        self.assertEqual(job._runtime_session_id, "sid-child")
        self.assertEqual(len(job.subagents), 1)
        self.assertEqual(job.subagents[0].agent_type, "fact-check")
        self.assertTrue(job.subagents[0].active)
        self.assertEqual(job.subagents[0].source, "claude-attempt-stream")
        self.assertIsNone(job.context)
        self.assertIsNone(job._context_evidence)
        self.assertEqual(job.to_dict()["subagents"][0]["agent_type"], "fact-check")

    def test_multiple_stream_session_ids_and_foreign_path_fail_closed(self):
        job = self._job()
        self._write_log(job, [
            self._assistant("sid-a", "claude-fable-5", 100),
            self._assistant("sid-b", "claude-fable-5", 160),
        ])
        dispatch_collector._enrich_claude_stream_session(job)
        self.assertFalse(hasattr(job, "_runtime_session_id"))
        self.assertEqual(job.association_ambiguity, "multiple-stream-session-ids")
        self.assertIsNone(job.subagents)

        foreign = self._job("att-foreign")
        foreign._log_file = os.path.join(self.tmp.name, "foreign.att-foreign.claude.jsonl")
        with open(foreign._log_file, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(self._assistant("sid-x", "claude-fable-5", 160)) + "\n")
        dispatch_collector._enrich_claude_stream_session(foreign)
        self.assertFalse(hasattr(foreign, "_runtime_session_id"))


class ChildAssociationTest(unittest.TestCase):
    def _child(self, pid, start, cwd, harness="claude"):
        return Session(harness=harness, pid=pid, proc_start=start, cwd=cwd,
                       session_id="sid-%s" % pid, is_child=True, liveness="working",
                       title="Child title", summary="Child now",
                       context=ContextProjection(70, "tight", "child"))

    def test_exact_identity_copies_title_and_now_only(self):
        child = self._child(7, "new", "/child")
        child.subagents = [SubAgent(agent_type="exact-child", active=True)]
        job = DispatchJob(key="code", slug="job", pid=7, proc_start="new", cwd="/other",
                          harness="claude", liveness="working", is_child=True)
        fleet_collectors._adopt_child_titles([child], [job])
        self.assertEqual((job.title, job.summary, job.context),
                         ("Child title", "Child now", None))
        self.assertEqual(job.subagents[0].agent_type, "exact-child")

    def test_wrapper_pid_uses_attempt_stream_session_id_for_title_and_now(self):
        child = self._child(7, "runtime", "/child")
        child.subagents = [SubAgent(agent_type="sid-child", active=True)]
        job = DispatchJob(
            key="code", slug="job", pid=99, proc_start="wrapper", cwd="/child",
            harness="claude", liveness="working", is_child=True,
        )
        job._runtime_session_id = child.session_id
        fleet_collectors._adopt_child_titles([child], [job])
        self.assertEqual((job.title, job.summary, job.context),
                         ("Child title", "Child now", None))
        self.assertEqual(job.subagents[0].agent_type, "sid-child")
        self.assertEqual(child.context.used_pct, 70)

    def test_attempt_stream_subagents_win_over_associated_session(self):
        child = self._child(7, "runtime", "/child")
        child.subagents = [SubAgent(agent_type="persistent-child", active=True)]
        job = DispatchJob(
            key="code", slug="job", pid=99, proc_start="wrapper", cwd="/child",
            harness="claude", liveness="working", is_child=True,
            subagents=[SubAgent(agent_type="attempt-stream", active=True)],
        )
        job._runtime_session_id = child.session_id
        fleet_collectors._adopt_child_titles([child], [job])
        self.assertEqual(job.subagents[0].agent_type, "attempt-stream")

    def test_duplicate_stream_session_id_candidates_fail_closed(self):
        first = self._child(7, "a", "/first")
        second = self._child(8, "b", "/second")
        second.session_id = first.session_id
        job = DispatchJob(
            key="code", slug="job", harness="claude", is_child=True,
        )
        job._runtime_session_id = first.session_id
        fleet_collectors._adopt_child_titles([first, second], [job])
        self.assertIsNone(job.title)
        self.assertIsNone(job.summary)
        self.assertIsNone(job.context)
        self.assertEqual(job.association_ambiguity,
                         "multiple-child-session-id-candidates")

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

    def test_group_dispatch_row_uses_job_subagents_without_runtime_session(self):
        parent = Session(
            harness="claude", pid=300, proc_start="parent", cwd="/x",
            session_id="sid-parent", slug="parent", liveness="working",
        )
        job = DispatchJob(
            key="code", slug="wrapper-child", pid=999, proc_start="wrapper",
            cwd="/x", parent_sid="sid-parent", harness="claude", is_child=True,
            liveness="working", subagents=[SubAgent(agent_type="stream-tool", active=True)],
        )
        for width, layout in ((168, "wide"), (120, "wide"),
                              (100, "narrow"), (60, "stack")):
            visible = text(render._build_lines(
                [parent], [job], "both", False, 0, layout=layout, term_width=width))
            with self.subTest(width=width):
                self.assertEqual(visible.count("⚡stream-tool"), 1)
                self.assertNotIn("🧩", next(
                    line for line in visible.splitlines() if "stream-tool" in line))

    def test_process_route_chunk_orders_job_now_then_attempt_subagents(self):
        rid = route.load(REAL)["route_id"]
        job = DispatchJob(key="code", slug="process-leaf", pid=999, proc_start="wrapper",
                          route_id=rid, route_file=REAL, route_node="execute",
                          harness="claude", liveness="working", summary="NOW",
                          subagents=[SubAgent(agent_type="tool", active=True)])
        projection.attach_projections([], [job], now=100.0)
        render.set_process_view(True)
        try:
            lines = render._build_lines([], [job], "both", False, 0,
                                        layout="wide", term_width=168)
        finally:
            render.set_process_view(False)
        visible = "\n".join("".join(part for part, _ in line) for line in lines if line)
        self.assertNotIn("💬", visible)
        self.assertLess(visible.index("└▸🚀"), visible.index("NOW"))
        self.assertLess(visible.index("NOW"), visible.index("⚡tool"))
        now_line = next(line for line in visible.splitlines() if "NOW" in line)
        self.assertEqual(now_line.index("NOW"), render._NAME_COL)


if __name__ == "__main__":
    unittest.main()
