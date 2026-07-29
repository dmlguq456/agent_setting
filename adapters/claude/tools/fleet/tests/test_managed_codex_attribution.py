#!/usr/bin/env python3
"""Hermetic test — managed (client-server) Codex must attribute its rollout to the TUI row.

`codex-managed-entry.py` splits one session across two `codex` processes sharing a
`~/.codex/.harness/managed-sessions/<name>/` state dir:
  · `codex app-server --listen unix://<dir>/app-server.sock` — holds the rollout fd, and
    procscan marks it an app_server companion (hidden from the render).
  · `codex --remote unix://<dir>/managed-tui.sock` — the row the user actually sees, with
    NO transcript fd at all.
Before this transfer the visible row lost session_id/title/context entirely (사용자
2026-07-29 "codex가 아예 안 잡혀"). The state dir is the deterministic join key; a dir
without exactly one owning app-server and one TUI client stays unattributed (F-26), and a
donated rollout is never claimed twice (F-24).
/proc fd reads are monkeypatched; the rollout file is real so `_rollout_meta`/`_sid` run.
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from fleet.collectors import codex, procscan  # noqa: E402
from fleet.model import Session  # noqa: E402

_SID = "019facc9-fe83-7480-89f6-9e64fbebf0ca"
_REAL_LISTDIR = os.listdir
_REAL_READLINK = os.readlink


def _make_rollout(home, cwd, sid=_SID):
    d = os.path.join(home, "sessions", "2026", "07", "29")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "rollout-2026-07-29T09-15-02-%s.jsonl" % sid)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "session_meta",
                            "payload": {"cwd": cwd, "id": sid}}) + "\n")
    return path


def _session(pid, cwd, managed_dir, app_server=False):
    return Session(harness="codex", pid=pid, cwd=cwd, app_server=app_server,
                   managed_dir=managed_dir, elapsed_min=5,
                   slug=os.path.basename(cwd.rstrip("/")))


class _FdStub:
    """Serve /proc/<pid>/fd from a pid -> [paths] map; every other path hits the real os."""

    def __init__(self, fds):
        self.fds = fds

    def _pid(self, path):
        parts = path.split("/")
        if len(parts) >= 4 and parts[1] == "proc" and parts[3] == "fd":
            try:
                return int(parts[2]), (parts[4] if len(parts) > 4 else None)
            except ValueError:
                return None, None
        return None, None

    def listdir(self, path):
        pid, _ = self._pid(path)
        if pid is None:
            return _REAL_LISTDIR(path)
        return [str(i) for i in range(len(self.fds.get(pid, [])))]

    def readlink(self, path):
        pid, fd = self._pid(path)
        if pid is None or fd is None:
            return _REAL_READLINK(path)
        return self.fds[pid][int(fd)]


class ManagedCodexAttributionTest(unittest.TestCase):
    def _prepare(self, sessions, fds, home):
        stub = _FdStub(fds)
        with mock.patch.dict(os.environ, {"CODEX_HOME": home}), \
             mock.patch.object(codex.os, "listdir", side_effect=stub.listdir), \
             mock.patch.object(codex.os, "readlink", side_effect=stub.readlink):
            return codex.prepare_tick(sessions)

    def test_tui_row_inherits_the_app_server_rollout(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, cwd = os.path.join(tmp, "dot-codex"), os.path.join(tmp, "agent_setting")
            os.makedirs(cwd, exist_ok=True)
            rollout = _make_rollout(home, cwd)
            managed = os.path.join(home, ".harness", "managed-sessions", "session-r5rh60f9")
            server = _session(100, cwd, managed, app_server=True)
            tui = _session(200, cwd, managed)
            tick = self._prepare([server, tui], {100: [rollout], 200: []}, home)

            self.assertEqual(tick.proc_paths, {200: rollout})
            self.assertIn(100, tick.no_fallback_pids)

            with mock.patch.dict(os.environ, {"CODEX_HOME": home}):
                for sess in (server, tui):
                    codex.enrich(sess, tick=tick)
            self.assertEqual(tui.session_id, _SID)
            self.assertIsNotNone(tui.mtime)
            # F-24: one sid, one row — the donor must not re-claim it via the fallback.
            self.assertIsNone(server.session_id)
            sids = [s.session_id for s in (server, tui) if s.session_id]
            self.assertEqual(len(sids), len(set(sids)))

    def test_different_managed_dirs_do_not_transfer(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, cwd = os.path.join(tmp, "dot-codex"), os.path.join(tmp, "agent_setting")
            os.makedirs(cwd, exist_ok=True)
            rollout = _make_rollout(home, cwd)
            base = os.path.join(home, ".harness", "managed-sessions")
            server = _session(100, cwd, os.path.join(base, "session-aaa"), app_server=True)
            tui = _session(200, cwd, os.path.join(base, "session-bbb"))
            tick = self._prepare([server, tui], {100: [rollout], 200: []}, home)
            self.assertEqual(tick.proc_paths, {100: rollout})
            self.assertEqual(tick.no_fallback_pids, frozenset())

    def test_two_clients_in_one_managed_dir_stay_unattributed(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, cwd = os.path.join(tmp, "dot-codex"), os.path.join(tmp, "agent_setting")
            os.makedirs(cwd, exist_ok=True)
            rollout = _make_rollout(home, cwd)
            managed = os.path.join(home, ".harness", "managed-sessions", "session-r5rh60f9")
            server = _session(100, cwd, managed, app_server=True)
            tick = self._prepare(
                [server, _session(200, cwd, managed), _session(201, cwd, managed)],
                {100: [rollout], 200: [], 201: []}, home)
            self.assertEqual(tick.proc_paths, {100: rollout})

    def test_plain_codex_row_has_no_managed_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, cwd = os.path.join(tmp, "dot-codex"), os.path.join(tmp, "agent_setting")
            os.makedirs(cwd, exist_ok=True)
            rollout = _make_rollout(home, cwd)
            tick = self._prepare([_session(100, cwd, None)], {100: [rollout]}, home)
            self.assertEqual(tick.proc_paths, {100: rollout})
            self.assertEqual(tick.no_fallback_pids, frozenset())


class ManagedDirParseTest(unittest.TestCase):
    def test_listen_and_remote_argv_yield_the_same_dir(self):
        managed = "/home/u/.codex/.harness/managed-sessions/session-r5rh60f9"
        self.assertEqual(
            procscan._managed_dir("codex app-server --listen unix://%s/app-server.sock" % managed),
            managed)
        self.assertEqual(
            procscan._managed_dir("codex --remote unix://%s/managed-tui.sock --yolo" % managed),
            managed)

    def test_unrelated_argv_yields_none(self):
        self.assertIsNone(procscan._managed_dir("codex --yolo"))
        self.assertIsNone(procscan._managed_dir("codex exec --cd /repo 'do a thing'"))
        self.assertIsNone(procscan._managed_dir(""))
        self.assertIsNone(procscan._managed_dir(None))


if __name__ == "__main__":
    unittest.main()
