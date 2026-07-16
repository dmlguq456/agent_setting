"""F-29 (v9) — sub-agent observation (prd.md:290-295).

Enrichment ONLY: every test in NoRegressionTest exists to pin prd.md:291's "never touches
session-existence" contract. Fixtures are a throwaway sqlite DB (OpenCode) and throwaway
jsonl transcripts (Claude) — no real opencode/claude state is ever touched.
"""
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet import render                                          # noqa: E402
from fleet.collectors import claude, opencode                     # noqa: E402
from fleet.model import Session, SubAgent                         # noqa: E402


class OpenCodeSubagentTest(unittest.TestCase):
    """Temp sqlite DB fixture — real opencode.db never touched."""

    def _db(self, tmp, rows, with_agent_col=True, table_extra=""):
        path = os.path.join(tmp, "opencode.db")
        con = sqlite3.connect(path)
        cols = ["id TEXT", "slug TEXT"]
        if with_agent_col:
            cols.append("agent TEXT")
        cols += ["model TEXT", "cost REAL", "tokens_input INT", "tokens_output INT",
                "tokens_reasoning INT", "time_updated INT", "parent_id TEXT",
                "directory TEXT", "title TEXT"]
        con.execute("CREATE TABLE session (%s)" % ", ".join(cols))
        for r in rows:
            keys = list(r.keys())
            con.execute("INSERT INTO session (%s) VALUES (%s)" %
                       (", ".join(keys), ", ".join("?" for _ in keys)),
                       [r[k] for k in keys])
        con.commit()
        con.close()
        return path

    def test_child_rows_become_subagents(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = self._db(tmp, [
                {"id": "parent1", "slug": "p", "agent": None, "directory": "/x",
                 "time_updated": 1000, "parent_id": None},
                {"id": "child1", "slug": "c1", "agent": "explore", "directory": "/x",
                 "time_updated": 2000, "parent_id": "parent1"},
            ])
            con = sqlite3.connect(db)
            subs = opencode._child_sessions(con, "parent1")
            con.close()
            self.assertEqual(len(subs), 1)
            self.assertEqual(subs[0].agent_type, "explore")

    def test_agent_column_maps_to_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = self._db(tmp, [
                {"id": "parent1", "slug": "p", "agent": None, "directory": "/x",
                 "time_updated": 1000, "parent_id": None},
                {"id": "child1", "slug": "c1", "agent": "code-reviewer", "directory": "/x",
                 "time_updated": 2000, "parent_id": "parent1"},
            ])
            con = sqlite3.connect(db)
            subs = opencode._child_sessions(con, "parent1")
            con.close()
            self.assertEqual(subs[0].agent_type, "code-reviewer")
            self.assertEqual(subs[0].source, "opencode-db")

    def test_absent_parent_id_yields_no_subagents(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = self._db(tmp, [
                {"id": "solo1", "slug": "solo", "agent": None, "directory": "/x",
                 "time_updated": 1000, "parent_id": None},
            ])
            con = sqlite3.connect(db)
            subs = opencode._child_sessions(con, "solo1")
            con.close()
            self.assertEqual(subs, [])

    def test_db_without_agent_column_degrades_to_none(self):
        """tolerant (F-3) — an older DB schema must never crash enrich(), and subagents
        stays the honest None (not []): the source itself is unconfirmed, not empty."""
        with tempfile.TemporaryDirectory() as tmp:
            db = self._db(tmp, [
                {"id": "parent1", "slug": "p", "directory": "/x",
                 "time_updated": 1000, "parent_id": None},
            ], with_agent_col=False)
            with mock.patch.dict(os.environ, {"OPENCODE_DB": db}):
                sess = Session(harness="opencode", pid=1, cwd="/x")
                opencode.enrich(sess)
            self.assertIsNone(sess.subagents)

    def test_enrich_wires_subagents_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = self._db(tmp, [
                {"id": "parent1", "slug": "p", "agent": None, "directory": "/x",
                 "time_updated": 1000, "parent_id": None},
                {"id": "child1", "slug": "c1", "agent": "explore", "directory": "/x",
                 "time_updated": 2000, "parent_id": "parent1"},
            ])
            with mock.patch.dict(os.environ, {"OPENCODE_DB": db}):
                sess = Session(harness="opencode", pid=1, cwd="/x")
                opencode.enrich(sess)
            self.assertEqual(len(sess.subagents), 1)
            self.assertEqual(sess.subagents[0].agent_type, "explore")


def _tool_use_line(tid, agent_type, ts="2026-07-15T10:00:00Z", name="Task"):
    return {"type": "assistant", "isSidechain": False, "timestamp": ts,
            "message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": tid, "name": name,
                 "input": {"subagent_type": agent_type}}]}}


