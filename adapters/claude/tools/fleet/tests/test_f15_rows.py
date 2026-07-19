#!/usr/bin/env python3
"""F-15 (분사 row 재설계) / F-16 (세션 표시명 짧게) — hermetic unit tests.

Runnable directly or via `python3 -m unittest fleet.tests.test_f15_rows -v` (from `tools/`).
"""
import os
import sys
import tempfile
import unittest
from unittest import mock

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from fleet import render               # noqa: E402
from fleet.collectors import dispatch  # noqa: E402
from fleet.model import DispatchJob, Session  # noqa: E402


class SlugStemTest(unittest.TestCase):

    def test_strips_execute_suffix(self):
        self.assertEqual(dispatch._slug_stem("fleet-ui-v2-execute"), "fleet-ui-v2")

    def test_strips_code_plan_suffix(self):
        self.assertEqual(dispatch._slug_stem("x-code-plan"), "x")

    def test_unmatched_slug_unchanged(self):
        self.assertEqual(dispatch._slug_stem("already"), "already")

    def test_no_over_strip_of_multiple_hyphen_tokens(self):
        self.assertEqual(dispatch._slug_stem("foo-bar-baz-test"), "foo-bar-baz")
        self.assertEqual(dispatch._slug_stem("foo-bar-baz"), "foo-bar-baz")


class DedupKeyTest(unittest.TestCase):

    def test_same_cwd_same_stem_merges_to_one_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            wt = os.path.join(tmp, "wtA")
            os.makedirs(wt, exist_ok=True)
            jobs_log = os.path.join(tmp, "jobs.log")
            with open(jobs_log, "w") as f:
                f.write("\t".join([
                    "2026-07-10T01:00:00+00:00", "open", "repo", wt,
                    "fleet-ui-v2-execute",
                    "capability=autopilot-code,mode=dev,qa=standard",
                ]) + "\n")
            proc_job = DispatchJob(key="code", slug="fleet-ui-v2", cwd=wt, pid=1, harness="claude")
            with mock.patch.object(dispatch, "_scan_processes", return_value=[proc_job]), \
                 mock.patch.object(dispatch, "_live_claude_cwds", return_value={}), \
                 mock.patch.object(dispatch, "_dispatch_liveness",
                                   side_effect=lambda *a, **k: "working"):
                jobs = dispatch.collect(jobs_path=jobs_log)
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0].slug, "fleet-ui-v2")

    def test_different_cwd_same_stem_keeps_both_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            wt_a = os.path.join(tmp, "wtA")
            wt_b = os.path.join(tmp, "wtB")
            os.makedirs(wt_a, exist_ok=True)
            os.makedirs(wt_b, exist_ok=True)
            jobs_log = os.path.join(tmp, "jobs.log")
            with open(jobs_log, "w") as f:
                f.write("\t".join([
                    "2026-07-10T01:00:00+00:00", "open", "repo", wt_b,
                    "fleet-ui-v2-execute",
                    "capability=autopilot-code,mode=dev,qa=standard",
                ]) + "\n")
            proc_job = DispatchJob(key="code", slug="fleet-ui-v2", cwd=wt_a, pid=1, harness="claude")
            with mock.patch.object(dispatch, "_scan_processes", return_value=[proc_job]), \
                 mock.patch.object(dispatch, "_live_claude_cwds", return_value={}), \
                 mock.patch.object(dispatch, "_dispatch_liveness",
                                   side_effect=lambda *a, **k: "working"):
                jobs = dispatch.collect(jobs_path=jobs_log)
            self.assertEqual({j.slug for j in jobs},
                              {"fleet-ui-v2", "fleet-ui-v2-execute"})


class QueuedLivenessTest(unittest.TestCase):

    def _job(self, elapsed_min):
        return DispatchJob(key="code", slug="s", cwd="/tmp/x", source="jobs", status="open",
                           elapsed_min=elapsed_min)

    def test_open_no_transcript_small_elapsed_is_queued(self):
        job = self._job(2)
        with mock.patch.object(dispatch, "_job_liveness", return_value="dead"):
            self.assertEqual(dispatch._dispatch_liveness(job, now=0), "queued")

    def test_open_no_transcript_large_elapsed_is_dead(self):
        job = self._job(60)
        with mock.patch.object(dispatch, "_job_liveness", return_value="dead"):
            self.assertEqual(dispatch._dispatch_liveness(job, now=0), "dead")

    def test_open_with_transcript_activity_is_working(self):
        job = self._job(2)
        with mock.patch.object(dispatch, "_job_liveness", return_value="working"):
            self.assertEqual(dispatch._dispatch_liveness(job, now=0), "working")


