#!/usr/bin/env python3
"""F-18 (loop·drill·mem-워커 귀속 정밀화) — hermetic unit tests.

Runnable directly or via `python3 -m unittest fleet.tests.test_f18_attribution -v` (from `tools/`).
"""
import os
import sys
import unittest
from unittest import mock

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from fleet import render                       # noqa: E402
from fleet.collectors import codex, dispatch, procscan  # noqa: E402
from fleet.model import DispatchJob, Session    # noqa: E402


class ProcscanTaggingTest(unittest.TestCase):
    """F-18b: scan() environ 마커 → Session.mem_worker."""

    def _scan_one(self, environ):
        ps_line = "123\tclaude\t00:05\t/usr/bin/claude"
        with mock.patch.object(procscan, "_ps_lines", return_value=[ps_line]), \
             mock.patch.object(procscan, "_read_cwd", return_value=("/home/u/proj", False)), \
             mock.patch.object(procscan, "_pid_ttys", return_value={}), \
             mock.patch.object(procscan, "_detached_ttys", return_value=set()), \
             mock.patch.object(procscan, "_is_detached", return_value=False), \
             mock.patch.object(procscan, "read_environ", return_value=environ):
            sessions = procscan.scan()
        self.assertEqual(len(sessions), 1)
        return sessions[0]

    def test_mem_distill_marker_tags_true(self):
        s = self._scan_one({"MEM_DISTILL": "1"})
        self.assertTrue(s.mem_worker)

    def test_title_refresh_marker_tags_true(self):
        s = self._scan_one({"FLEET_TITLE_REFRESH": "1"})
        self.assertTrue(s.mem_worker)

    def test_no_marker_tags_false(self):
        s = self._scan_one({})
        self.assertFalse(s.mem_worker)

    def test_environ_read_failure_degrades_to_false(self):
        # read_environ() already returns {} on OSError — same code path as no-marker.
        s = self._scan_one({})
        self.assertFalse(s.mem_worker)

    def test_cross_harness_dispatch_markers_hide_children_but_not_ordinary_codex(self):
        s = self._scan_one({"AGENT_DISPATCH_CHILD": "1"})
        self.assertTrue(s.is_child)
        self.assertTrue(self._scan_one({"AGENT_DISPATCH_DEPTH": "2"}).is_child)
        self.assertFalse(self._scan_one({}).is_child)


class CodexRolloutAttributionTest(unittest.TestCase):
    def test_two_same_cwd_sessions_remain_unknown_when_fallback_is_ambiguous(self):
        sessions = [Session(harness="codex", pid=1, cwd="/work/repo", elapsed_min=1),
                    Session(harness="codex", pid=2, cwd="/work/repo", elapsed_min=1)]
        with mock.patch.object(codex, "_index", return_value={"/work/repo": ["/r/one", "/r/two"]}), \
             mock.patch.object(codex, "_sid", side_effect=lambda p: {"/r/one": "one", "/r/two": "two"}[p]), \
             mock.patch.object(codex, "_rollout_meta", return_value={"timestamp": "2024-07-13T00:00:00Z"}), \
             mock.patch.object(codex.time, "time", return_value=1720828860):
            codex._FALLBACK_CLAIMS.update(ts=0, sids=set())
            self.assertEqual([codex._fallback_rollout(s, "/home/codex") for s in sessions], [None, None])

    def test_root_rollout_beats_open_subagent_rollout(self):
        fd_links = {"3": "/home/codex/sessions/a/rollout-2026-07-13T00-00-00-11111111-1111-1111-1111-111111111111.jsonl",
                    "4": "/home/codex/sessions/a/rollout-2026-07-13T00-00-00-22222222-2222-2222-2222-222222222222.jsonl"}
        with mock.patch.object(codex.os, "listdir", return_value=list(fd_links)), \
             mock.patch.object(codex.os, "readlink", side_effect=lambda p: fd_links[p.rsplit("/", 1)[-1]]), \
             mock.patch.object(codex.os.path, "realpath", side_effect=lambda p: p), \
             mock.patch.object(codex, "_rollout_meta", side_effect=lambda p: {
                 "cwd": "/work/repo",
                 "source": {"subagent": {"thread_spawn": {}}} if "2222" in p else "cli",
             }):
            path = codex._proc_rollout(99, "/work/repo", "/home/codex")
        self.assertIn("11111111", path)


class RenderDuplicateParentTest(unittest.TestCase):
    def test_duplicate_session_id_renders_child_tree_once(self):
        sessions = [Session(harness="codex", pid=1, cwd="/work/repo", session_id="same", slug="repo", liveness="working"),
                    Session(harness="codex", pid=2, cwd="/work/repo", session_id="same", slug="repo", liveness="working")]
        job = DispatchJob(key="autopilot-code", slug="child", cwd="/work/child", parent_sid="same", is_child=True,
                          harness="codex", mode="dev/refactor", liveness="working")
        lines = render._build_lines(sessions, [job], section="both", narrow=False, malformed=0, layout="wide")
        text = "\n".join("".join(part for part, _key in line) for line in lines if line)
        self.assertEqual(text.count("dev/refactor"), 1)