def _tool_result_line(tid, ts="2026-07-15T10:05:00Z", content="done"):
    return {"type": "user", "isSidechain": False, "timestamp": ts,
            "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tid, "content": content}]}}


def _async_ack_line(tid, agent_id, ts="2026-07-15T10:00:01Z"):
    """The harness's immediate answer to a background Agent launch — NOT completion."""
    return _tool_result_line(tid, ts=ts, content=(
        "Async agent launched successfully. agentId: %s (internal ID)." % agent_id))


def _task_notification_line(agent_id, ts="2026-07-15T10:07:00Z"):
    """The user-turn stop notification the harness injects when a background agent ends."""
    return {"type": "user", "isSidechain": False, "timestamp": ts,
            "message": {"role": "user", "content":
                "<task-notification><task-id>%s</task-id>"
                "<status>completed</status></task-notification>" % agent_id}}


def _write_transcript(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        for ln in lines:
            f.write(json.dumps(ln) + "\n")


class ClaudeSidechainTest(unittest.TestCase):
    """Temp jsonl transcript fixture — real ~/.claude never touched."""

    def setUp(self):
        claude._SUBAGENT_CACHE.clear()

    def test_sidechain_lines_pair_tool_use_and_tool_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.jsonl")
            _write_transcript(path, [
                _tool_use_line("t1", "explore"),
                _tool_result_line("t1"),
            ])
            subs = claude._tail_subagents(path)
            self.assertEqual(len(subs), 1)
            self.assertFalse(subs[0].active, "paired tool_use/tool_result = completed")

    def test_unpaired_tool_use_counts_as_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.jsonl")
            _write_transcript(path, [_tool_use_line("t1", "code-reviewer")])
            subs = claude._tail_subagents(path)
            self.assertEqual(len(subs), 1)
            self.assertTrue(subs[0].active)
            self.assertEqual(subs[0].agent_type, "code-reviewer")

    def test_current_runtime_agent_tool_name_is_matched(self):
        """claude.py:197 matched tool_use name == "Task" only; current runtimes emit
        "Agent" instead, so this collector counted 0 sub-agents against every live
        transcript until fixed — regression fixture for that drift."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.jsonl")
            _write_transcript(path, [_tool_use_line("t1", "explore", name="Agent")])
            subs = claude._tail_subagents(path)
            self.assertEqual(len(subs), 1)
            self.assertTrue(subs[0].active)
            self.assertEqual(subs[0].agent_type, "explore")

    def test_task_and_agent_names_both_pair_with_tool_result(self):
        """Old ("Task") and current ("Agent") transcripts must both resolve to completed
        when a tool_result answers them — compatibility, not an either/or switch."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.jsonl")
            _write_transcript(path, [
                _tool_use_line("t1", "explore", name="Task"),
                _tool_result_line("t1"),
                _tool_use_line("t2", "code-reviewer", name="Agent", ts="2026-07-15T10:01:00Z"),
                _tool_result_line("t2", ts="2026-07-15T10:06:00Z"),
            ])
            subs = claude._tail_subagents(path)
            self.assertEqual(len(subs), 2)
            self.assertFalse(subs[0].active)
            self.assertFalse(subs[1].active)

    def test_async_launch_ack_keeps_the_agent_active(self):
        """Background agents answer their tool_use IMMEDIATELY with a launch ack while the
        agent keeps running — pairing alone misread every async agent as completed on the
        spot, so the active ● state never showed live (user 2026-07-16)."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.jsonl")
            _write_transcript(path, [
                _tool_use_line("t1", "explore", name="Agent"),
                _async_ack_line("t1", "a1b2c3d4e5"),
            ])
            subs = claude._tail_subagents(path)
            self.assertEqual(len(subs), 1)
            self.assertTrue(subs[0].active, "launch ack ≠ completion")

    def test_async_agent_completes_on_task_notification(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.jsonl")
            _write_transcript(path, [
                _tool_use_line("t1", "explore", name="Agent"),
                _async_ack_line("t1", "a1b2c3d4e5"),
                _task_notification_line("a1b2c3d4e5"),
            ])
            subs = claude._tail_subagents(path)
            self.assertEqual(len(subs), 1)
            self.assertFalse(subs[0].active)

    def test_foreign_notification_does_not_complete_the_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.jsonl")
            _write_transcript(path, [
                _tool_use_line("t1", "explore", name="Agent"),
                _async_ack_line("t1", "a1b2c3d4e5"),
                _task_notification_line("other-task-id"),
            ])
            subs = claude._tail_subagents(path)
            self.assertTrue(subs[0].active)

    def test_async_ack_without_id_falls_back_to_completed(self):
        # Untrackable launch (marker but no parseable agentId) fails toward the pre-async
        # pairing — completed — rather than showing an active row forever.
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.jsonl")
            _write_transcript(path, [
                _tool_use_line("t1", "explore", name="Agent"),
                _tool_result_line("t1", content="Async agent launched successfully."),
            ])
            subs = claude._tail_subagents(path)
            self.assertFalse(subs[0].active)

    def test_malformed_lines_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write('{"type":"assistant","message":{"content":[{"type":"tool_use"\n')
                f.write("not even json at all\n")
                f.write(json.dumps(_tool_use_line("t2", "explore")) + "\n")
            subs = claude._tail_subagents(path)
            self.assertEqual(len(subs), 1)
            self.assertEqual(subs[0].agent_type, "explore")

    def test_cache_keyed_on_mtime_and_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.jsonl")
            _write_transcript(path, [_tool_use_line("t1", "explore")])
            first = claude._tail_subagents(path)
            self.assertEqual(len(first), 1)
            st = os.stat(path)
            claude._SUBAGENT_CACHE[path] = (st.st_mtime, st.st_size, [])   # poison the cache
            cached = claude._tail_subagents(path)
            self.assertEqual(cached, [], "재읽기 없이 (mtime,size) 캐시를 그대로 반환해야 함")


class NoRegressionTest(unittest.TestCase):
    """prd.md:291/293/294 — enrichment cannot touch existence, pulse, or --json shape."""

    def setUp(self):
        render.reset_selection()

    def _rows(self, subagents=None):
        s = Session(harness="claude", pid=90001, cwd="/x", slug="a",
                   liveness="working", title="live", elapsed_min=5)
        s.proc_start = "111"
        s.subagents = subagents
        return [s]

    def test_source_absent_omits_subrow_entirely(self):
        lines = render._build_lines(self._rows(subagents=None), [], section="fleet",
                                    narrow=False, malformed=0, term_width=168)
        joined = "\n".join("".join(t for t, _k in ln) for ln in lines if ln)
        self.assertNotIn(render._ICON_SUBAGENT, joined)

    def test_subagents_render_as_one_horizontal_strip_row(self):
        """F-29 v11 (사용자 확정 2026-07-16) — 2+ sub-agents render as ONE horizontal strip
        row per session (`⚡ type ● elapsed · type ● elapsed …`), replacing the old
        one-row-per-subagent ├⚡/└⚡ stack."""
        subs = [SubAgent(agent_type="explore", active=True),
               SubAgent(agent_type="code-reviewer", active=True),
               SubAgent(agent_type="fact-check", active=True)]
        lines = render._build_lines(self._rows(subagents=subs), [], section="fleet",
                                    narrow=False, malformed=0, term_width=168)
        sub_lines = [ln for ln in lines
                    if ln and "explore" in "".join(t for t, _k in ln)]
        self.assertEqual(len(sub_lines), 1, "3개 서브에이전트가 한 줄 스트립이어야 함")
        text = "".join(t for t, _k in sub_lines[0])
        self.assertIn("explore", text)
        self.assertIn("code-reviewer", text)
        self.assertIn("fact-check", text)
        self.assertIn(" · ", text, "가로 나열은 가운뎃점으로 구분")
        self.assertNotIn("├", text)
        self.assertNotIn("└", text)

    def test_strip_hides_completed_by_default_shows_with_show_all(self):
        subs = [SubAgent(agent_type="explore", active=True),
               SubAgent(agent_type="fact-check", active=False)]
        try:
            lines = render._build_lines(self._rows(subagents=subs), [], section="fleet",
                                        narrow=False, malformed=0, term_width=168)
            text = "".join("".join(t for t, _k in ln) for ln in lines if ln)
            self.assertIn("explore", text)
            self.assertNotIn("fact-check", text)
            render.set_show_all(True)
            lines = render._build_lines(self._rows(subagents=subs), [], section="fleet",
                                        narrow=False, malformed=0, term_width=168)
            text = "".join("".join(t for t, _k in ln) for ln in lines if ln)
            self.assertIn("fact-check", text)
        finally:
            render.set_show_all(False)

    def test_strip_indent_is_a_deep_pure_inset(self):
        """`_SUBAGENT_IND` stays a pure inset (spaces only, no connector) and lands at least
        as deep as a dispatch row's full "  ↳ " prefix (사용자 2026-07-16 '좀 더 들여쓰기' —
        the earlier shallower-than-dispatch contract read as a sibling, not a child)."""
        self.assertEqual(render._SUBAGENT_IND.strip(), "")
        self.assertGreaterEqual(len(render._SUBAGENT_IND), len("  " + render._dispatch_prefix(
            type("J", (), {"depth": 1})())))

    def test_no_subagent_count_badge_on_the_session_name_row(self):
        """The ⚡N name-zone badge is retired — the strip is inline under the row, so a
        second count on the name line would be redundant (사용자 확정 2026-07-16)."""
        subs = [SubAgent(agent_type="explore", active=True),
               SubAgent(agent_type="code-reviewer", active=True)]
        lines = render._build_lines(self._rows(subagents=subs), [], section="fleet",
                                    narrow=False, malformed=0, term_width=168)
        name_lines = [ln for ln in lines
                     if ln and any(k == "name_work" for _t, k in ln)]
        self.assertEqual(len(name_lines), 1)
        name_text = "".join(t for t, _k in name_lines[0])
        self.assertNotIn("⚡2", name_text)
        self.assertNotIn(render._ICON_SUBAGENT, name_text)

    def test_parse_failure_omits_subrow_entirely(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "opencode.db")
            con = sqlite3.connect(db)
            con.execute("CREATE TABLE session (id TEXT)")   # missing every expected column
            con.commit()
            con.close()
            with mock.patch.dict(os.environ, {"OPENCODE_DB": db}):
                sess = Session(harness="opencode", pid=1, cwd="/x")
                opencode.enrich(sess)          # must not raise
            self.assertIsNone(sess.subagents)

    def test_subagents_never_enter_pulse_counts(self):
        active = [SubAgent(agent_type="explore", active=True)]
        with_subs = self._rows(subagents=active)
        without_subs = self._rows(subagents=None)
        lines_with = render._build_lines(with_subs, [], section="fleet", narrow=False,
                                         malformed=0, term_width=168)
        lines_without = render._build_lines(without_subs, [], section="fleet", narrow=False,
                                            malformed=0, term_width=168)
        pulse_with = "".join(t for t, _k in lines_with[1])
        pulse_without = "".join(t for t, _k in lines_without[1])
        self.assertEqual(pulse_with, pulse_without,
                         "서브에이전트 존재가 fleet pulse 줄을 바꿨다")

    def test_session_existence_unaffected_by_subagents(self):
        """prd.md:291 — classify_session doesn't even see the field; subagents lives on
        Session AFTER classification, purely as enrichment."""
        import inspect
        from fleet import model
        self.assertNotIn("subagents", inspect.getsource(model.classify_session))

    def test_json_key_is_additive(self):
        plain = Session(harness="claude", pid=1, cwd="/x").to_dict()
        self.assertIn("subagents", plain)
        self.assertIsNone(plain["subagents"])
        # every other key from a bare Session must still be there — additive, not replaced.
        self.assertIn("pid", plain)
        self.assertIn("liveness", plain)


if __name__ == "__main__":
    unittest.main()