class WorkingRegistryStageInductionTest(unittest.TestCase):

    def test_working_registry_row_stage_is_live_derived_not_raw_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            jobs_log = os.path.join(tmp, "jobs.log")
            wt = os.path.join(tmp, "wt")
            os.makedirs(wt, exist_ok=True)
            with open(jobs_log, "w") as f:
                f.write("\t".join([
                    "2026-07-10T01:00:00+00:00", "open", "repo", wt,
                    "docs-sync",
                    "capability=autopilot-note,mode=note,qa=light",
                ]) + "\n")
            with mock.patch.object(dispatch, "_scan_processes", return_value=[]), \
                 mock.patch.object(dispatch, "_live_claude_cwds", return_value={}), \
                 mock.patch.object(dispatch, "_job_liveness", return_value="working"), \
                 mock.patch.object(dispatch, "live_stage", return_value="analyze") as m_live:
                jobs = dispatch.collect(jobs_path=jobs_log)
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0].liveness, "working")
            self.assertEqual(jobs[0].stage, "analyze")
            m_live.assert_called()

    def test_non_code_plans_path_never_derives_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = os.path.join(tmp, ".agent_reports", "plans", "nearby_docs")
            os.makedirs(os.path.join(plan, "test_logs"))
            self.assertEqual(dispatch.live_stage(tmp, "nearby-docs", "note", "autopilot-note"), "note")

    def test_code_worker_derives_stage_from_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = os.path.join(tmp, ".agent_reports", "plans", "x_code-run")
            os.makedirs(os.path.join(plan, "test_logs"))
            with open(os.path.join(plan, "test_logs", "focused.log"), "w") as f:
                f.write("ok\n")
            self.assertEqual(dispatch.live_stage(tmp, "code-run", "code-test", "autopilot-code", "code-test"), "test")


class WideRowNoParentheticalTagTest(unittest.TestCase):

    def test_wide_row_name_zone_has_no_bracket_option_tag(self):
        job = DispatchJob(key="code", slug="top-conductor", depth=1, liveness="working",
                          mode="dev", qa="standard", qa_source="argv")
        segs = render._dispatch_row(job)
        name_text = next(text for text, key in segs if key == "name_dim")
        self.assertNotIn("(", name_text)
        self.assertNotIn(")", name_text)

    def test_wide_row_child_name_zone_shows_stage_label(self):
        child = DispatchJob(key="code-execute", slug="fleet-ui-v2-execute", depth=2,
                            parent_slug="fleet-ui-v2", worker_role="code-execute",
                            liveness="working")
        segs = render._dispatch_row(child)
        text = "".join(t for t, _k in segs)
        self.assertIn("exec fleet-ui-v2-execute", text)

    def test_wide_row_child_does_not_duplicate_parent_breadcrumb(self):
        child = DispatchJob(key="code-execute", slug="fleet-ui-v2-execute", depth=2,
                            parent_slug="fleet-ui-v2", worker_role="code-execute",
                            liveness="working", stage="exec")
        segs = render._dispatch_row(child)
        text = "".join(t for t, _k in segs)
        self.assertNotIn("plan", text)
        self.assertNotIn("test", text)
        self.assertIn("running", text)


class FoldingTest(unittest.TestCase):

    def _emit(self, conductor, children, show_all=False):
        render.set_show_all(show_all)
        try:
            lines = render._build_lines([], [conductor] + children, section="dispatch",
                                        narrow=False, malformed=0, layout="wide")
        finally:
            render.set_show_all(False)
        return "\n".join("".join(t for t, _k in ln) for ln in lines if ln)

    def test_only_working_child_gets_own_row_others_folded(self):
        conductor = DispatchJob(key="code", slug="fleet-ui-v2", depth=1, liveness="idle",
                                stage="exec", worker_role="capability-owner")
        plan_c = DispatchJob(key="code-plan", slug="fleet-ui-v2-plan", depth=2,
                             parent_slug="fleet-ui-v2", worker_role="code-plan", liveness="done")
        exec_c = DispatchJob(key="code-execute", slug="fleet-ui-v2-execute", depth=2,
                             parent_slug="fleet-ui-v2", worker_role="code-execute",
                             liveness="working")
        test_c = DispatchJob(key="code-test", slug="fleet-ui-v2-test", depth=2,
                             parent_slug="fleet-ui-v2", worker_role="code-test",
                             liveness="queued")
        text = self._emit(conductor, [plan_c, exec_c, test_c])
        self.assertIn("exec fleet-ui-v2-execute", text)
        self.assertNotIn("plan fleet-ui-v2-plan", text)
        self.assertNotIn("test fleet-ui-v2-test", text)

    def test_dead_children_fold_to_alert_by_default(self):
        conductor = DispatchJob(key="code", slug="fleet-ui-v2", depth=1, liveness="idle",
                                stage="exec", worker_role="capability-owner")
        dead_c = DispatchJob(key="code-test", slug="fleet-ui-v2-test", depth=2,
                             parent_slug="fleet-ui-v2", worker_role="code-test",
                             liveness="dead")
        text = self._emit(conductor, [dead_c])
        self.assertNotIn("test fleet-ui-v2-test", text)
        self.assertIn("dead fleet-ui-v2-test", text)

        all_text = self._emit(conductor, [dead_c], show_all=True)
        self.assertIn("test fleet-ui-v2-test", all_text)

    def test_stale_children_stay_visible(self):
        conductor = DispatchJob(key="code", slug="fleet-ui-v2", depth=1, liveness="idle",
                                stage="exec", worker_role="capability-owner")
        stale_c = DispatchJob(key="code-test", slug="fleet-ui-v2-test", depth=2,
                              parent_slug="fleet-ui-v2", worker_role="code-test",
                              liveness="stale")
        text = self._emit(conductor, [stale_c])
        self.assertIn("test fleet-ui-v2-test", text)

    def test_show_all_restores_folded_children(self):
        conductor = DispatchJob(key="code", slug="fleet-ui-v2", depth=1, liveness="idle",
                                stage="exec", worker_role="capability-owner")
        plan_c = DispatchJob(key="code-plan", slug="fleet-ui-v2-plan", depth=2,
                             parent_slug="fleet-ui-v2", worker_role="code-plan", liveness="done")
        text = self._emit(conductor, [plan_c], show_all=True)
        self.assertIn("plan fleet-ui-v2-plan", text)


