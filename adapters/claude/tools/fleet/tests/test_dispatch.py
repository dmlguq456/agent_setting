#!/usr/bin/env python3
"""Hermetic unit tests — tools/fleet registry-home split (Phase A), cwd-fallback
enrichment (Phase B), claude.py runtime-home (Phase C). Stdlib unittest, zero external
deps. Every OS/process access is monkeypatched (unittest.mock) — no test here touches the
real ps/proc/home.

Runnable directly (`python3 tools/fleet/tests/test_dispatch.py`) or via
`python3 -m unittest` / `python3 -m unittest fleet.tests.test_dispatch -v` (from `tools/`).
"""
import os
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

# Make `tools/` importable so `from fleet.collectors import ...` resolves regardless of
# invocation style. This file lives one level deeper than fleet.py
# (tools/fleet/tests/test_dispatch.py vs tools/fleet/fleet.py), so THREE dirname() hops
# (mirroring fleet.py:20's two-hop insert) reach `tools/`.
_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from fleet.collectors import dispatch  # noqa: E402
from fleet.collectors import claude    # noqa: E402
from fleet.collectors import opencode  # noqa: E402
from fleet import render             # noqa: E402
from fleet import collectors as fleet_collectors  # noqa: E402
from fleet.model import DispatchJob, Session  # noqa: E402


class RenderDispatchPresentationTest(unittest.TestCase):

    def test_depth_two_prefix_indents_without_repeated_arrow(self):
        top = DispatchJob(key="code", slug="top", depth=1)
        nested = DispatchJob(key="code", slug="nested", depth=2)

        self.assertEqual(render._dispatch_prefix(top), "↳ ")
        self.assertEqual(render._dispatch_prefix(nested), "    ")
        self.assertNotIn("↳", render._dispatch_prefix(nested))

    def test_dispatch_tag_labels_path_before_assurance(self):
        job = DispatchJob(key="plan", worker_role="planner", intensity="thorough")
        tag, _width = render._mq_tag(
            "review", None, "qa_standard", profile=render._dispatch_role_suffix(job, "~standard")
        )
        text = "".join(part for part, _key in tag)

        self.assertEqual(text, " (review·thr/planner/qa:~std)")
        self.assertNotIn("path:", text)
        self.assertNotIn("role:", text)
        self.assertNotIn("check:", text)

    def test_dispatch_two_line_compacts_long_session_name(self):
        job = DispatchJob(
            key="code",
            slug="smoke-claude-dispatch-with-overlong-name",
            harness="claude",
            mode="qa/test",
            qa="quick",
            qa_source="jobslog",
            intensity="quick",
            worker_role="verifier",
        )
        l1, _l2 = render._dispatch_row_2line(job)
        text = "".join(part for part, _key in l1)

        self.assertIn("smoke-claude-disp…", text)
        self.assertNotIn("smoke-claude-dispatch-with-overlong-name", text)

    def test_loop_dispatch_profile_omits_duplicate_case_role(self):
        job = DispatchJob(
            key="drill",
            slug="g8_design_verifier_breakage",
            mode="loop/drill",
            worker_role="g8_design_verifier_breakage",
        )

        self.assertIsNone(render._dispatch_profile(job))




