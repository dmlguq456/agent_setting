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

    def test_codex_auth_ignores_warnings_before_valid_login_line(self):
        result = mock.Mock(
            returncode=0,
            stdout="",
            stderr=(
                "WARNING: failed to clean up stale arg0 temp dirs\n"
                "Logged in using ChatGPT\n"
            ),
        )
        with mock.patch.object(N.shutil, "which", return_value="/bin/codex"), \
             mock.patch.object(N.subprocess, "run", return_value=result):
            self.assertEqual(N.auth_check("codex"), (True, ""))

    def test_codex_auth_still_requires_zero_exit_with_valid_status_line(self):
        result = mock.Mock(
            returncode=1,
            stdout="Logged in using ChatGPT\n",
            stderr="transient failure\n",
        )
        with mock.patch.object(N.shutil, "which", return_value="/bin/codex"), \
             mock.patch.object(N.subprocess, "run", return_value=result):
            self.assertEqual(N.auth_check("codex"), (False, "auth-unavailable"))

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

    def test_preflight_reason_word_becomes_the_failure_class(self):
        # A route reads `failure_class` back to decide whether another hop is
        # worth attempting, so it must carry the preflight's own enum rather
        # than a joined diagnostic blob.
        result = mock.Mock(
            returncode=65,
            stdout=("check=failed\nreason=invalid-worktree-codex-mount-target\n"
                    "detail=.codex must be a directory while the Codex sandbox is enabled\n"),
            stderr="",
        )
        with tempfile.TemporaryDirectory() as worktree, \
             mock.patch.object(N, "auth_check", return_value=(True, "")), \
             mock.patch.object(N.subprocess, "run", return_value=result):
            self.assertEqual(
                N.command_check("codex", worktree),
                ("unsupported", "direct-headless-check",
                 "invalid-worktree-codex-mount-target"),
            )

    def test_unstructured_preflight_failure_keeps_the_joined_detail(self):
        result = mock.Mock(returncode=69, stdout="", stderr="boom\nsecond line")
        with tempfile.TemporaryDirectory() as worktree, \
             mock.patch.object(N, "auth_check", return_value=(True, "")), \
             mock.patch.object(N.subprocess, "run", return_value=result):
            self.assertEqual(
                N.command_check("codex", worktree),
                ("unsupported", "direct-headless-check", "boom;second line"),
            )

    def test_runtime_surface_label_is_not_a_transport_tuple_value(self):
        with tempfile.TemporaryDirectory() as worktree, \
             mock.patch.object(N, "command_check") as checked:
            args = self.args(worktree)
            args.parent_transport = "codex-exec-headless"
            row = N.evaluate(args)
        self.assertEqual(row["status"], "unsupported")
        self.assertEqual(row["failure_class"], "noncanonical-parent-transport")
        checked.assert_not_called()

    def test_opencode_depth2_child_fails_closed_before_runtime_probe(self):
        with tempfile.TemporaryDirectory() as worktree, \
             mock.patch.dict(os.environ, {"AGENT_NESTED_HEADLESS_NETWORK": "1"}, clear=True), \
             mock.patch.object(N, "command_check") as checked:
            args = self.args(worktree)
            args.child_harness = "opencode"
            row = N.evaluate(args)
        self.assertEqual(row["status"], "unsupported")
        self.assertEqual(row["probe_source"], "dispatch-contract-v3")
        self.assertEqual(
            row["failure_class"],
            "opencode-standard-depth2-unsupported",
        )
        checked.assert_not_called()


if __name__ == "__main__":
    unittest.main()