class StageDoneMarkerTest(unittest.TestCase):

    def test_stage_segs_marks_past_stages_done(self):
        segs = render._stage_segs("code", "exec", working=False)
        text = "".join(t for t, _k in segs)
        self.assertIn("plan✓", text)
        self.assertNotIn("exec✓", text)
        self.assertNotIn("test✓", text)


class LayoutCutoffTest(unittest.TestCase):

    def test_narrow_below_138(self):
        self.assertEqual(render._layout_mode(120), "narrow")

    def test_wide_at_or_above_138(self):
        self.assertEqual(render._layout_mode(140), "wide")

    def test_stack_below_70(self):
        self.assertEqual(render._layout_mode(60), "stack")


class TitleCapTest(unittest.TestCase):

    def test_session_title_keeps_legacy_cap_without_terminal_width(self):
        long_title = "a" * 60
        sess = Session(harness="claude", pid=1, cwd="", slug="s",
                       title=long_title, liveness="idle")
        segs = render._session_row(sess, narrow=False)
        name_seg = segs[4][0]
        self.assertLessEqual(render._dw(name_seg), render._TITLE_MAX)

    def test_wide_session_title_expands_with_terminal_width(self):
        long_title = "responsive session title " * 8
        sess = Session(harness="codex", pid=1, cwd="", slug="s",
                       title=long_title, liveness="idle")
        name_width = render._wide_name_width(168)
        segs = render._session_row(sess, narrow=False, name_width=name_width)
        name_text = segs[4][0]
        self.assertGreater(name_width, render._NW_S)
        self.assertGreater(render._dw(name_text), render._TITLE_MAX)
        self.assertLessEqual(render._dw(name_text), name_width)

    def test_wide_session_title_clips_cjk_on_display_cell_boundary(self):
        sess = Session(harness="codex", pid=1, cwd="", slug="s",
                       title="반응형세션제목" * 20, liveness="idle")
        name_width = render._wide_name_width(168)
        segs = render._session_row(sess, narrow=False, name_width=name_width)
        name_text = segs[4][0]
        self.assertLessEqual(render._dw(name_text), name_width)
        self.assertNotEqual(name_text[-1:], "")

    def test_narrow_session_title_reserves_suffixes(self):
        sess = Session(harness="codex", pid=1, cwd="", branch="feature/long",
                       slug="s", title="responsive session title " * 8, liveness="idle")
        l1, _l2 = render._session_row_2line(sess, term_width=60)
        self.assertLessEqual(sum(render._dw(text) for text, _key in l1), 54)
        text = "".join(part for part, _key in l1)
        self.assertIn("feature/long", text)

    def test_dispatch_composed_label_plus_slug_stays_capped_in_wide_column(self):
        job = DispatchJob(key="code-execute", slug="a-very-long-dispatch-session-slug-name",
                          depth=2, parent_slug="p", worker_role="code-execute",
                          liveness="working")
        segs = render._dispatch_row(job, name_width=render._wide_name_width(168))
        name_text = next(text for text, key in segs if key == "name_dim")
        self.assertLessEqual(len(name_text), render._TITLE_MAX)


if __name__ == "__main__":
    unittest.main(verbosity=2)