# --- D1: _registry_home() / _jobs_path() precedence ---
class RegistryHomeTest(unittest.TestCase):

    def test_agent_home_wins_over_claude_home(self):
        with mock.patch.dict(os.environ,
                              {"AGENT_HOME": "/agent-home", "CLAUDE_HOME": "/claude-home"},
                              clear=True):
            self.assertEqual(dispatch._registry_home(), "/agent-home")

    def test_claude_home_used_when_agent_home_absent(self):
        with mock.patch.dict(os.environ, {"CLAUDE_HOME": "/claude-home"}, clear=True):
            self.assertEqual(dispatch._registry_home(), "/claude-home")

    def test_agent_setting_isdir_fallback(self):
        # Regression guard: the OLD _jobs_path/_proj_home fallback skipped this
        # $HOME/agent_setting step entirely (plan Current State §2) — this is the step
        # that must now be honored when no env var is set and the dir exists.
        with mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch("fleet.collectors.dispatch.os.path.expanduser",
                         side_effect=lambda p: p.replace("~", "/home/u")), \
             mock.patch("fleet.collectors.dispatch.os.path.isdir", return_value=True):
            self.assertEqual(dispatch._registry_home(), "/home/u/agent_setting")

    def test_dot_claude_fallback_when_agent_setting_absent(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch("fleet.collectors.dispatch.os.path.expanduser",
                         side_effect=lambda p: p.replace("~", "/home/u")), \
             mock.patch("fleet.collectors.dispatch.os.path.isdir", return_value=False):
            self.assertEqual(dispatch._registry_home(), "/home/u/.claude")

    def test_jobs_path_override_beats_everything(self):
        with mock.patch.dict(os.environ,
                              {"AGENT_DISPATCH_JOBS": "/env/jobs.log", "AGENT_HOME": "/agent-home"},
                              clear=True):
            self.assertEqual(dispatch._jobs_path(override="/override/jobs.log"),
                              "/override/jobs.log")

    def test_jobs_path_env_beats_registry_home(self):
        with mock.patch.dict(os.environ,
                              {"AGENT_DISPATCH_JOBS": "/env/jobs.log", "AGENT_HOME": "/agent-home"},
                              clear=True):
            self.assertEqual(dispatch._jobs_path(), "/env/jobs.log")

    def test_jobs_path_uses_registry_home(self):
        with mock.patch.dict(os.environ, {"AGENT_HOME": "/agent-home"}, clear=True):
            self.assertEqual(dispatch._jobs_path(),
                              os.path.join("/agent-home", ".dispatch", "jobs.log"))

    def test_candidate_jobs_paths_env_is_single_explicit_registry(self):
        with mock.patch.dict(os.environ, {"AGENT_DISPATCH_JOBS": "/env/jobs.log"}, clear=True), \
             mock.patch("fleet.collectors.dispatch.os.path.exists", return_value=True):
            self.assertEqual(dispatch._candidate_jobs_paths(), ["/env/jobs.log"])

    def test_candidate_jobs_paths_default_adds_legacy_claude_registry(self):
        def fake_expanduser(path):
            return path.replace("~", "/home/u")

        with mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch.object(dispatch, "_jobs_path",
                               return_value="/home/u/agent_setting/.dispatch/jobs.log"), \
             mock.patch("fleet.collectors.dispatch.os.path.expanduser",
                        side_effect=fake_expanduser), \
             mock.patch("fleet.collectors.dispatch.os.path.exists", return_value=True):
            self.assertEqual(dispatch._candidate_jobs_paths(), [
                "/home/u/agent_setting/.dispatch/jobs.log",
                "/home/u/.claude/.dispatch/jobs.log",
            ])

    def test_candidate_jobs_paths_skips_duplicate_legacy_registry(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch.object(dispatch, "_jobs_path",
                               return_value="/home/u/.claude/.dispatch/jobs.log"), \
             mock.patch("fleet.collectors.dispatch.os.path.expanduser",
                        return_value="/home/u/.claude/.dispatch/jobs.log"), \
             mock.patch("fleet.collectors.dispatch.os.path.exists", return_value=True):
            self.assertEqual(dispatch._candidate_jobs_paths(), [
                "/home/u/.claude/.dispatch/jobs.log",
            ])


# --- D2: runtime home (_proj_home / claude._home) must NOT follow the registry home ---
class RuntimeHomeIndependenceTest(unittest.TestCase):

    def test_dispatch_proj_home_ignores_agent_home(self):
        with mock.patch.dict(os.environ, {"AGENT_HOME": "/agent-home"}, clear=True), \
             mock.patch("fleet.collectors.dispatch.os.path.expanduser",
                         side_effect=lambda p: p.replace("~", "/home/u")):
            self.assertEqual(dispatch._proj_home(), "/home/u/.claude")

    def test_claude_home_ignores_agent_home(self):
        with mock.patch.dict(os.environ, {"AGENT_HOME": "/agent-home"}, clear=True), \
             mock.patch("fleet.collectors.claude.os.path.expanduser",
                         side_effect=lambda p: p.replace("~", "/home/u")):
            self.assertEqual(claude._home(), "/home/u/.claude")

    def test_dispatch_proj_home_honors_claude_config_dir(self):
        with mock.patch.dict(os.environ,
                              {"AGENT_HOME": "/agent-home", "CLAUDE_CONFIG_DIR": "/cfg"},
                              clear=True):
            self.assertEqual(dispatch._proj_home(), "/cfg")

    def test_claude_home_honors_claude_config_dir(self):
        with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": "/cfg"}, clear=True):
            self.assertEqual(claude._home(), "/cfg")


class OpenCodeContextTest(unittest.TestCase):

    def test_last_request_context_uses_latest_nonzero_message_tokens(self):
        con = sqlite3.connect(":memory:")
        con.execute("CREATE TABLE message (session_id text, time_updated integer, data text)")
        con.execute("INSERT INTO message VALUES (?, ?, ?)", (
            "sid", 3, '{"role":"assistant","tokens":{"input":0,"cache":{"read":0,"write":0}}}',
        ))
        con.execute("INSERT INTO message VALUES (?, ?, ?)", (
            "sid", 2, '{"role":"assistant","tokens":{"input":14,"cache":{"read":182016,"write":7},"output":703}}',
        ))

        self.assertEqual(opencode._last_request_context(con, "sid"), 182037)
        con.close()

    def test_opencode_enrich_uses_message_context_before_closing_db(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "opencode.db")
            con = sqlite3.connect(db)
            con.execute("""
                CREATE TABLE session (
                    id text, slug text, agent text, model text, cost real,
                    tokens_input integer, tokens_output integer, tokens_reasoning integer,
                    time_updated integer, parent_id text, directory text
                )
            """)
            con.execute("CREATE TABLE message (session_id text, time_updated integer, data text)")
            con.execute("INSERT INTO session VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                "sid", "shiny-wizard", "build", '{"id":"glm-5.2"}', 0.0,
                5862526, 0, 0, 1234567890, None, "/repo",
            ))
            con.execute("INSERT INTO message VALUES (?, ?, ?)", (
                "sid", 2, '{"role":"assistant","tokens":{"input":14,"cache":{"read":182016,"write":7},"output":703}}',
            ))
            con.commit()
            con.close()

            sess = Session(harness="opencode", pid=1, cwd="/repo")
            with mock.patch.dict(os.environ, {"OPENCODE_DB": db}, clear=True), \
                 mock.patch.object(opencode, "_model_ctx_limit", return_value=2_000_000):
                opencode.enrich(sess)

        self.assertEqual(sess.ctx_pct, 9)


# --- D3: cwd-fallback enrichment (fully hermetic) ---
class CwdFallbackEnrichmentTest(unittest.TestCase):

    def test_proc_scanned_drill_loop_surfaces_parent_and_current_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "drill-post-phase2.log")
            with open(log_path, "w") as f:
                f.write("▶ g7_semantic_deterministic_boundary (work=/tmp/drill-g7-aaaa)\n")
                f.write("  → PASS(g)\n")
                f.write("▶ growing:g8b_design_verifier_clean_pass (work=/tmp/drill-g8b-bbbb)\n")

            ps_lines = [
                "1001 zsh 00:58 /usr/bin/zsh -c bash ~/.claude/loops/drill/run.sh > %s 2>&1" % log_path,
                "1002 bash 00:57 bash /home/u/.claude/loops/drill/run.sh",
            ]

            with mock.patch("fleet.collectors.procscan._ps_lines", return_value=ps_lines), \
                 mock.patch("fleet.collectors.dispatch.os.readlink",
                            return_value="/home/u/agent_setting"), \
                 mock.patch("fleet.collectors.procscan.read_environ", return_value={
                     "CLAUDE_CODE_SESSION_ID": "parent-sid",
                     "CLAUDE_CODE_CHILD_SESSION": "1",
                     "CLAUDECODE": "1",
                     "PWD": "/home/u/agent_setting",
                 }):
                jobs = dispatch._scan_processes()

        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job.key, "drill")
        self.assertEqual(job.slug, "g8b_design_verifier_clean_pass")
        self.assertEqual(job.mode, "loop/drill")
        self.assertEqual(job.stage, "running")
        self.assertEqual(job.cwd, "/home/u/agent_setting")
        self.assertEqual(job.parent_sid, "parent-sid")
        self.assertEqual(job.parent_cwd, "/home/u/agent_setting")
        self.assertTrue(job.is_child)
        self.assertEqual(job.harness, "claude")
        self.assertEqual(job.worker_role, "g8b_design_verifier_clean_pass")

    def test_collect_reads_current_and_legacy_jobs_logs_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            current = os.path.join(tmp, "current.jobs.log")
            legacy = os.path.join(tmp, "legacy.jobs.log")
            current_wt = os.path.join(tmp, "current-wt")
            legacy_wt = os.path.join(tmp, "legacy-wt")
            os.makedirs(current_wt, exist_ok=True)
            os.makedirs(legacy_wt, exist_ok=True)
            with open(current, "w") as f:
                f.write("\t".join([
                    "2026-07-05T01:00:00+00:00", "open", "repo", current_wt,
                    "current-codex-job",
                    "capability=autopilot-code,mode=dev,qa=standard,harness=codex",
                ]) + "\n")
            with open(legacy, "w") as f:
                f.write("\t".join([
                    "2026-07-05T01:00:01+00:00", "open", "repo", legacy_wt,
                    "legacy-claude-drill",
                    "capability=drill,mode=loop/drill,qa=quick,harness=claude",
                ]) + "\n")

            with mock.patch.object(dispatch, "_candidate_jobs_paths",
                                   return_value=[current, legacy]), \
                 mock.patch.object(dispatch, "_scan_processes", return_value=[]), \
                 mock.patch.object(dispatch, "_dispatch_liveness",
                                   side_effect=lambda *a, **k: "working"):
                jobs = dispatch.collect()

            self.assertEqual({j.slug for j in jobs}, {
                "current-codex-job",
                "legacy-claude-drill",
            })
            self.assertEqual(dispatch.collect.last_malformed, 0)

    def test_collect_enriches_tokenless_log_job(self):
        """Case 1 — collect() end-to-end: a harness=None jobs.log row whose worktree
        matches a live (mocked) claude -p cwd gets harness/pid/model backfilled."""
        with tempfile.TemporaryDirectory() as tmp:
            worktree = os.path.join(tmp, "worktree")
            os.makedirs(worktree, exist_ok=True)
            jobs_log = os.path.join(tmp, "jobs.log")
            row = "\t".join([
                "2026-07-05T01:00:00+00:00", "open", "testrepo", worktree,
                "test-slug", "capability=autopilot-code,mode=dev,qa=quick",
            ])
            with open(jobs_log, "w") as f:
                f.write(row + "\n")

            # Key normalized with the SAME helper collect()'s lookup uses, so the tempdir
            # path matches even if realpath rewrites it (plan D3 note).
            norm_key = dispatch._norm_cwd(worktree)

            with mock.patch.object(dispatch, "_scan_processes", return_value=[]), \
                 mock.patch.object(dispatch, "_live_claude_cwds",
                                    return_value={norm_key: 4242}), \
                 mock.patch.object(dispatch, "_claude_job_model", return_value="Opus 4.8"), \
                 mock.patch.object(dispatch, "_job_liveness",
                                    side_effect=lambda *a, **k: "working"):
                # live_stage() is intentionally left unmocked — it only walks the tmp
                # worktree (no plans/ dir there → falls back to the raw status), which
                # stays hermetic (plan D3 note).
                jobs = dispatch.collect(jobs_path=jobs_log)

            self.assertEqual(len(jobs), 1)
            job = jobs[0]
            self.assertEqual(job.harness, "claude")
            self.assertEqual(job.pid, 4242)
            self.assertEqual(job.model, "Opus 4.8")

    def test_argv_matched_pid_excluded_from_cwd_scan(self):
        """Case 2 — an already argv-matched (proc-scanned) pid is passed into
        _live_claude_cwds's exclude_pids, so it is never re-resolved via cwd. A distinct
        tokenless open row is present so the candidate guard in collect() actually runs the
        cwd scan (an all-argv-matched collect legitimately skips the second `ps`)."""
        with tempfile.TemporaryDirectory() as tmp:
            jobs_log = os.path.join(tmp, "jobs.log")
            worktree = os.path.join(tmp, "wt")
            with open(jobs_log, "w") as f:
                f.write("2026-07-05T01:00:00+09:00\topen\trepo\t%s\ttokenless-slug\t"
                        "capability=autopilot-code,mode=dev,qa=standard\n" % worktree)

            proc_job = dispatch.DispatchJob(
                key="code", slug="proc-slug", cwd=tmp, pid=4242, harness="claude",
            )
            with mock.patch.object(dispatch, "_scan_processes", return_value=[proc_job]), \
                 mock.patch.object(dispatch, "_live_claude_cwds",
                                    return_value={}) as m_live, \
                 mock.patch.object(dispatch, "_job_liveness",
                                    side_effect=lambda *a, **k: "working"):
                dispatch.collect(jobs_path=jobs_log)

            m_live.assert_called_once()
            self.assertEqual(m_live.call_args.args[0], {4242})

    def test_no_cwd_scan_when_no_tokenless_candidate(self):
        """Guard — when every job is already argv-matched (no log job with harness=None+cwd),
        collect() skips the extra `ps` spawn: _live_claude_cwds is never called."""
        with tempfile.TemporaryDirectory() as tmp:
            jobs_log = os.path.join(tmp, "jobs.log")
            open(jobs_log, "w").close()  # empty log → no candidate log jobs
            proc_job = dispatch.DispatchJob(
                key="code", slug="proc-slug", cwd=tmp, pid=4242, harness="claude",
            )
            with mock.patch.object(dispatch, "_scan_processes", return_value=[proc_job]), \
                 mock.patch.object(dispatch, "_live_claude_cwds",
                                    return_value={}) as m_live, \
                 mock.patch.object(dispatch, "_job_liveness",
                                    side_effect=lambda *a, **k: "working"):
                dispatch.collect(jobs_path=jobs_log)
            m_live.assert_not_called()

    def test_p_token_gate_and_exclude_filtering(self):
        """Case 3 (helper-level) — _live_claude_cwds keeps only non-excluded exact `-p`
        token rows, rejecting an interactive `claude --resume` row. procscan._ps_lines
        carries no cwd column (pid comm etime args only — procscan.py:53), so cwd is
        ALWAYS resolved via os.readlink("/proc/<pid>/cwd"); that seam is mocked here too
        (mapping each synthetic pid to a distinct tmp cwd) so this case touches NO real
        /proc or sessions path — without it the helper would hit the real /proc/<pid>/cwd,
        get OSError, fall back to the real ~/.claude/sessions/<pid>.json, get None, and
        skip the pid entirely (returned dict {}), which would make this assertion
        unprovable (plan D3 round-2 fix)."""
        ps_lines = [
            "1001 claude 00:10 claude -p --model opus",   # -p token, EXCLUDED pid
            "1002 claude 00:05 claude -p --model opus",   # -p token, kept
            "1003 claude 00:20 claude --resume",          # interactive — no -p token
        ]
        cwd_by_proc_path = {
            "/proc/1001/cwd": "/tmp/fleet-test-cwd-1001",
            "/proc/1002/cwd": "/tmp/fleet-test-cwd-1002",
            "/proc/1003/cwd": "/tmp/fleet-test-cwd-1003",
        }

        def fake_readlink(path):
            if path in cwd_by_proc_path:
                return cwd_by_proc_path[path]
            raise OSError(2, "No such file or directory", path)

        with mock.patch("fleet.collectors.procscan._ps_lines", return_value=ps_lines), \
             mock.patch("fleet.collectors.dispatch.os.readlink", side_effect=fake_readlink):
            result = dispatch._live_claude_cwds({1001})

        expected_key = dispatch._norm_cwd("/tmp/fleet-test-cwd-1002")
        self.assertEqual(result, {expected_key: 1002})


