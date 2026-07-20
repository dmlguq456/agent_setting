"""Tap-based sid recovery + neighbor ai-title theft guard (2026-07-20 fallback-name incident).

Root-cause pair, both fixed here and pinned by these tests:
  (a) `~/.claude/sessions/<pid>.json` registry rows can vanish while their process lives,
      leaving interactive rows sid-less — the statusline tap (§5) now carries the owning
      claude pid + /proc starttime, and enrich() recovers the sid from it (F-25 tier-2);
  (b) a sid-less row borrows the NEWEST neighbor .jsonl in the project dir for liveness and
      also adopted its ai-title — every registry-less same-cwd row collapsed onto one stale
      title. Adoption is now own-`<sid>.jsonl` only (F-26 — misattribution over absence).

Hermetic: temp CLAUDE_CONFIG_DIR only; no real ~/.claude, no live process dependency.
The statusline.sh injection tests drive the real script with a stub `claude` ancestor.
"""
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from fleet.collectors import claude    # noqa: E402
from fleet.model import Session        # noqa: E402

def _find_statusline(start):
    """Repo-root statusline.sh from either home: canonical (adapters/claude/tools) needs
    three hops up, the byte-identical mirror (tools/) needs one — walk until it appears."""
    d = start
    for _ in range(6):
        cand = os.path.join(d, "adapters", "claude", "statusline.sh")
        if os.path.exists(cand):
            return cand
        d = os.path.dirname(d)
    return ""


_STATUSLINE = _find_statusline(_TOOLS_DIR)


class _HomeMixin:
    """Temp CLAUDE_CONFIG_DIR with helpers for registry/tap/transcript fixtures."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = {k: os.environ.get(k) for k in ("CLAUDE_CONFIG_DIR", "FLEET_TITLE_STATE_DIR")}
        self.home = os.path.join(self._tmp.name, "claude")
        os.makedirs(self.home)
        os.environ["CLAUDE_CONFIG_DIR"] = self.home
        os.environ["FLEET_TITLE_STATE_DIR"] = os.path.join(self._tmp.name, "titles")

    def tearDown(self):
        for k, v in self._old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self._tmp.cleanup()

    def _transcript(self, cwd, sid, ai_title=None):
        proj = os.path.join(self.home, "projects", claude._enc_cwd(cwd))
        os.makedirs(proj, exist_ok=True)
        path = os.path.join(proj, sid + ".jsonl")
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "user", "message": "hello"}) + "\n")
            if ai_title:
                f.write(json.dumps({"type": "ai-title", "aiTitle": ai_title}) + "\n")
        return path

    def _tap(self, sid, payload, mtime=None):
        sldir = os.path.join(self.home, ".statusline")
        os.makedirs(sldir, exist_ok=True)
        path = os.path.join(sldir, sid + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        if mtime is not None:
            os.utime(path, (mtime, mtime))
        return path

    def _registry(self, pid, payload):
        rdir = os.path.join(self.home, "sessions")
        os.makedirs(rdir, exist_ok=True)
        with open(os.path.join(rdir, "%d.json" % pid), "w", encoding="utf-8") as f:
            json.dump(payload, f)


class TitleTheftGuardTest(_HomeMixin, unittest.TestCase):
    """(b) — a sid-less row must not wear a neighbor transcript's ai-title."""

    def test_sidless_row_never_adopts_neighbor_ai_title(self):
        self._transcript("/proj/x", "neighbor-sid", ai_title="Stolen Neighbor Title")
        s = Session(harness="claude", pid=999942, cwd="/proj/x", slug="x")
        claude.enrich(s)
        self.assertIsNone(s.title)                 # falls to registry name → slug in render

    def test_sidless_row_still_borrows_mtime_for_liveness(self):
        """Deliberately unchanged this cycle: the mtime borrow (liveness heuristic) stays."""
        self._transcript("/proj/x", "neighbor-sid", ai_title="Stolen Neighbor Title")
        s = Session(harness="claude", pid=999942, cwd="/proj/x", slug="x")
        claude.enrich(s)
        self.assertIsNotNone(s.mtime)

    def test_own_transcript_ai_title_still_adopted(self):
        """Control: the F-14 chain is intact when the row knows its own sid."""
        self._transcript("/proj/x", "own-sid", ai_title="Own Honest Title")
        s = Session(harness="claude", pid=999942, cwd="/proj/x", slug="x", session_id="own-sid")
        claude.enrich(s)
        self.assertEqual(s.title, "Own Honest Title")


