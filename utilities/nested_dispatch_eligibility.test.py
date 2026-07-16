#!/usr/bin/env python3
import argparse
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

P = Path(__file__).with_name("nested-dispatch-eligibility.py")
S = importlib.util.spec_from_file_location("nested_eligibility", P)
N = importlib.util.module_from_spec(S)
S.loader.exec_module(N)


class NestedEligibilityTest(unittest.TestCase):
    def args(self, worktree):
        return argparse.Namespace(
            parent_harness="codex",
            parent_transport="headless",
            parent_sandbox="workspace-write",
            child_harness="codex",
            launch_authority="conductor",
            worktree=worktree,
        )

    def test_codex_auth_status_is_required_without_leaking_output(self):
        result = mock.Mock(returncode=1, stdout="private account metadata", stderr="")
        with mock.patch.object(N.shutil, "which", return_value="/bin/codex"), \
             mock.patch.object(N.subprocess, "run", return_value=result):
            self.assertEqual(N.auth_check("codex"), (False, "auth-unavailable"))

    def test_nested_auth_probe_runs_inside_checked_worktree(self):
        result = mock.Mock(returncode=0, stdout="", stderr="Logged in using ChatGPT\n")
        with tempfile.TemporaryDirectory() as worktree, \
             mock.patch.object(N.shutil, "which", return_value="/bin/codex"), \
             mock.patch.object(N.subprocess, "run", return_value=result) as run:
            self.assertEqual(N.auth_check("codex", worktree), (True, ""))
        self.assertEqual(run.call_args.kwargs["cwd"], Path(worktree).resolve())

    def test_codex_owner_requires_network_profile_before_command_check(self):
        with tempfile.TemporaryDirectory() as worktree, \
             mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch.object(N, "command_check") as checked:
            row = N.evaluate(self.args(worktree))
        self.assertEqual(row["status"], "unsupported")
        self.assertEqual(row["failure_class"], "nested-network-unconfirmed")
        checked.assert_not_called()

    def test_checked_owner_profile_and_auth_surface_is_supported(self):
        with tempfile.TemporaryDirectory() as worktree, \
             mock.patch.dict(os.environ, {"AGENT_NESTED_HEADLESS_NETWORK": "1"}, clear=True), \
             mock.patch.object(N, "command_check", return_value=("supported", "direct-auth+headless-check", "")):
            row = N.evaluate(self.args(worktree))
        self.assertEqual(row["status"], "supported")
        self.assertEqual(
            row["probe_source"],
            "codex-owner-network-contract+direct-auth+headless-check",
        )


if __name__ == "__main__":
    unittest.main()
