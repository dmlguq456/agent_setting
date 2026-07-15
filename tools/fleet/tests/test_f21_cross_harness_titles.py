#!/usr/bin/env python3
"""F-21 — Codex native titles and shared fleet title provider."""
import contextlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import time
import unittest

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from fleet import fleet as fleet_main  # noqa: E402
from fleet import refresh_title as rt  # noqa: E402
from fleet import render  # noqa: E402
from fleet import titles  # noqa: E402
from fleet.collectors import codex  # noqa: E402
from fleet.model import Session  # noqa: E402


class _EnvMixin:
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.saved = {key: os.environ.get(key) for key in (
            "CODEX_HOME", "CLAUDE_CONFIG_DIR", "FLEET_TITLE_STATE_DIR",
            "FLEET_TITLE_COMMAND", "FLEET_TITLE_MODEL", "FLEET_TITLE_REFRESH",
            "FLEET_TITLE_DISABLE", "FLEET_TITLE_CONCURRENCY", "FLEET_TITLE_MAX_STARTS",
        )}
        os.environ["CODEX_HOME"] = os.path.join(self.tmp.name, "codex")
        os.environ["CLAUDE_CONFIG_DIR"] = os.path.join(self.tmp.name, "claude")
        os.environ["FLEET_TITLE_STATE_DIR"] = os.path.join(self.tmp.name, "title-state")
        for key in (
            "FLEET_TITLE_COMMAND", "FLEET_TITLE_MODEL", "FLEET_TITLE_REFRESH",
            "FLEET_TITLE_DISABLE", "FLEET_TITLE_CONCURRENCY", "FLEET_TITLE_MAX_STARTS",
        ):
            os.environ.pop(key, None)
        codex._TITLE_INDEX.update(stamp=None, map={})
        codex._CFG.update(ts=0.0, model=None, effort=None)

    def tearDown(self):
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()


class NeutralStateTest(_EnvMixin, unittest.TestCase):
    def test_harness_namespaces_do_not_collide(self):
        titles.write("same-sid", "Claude title", harness="claude", now=100)
        titles.write("same-sid", "Codex title", harness="codex", now=100)
        self.assertEqual(titles.read("same-sid", harness="claude")["title"], "Claude title")
        self.assertEqual(titles.read("same-sid", harness="codex")["title"], "Codex title")
        self.assertNotEqual(
            titles.sidecar_path("same-sid", harness="claude"),
            titles.sidecar_path("same-sid", harness="codex"),
        )

    def test_legacy_claude_sidecar_is_read_only_fallback(self):
        legacy_dir = os.path.join(os.environ["CLAUDE_CONFIG_DIR"], ".fleet-titles")
        os.makedirs(legacy_dir, exist_ok=True)
        with open(os.path.join(legacy_dir, "legacy-sid.json"), "w", encoding="utf-8") as f:
            json.dump({"title": "Legacy", "ts": time.time(), "source": "old", "offset": 3}, f)
        self.assertEqual(titles.fresh_title("legacy-sid", harness="claude"), "Legacy")
        self.assertFalse(os.path.exists(titles.sidecar_path("legacy-sid", harness="claude")))


class CodexCollectorTitleTest(_EnvMixin, unittest.TestCase):
    SID = "11111111-2222-3333-4444-555555555555"

    def _fixture(self, native_title="Native Codex Title"):
        home = os.environ["CODEX_HOME"]
        sessions = os.path.join(home, "sessions", "2026", "07", "13")
        os.makedirs(sessions, exist_ok=True)
        rollout = os.path.join(sessions, "rollout-2026-07-13T00-00-00-" + self.SID + ".jsonl")
        with open(rollout, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "session_meta", "payload": {"cwd": "/repo"}}) + "\n")
        with open(os.path.join(home, "session_index.jsonl"), "w", encoding="utf-8") as f:
            f.write("{broken\n")
            f.write(json.dumps({"id": self.SID, "thread_name": "Old"}) + "\n")
            f.write(json.dumps({"id": self.SID, "thread_name": native_title}) + "\n")
        return rollout

    def _state_db_title(self, title):
        home = os.environ["CODEX_HOME"]
        path = os.path.join(home, "state_5.sqlite")
        connection = sqlite3.connect(path)
        try:
            connection.execute("CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT NOT NULL)")
            connection.execute("INSERT INTO threads(id, title) VALUES (?, ?)", (self.SID, title))
            connection.commit()
        finally:
            connection.close()
        codex._TITLE_INDEX.update(stamp=None, map={})

    def _enrich(self, rollout):
        session = Session(harness="codex", pid=123, cwd="/repo", slug="repo")
        original = codex._proc_rollout
        codex._proc_rollout = lambda *_args: rollout
        try:
            codex.enrich(session)
        finally:
            codex._proc_rollout = original
        return session

    def test_native_thread_name_is_used(self):
        rollout = self._fixture()
        session = self._enrich(rollout)
        self.assertEqual(session.title, "Native Codex Title")
        self.assertEqual(session.session_id, self.SID)
        self.assertEqual(session._transcript_path, rollout)

    def test_state_db_title_beats_session_index_fallback(self):
        rollout = self._fixture(native_title="Older Index Title")
        self._state_db_title("Current State DB Title")
        self.assertEqual(self._enrich(rollout).title, "Current State DB Title")

    def test_fresh_sidecar_beats_native_thread_name(self):
        rollout = self._fixture()
        titles.write(self.SID, "Live Shared Title", harness="codex", now=time.time())
        self.assertEqual(self._enrich(rollout).title, "Live Shared Title")

    def test_stale_sidecar_falls_back_to_native_thread_name(self):
        rollout = self._fixture()
        titles.write(self.SID, "Stale", harness="codex", now=time.time() - 25 * 3600)
        self.assertEqual(self._enrich(rollout).title, "Native Codex Title")