# --- D4: _job_liveness profile-path assembly (string check, no real filesystem) ---
class JobLivenessPathAssemblyTest(unittest.TestCase):

    def test_profile_branch_composes_under_registry_home(self):
        calls = []

        def fake_listdir(path):
            calls.append(path)
            raise OSError

        with mock.patch.object(dispatch, "_registry_home", return_value="/REGISTRY"), \
             mock.patch.object(dispatch, "_proj_home", return_value="/RUNTIME"), \
             mock.patch("fleet.collectors.dispatch.os.listdir", side_effect=fake_listdir):
            result = dispatch._job_liveness("/some/jcwd", now=0, profile="lab-runner",
                                             slug="my-slug")

        expected = os.path.join("/REGISTRY", ".dispatch", "homes", "my-slug.lab-runner",
                                 "projects", dispatch._enc("/some/jcwd"))
        self.assertEqual(calls, [expected])
        self.assertEqual(result, "dead")

    def test_non_profile_branch_composes_under_proj_home(self):
        calls = []

        def fake_listdir(path):
            calls.append(path)
            raise OSError

        with mock.patch.object(dispatch, "_registry_home", return_value="/REGISTRY"), \
             mock.patch.object(dispatch, "_proj_home", return_value="/RUNTIME"), \
             mock.patch("fleet.collectors.dispatch.os.listdir", side_effect=fake_listdir):
            result = dispatch._job_liveness("/some/jcwd", now=0, profile=None, slug=None)

        expected = os.path.join("/RUNTIME", "projects", dispatch._enc("/some/jcwd"))
        self.assertEqual(calls, [expected])
        self.assertEqual(result, "dead")