class TapSidRecoveryTest(_HomeMixin, unittest.TestCase):
    """(a) — registry silence + matching (pid, proc_start) tap recovers the sid."""

    def _sess(self, **over):
        base = dict(harness="claude", pid=994242, cwd="/proj/y", slug="y")
        base.update(over)
        s = Session(**{k: v for k, v in base.items() if k in ("harness", "pid", "cwd", "slug", "session_id")})
        s.proc_start = over.get("proc_start", "777")
        return s

    def test_recovers_sid_and_own_title(self):
        self._transcript("/proj/y", "own-sid", ai_title="Recovered Own Title")
        self._tap("own-sid", {"session_id": "own-sid", "pid": 994242, "proc_start": "777"})
        s = self._sess()
        claude.enrich(s)
        self.assertEqual(s.session_id, "own-sid")
        self.assertEqual(s.title, "Recovered Own Title")

    def test_proc_start_mismatch_refuses(self):
        """PID reuse: same pid, different starttime → the tap belongs to a dead session."""
        self._tap("own-sid", {"session_id": "own-sid", "pid": 994242, "proc_start": "778"})
        s = self._sess()
        claude.enrich(s)
        self.assertIsNone(s.session_id)

    def test_tap_without_proc_start_refuses(self):
        self._tap("own-sid", {"session_id": "own-sid", "pid": 994242})
        s = self._sess()
        claude.enrich(s)
        self.assertIsNone(s.session_id)

    def test_row_without_proc_start_refuses(self):
        """No /proc identity on our side either → cannot verify, so do not guess."""
        self._tap("own-sid", {"session_id": "own-sid", "pid": 994242, "proc_start": "777"})
        s = self._sess(proc_start=None)
        claude.enrich(s)
        self.assertIsNone(s.session_id)

    def test_registry_sid_wins_over_tap(self):
        """Tier order (F-25): a present registry sessionId is never overridden."""
        self._registry(994242, {"pid": 994242, "sessionId": "registry-sid"})
        self._tap("tap-sid", {"session_id": "tap-sid", "pid": 994242, "proc_start": "777"})
        s = self._sess()
        claude.enrich(s)
        self.assertEqual(s.session_id, "registry-sid")

    def test_newest_matching_tap_wins(self):
        self._tap("old-sid", {"session_id": "old-sid", "pid": 994242, "proc_start": "777"},
                  mtime=1000.0)
        self._tap("new-sid", {"session_id": "new-sid", "pid": 994242, "proc_start": "777"},
                  mtime=2000.0)
        s = self._sess()
        claude.enrich(s)
        self.assertEqual(s.session_id, "new-sid")

    def test_malformed_tap_is_silence(self):
        sldir = os.path.join(self.home, ".statusline")
        os.makedirs(sldir, exist_ok=True)
        with open(os.path.join(sldir, "bad.json"), "w") as f:
            f.write("{not json")
        s = self._sess()
        claude.enrich(s)                            # must not raise
        self.assertIsNone(s.session_id)

    def test_missing_tap_dir_is_silence(self):
        s = self._sess()
        claude.enrich(s)
        self.assertIsNone(s.session_id)

    def test_recovered_sid_feeds_telemetry_and_sidecar_steps(self):
        """The recovery lands BEFORE step 2, so the tap telemetry itself is consumed."""
        self._transcript("/proj/y", "own-sid")
        self._tap("own-sid", {"session_id": "own-sid", "pid": 994242, "proc_start": "777",
                              "cost": {"total_cost_usd": 1.25}})
        s = self._sess()
        claude.enrich(s)
        self.assertEqual(s.session_id, "own-sid")
        self.assertEqual(s.cost, 1.25)


@unittest.skipUnless(os.path.exists(_STATUSLINE) and os.path.isdir("/proc"),
                     "needs adapters/claude/statusline.sh and /proc")
class StatuslineTapInjectionTest(unittest.TestCase):
    """Drives the real statusline.sh under a stub `claude` ancestor: the tap file must be
    valid JSON carrying pid/proc_start, and non-`{"`-prefixed input must stay verbatim."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.agent_home = os.path.join(self._tmp.name, "home")
        os.makedirs(self.agent_home)
        # Stub `claude`: a script whose comm is "claude"; it runs statusline.sh as a child
        # so the ancestor walk finds it (statusline PPID → bash stub, comm == "claude").
        self.stub = os.path.join(self._tmp.name, "claude")
        with open(self.stub, "w", encoding="utf-8") as f:
            # Direct-shebang: `#!/usr/bin/env bash` would exec twice (env → bash) and leave
            # comm "bash"; a direct interpreter keeps comm = script basename = "claude".
            # Trailing `:` stops bash's tail-call exec of the last command — the stub must
            # STAY alive as the statusline child's parent, or the ancestor walk skips it.
            f.write("#!/bin/bash\nbash \"$1\"\nrc=$?\n:\nexit $rc\n")
        os.chmod(self.stub, os.stat(self.stub).st_mode | stat.S_IEXEC)

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, stdin_json):
        env = dict(os.environ)
        env["AGENT_HOME"] = self.agent_home
        env["FLEET_TITLE_DISABLE"] = "1"           # keep the refresher out of the test
        proc = subprocess.Popen([self.stub, _STATUSLINE], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        out, err = proc.communicate(stdin_json.encode("utf-8"), timeout=30)
        return proc, out, err

    def _tap(self, sid):
        with open(os.path.join(self.agent_home, ".statusline", sid + ".json"),
                  encoding="utf-8") as f:
            return f.read()

    def test_tap_gains_pid_and_proc_start(self):
        stdin_json = json.dumps({"session_id": "sidZ", "cwd": "/tmp",
                                 "model": {"display_name": "M"}})
        proc, _out, _err = self._run(stdin_json)
        raw = self._tap("sidZ")
        d = json.loads(raw)                        # valid JSON after injection
        self.assertEqual(d["pid"], proc.pid)       # the stub IS the claude ancestor
        self.assertTrue(str(d["proc_start"]).isdigit())
        self.assertEqual(d["session_id"], "sidZ")  # original fields intact

    def test_non_brace_quote_input_stays_verbatim(self):
        stdin_json = '{ "session_id": "sidY", "cwd": "/tmp" }'
        self._run(stdin_json)
        self.assertEqual(self._tap("sidY"), stdin_json)


if __name__ == "__main__":
    unittest.main()
