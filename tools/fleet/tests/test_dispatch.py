#!/usr/bin/env python3
"""Hermetic unit tests — tools/fleet registry-home split (Phase A), cwd-fallback
enrichment (Phase B), claude.py runtime-home (Phase C). Stdlib unittest, zero external
deps. Every OS/process access is monkeypatched (unittest.mock) — no test here touches the
real ps/proc/home.

Runnable directly (`python3 tools/fleet/tests/test_dispatch.py`) or via
`python3 -m unittest` / `python3 -m unittest fleet.tests.test_dispatch -v` (from `tools/`).
"""
import json
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
from fleet.model import ATTEMPT_CLASSIFIER_SOURCE, DispatchJob, Session  # noqa: E402


class RenderDispatchPresentationTest(unittest.TestCase):

    def test_cross_harness_child_does_not_inherit_parent_model(self):
        parent = Session(harness="codex", pid=1, cwd="/work/repo",
                         session_id="codex-parent", slug="repo", model="gpt-5.6-sol",
                         effort="xhigh", liveness="working")
        child = DispatchJob(key="audit", slug="claude-child", cwd="/work/child",
                            parent_sid="codex-parent", is_child=True, harness="claude",
                            mode="qa/code-review", liveness="working")

        lines = render._build_lines([parent], [child], section="both", narrow=False,
                                    malformed=0, layout="wide")
        text = "\n".join("".join(part for part, _key in line) for line in lines if line)

        self.assertEqual(text.count("gpt-5.6-sol"), 1)

    def test_depth_two_prefix_nests_the_spawn_arrow_deeper(self):
        # user 2026-07-16: every depth fans out with the same ↳ arrow, two cells deeper
        # per level, and the ladder starts one level in ("분사 세션의 화살표를 좀 더
        # 들여쓰자") — the depth-1 arrow sits under the parent's text, not on its glyph
        # column. Widths are (depth+1)*2.
        top = DispatchJob(key="code", slug="top", depth=1)
        nested = DispatchJob(key="code", slug="nested", depth=2)

        self.assertEqual(render._dispatch_prefix(top), "  ↳ ")
        self.assertEqual(render._dispatch_prefix(nested), "    ↳ ")
        self.assertEqual(len(render._dispatch_prefix(nested)), 6)

    def test_dispatch_role_suffix_has_no_qa_token(self):
        # qa axis retired (CONVENTIONS §1.1); intensity moved to the dial's paren knob
        # group (2026-07-20 hierarchical dial) — this suffix is the ROLE tail only now.
        job = DispatchJob(key="plan", worker_role="planner", intensity="thorough")
        suffix = render._dispatch_role_suffix(job)

        self.assertEqual(suffix, "planner")
        self.assertNotIn("qa:", suffix)

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

    def test_runtime_watch_loop_is_recognized(self):
        match = dispatch._LOOPS.search("bash loops/runtime-watch.sh --probe")

        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "runtime-watch")

    def test_shared_cwd_requires_exact_parent_session_id(self):
        sessions = [
            Session(harness="codex", pid=1, cwd="/work/repo",
                    session_id="codex-thread", slug="repo", liveness="working"),
            Session(harness="claude", pid=2, cwd="/work/repo",
                    session_id="claude-thread", slug="repo", liveness="idle"),
        ]

        def rendered(parent_sid):
            job = DispatchJob(key="code", slug="owner", cwd="/work/owner-wt",
                              parent_sid=parent_sid, parent_cwd="/work/repo", is_child=True,
                              harness="codex", mode="debug", qa="standard",
                              qa_source="jobslog", liveness="working")
            lines = render._build_lines(sessions, [job], section="both", narrow=False,
                                        malformed=0, layout="wide")
            return "\n".join("".join(part for part, _key in line)
                             for line in lines if line)

        self.assertNotIn("(orphan)", rendered("codex-thread"))
        self.assertIn("(orphan)", rendered("synthetic-thread"))




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

    def _make_db(self, tmp, with_title_col):
        db = os.path.join(tmp, "opencode.db")
        con = sqlite3.connect(db)
        cols = ("id text, slug text, agent text, model text, cost real, "
                "tokens_input integer, tokens_output integer, tokens_reasoning integer, "
                "time_updated integer, parent_id text, directory text")
        if with_title_col:
            cols += ", title text"
        con.execute("CREATE TABLE session (%s)" % cols)
        vals = ["sid", "shiny-wizard", "build", '{"id":"glm-5.2"}', 0.0,
                0, 0, 0, 1234567890, None, "/repo"]
        if with_title_col:
            vals.append("개발 서버 시작")
        con.execute("INSERT INTO session VALUES (%s)" %
                     ",".join("?" * len(vals)), vals)
        con.commit()
        con.close()
        return db

    def test_opencode_enrich_fills_title_when_column_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = self._make_db(tmp, with_title_col=True)
            sess = Session(harness="opencode", pid=1, cwd="/repo")
            with mock.patch.dict(os.environ, {"OPENCODE_DB": db}, clear=True):
                opencode.enrich(sess)
        self.assertEqual(sess.title, "개발 서버 시작")
        self.assertEqual(sess.slug, "shiny-wizard")

    def test_opencode_enrich_tolerates_missing_title_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = self._make_db(tmp, with_title_col=False)
            sess = Session(harness="opencode", pid=1, cwd="/repo")
            with mock.patch.dict(os.environ, {"OPENCODE_DB": db}, clear=True):
                opencode.enrich(sess)
        self.assertIsNone(sess.title)
        self.assertEqual(sess.slug, "shiny-wizard")