# --- D5: depth-2 registry metadata ---
class DepthTwoRegistryMetadataTest(unittest.TestCase):


    def test_parent_sid_groups_drill_temp_job_under_parent_project(self):
        from fleet.model import Session
        sess = Session(harness="codex", pid=1, cwd="/work/agent_setting", session_id="parent-sid",
                       slug="agent_setting", liveness="working")
        job = DispatchJob(key="drill", slug="drill-g9", cwd="/tmp/drill-g9-abcd/repo",
                          parent_sid="parent-sid", is_child=True, harness="codex",
                          mode="loop/drill", qa="quick", qa_source="jobslog",
                          liveness="working", worker_role="g9_cross_harness_depth2_dispatch")
        lines = render._build_lines([sess], [job], section="both", narrow=False, malformed=0,
                                    layout="wide")
        text = "\n".join("".join(part for part, _key in line) for line in lines if line)

        self.assertIn("agent_setting/", text)
        self.assertIn("loop/drill·g9", text)
        self.assertNotIn("drill:g9", text)

    def test_parent_cwd_fallback_groups_drill_temp_job_without_matching_sid(self):
        from fleet.model import Session
        sess = Session(harness="codex", pid=1, cwd="/work/agent_setting", session_id="runtime-sid",
                       slug="agent_setting", liveness="working")
        job = DispatchJob(key="drill", slug="drill-g9", cwd="/tmp/drill-g9-abcd/repo",
                          parent_sid="stale-sid", parent_cwd="/work/agent_setting", is_child=True,
                          harness="codex", mode="loop/drill", qa="quick", qa_source="jobslog",
                          liveness="working", worker_role="g9_cross_harness_depth2_dispatch")
        lines = render._build_lines([sess], [job], section="both", narrow=False, malformed=0,
                                    layout="wide")
        text = "\n".join("".join(part for part, _key in line) for line in lines if line)

        self.assertIn("agent_setting/", text)
        self.assertIn("loop/drill·g9", text)
        self.assertNotIn("drill:g9", text)
        self.assertNotIn(" main", text)

    def test_unparented_drill_temp_job_groups_under_loops(self):
        job = DispatchJob(key="drill", slug="drill-g9", cwd="/tmp/drill-g9-abcd/repo",
                          harness="codex", mode="loop/drill", qa="quick", qa_source="jobslog",
                          liveness="working", worker_role="g9_cross_harness_depth2_dispatch")
        lines = render._build_lines([], [job], section="both", narrow=False, malformed=0,
                                    layout="wide")
        text = "\n".join("".join(part for part, _key in line) for line in lines if line)

        self.assertIn("loops/", text)
        self.assertNotIn("drill:g9", text)


    def test_dispatch_child_session_matching_jobs_log_cwd_is_hidden(self):
        from fleet.model import Session
        parent = Session(harness="codex", pid=1, cwd="/work/agent_setting",
                         session_id="parent-sid", slug="agent_setting", liveness="working")
        child_session = Session(harness="codex", pid=2, cwd="/tmp/drill-g9-abcd/repo",
                                session_id="child-sid", slug="repo", liveness="working")
        job = DispatchJob(key="drill", slug="drill-g9", cwd="/tmp/drill-g9-abcd/repo",
                          parent_sid="parent-sid", parent_cwd="/work/agent_setting",
                          is_child=True, harness="codex", mode="loop/drill", qa="quick",
                          qa_source="jobslog", liveness="working",
                          worker_role="g9_cross_harness_depth2_dispatch")

        fleet_collectors._mark_dispatch_child_sessions([parent, child_session], [job])
        self.assertFalse(parent.is_child)
        self.assertTrue(child_session.is_child)

        lines = render._build_lines([parent, child_session], [job], section="both",
                                    narrow=False, malformed=0, layout="wide")
        text = "\n".join("".join(part for part, _key in line) for line in lines if line)
        self.assertIn("agent_setting/", text)
        self.assertIn("loop/drill·g9", text)
        self.assertNotIn("drill:g9", text)

    def test_dispatch_child_session_marker_does_not_hide_parent_cwd(self):
        from fleet.model import Session
        parent = Session(harness="codex", pid=1, cwd="/work/agent_setting",
                         session_id="parent-sid", slug="agent_setting", liveness="working")
        job = DispatchJob(key="drill", slug="drill-g9", cwd="/work/agent_setting",
                          parent_sid="parent-sid", parent_cwd="/work/agent_setting",
                          is_child=True, harness="codex", mode="loop/drill", qa="quick",
                          qa_source="jobslog", liveness="working")

        fleet_collectors._mark_dispatch_child_sessions([parent], [job])
        self.assertFalse(parent.is_child)

    def test_drill_jobs_log_row_is_visible_as_loop_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            jobs_log = os.path.join(tmp, "jobs.log")
            worktree = os.path.join(tmp, "drill-g6_worktree_dispatch-abcd", "repo")
            os.makedirs(worktree, exist_ok=True)
            row = "\t".join([
                "2026-07-05T01:00:00+00:00", "open", "repo", worktree,
                "drill-codex-g6_worktree_dispatch-010000-1234",
                "capability=drill,mode=loop/drill,qa=quick,intensity=quick,"
                "depth=1,harness=codex,worker_role=g6_worktree_dispatch,owner=drill",
            ])
            with open(jobs_log, "w") as f:
                f.write(row + "\n")

            with mock.patch.object(dispatch, "_scan_processes", return_value=[]), \
                 mock.patch.object(dispatch, "_live_claude_cwds", return_value={}), \
                 mock.patch.object(dispatch, "_dispatch_liveness",
                                    side_effect=lambda *a, **k: "working"):
                jobs = dispatch.collect(jobs_path=jobs_log)

            self.assertEqual(len(jobs), 1)
            job = jobs[0]
            self.assertEqual(job.key, "drill")
            self.assertEqual(job.mode, "loop/drill")
            self.assertEqual(job.qa, "quick")
            self.assertEqual(job.harness, "codex")
            self.assertEqual(job.worker_role, "g6_worktree_dispatch")
            self.assertEqual(job.capability_owner, "drill")
            self.assertEqual(job.status, "open")
            self.assertEqual(job.source, "jobs")

    def test_jobs_log_pipe_metadata_surfaces_depth_two_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            jobs_log = os.path.join(tmp, "jobs.log")
            worktree = os.path.join(tmp, "wt")
            os.makedirs(worktree, exist_ok=True)
            row = "\t".join([
                "2026-07-05T01:00:00+00:00", "open", "repo", worktree,
                "child-worker",
                "capability=autopilot-code,mode=verify,qa=adversarial,"
                "depth=2,harness=codex,parent=owner-job,parent_sid=codex-main,intensity=adversarial,"
                "worker_role=verifier,owner=autopilot-code",
            ])
            with open(jobs_log, "w") as f:
                f.write(row + "\n")

            with mock.patch.object(dispatch, "_scan_processes", return_value=[]), \
                 mock.patch.object(dispatch, "_live_claude_cwds", return_value={}), \
                 mock.patch.object(dispatch, "_job_liveness",
                                    side_effect=lambda *a, **k: "working"):
                jobs = dispatch.collect(jobs_path=jobs_log)

            self.assertEqual(len(jobs), 1)
            job = jobs[0]
            self.assertEqual(job.key, "code")
            self.assertEqual(job.mode, "verify")
            self.assertEqual(job.qa, "adversarial")
            self.assertEqual(job.depth, 2)
            self.assertEqual(job.harness, "codex")
            self.assertEqual(job.parent_slug, "owner-job")
            self.assertEqual(job.parent_sid, "codex-main")
            self.assertIsNone(job.parent_cwd)
            self.assertTrue(job.is_child)
            self.assertEqual(job.intensity, "adversarial")
            self.assertEqual(job.worker_role, "verifier")
            self.assertEqual(job.capability_owner, "autopilot-code")

    def test_legacy_jobs_log_infers_harness_from_runtime_model_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            jobs_log = os.path.join(tmp, "jobs.log")
            worktree = os.path.join(tmp, "wt")
            os.makedirs(worktree, exist_ok=True)
            rows = [
                "\t".join([
                    "2026-07-05T01:00:00+00:00", "open", "repo", worktree,
                    "legacy-codex",
                    "capability=sync-skills,mode=qa/test,qa=quick,intensity=quick,"
                    "depth=1,model=gpt-test,reasoning=low,approval=never",
                ]),
                "\t".join([
                    "2026-07-05T01:00:01+00:00", "open", "repo", worktree,
                    "legacy-opencode",
                    "capability=sync-skills,mode=qa/test,qa=quick,intensity=quick,"
                    "depth=1,model=provider/test,variant=low",
                ]),
                "\t".join([
                    "2026-07-05T01:00:02+00:00", "open", "repo", worktree,
                    "legacy-claude",
                    "capability=sync-skills,mode=ops/verification,qa=quick,intensity=quick,"
                    "depth=1,model=sonnet,effort=medium",
                ]),
            ]
            with open(jobs_log, "w") as f:
                f.write("\n".join(rows) + "\n")

            with mock.patch.object(dispatch, "_scan_processes", return_value=[]), \
                 mock.patch.object(dispatch, "_live_claude_cwds", return_value={}), \
                 mock.patch.object(dispatch, "_dispatch_liveness",
                                    side_effect=lambda *a, **k: "working"):
                jobs = dispatch.collect(jobs_path=jobs_log)

            by_slug = {j.slug: j for j in jobs}
            self.assertEqual(by_slug["legacy-codex"].harness, "codex")
            self.assertEqual(by_slug["legacy-opencode"].harness, "opencode")
            self.assertEqual(by_slug["legacy-claude"].harness, "claude")


if __name__ == "__main__":
    unittest.main(verbosity=2)
