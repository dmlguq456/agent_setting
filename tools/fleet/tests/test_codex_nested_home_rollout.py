#!/usr/bin/env python3
"""Hermetic test — codex `_proc_rollout` must resolve rollouts outside the fleet's own home.

A dispatched codex worker runs with a worktree-local CODEX_HOME
(`.dispatch/nested-codex-home`), so its rollout never lives under the fleet process's
default home. The old home-prefix filter silently dropped every nested child, which is
why they never earned a title/subtitle (사용자 2026-07-19 "codex 분사 세션에는 안 뜨길래").
/proc access is monkeypatched; the rollout file itself is a real tmp file so
`_rollout_meta`/`_sid` run for real.
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

from fleet.collectors import codex  # noqa: E402

_SID = "019f78f9-c11c-7fb2-afed-ae3730e4d811"


def _make_rollout(root, cwd, sid=_SID):
    d = os.path.join(root, "sessions", "2026", "07", "19")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "rollout-2026-07-19T15-04-21-%s.jsonl" % sid)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "session_meta",
                            "payload": {"cwd": cwd, "id": sid}}) + "\n")
    return path


class NestedHomeRolloutTest(unittest.TestCase):
    def _resolve(self, rollout_path, cwd, home):
        with mock.patch.object(codex.os, "listdir", return_value=["7"]), \
             mock.patch.object(codex.os, "readlink", return_value=rollout_path):
            return codex._proc_rollout(4242, cwd, home)

    def test_nested_home_rollout_is_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            worktree = os.path.join(tmp, "agent_setting-wt", "conductor-reliability")
            nested_home = os.path.join(worktree, ".dispatch", "nested-codex-home")
            default_home = os.path.join(tmp, "dot-codex")
            os.makedirs(worktree, exist_ok=True)
            rollout = _make_rollout(nested_home, worktree)
            self.assertEqual(self._resolve(rollout, worktree, default_home), rollout)

    def test_single_held_fd_wins_despite_cwd_mismatch(self):
        # `codex exec --cd <worktree>` keeps the PROCESS cwd at the launch dir while
        # session_meta records the --cd target — the fd itself is the ownership proof
        # when it is the only rollout the process holds.
        with tempfile.TemporaryDirectory() as tmp:
            worktree = os.path.join(tmp, "wt-a")
            launch_dir = os.path.join(tmp, "primary")
            os.makedirs(worktree, exist_ok=True)
            os.makedirs(launch_dir, exist_ok=True)
            rollout = _make_rollout(os.path.join(worktree, ".dispatch", "nested-codex-home"),
                                    worktree)
            self.assertEqual(self._resolve(rollout, launch_dir,
                                           os.path.join(tmp, "dot-codex")), rollout)

    def test_multiple_unmatched_rollouts_still_refused(self):
        # An app-server holds many sessions' rollouts — guessing among cwd-unmatched
        # candidates would be the misattribution F-26 forbids.
        with tempfile.TemporaryDirectory() as tmp:
            wt_a = os.path.join(tmp, "wt-a")
            wt_b = os.path.join(tmp, "wt-b")
            launch_dir = os.path.join(tmp, "primary")
            for d in (wt_a, wt_b, launch_dir):
                os.makedirs(d, exist_ok=True)
            r1 = _make_rollout(os.path.join(wt_a, "home"), wt_a)
            r2 = _make_rollout(os.path.join(wt_b, "home"), wt_b,
                               sid="019f78f9-c11c-7fb2-afed-ae3730e4d812")
            links = {"5": r1, "6": r2}
            with mock.patch.object(codex.os, "listdir", return_value=list(links)), \
                 mock.patch.object(codex.os, "readlink",
                                   side_effect=lambda p: links[p.rsplit("/", 1)[-1]]):
                self.assertIsNone(codex._proc_rollout(4242, launch_dir,
                                                      os.path.join(tmp, "dot-codex")))

    def test_non_rollout_fd_still_refused(self):
        # A random jsonl outside any sessions/ tree (or without the rollout filename
        # shape) must not be picked up.
        with tempfile.TemporaryDirectory() as tmp:
            stray = os.path.join(tmp, "notes.jsonl")
            with open(stray, "w", encoding="utf-8") as f:
                f.write("{}\n")
            self.assertIsNone(self._resolve(stray, tmp, os.path.join(tmp, "dot-codex")))


if __name__ == "__main__":
    unittest.main()
