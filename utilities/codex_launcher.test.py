#!/usr/bin/env python3
"""Unit tests for interactive/pass-through Codex launcher routing."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).with_name("codex-launcher.py")
SPEC = importlib.util.spec_from_file_location("codex_launcher_runtime", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


class CodexLauncherRuntimeTest(unittest.TestCase):
    def test_only_interactive_surfaces_are_managed(self) -> None:
        managed = (
            [],
            ["hello"],
            ["resume", "--last"],
            ["fork"],
            ["--model", "gpt-test", "resume", "thread-id"],
        )
        passed_through = (
            ["exec", "task"],
            ["--model", "gpt-test", "exec", "task"],
            ["plugin", "list"],
            ["app-server", "--help"],
            ["--help"],
            ["resume", "--help"],
            ["--remote", "unix:///tmp/codex.sock"],
        )
        for args in managed:
            with self.subTest(args=args):
                self.assertTrue(launcher.should_manage(list(args)))
        for args in passed_through:
            with self.subTest(args=args):
                self.assertFalse(launcher.should_manage(list(args)))

    def test_bypass_environment_is_explicit(self) -> None:
        with mock.patch.dict(os.environ, {"AGENT_CODEX_LAUNCHER_BYPASS": "1"}):
            self.assertFalse(launcher.should_manage(["resume", "--last"]))

    def test_workspace_honors_global_cd(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with mock.patch.object(launcher.Path, "cwd", return_value=root):
                self.assertEqual(
                    launcher.workspace(["-C", "nested", "resume"]),
                    root / "nested",
                )
                self.assertEqual(
                    launcher.workspace(["--cd=other", "fork"]),
                    root / "other",
                )

    def test_managed_command_uses_private_per_session_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / ".codex"
            home.mkdir()
            agent_home = root / "agent-harness"
            entry = agent_home / "utilities" / "codex-managed-entry.py"
            entry.parent.mkdir(parents=True)
            entry.write_text("# fixture\n", encoding="utf-8")
            real = root / "codex-real"
            real.write_text("# fixture\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"AGENT_HOME": str(agent_home)}):
                command = launcher.managed_command(["resume", "--last"], home, real)
            self.assertEqual(command[1], str(entry))
            self.assertEqual(command[command.index("--codex") + 1], str(real))
            state_dir = Path(command[command.index("--state-dir") + 1])
            self.assertEqual(state_dir.parent, home / ".harness" / "managed-sessions")
            self.assertEqual(state_dir.stat().st_mode & 0o777, 0o700)
            self.assertEqual(
                command[command.index("--jobs") + 1],
                str(home / ".harness" / "dispatch" / "jobs.log"),
            )
            self.assertEqual(command[-3:], ["--", "resume", "--last"])

    def test_auth_readiness_preserves_first_login_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            self.assertFalse(launcher.managed_auth_ready(home))
            auth = home / "auth.json"
            auth.write_text("{}\n", encoding="utf-8")
            auth.chmod(0o600)
            self.assertTrue(launcher.managed_auth_ready(home))
            auth.chmod(0o644)
            self.assertFalse(launcher.managed_auth_ready(home))

    def test_private_runtime_home_falls_back_to_global_binding_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            private_home = root / "private-codex"
            private_home.mkdir()
            default_home = root / ".codex"
            state = default_home / ".harness" / "codex-launcher.json"
            state.parent.mkdir(parents=True)
            state.write_text("{}\n", encoding="utf-8")
            with mock.patch.object(launcher.Path, "home", return_value=root):
                self.assertEqual(launcher.launcher_state_home(private_home), default_home)

            private_state = private_home / ".harness" / "codex-launcher.json"
            private_state.parent.mkdir()
            private_state.write_text("{}\n", encoding="utf-8")
            with mock.patch.object(launcher.Path, "home", return_value=root):
                self.assertEqual(launcher.launcher_state_home(private_home), private_home)


if __name__ == "__main__":
    unittest.main()