class RenderMemExclusionTest(unittest.TestCase):
    """F-18b: render._build_lines 기본 제외·요약·`a`-토글 노출."""

    def tearDown(self):
        render.set_show_all(False)

    def _sessions(self):
        mem = Session(harness="claude", pid=1, cwd="/home/u/proj", slug="mem-worker",
                      title="distiller", liveness="working", mem_worker=True)
        normal = Session(harness="claude", pid=2, cwd="/home/u/proj", slug="work",
                         title="normal work", liveness="working")
        return mem, normal

    def _text(self, lines):
        return "\n".join("".join(t for t, _k in ln) for ln in lines if ln)

    def test_default_excludes_mem_from_pulse_and_rows(self):
        mem, normal = self._sessions()
        render.set_show_all(False)
        lines = render._build_lines([mem, normal], [], section="fleet", narrow=False,
                                    malformed=0, layout="wide")
        text = self._text(lines)
        self.assertIn("1 working", text)
        self.assertNotIn("distiller", text)   # mem-worker session row itself not shown
        self.assertIn("🧠", text)   # legend/group badge summary still present

    def test_show_all_reveals_mem_row(self):
        mem, normal = self._sessions()
        render.set_show_all(True)
        lines = render._build_lines([mem, normal], [], section="fleet", narrow=False,
                                    malformed=0, layout="wide")
        text = self._text(lines)
        self.assertIn("mem ", text)

    def test_pure_mem_only_group_folds_but_legend_shows_total(self):
        mem = Session(harness="claude", pid=1, cwd="/home/u/onlymem", slug="mem-worker",
                     title="distiller", liveness="working", mem_worker=True)
        render.set_show_all(False)
        lines = render._build_lines([mem], [], section="fleet", narrow=False,
                                    malformed=0, layout="wide")
        text = self._text(lines)
        self.assertIn("🧠 1", text)


class DrillCaseExtractionTest(unittest.TestCase):
    """F-18a: registry slug / tmp cwd → drill case name."""

    def test_case_from_slug(self):
        self.assertEqual(
            dispatch._drill_case_from_slug("drill-claude-g_stage_dispatch-20260711160000-12345"),
            "g_stage_dispatch")

    def test_case_from_cwd(self):
        self.assertEqual(
            dispatch._drill_case_from_cwd("/tmp/drill-g_stage_dispatch-Ab3d/repo"),
            "g_stage_dispatch")

    def test_non_drill_slug_returns_none(self):
        self.assertIsNone(dispatch._drill_case_from_slug("fleet-ui-v2-execute"))

    def test_non_drill_cwd_returns_none(self):
        self.assertIsNone(dispatch._drill_case_from_cwd("/home/u/proj/repo"))


class DrillReconcileTest(unittest.TestCase):
    """F-18a: registry row(정본) + proc drill loop job → 1행 병합."""

    def test_merges_matching_case_and_absorbs_proc_liveness(self):
        registry = DispatchJob(key="drill", slug="drill-claude-CASE-20260711160000-12345",
                               cwd="/tmp/drill-CASE-x/repo", pid=None, source="jobs",
                               liveness="queued")
        proc = DispatchJob(key="drill", slug="drill", worker_role="CASE",
                           cwd="/tmp/drill-CASE-x/repo", pid=999, liveness="working",
                           source="proc")
        jobs = dispatch._reconcile_drill_rows([registry, proc])
        self.assertEqual(len(jobs), 1)
        self.assertIs(jobs[0], registry)
        self.assertEqual(jobs[0].pid, 999)
        self.assertEqual(jobs[0].liveness, "working")

    def test_case_mismatch_keeps_both_rows(self):
        registry = DispatchJob(key="drill", slug="drill-claude-CASEA-20260711160000-12345",
                               cwd="/tmp/drill-CASEA-x/repo", pid=None, source="jobs",
                               liveness="queued")
        proc = DispatchJob(key="drill", slug="drill", worker_role="CASEB",
                           cwd="/tmp/drill-CASEB-y/repo", pid=999, liveness="working",
                           source="proc")
        jobs = dispatch._reconcile_drill_rows([registry, proc])
        self.assertEqual(len(jobs), 2)

    def test_registry_cwd_not_tmp_drill_skips_merge(self):
        registry = DispatchJob(key="drill", slug="drill-claude-CASE-20260711160000-12345",
                               cwd="/home/u/other/repo", pid=None, source="jobs",
                               liveness="queued")
        proc = DispatchJob(key="drill", slug="drill", worker_role="CASE",
                           cwd="/tmp/drill-CASE-x/repo", pid=999, liveness="working",
                           source="proc")
        jobs = dispatch._reconcile_drill_rows([registry, proc])
        self.assertEqual(len(jobs), 2)


if __name__ == "__main__":
    unittest.main()