# --- D3: cwd-fallback enrichment (fully hermetic) ---
class CwdFallbackEnrichmentTest(unittest.TestCase):

    def test_proc_dispatch_unit_env_is_additive_and_legacy_absence_is_none(self):
        ps_lines = ["123 claude 00:08 claude -p /autopilot-code --mode dev"]
        base_env = {
            "AGENT_SESSION_ROLE": "worker",
            "AGENT_DISPATCH_WORKER_TYPE": "stage",
            "AGENT_DISPATCH_ASSIGNED_CONTRACT": "code-test",
        }

        def scan(env):
            with mock.patch("fleet.collectors.procscan._ps_lines", return_value=ps_lines), \
                 mock.patch("fleet.collectors.dispatch.os.readlink", return_value="/tmp/unit-wt"), \
                 mock.patch("fleet.collectors.procscan.read_environ", return_value=env), \
                 mock.patch("fleet.collectors.procscan.read_proc_start", return_value="11"), \
                 mock.patch.object(dispatch, "_claude_job_model", return_value="claude-test"):
                return dispatch._scan_processes()[0]

        current = scan({**base_env, "AGENT_DISPATCH_UNIT": "verify"})
        legacy = scan(base_env)
        self.assertEqual(current.assigned_contract, "code-test")
        self.assertEqual(current.worker_type, "stage")
        self.assertEqual(current.unit, "verify")
        self.assertIsNone(legacy.unit)

    def test_mem_distiller_prompt_is_not_a_dispatch_job(self):
        ps_lines = [
            "123 claude 00:08 claude -p /autopilot-apply session summary --model opus"
        ]
        with mock.patch("fleet.collectors.procscan._ps_lines", return_value=ps_lines), \
             mock.patch("fleet.collectors.procscan.read_environ", return_value={
                 "MEM_DISTILL": "1",
                 "AGENT_DISPATCH_PARENT_SESSION_ID": "codex-parent",
             }), \
             mock.patch("fleet.collectors.dispatch.os.readlink") as m_readlink:
            jobs = dispatch._scan_processes()

        self.assertEqual(jobs, [])
        m_readlink.assert_not_called()

    def test_portable_worker_marker_marks_unregistered_loop_as_child(self):
        ps_lines = ["1002 bash 00:57 bash /home/u/.claude/loops/study.sh"]
        with mock.patch("fleet.collectors.procscan._ps_lines", return_value=ps_lines), \
             mock.patch("fleet.collectors.dispatch.os.readlink", return_value="/home/u/agent_setting"), \
             mock.patch("fleet.collectors.procscan.read_environ", return_value={
                 "AGENT_SESSION_ROLE": "worker",
                 "CLAUDECODE": "1",
             }):
            jobs = dispatch._scan_processes()
        self.assertEqual(len(jobs), 1)
        self.assertTrue(jobs[0].is_child)

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


class CodexJobLivenessPathTest(unittest.TestCase):

    def test_nested_worker_uses_worktree_local_codex_home(self):
        with tempfile.TemporaryDirectory() as tmp:
            worktree = os.path.join(tmp, "nested-worktree")
            sessions = os.path.join(
                worktree, ".dispatch", "codex-home", "sessions", "2026", "07", "13"
            )
            os.makedirs(sessions)
            rollout = os.path.join(sessions, "rollout-test.jsonl")
            with open(rollout, "w", encoding="utf-8") as f:
                f.write(json.dumps({"payload": {"cwd": worktree}}) + "\n")

            now = os.path.getmtime(rollout)
            with mock.patch.object(
                dispatch, "_codex_home", return_value=os.path.join(tmp, "missing")
            ):
                result = dispatch._codex_job_liveness(
                    worktree, now=now, profile=None, slug="nested-child"
                )

        self.assertEqual(result, "working")

    def test_profile_job_does_not_fall_back_to_worktree_local_home(self):
        with mock.patch.object(dispatch, "_registry_home", return_value="/REGISTRY"):
            result = dispatch._codex_sessions_dirs(
                "/worktree", profile="lab", slug="nested-child"
            )

        self.assertEqual(result, [
            "/REGISTRY/.dispatch/homes/nested-child.lab/sessions"
        ])


