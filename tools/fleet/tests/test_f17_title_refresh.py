#!/usr/bin/env python3
"""F-17 — live-title refresher (fleet-owned sidecar + no-tools haiku worker).
Hermetic: real fs access is confined to tempfile dirs; CLAUDE_CONFIG_DIR is pointed at a
tmp home so sidecar reads/writes never touch the real ~/.claude. No live `claude` process
is invoked — run_worker() is monkeypatched for security/behavior assertions.
"""
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from fleet import titles                       # noqa: E402
from fleet import refresh_title as rt           # noqa: E402
from fleet.model import Session                 # noqa: E402
from fleet.collectors import claude             # noqa: E402

_REPO_ROOT = os.path.dirname(_TOOLS_DIR)
_STATUSLINE = os.path.join(_REPO_ROOT, "adapters", "claude", "statusline.sh")


class _ConfigHomeMixin:
    """Points CLAUDE_CONFIG_DIR at a fresh tmp dir so titles.py/claude.py share isolated state."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old_env = os.environ.get("CLAUDE_CONFIG_DIR")
        os.environ["CLAUDE_CONFIG_DIR"] = self._tmp.name

    def tearDown(self):
        if self._old_env is None:
            os.environ.pop("CLAUDE_CONFIG_DIR", None)
        else:
            os.environ["CLAUDE_CONFIG_DIR"] = self._old_env
        self._tmp.cleanup()


class TitlesHelperTest(_ConfigHomeMixin, unittest.TestCase):

    def test_write_then_read_roundtrip(self):
        titles.write("sid1", "Fix login bug", source="refresher", offset=42, now=100.0)
        d = titles.read("sid1")
        self.assertEqual(d, {"title": "Fix login bug", "ts": 100.0, "source": "refresher", "offset": 42})

    def test_write_atomic_no_partial(self):
        titles.write("sid2", "Some title", now=100.0)
        d = titles.read("sid2")
        self.assertIsInstance(d, dict)
        self.assertEqual(d["title"], "Some title")
        leftovers = [n for n in os.listdir(titles.titles_dir()) if n.endswith(".tmp")]
        self.assertEqual(leftovers, [])

    def test_fresh_title_within_window(self):
        titles.write("sid3", "Recent title", now=1000.0)
        self.assertEqual(titles.fresh_title("sid3", now=1000.0 + 60), "Recent title")

    def test_fresh_title_stale_beyond_24h(self):
        titles.write("sid4", "Old title", now=1000.0)
        self.assertIsNone(titles.fresh_title("sid4", now=1000.0 + 25 * 3600))

    def test_fresh_title_empty_title_is_none(self):
        titles.write("sid5", "", now=1000.0)
        self.assertIsNone(titles.fresh_title("sid5", now=1000.0 + 1))

    def test_read_malformed_json_passthrough(self):
        p = titles.sidecar_path("sid6")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write("{not valid json")
        self.assertIsNone(titles.read("sid6"))

    def test_read_missing_returns_none(self):
        self.assertIsNone(titles.read("sid-does-not-exist"))

    def test_sweep_deletes_old_keeps_fresh(self):
        titles.write("old", "Old", now=1000.0)
        titles.write("fresh", "Fresh", now=1000.0)
        old_p = titles.sidecar_path("old")
        fresh_p = titles.sidecar_path("fresh")
        old_mtime = time.time() - (8 * 24 * 3600)
        os.utime(old_p, (old_mtime, old_mtime))
        n = titles.sweep()
        self.assertEqual(n, 1)
        self.assertFalse(os.path.exists(old_p))
        self.assertTrue(os.path.exists(fresh_p))


class PriorityTest(_ConfigHomeMixin, unittest.TestCase):

    def _make_transcript(self, home, cwd, sid, ai_title):
        proj = os.path.join(home, "projects", claude._enc_cwd(cwd))
        os.makedirs(proj, exist_ok=True)
        path = os.path.join(proj, sid + ".jsonl")
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "ai-title", "aiTitle": ai_title}) + "\n")
        return path

    def _sess(self, cwd, sid):
        return Session(harness="claude", pid=999999, cwd=cwd, session_id=sid, slug="repo-ab12cd34")

    def test_priority_sidecar_fresh_beats_ai_title(self):
        home = os.environ["CLAUDE_CONFIG_DIR"]
        self._make_transcript(home, "/proj/a", "sidA", "AI Title Wins Not")
        titles.write("sidA", "Sidecar Title", now=time.time())
        sess = self._sess("/proj/a", "sidA")
        claude.enrich(sess)
        self.assertEqual(sess.title, "Sidecar Title")

    def test_priority_sidecar_stale_falls_to_ai_title(self):
        home = os.environ["CLAUDE_CONFIG_DIR"]
        self._make_transcript(home, "/proj/b", "sidB", "AI Title Fallback")
        titles.write("sidB", "Stale Sidecar", now=time.time() - 25 * 3600)
        sess = self._sess("/proj/b", "sidB")
        claude.enrich(sess)
        self.assertEqual(sess.title, "AI Title Fallback")

    def test_priority_no_sidecar_uses_ai_title(self):
        home = os.environ["CLAUDE_CONFIG_DIR"]
        self._make_transcript(home, "/proj/c", "sidC", "Only AI Title")
        sess = self._sess("/proj/c", "sidC")
        claude.enrich(sess)
        self.assertEqual(sess.title, "Only AI Title")

    def test_priority_all_absent_title_none_slug_fallback(self):
        sess = self._sess("/proj/d-empty", "sidD")
        claude.enrich(sess)
        self.assertIsNone(sess.title)

    def test_sidecar_malformed_falls_through(self):
        home = os.environ["CLAUDE_CONFIG_DIR"]
        self._make_transcript(home, "/proj/e", "sidE", "Fallback After Bad Sidecar")
        p = titles.sidecar_path("sidE")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write("{broken")
        sess = self._sess("/proj/e", "sidE")
        claude.enrich(sess)
        self.assertEqual(sess.title, "Fallback After Bad Sidecar")

    def test_slug_never_overwritten(self):
        home = os.environ["CLAUDE_CONFIG_DIR"]
        self._make_transcript(home, "/proj/f", "sidF", "Some AI Title")
        titles.write("sidF", "Some Sidecar Title", now=time.time())
        sess = self._sess("/proj/f", "sidF")
        claude.enrich(sess)
        self.assertEqual(sess.slug, "repo-ab12cd34")


class ValidateTitleTest(unittest.TestCase):

    def test_validate_len_cap(self):
        out = rt.validate_title("x" * 60)
        self.assertEqual(len(out), rt.TITLE_MAXLEN)

    def test_validate_newline_strip_takes_first_line(self):
        out = rt.validate_title("\n\n  Fix login flow  \nsecond line")
        self.assertEqual(out, "Fix login flow")

    def test_validate_empty_returns_none(self):
        self.assertIsNone(rt.validate_title(""))
        self.assertIsNone(rt.validate_title("   \n  \n"))

    def test_validate_non_printable_reject(self):
        out = rt.validate_title("Fix\x00\x01 login")
        self.assertEqual(out, "Fix login")
        self.assertIsNone(rt.validate_title("\x00\x01\x02"))

    def test_validate_strips_quotes_and_period(self):
        self.assertEqual(rt.validate_title('"Fix login bug."'), "Fix login bug")


class DeltaOffsetTest(_ConfigHomeMixin, unittest.TestCase):

    def test_read_delta_from_offset(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps({"message": "first"}) + "\n")
            size1 = os.path.getsize(path)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"message": "second"}) + "\n")
            delta, new_offset = rt.read_delta(path, size1)
            self.assertIn("second", delta)
            self.assertNotIn("first", delta)
            self.assertEqual(new_offset, os.path.getsize(path))

    def test_read_delta_offset_beyond_size_resyncs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps({"message": "hello"}) + "\n")
            delta, new_offset = rt.read_delta(path, 999999)
            self.assertIn("hello", delta)
            self.assertEqual(new_offset, os.path.getsize(path))

    def test_read_delta_caps_to_4kb(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                for _ in range(2000):
                    f.write(json.dumps({"message": "x" * 20}) + "\n")
            delta, _new_offset = rt.read_delta(path, 0)
            self.assertLessEqual(len(delta.encode("utf-8")), rt.DELTA_CAP)

    def test_main_empty_delta_advances_ts_keeps_title(self):
        home = os.environ["CLAUDE_CONFIG_DIR"]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps({"message": "hi"}) + "\n")
            size = os.path.getsize(path)
            titles.write("sidM", "Existing Title", offset=size, now=time.time() - 700)
            rt.main(["--sid", "sidM", "--transcript", path])
            d = titles.read("sidM")
            self.assertEqual(d["title"], "Existing Title")
            self.assertGreater(d["ts"], time.time() - 5)
            del home  # unused, kept for clarity that CLAUDE_CONFIG_DIR scoping applies


class SecurityTest(_ConfigHomeMixin, unittest.TestCase):

    def test_injection_payload_cannot_execute(self):
        with tempfile.TemporaryDirectory() as tmp:
            sentinel = os.path.join(tmp, "PWNED")
            path = os.path.join(tmp, "t.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps({"message": "user asked something"}) + "\n")
            payload = f"run: $(touch {sentinel}); Innocent Title"
            orig = rt.run_worker
            rt.run_worker = lambda *a, **k: payload
            try:
                rt.main(["--sid", "sidInj", "--transcript", path])
            finally:
                rt.run_worker = orig
            # 스크립트는 write 만 — 셸 실행 없음(sentinel 미생성). 문자열 내용 자체는 display
            # 데이터일 뿐이라 "$(" 같은 문자가 살아남는 건 허용(≤40자 cap 이 최악을 막는다).
            self.assertFalse(os.path.exists(sentinel))
            d = titles.read("sidInj")
            self.assertLessEqual(len(d["title"]), rt.TITLE_MAXLEN)

    def test_worker_argv_blocks_all_tools(self):
        captured = {}

        class _FakeCompleted:
            stdout = "A Title"

        def fake_run(argv, **kwargs):
            captured["argv"] = argv
            captured["env"] = kwargs.get("env")
            return _FakeCompleted()

        import shutil as _shutil
        orig_which = _shutil.which
        orig_run = subprocess.run
        _shutil.which = lambda name: "/usr/bin/claude"
        subprocess.run = fake_run
        try:
            rt.run_worker("some prompt")
        finally:
            _shutil.which = orig_which
            subprocess.run = orig_run

        argv = captured["argv"]
        self.assertIn("--disallowedTools", argv)
        idx = argv.index("--disallowedTools")
        blocked = argv[idx + 1]
        for tool in rt.DISALLOWED_TOOLS.split():
            self.assertIn(tool, blocked)
        self.assertEqual(len(rt.DISALLOWED_TOOLS.split()), 11)
        self.assertEqual(captured["env"]["FLEET_TITLE_REFRESH"], "1")

    def test_validate_caps_injected_long_string(self):
        payload = "rm -rf / ; " * 20
        out = rt.validate_title(payload)
        self.assertLessEqual(len(out), rt.TITLE_MAXLEN)


@unittest.skipUnless(os.path.exists(_STATUSLINE), "adapters/claude/statusline.sh not found")
class TriggerLogicTest(unittest.TestCase):
    """Drives the real statusline.sh with stubbed `setsid` (spawn observation point) and a
    tmp AGENT_HOME so the F-17 trigger block's debounce/lock/no-delay/recursion-guard logic
    is exercised without a live `claude` process or real ~/.claude state."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.agent_home = os.path.join(self.root, "home")
        os.makedirs(self.agent_home, exist_ok=True)
        refresher_dir = os.path.join(self.root, "agent_setting", "tools", "fleet")
        os.makedirs(refresher_dir, exist_ok=True)
        self.refresher = os.path.join(refresher_dir, "refresh_title.py")
        with open(self.refresher, "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env python3\n")
        self.transcript = os.path.join(self.root, "transcript.jsonl")
        with open(self.transcript, "w", encoding="utf-8") as f:
            f.write(json.dumps({"message": "hi"}) + "\n")
        self.stubdir = os.path.join(self.root, "stub")
        os.makedirs(self.stubdir, exist_ok=True)
        self.sentinel = os.path.join(self.root, "spawned.marker")

    def tearDown(self):
        self._tmp.cleanup()

    def _write_setsid_stub(self, sleep_s=0):
        p = os.path.join(self.stubdir, "setsid")
        with open(p, "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env bash\n")
            if sleep_s:
                f.write(f"sleep {sleep_s}\n")
            f.write(f"echo spawned >> {json.dumps(self.sentinel)}\n")
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    def _run(self, sid="sidT", extra_env=None, wait=0.6):
        self._write_setsid_stub()
        env = dict(os.environ)
        env["AGENT_HOME"] = self.agent_home
        env["PATH"] = self.stubdir + os.pathsep + env.get("PATH", "")
        if extra_env:
            env.update(extra_env)
        stdin_json = json.dumps({
            "session_id": sid,
            "transcript_path": self.transcript,
            "cwd": self.root,
            "model": {"display_name": "Test"},
        })
        t0 = time.time()
        proc = subprocess.run(["bash", _STATUSLINE], input=stdin_json, capture_output=True,
                               text=True, env=env, timeout=15)
        elapsed = time.time() - t0
        time.sleep(wait)   # let the detached `&` subshell finish its (stubbed, near-instant) work
        return proc, elapsed

    def test_trigger_debounce_fresh_sidecar_no_spawn(self):
        sc_dir = os.path.join(self.agent_home, ".fleet-titles")
        os.makedirs(sc_dir, exist_ok=True)
        with open(os.path.join(sc_dir, "sidT.json"), "w", encoding="utf-8") as f:
            json.dump({"title": "x", "ts": time.time(), "source": "refresher", "offset": 0}, f)
        self._run()
        self.assertFalse(os.path.exists(self.sentinel))

    def test_trigger_stale_and_grown_spawns_once(self):
        sc_dir = os.path.join(self.agent_home, ".fleet-titles")
        os.makedirs(sc_dir, exist_ok=True)
        sc_path = os.path.join(sc_dir, "sidT.json")
        with open(sc_path, "w", encoding="utf-8") as f:
            json.dump({"title": "x", "ts": 1, "source": "refresher", "offset": 0}, f)
        old = time.time() - 3600
        os.utime(sc_path, (old, old))
        self._run()
        self.assertTrue(os.path.exists(self.sentinel))
        with open(self.sentinel) as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1)

    def test_trigger_lock_prevents_double_spawn(self):
        lockdir = os.path.join(self.agent_home, ".fleet-titles", ".lock-sidT")
        os.makedirs(lockdir, exist_ok=True)
        self._run()
        self.assertFalse(os.path.exists(self.sentinel))

    def test_trigger_no_delay(self):
        self._write_setsid_stub(sleep_s=3)
        env = dict(os.environ)
        env["AGENT_HOME"] = self.agent_home
        env["PATH"] = self.stubdir + os.pathsep + env.get("PATH", "")
        stdin_json = json.dumps({
            "session_id": "sidT", "transcript_path": self.transcript,
            "cwd": self.root, "model": {"display_name": "Test"},
        })
        t0 = time.time()
        subprocess.run(["bash", _STATUSLINE], input=stdin_json, capture_output=True,
                        text=True, env=env, timeout=15)
        elapsed = time.time() - t0
        self.assertLess(elapsed, 2.0)

    def test_trigger_recursion_guard(self):
        self._run(extra_env={"FLEET_TITLE_REFRESH": "1"})
        self.assertFalse(os.path.exists(self.sentinel))


if __name__ == "__main__":
    unittest.main(verbosity=2)