class CrossHarnessWorkerTest(_EnvMixin, unittest.TestCase):
    def test_codex_delta_extracts_only_user_and_assistant_messages(self):
        rows = [
            {"type": "response_item", "payload": {"type": "message", "role": "user",
             "content": [{"type": "input_text", "text": "implement titles"}]}},
            {"type": "response_item", "payload": {"type": "message", "role": "developer",
             "content": [{"type": "input_text", "text": "secret instructions"}]}},
            {"type": "response_item", "payload": {"type": "message", "role": "assistant",
             "content": [{"type": "output_text", "text": "working on it"}]}},
            {"type": "response_item", "payload": {"type": "custom_tool_call", "input": "ignored"}},
        ]
        text = rt._delta_text("\n".join(json.dumps(row) for row in rows), harness="codex")
        self.assertIn("implement titles", text)
        self.assertIn("working on it", text)
        self.assertNotIn("secret instructions", text)
        self.assertNotIn("ignored", text)

    def test_custom_provider_is_shell_free_argv_template(self):
        os.environ["FLEET_TITLE_COMMAND"] = "provider --model {model} --prompt {prompt}"
        os.environ["FLEET_TITLE_MODEL"] = "small-model"
        prompt = "$(touch /tmp/never-executed)"
        argv = rt.worker_argv(prompt)
        self.assertEqual(argv[0], "provider")
        self.assertIn("small-model", argv)
        self.assertIn(prompt, argv)

    def test_shared_scheduler_namespaces_codex_lock_and_spawn(self):
        transcript = os.path.join(self.tmp.name, "rollout.jsonl")
        with open(transcript, "w", encoding="utf-8") as f:
            f.write("{}\n")
        os.environ["FLEET_TITLE_COMMAND"] = sys.executable + " -c pass"
        captured = {}

        class _Proc:
            pass

        original = rt.subprocess.Popen
        rt.subprocess.Popen = lambda argv, **kwargs: captured.update(argv=argv, kwargs=kwargs) or _Proc()
        try:
            self.assertTrue(rt.maybe_spawn("codex", "codex-sid", transcript))
        finally:
            rt.subprocess.Popen = original
        self.assertIn("--harness", captured["argv"])
        self.assertIn("codex", captured["argv"])
        self.assertIn("--slotdir", captured["argv"])
        self.assertTrue(os.path.isdir(titles.lock_path("codex-sid", harness="codex")))
        self.assertTrue(os.path.isdir(captured["argv"][captured["argv"].index("--slotdir") + 1]))
        self.assertEqual(captured["kwargs"]["env"]["FLEET_TITLE_REFRESH"], "1")
        self.assertEqual(captured["kwargs"]["env"]["AGENT_SESSION_ROLE"], "worker")

    def test_fleet_schedules_only_live_mode(self):
        session = Session(harness="codex", pid=1, cwd="/repo", session_id="sid", liveness="working")
        original_collect = fleet_main.collect_all
        original_schedule = rt.schedule_sessions
        original_run_live = render.run_live
        calls = []
        fleet_main.collect_all = lambda harness_filter=None: ([session], [])
        rt.schedule_sessions = lambda sessions: calls.append(list(sessions)) or 0
        render.run_live = lambda collector, hfilter, section, interval: collector(hfilter) and 0
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(fleet_main.main(["--json"]), 0)
            self.assertEqual(calls, [])
            self.assertEqual(fleet_main.main([]), 0)
            self.assertEqual(len(calls), 1)
        finally:
            fleet_main.collect_all = original_collect
            rt.schedule_sessions = original_schedule
            render.run_live = original_run_live


if __name__ == "__main__":
    unittest.main(verbosity=2)