class CodexAttemptIdentityTest(unittest.TestCase):
    """Exact registry identity outranks another retry's cwd-wide rollout mtime."""

    def test_scan_preserves_pid_start_and_attempt_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            jobs_log = os.path.join(tmp, "jobs.log")
            with open(jobs_log, "w", encoding="utf-8") as f:
                f.write(
                    "2026-07-16T00:00:00+00:00\topen\trepo\t%s\tretry-r5\t"
                    "capability=autopilot-code,harness=codex,depth=2,"
                    "route_id=rt-a,route_node=test,pid=4242,pid_start=777,pid_scope=namespace-local,"
                    "attempt_id=att-0123456789abcdef\n" % tmp
                )
            rows, malformed = dispatch._scan_jobs_log(jobs_log, set())

        self.assertEqual(malformed, 0)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].pid, 4242)
        self.assertEqual(rows[0].proc_start, "777")
        self.assertEqual(rows[0].pid_scope, "namespace-local")
        self.assertEqual(rows[0].attempt_id, "att-0123456789abcdef")
        self.assertEqual(rows[0].registry_order, 0)

    def test_exited_retries_cannot_share_fresh_rollout_liveness(self):
        jobs = [
            DispatchJob(key="code-test", slug="test-r%d" % retry, cwd="/work/wt",
                        source="jobs", status="open", harness="codex", depth=2,
                        route_id="rt-a", route_node="test", pid=4200 + retry,
                        proc_start=str(700 + retry),
                        attempt_id="att-%016x" % retry)
            for retry in range(2, 6)
        ]
        with mock.patch.object(dispatch, "_job_transcript_signal", return_value="working"), \
             mock.patch("fleet.collectors.dispatch.os.path.exists", return_value=False):
            states = [dispatch._dispatch_liveness(job, now=1000.0, track=False) for job in jobs]

        self.assertEqual(states, ["dead"] * 4)
        self.assertTrue(all(job.state_evidence["tier"] == 2 for job in jobs))

    def test_matching_attempt_identity_beats_stale_rollout(self):
        job = DispatchJob(key="code-test", slug="test-r5", cwd="/work/wt",
                          source="jobs", status="open", harness="codex", pid=4242,
                          proc_start="777", attempt_id="att-0123456789abcdef")
        with mock.patch.object(dispatch, "_job_transcript_signal", return_value="stale"), \
             mock.patch("fleet.collectors.dispatch.os.path.exists", return_value=True), \
             mock.patch.object(dispatch.procscan, "read_proc_start", return_value="777"):
            state = dispatch._dispatch_liveness(job, now=1000.0, track=False)

        self.assertEqual(state, "working")
        self.assertEqual(job.state_evidence["tier"], 2)
        self.assertEqual(job.state_evidence["classifier_source"], ATTEMPT_CLASSIFIER_SOURCE)
        self.assertEqual(job.state_evidence["attempt"]["attempt_id"], "att-0123456789abcdef")

    def test_attempt_heartbeat_is_exposed_through_the_same_classifier(self):
        with tempfile.TemporaryDirectory() as tmp:
            heartbeat_dir=os.path.join(tmp,".dispatch","heartbeats");os.makedirs(heartbeat_dir)
            attempt="att-heartbeat00001"
            with open(os.path.join(heartbeat_dir,attempt+".json"),"w",encoding="utf-8") as out:
                json.dump({"phase":"test","sequence":4,"evidence_digest":"d","updated_at":900},out)
            job=DispatchJob(key="code-test",slug="heartbeat",cwd="/work/wt",source="jobs",
                            status="open",harness="codex",pid=4242,proc_start="777",
                            attempt_id=attempt,route_id="rt-a",route_node="test")
            with mock.patch.object(dispatch,"_registry_home",return_value=tmp),\
                 mock.patch.object(dispatch,"_job_transcript_signal",return_value="stale"),\
                 mock.patch("fleet.collectors.dispatch.os.path.exists",return_value=True),\
                 mock.patch.object(dispatch.procscan,"read_proc_start",return_value="777"):
                state=dispatch._dispatch_liveness(job,now=1000.0,track=False)
        self.assertEqual(state,"working")
        self.assertEqual(job.state_evidence["classifier_source"],ATTEMPT_CLASSIFIER_SOURCE)
        self.assertEqual(job.state_evidence["attempt"]["heartbeat"]["sequence"],4)
        self.assertTrue(job.state_evidence["attempt"]["progress_fingerprint"])

    def test_namespace_local_pid_uses_exact_fresh_heartbeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            heartbeat_dir = os.path.join(tmp, ".dispatch", "heartbeats")
            os.makedirs(heartbeat_dir)
            attempt = "att-namespace-fresh"
            with open(os.path.join(heartbeat_dir, attempt + ".json"), "w", encoding="utf-8") as out:
                json.dump({"attempt_id": attempt, "route_id": "rt-a", "route_node": "test",
                           "phase": "tool", "sequence": 3, "updated_at": 990}, out)
            job = DispatchJob(key="code-test", slug="namespace", cwd="/work/wt", source="jobs",
                              status="open", harness="codex", pid=437, proc_start="777",
                              pid_scope="namespace-local", attempt_id=attempt,
                              route_id="rt-a", route_node="test")
            with mock.patch.object(dispatch, "_registry_home", return_value=tmp), \
                 mock.patch.object(dispatch, "_job_transcript_signal", return_value="stale"), \
                 mock.patch("fleet.collectors.dispatch.os.path.exists", return_value=False):
                state = dispatch._dispatch_liveness(job, now=1000.0, track=False)

        self.assertEqual(state, "working")
        self.assertEqual(job.state_evidence["attempt"]["source"], "heartbeat")
        self.assertEqual(job.state_evidence["attempt"]["pid_scope"], "namespace-local")

    def test_namespace_local_visible_pid_is_live_without_route_or_heartbeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = DispatchJob(key="code-execute", slug="namespace-visible", cwd="/work/wt",
                              source="jobs", status="open", harness="codex", pid=437,
                              proc_start="777", pid_scope="namespace-local",
                              attempt_id="att-namespace-visible")
            with mock.patch.object(dispatch, "_registry_home", return_value=tmp), \
                 mock.patch.object(dispatch, "_job_transcript_signal", return_value="stale"), \
                 mock.patch("fleet.collectors.dispatch.os.path.exists", return_value=True), \
                 mock.patch.object(dispatch.procscan, "read_proc_start", return_value="777"):
                state = dispatch._dispatch_liveness(job, now=1000.0, track=False)

        self.assertEqual(state, "working")
        self.assertEqual(job.state_evidence["attempt"]["source"], "proc")
        self.assertIn("visible and live", job.state_evidence["attempt"]["rule"])

    def test_namespace_local_terminal_heartbeat_is_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            heartbeat_dir = os.path.join(tmp, ".dispatch", "heartbeats")
            os.makedirs(heartbeat_dir)
            attempt = "att-namespace-terminal"
            with open(os.path.join(heartbeat_dir, attempt + ".json"), "w", encoding="utf-8") as out:
                json.dump({"attempt_id": attempt, "route_id": "rt-a", "route_node": "test",
                           "phase": "terminal", "sequence": 4, "updated_at": 995}, out)
            job = DispatchJob(key="code-test", slug="namespace", cwd="/work/wt", source="jobs",
                              status="open", harness="codex", pid=437, proc_start="777",
                              pid_scope="namespace-local", attempt_id=attempt,
                              route_id="rt-a", route_node="test")
            with mock.patch.object(dispatch, "_registry_home", return_value=tmp), \
                 mock.patch.object(dispatch, "_job_transcript_signal", return_value="working"), \
                 mock.patch("fleet.collectors.dispatch.os.path.exists", return_value=False):
                state = dispatch._dispatch_liveness(job, now=1000.0, track=False)

        self.assertEqual(state, "done")
        self.assertIn("terminal heartbeat", job.state_evidence["attempt"]["rule"])

    def test_namespace_local_stale_heartbeat_never_uses_cwd_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            heartbeat_dir = os.path.join(tmp, ".dispatch", "heartbeats")
            os.makedirs(heartbeat_dir)
            attempt = "att-namespace-stale"
            with open(os.path.join(heartbeat_dir, attempt + ".json"), "w", encoding="utf-8") as out:
                json.dump({"attempt_id": attempt, "route_id": "rt-a", "route_node": "test",
                           "phase": "tool", "sequence": 2, "updated_at": 1}, out)
            job = DispatchJob(key="code-test", slug="namespace", cwd="/work/wt", source="jobs",
                              status="open", harness="codex", pid=437, proc_start="777",
                              pid_scope="namespace-local", attempt_id=attempt,
                              route_id="rt-a", route_node="test")
            with mock.patch.object(dispatch, "_registry_home", return_value=tmp), \
                 mock.patch.object(dispatch, "_job_transcript_signal", return_value="working"), \
                 mock.patch("fleet.collectors.dispatch.os.path.exists", return_value=False):
                state = dispatch._dispatch_liveness(job, now=1000.0, track=False)

        self.assertEqual(state, "unknown")
        self.assertEqual(job.state_evidence["tier"], 2)
        self.assertEqual(job.state_evidence["attempt"]["state"], "unknown")

    def test_namespace_local_process_exit_beats_fresh_unrelated_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            heartbeat_dir = os.path.join(tmp, ".dispatch", "heartbeats")
            watchdog_dir = os.path.join(tmp, ".dispatch", "watchdog")
            os.makedirs(heartbeat_dir)
            os.makedirs(watchdog_dir)
            attempt = "att-namespace-exited"
            with open(os.path.join(heartbeat_dir, attempt + ".json"), "w", encoding="utf-8") as out:
                json.dump({"attempt_id": attempt, "route_id": "rt-a", "route_node": "test",
                           "phase": "launch", "sequence": 1, "updated_at": 995}, out)
            with open(os.path.join(watchdog_dir, attempt + ".json"), "w", encoding="utf-8") as out:
                json.dump({"terminal_action": "process-exited", "observed_at": 996}, out)
            job = DispatchJob(key="code-test", slug="namespace", cwd="/work/wt",
                              source="jobs", status="open", harness="codex", pid=437,
                              proc_start="777", pid_scope="namespace-local",
                              attempt_id=attempt, route_id="rt-a", route_node="test")
            with mock.patch.object(dispatch, "_registry_home", return_value=tmp), \
                 mock.patch.object(dispatch, "_job_transcript_signal", return_value="working"), \
                 mock.patch("fleet.collectors.dispatch.os.path.exists", return_value=False):
                state = dispatch._dispatch_liveness(job, now=1000.0, track=False)

        self.assertEqual(state, "dead")
        self.assertEqual(job.state_evidence["attempt"]["source"], "terminal-observation")
        self.assertIn("process-exited", job.state_evidence["attempt"]["rule"])

    def test_legacy_row_without_process_identity_keeps_rollout_fallback(self):
        job = DispatchJob(key="code-test", slug="legacy", cwd="/work/wt",
                          source="jobs", status="open", harness="codex")
        with mock.patch.object(dispatch, "_job_transcript_signal", return_value="working"):
            state = dispatch._dispatch_liveness(job, now=1000.0, track=False)

        self.assertEqual(state, "working")
        self.assertEqual(job.state_evidence["tier"], 3)

    def test_exact_registered_attempt_without_pid_ignores_cwd_transcript(self):
        job = DispatchJob(key="code-test", slug="registered", cwd="/work/wt",
                          source="jobs", status="open", harness="codex",
                          attempt_id="att-registered-no-pid",
                          route_id="rt-a", route_node="test")
        with mock.patch.object(dispatch, "_job_transcript_signal", return_value="working"):
            state = dispatch._dispatch_liveness(job, now=1000.0, track=False)

        self.assertEqual(state, "unknown")
        self.assertEqual(job.state_evidence["tier"], 2)
        self.assertIn("no process identity", job.state_evidence["rule"])

    def test_latest_retry_owns_route_node_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            jobs_log = os.path.join(tmp, "jobs.log")
            with open(jobs_log, "w", encoding="utf-8") as f:
                for retry in range(2, 6):
                    f.write(
                        "2026-07-16T00:0%d:00+00:00\topen\trepo\t%s\ttest-r%d\t"
                        "capability=autopilot-code,harness=codex,"
                        "attempt_schema_version=2,dispatch_depth=2,transport=headless,"
                        "execution_surface=registered-headless,registered_worker=1,"
                        "fallback_hop=same-harness-headless,"
                        "route_id=rt-a,route_node=test,attempt_id=att-%016x\n"
                        % (retry, tmp, retry, retry)
                    )

            evidence = dispatch._scan_route_nodes([jobs_log])

        self.assertEqual(evidence["rt-a"]["test"]["slug"], "test-r5")

    def test_default_render_hides_superseded_dead_retries(self):
        jobs = [
            DispatchJob(key="code-test", slug="test-r%d" % retry, cwd="/work/wt",
                        source="jobs", status="open", harness="codex", depth=2,
                        route_id="rt-a", route_node="test",
                        liveness="working" if retry == 5 else "dead")
            for retry in range(2, 6)
        ]
        render.set_show_all(False)
        lines = render._build_lines([], jobs, section="dispatch", narrow=False,
                                    malformed=0, layout="wide")
        text = "\n".join("".join(part for part, _key in line) for line in lines if line)
        body = "\n".join(line for line in text.splitlines() if "alert" not in line)

        self.assertIn("test-r5", body)
        for retry in range(2, 5):
            self.assertNotIn("test-r%d" % retry, body)
        self.assertIn("3 dead jobs", text)  # history remains visible as a diagnostic summary

    def test_default_render_hides_older_working_attempt(self):
        older = DispatchJob(key="code-test", slug="test-r4", cwd="/work/wt",
                            source="jobs", status="open", harness="codex", depth=2,
                            route_id="rt-a", route_node="test", liveness="working",
                            attempt_id="att-0000000000000004", registry_order=4)
        newest = DispatchJob(key="code-test", slug="test-r5", cwd="/work/wt",
                             source="jobs", status="open", harness="codex", depth=2,
                             route_id="rt-a", route_node="test", liveness="working",
                             attempt_id="att-0000000000000005", registry_order=5)
        render.set_show_all(False)
        lines = render._build_lines([], [older, newest], section="dispatch", narrow=False,
                                    malformed=0, layout="wide")
        text = "\n".join("".join(part for part, _key in line) for line in lines if line)
        self.assertIn("test-r5", text)
        self.assertNotIn("test-r4", text)

    def test_canonical_registry_attempt_beats_later_legacy_file_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            current = os.path.join(tmp, "current.jobs.log")
            legacy = os.path.join(tmp, "legacy.jobs.log")
            with open(current, "w", encoding="utf-8") as f:
                f.write(
                    "2026-07-16T01:00:00+00:00\topen\trepo\t%s\ttest-current\t"
                    "capability=autopilot-code,harness=codex,route_id=rt-a,"
                    "route_node=test,attempt_id=att-current000001\n" % tmp
                )
            with open(legacy, "w", encoding="utf-8") as f:
                for index in range(20):
                    f.write(
                        "2026-07-15T00:%02d:00+00:00\tdone\trepo\t%s\tlegacy-%d\t"
                        "capability=autopilot-code\n" % (index, tmp, index)
                    )
                f.write(
                    "2026-07-15T02:00:00+00:00\topen\trepo\t%s\ttest-legacy\t"
                    "capability=autopilot-code,harness=codex,route_id=rt-a,"
                    "route_node=test,attempt_id=att-legacy0000001\n" % tmp
                )
            with mock.patch.object(dispatch, "_candidate_jobs_paths", return_value=[current, legacy]), \
                 mock.patch.object(dispatch, "_scan_processes", return_value=[]), \
                 mock.patch.object(dispatch, "_dispatch_liveness", return_value="working"):
                jobs = dispatch.collect()

        visible = render._current_attempt_jobs(jobs)
        self.assertEqual([job.slug for job in visible], ["test-current"])
        self.assertEqual({job.slug: job.registry_priority for job in jobs}, {
            "test-current": 0,
            "test-legacy": 1,
        })

    def test_canonical_terminal_evidence_beats_legacy_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            current = os.path.join(tmp, "current.jobs.log")
            legacy = os.path.join(tmp, "legacy.jobs.log")
            with open(current, "w", encoding="utf-8") as f:
                f.write(
                    "2026-07-16T01:00:00+00:00\tdone\trepo\t-\ttest-current\t"
                    "attempt_schema_version=2,dispatch_depth=2,transport=headless,"
                    "execution_surface=registered-headless,registered_worker=1,"
                    "fallback_hop=same-harness-headless,attempt_id=att-current,"
                    "route_id=rt-a,route_node=test,note=current\n"
                )
            with open(legacy, "w", encoding="utf-8") as f:
                f.write(
                    "2026-07-15T01:00:00+00:00\tkilled\trepo\t-\ttest-legacy\t"
                    "route_id=rt-a,route_node=test,note=legacy\n"
                )

            evidence = dispatch._scan_route_nodes([current, legacy])

        self.assertEqual(evidence["rt-a"]["test"]["slug"], "test-current")
        self.assertEqual(evidence["rt-a"]["test"]["note"], "current")


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

    def test_unparented_drill_temp_job_groups_under_fixture(self):
        job = DispatchJob(key="drill", slug="drill-g9", cwd="/tmp/drill-g9-abcd/repo",
                          harness="codex", mode="loop/drill", qa="quick", qa_source="jobslog",
                          liveness="working", worker_role="g9_cross_harness_depth2_dispatch")
        lines = render._build_lines([], [job], section="both", narrow=False, malformed=0,
                                    layout="wide")
        text = "\n".join("".join(part for part, _key in line) for line in lines if line)

        self.assertIn("drill:g9/", text)
        self.assertNotIn("loops/", text)


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

    def test_existing_marked_child_same_cwd_protects_interactive_roots(self):
        from fleet.model import Session
        root_a = Session(harness="claude", pid=1, cwd="/work/agent_setting",
                         session_id="root-a", slug="agent-setting-a", liveness="working")
        root_b = Session(harness="claude", pid=2, cwd="/work/agent_setting",
                         session_id="root-b", slug="agent-setting-b", liveness="idle")
        worker = Session(harness="claude", pid=3, cwd="/work/agent_setting",
                         session_id="worker", slug="agent-setting-worker", liveness="working",
                         is_child=True)
        job = DispatchJob(key="apply", slug="agent_setting", cwd="/work/agent_setting",
                          parent_sid="worker-parent", is_child=True, harness="claude",
                          mode="presentation", liveness="working")

        fleet_collectors._mark_dispatch_child_sessions([root_a, root_b, worker], [job])

        self.assertFalse(root_a.is_child)
        self.assertFalse(root_b.is_child)
        self.assertTrue(worker.is_child)

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
                "worker_type=review,assigned_contract=code-test,"
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
            self.assertEqual(job.worker_type, "review")
            self.assertEqual(job.assigned_contract, "code-test")
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
                    "capability=audit,mode=qa/test,qa=quick,intensity=quick,"
                    "depth=1,model=gpt-test,reasoning=low,approval=never",
                ]),
                "\t".join([
                    "2026-07-05T01:00:01+00:00", "open", "repo", worktree,
                    "legacy-opencode",
                    "capability=audit,mode=qa/test,qa=quick,intensity=quick,"
                    "depth=1,model=provider/test,variant=low",
                ]),
                "\t".join([
                    "2026-07-05T01:00:02+00:00", "open", "repo", worktree,
                    "legacy-claude",
                    "capability=audit,mode=ops/verification,qa=quick,intensity=quick,"
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


# --- fleet UI v2: SD-F4 tolerant pipe parsing + SD-F1~F3 stage rows + F-9~F-13 readability ---
class TolerantPipeParsingTest(unittest.TestCase):
    """SD-F4 continuation tokenizer — comma/space tolerant, value-internal-space safe."""

    def test_parse_pipe_space_separated_row(self):
        fields = dispatch._parse_pipe_meta("capability=code a=1 b=2 c=3")
        self.assertEqual(fields["a"], "1")
        self.assertEqual(fields["b"], "2")
        self.assertEqual(fields["c"], "3")
        self.assertEqual(fields["capability"], "code")

    def test_parse_pipe_value_internal_space(self):
        fields = dispatch._parse_pipe_meta("model_role=deep maker,model=opus")
        self.assertEqual(fields["model_role"], "deep maker")
        self.assertEqual(fields["model"], "opus")

    def test_parse_pipe_continuation_then_field(self):
        # N2 — a continuation (value-internal space) followed by MORE key=value pairs must not
        # get swallowed into the continuation; the next `=`-bearing token starts a fresh pair.
        fields = dispatch._parse_pipe_meta(
            "capability=code,model_role=deep maker,model=opus,qa=quick")
        self.assertEqual(fields["capability"], "code")
        self.assertEqual(fields["model_role"], "deep maker")
        self.assertEqual(fields["model"], "opus")
        self.assertEqual(fields["qa"], "quick")

    def test_parse_pipe_unknown_key_ignored(self):
        fields = dispatch._parse_pipe_meta("capability=code,bogus=nonsense,qa=quick")
        self.assertEqual(fields["capability"], "code")
        self.assertEqual(fields["qa"], "quick")
        # unknown key is stored but nothing reads it — the point is it doesn't crash and
        # doesn't corrupt the known fields.
        self.assertEqual(fields.get("bogus"), "nonsense")

    def test_canonical_comma_pipe_still_parses_unchanged(self):
        # R1 regression guard alongside the existing D5 class — continuation tokenizer must
        # not disturb the canonical comma-only form.
        fields = dispatch._parse_pipe_meta(
            "capability=autopilot-code,mode=verify,qa=adversarial,depth=2,"
            "worker_role=verifier,owner=autopilot-code")
        self.assertEqual(fields["_name"], "code")
        self.assertEqual(fields["mode"], "verify")
        self.assertEqual(fields["qa"], "adversarial")
        self.assertEqual(fields["depth"], "2")
        self.assertEqual(fields["worker_role"], "verifier")
        self.assertEqual(fields["owner"], "autopilot-code")


class StageWorkerRenderTest(unittest.TestCase):
    """SD-F1/F-15 — child name is humanized; its options cell names the assigned skill."""

    def test_stage_worker_rows_render_stage_labels(self):
        cases = [
            ("code-plan", "plan"),
            ("code-execute", "exec"),
            ("code-test", "test"),
            ("code-report", "report"),
        ]
        for worker_role, label in cases:
            # D2 (test_round1.md): a live depth-2 stage worker's `j.key` IS its capability
            # (collectors/dispatch.py `pname = meta["capability"]`, e.g. "code-execute") — the
            # old fixture used key="code" (the depth-1 conductor's track key), which masked the
            # D1 raw-prefix leak since "code: " looks like a legitimate label already.
            job = DispatchJob(key=worker_role, slug="stage-job", depth=2, worker_role=worker_role,
                              intensity="strong", liveness="working")
            lines = render._build_lines([], [job], section="both", narrow=False, malformed=0,
                                        layout="wide")
            text = "\n".join("".join(part for part, _key in line) for line in lines if line)
            self.assertIn(label + " stage-job", text)
            self.assertIn(worker_role + "(strong)", text)
            # the raw capability key must never leak as a breadcrumb prefix (D1) — only its
            # humanized _STAGE_ROLE label may drive the micro-status. It is intentionally
            # present in the options cell as the child's assigned skill.
            self.assertNotIn(worker_role + ":", text)

    def test_g_case_prefix_general_rule_matches_known_drill_cases(self):
        # N1 — the general rule replacing the removed g6/g9 hardcoded _ROLE_SHORT entries must
        # still shrink live drill/loop case ids to their gN prefix.
        self.assertEqual(render._short_role("g9_cross_harness_depth2_dispatch"), "g9")
        self.assertEqual(render._short_role("g6_worktree_dispatch"), "g6")
        self.assertEqual(render._short_role("g8b_design_verifier_clean_pass"), "g8b")


class QuickDispatchRenderTest(unittest.TestCase):
    def test_quick_depth_one_renders_single_quick_exec_breadcrumb(self):
        job = DispatchJob(key="code", slug="quick-worker", depth=1, intensity="quick",
                          liveness="working", worker_role="capability-owner")
        texts = []
        texts.append("\n".join("".join(part for part, _key in line)
                                 for line in render._build_lines([], [job], section="both",
                                                                 narrow=False, malformed=0,
                                                                 layout="wide") if line))
        l1, l2 = render._dispatch_row_2line(job)
        texts.append("".join(part for part, _key in l1 + l2))
        for text in texts:
            self.assertIn("quick/exec", text)
            self.assertEqual(text.count("quick/exec"), 1)
            self.assertNotIn("plan ›", text)
            self.assertNotIn("exec ›", text)
            self.assertNotIn("test ›", text)


class ConductorBreadcrumbTest(unittest.TestCase):
    """A conductor breadcrumb is projection-backed and never selects a first child."""

    def _stage_keys(self, lines, anchor_text):
        # anchor on the role tag ("owner"), not the slug — the dispatch name column
        # (_compact_dispatch_name) can tail-cut a long slug before this test's assertions run.
        # F-15b P1-5: a stage BEFORE the active one carries a done "✓" suffix (e.g. "plan✓") —
        # strip it here so lookups stay keyed by the bare stage word.
        for ln in lines:
            if ln and any(t == anchor_text for t, _k in ln):
                return {t.rstrip("✓"): k for t, k in ln
                        if t.rstrip("✓") in
                        ("plan", "exec", "test", "search", "analyze", "report")}
        return None

    def test_research_conductor_blinks_active_search_child(self):
        conductor = DispatchJob(key="research", slug="research-topic", depth=1,
                                liveness="working", stage="research",
                                worker_role="capability-owner")
        child = DispatchJob(key="research", slug="topic-search", depth=2,
                            parent_slug="research-topic", worker_role="stage-search",
                            liveness="working")

        def stage_keys(blink_on):
            with mock.patch.object(render, "_BLINK_ON", blink_on):
                lines = render._build_lines([], [conductor, child], section="both", narrow=False,
                                            malformed=0, layout="wide")
            return self._stage_keys(lines, "owner")

        on, off = stage_keys(True), stage_keys(False)
        self.assertIsNotNone(on)
        self.assertIsNotNone(off)
        self.assertEqual(on.get("search"), "stg0_off")
        self.assertEqual(off.get("search"), "stg0_off")
        self.assertEqual(on.get("analyze"), "stg1_off")

    def test_conductor_breadcrumb_aggregates_active_child_stage(self):
        conductor = DispatchJob(key="code", slug="fleet-ui-v2", depth=1, liveness="idle",
                                stage="plan", worker_role="capability-owner")
        child = DispatchJob(key="code", slug="fleet-ui-v2-exec", depth=2,
                            parent_slug="fleet-ui-v2", worker_role="code-execute",
                            liveness="working")
        lines = render._build_lines([], [conductor, child], section="both", narrow=False,
                                    malformed=0, layout="wide")
        stage_keys = self._stage_keys(lines, "owner")
        self.assertIsNotNone(stage_keys)
        self.assertEqual(stage_keys.get("exec"), "stg1_off")
        self.assertEqual(stage_keys.get("plan"), "stg0_off")
        self.assertEqual(stage_keys.get("test"), "stg2_off")

    def test_conductor_breadcrumb_falls_back_to_own_stage_when_child_not_working(self):
        # v16: a direct-construction job with no route/registry/artifact evidence at all
        # resolves to WorkProjection source="none", so the legacy compatibility `stage`
        # field is no longer fabricated from a static argv value — the breadcrumb instead
        # renders the honest record-less/pre-boot track (nothing lit) rather than lighting
        # a stage the projection authority never actually observed.
        conductor = DispatchJob(key="code", slug="fleet-ui-v2", depth=1, liveness="idle",
                                stage="test", worker_role="capability-owner")
        child = DispatchJob(key="code", slug="fleet-ui-v2-exec", depth=2,
                            parent_slug="fleet-ui-v2", worker_role="code-execute",
                            liveness="done")
        lines = render._build_lines([], [conductor, child], section="both", narrow=False,
                                    malformed=0, layout="wide")
        stage_keys = self._stage_keys(lines, "owner")
        self.assertIsNotNone(stage_keys)
        self.assertEqual(stage_keys.get("test"), "stg2_off")

    def test_conductor_breadcrumb_report_child_renders_lone_bright_token(self):
        # N5 — "report" sits outside the code track (plan/exec/test); the accepted minimal
        # behavior is a single bright lone "report" token (fallthrough), not a dim/unlit track.
        conductor = DispatchJob(key="code", slug="fleet-ui-v2", depth=1, liveness="idle",
                                stage="test", worker_role="capability-owner")
        child = DispatchJob(key="code", slug="fleet-ui-v2-report", depth=2,
                            parent_slug="fleet-ui-v2", worker_role="code-report",
                            liveness="working")
        lines = render._build_lines([], [conductor, child], section="both", narrow=False,
                                    malformed=0, layout="wide")
        stage_keys = self._stage_keys(lines, "owner")
        self.assertIsNotNone(stage_keys)
        self.assertNotIn("report", stage_keys)
        self.assertEqual(stage_keys.get("test"), "stg2_off")


class AlertHumanizeTest(unittest.TestCase):
    """F-10 — alert strip strips loop-job <case>-<ts>-<pid> tails and aggregates by kind."""

    def _alert_text(self, lines):
        for ln in lines:
            if ln and ln[0][0] == "  alert ":
                return "".join(t for t, _k in ln)
        return None

    def test_alert_humanize_aggregates_and_strips_tail(self):
        dead_a = DispatchJob(key="drill", slug="case-a-20260709-11111", liveness="dead")
        dead_b = DispatchJob(key="drill", slug="case-b-20260709-22222", liveness="dead")
        lines = render._build_lines([], [dead_a, dead_b], section="both", narrow=False,
                                    malformed=0, layout="wide")
        text = self._alert_text(lines)
        self.assertIsNotNone(text)
        self.assertIn("2 dead jobs: case-a·case-b", text)
        self.assertNotIn("20260709", text)

    def test_alert_humanize_single_stale_job_not_aggregated(self):
        stale = DispatchJob(key="drill", slug="lone-case-20260709-33333", liveness="stale")
        lines = render._build_lines([], [stale], section="both", narrow=False, malformed=0,
                                    layout="wide")
        text = self._alert_text(lines)
        self.assertIsNotNone(text)
        self.assertIn("stale lone-case", text)
        self.assertNotIn("20260709", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
