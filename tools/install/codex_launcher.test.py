#!/usr/bin/env python3
"""Unit tests for the reversible Codex CLI launcher installation."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parent))
import codex_launcher as launcher


class CodexLauncherInstallTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.codex_home = self.home / ".codex"
        self.bin_dir = self.home / ".local" / "bin"
        self.real = self.root / "runtime" / "codex-real"
        self.real.parent.mkdir(parents=True)
        self.real.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.real.chmod(0o755)
        self.codex_home.mkdir(parents=True)
        self.codex_home.chmod(0o775)
        self.bin_dir.mkdir(parents=True)
        self.target = self.bin_dir / "codex"
        self.target.symlink_to(self.real)
        self.environment = mock.patch.dict(
            os.environ,
            {
                "HOME": str(self.home),
                "CODEX_HOME": str(self.codex_home),
                "HARNESS_BIN_DIR": str(self.bin_dir),
                "PATH": str(self.bin_dir),
            },
            clear=False,
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_install_repair_and_uninstall_restore_exact_binding(self) -> None:
        created = launcher.install(codex_home=self.codex_home, bin_dir=self.bin_dir)
        self.assertEqual(created["status"], "created")
        self.assertTrue(self.target.is_file())
        self.assertFalse(self.target.is_symlink())
        self.assertEqual(self.target.stat().st_mode & 0o777, 0o755)
        self.assertEqual(self.codex_home.stat().st_mode & 0o777, 0o700)

        state = json.loads(launcher.state_path(self.codex_home).read_text())
        self.assertEqual(state["phase"], "installed")
        self.assertEqual(state["previous_wrapper"], {"kind": "symlink", "target": str(self.real)})
        self.assertEqual(state["previous_codex_home_mode"], 0o775)
        self.assertEqual(launcher.install(codex_home=self.codex_home, bin_dir=self.bin_dir)["status"], "unchanged")

        self.target.unlink()
        self.target.symlink_to(self.real)
        repaired = launcher.install(codex_home=self.codex_home, bin_dir=self.bin_dir)
        self.assertEqual(repaired["status"], "repaired")
        repaired_state = json.loads(launcher.state_path(self.codex_home).read_text())
        self.assertEqual(repaired_state["previous_codex_home_mode"], 0o775)

        restored = launcher.uninstall(codex_home=self.codex_home, bin_dir=self.bin_dir)
        self.assertEqual(restored["status"], "restored")
        self.assertTrue(self.target.is_symlink())
        self.assertEqual(os.readlink(self.target), str(self.real))
        self.assertEqual(self.codex_home.stat().st_mode & 0o777, 0o775)

    def test_adopts_byte_exact_orphaned_wrapper(self) -> None:
        self.target.unlink()
        self.target.write_bytes(launcher.wrapper_bytes())
        self.target.chmod(0o755)

        created = launcher.install(
            codex_home=self.codex_home,
            bin_dir=self.bin_dir,
            real_command=str(self.real),
        )

        self.assertEqual(created["status"], "created")
        state = json.loads(launcher.state_path(self.codex_home).read_text())
        self.assertEqual(
            state["previous_wrapper"],
            {"kind": "symlink", "target": str(self.real.absolute())},
        )
        self.assertEqual(
            launcher.uninstall(codex_home=self.codex_home, bin_dir=self.bin_dir)["status"],
            "restored",
        )
        self.assertTrue(self.target.is_symlink())
        self.assertEqual(os.readlink(self.target), str(self.real.absolute()))
        self.assertFalse(launcher.state_path(self.codex_home).exists())

    def test_upgrade_repairs_previous_managed_wrapper_bytes(self) -> None:
        launcher.install(codex_home=self.codex_home, bin_dir=self.bin_dir)
        upgraded = launcher.wrapper_bytes() + b"# upgraded fixture\n"

        with mock.patch.object(launcher, "wrapper_bytes", return_value=upgraded):
            repaired = launcher.install(codex_home=self.codex_home, bin_dir=self.bin_dir)

        self.assertEqual(repaired["status"], "repaired")
        self.assertEqual(self.target.read_bytes(), upgraded)

    def test_update_recovers_when_recorded_real_command_moves(self) -> None:
        launcher.install(codex_home=self.codex_home, bin_dir=self.bin_dir)
        replacement = self.root / "codex-new"
        replacement.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        replacement.chmod(0o755)
        self.real.unlink()

        repaired = launcher.install(
            codex_home=self.codex_home,
            bin_dir=self.bin_dir,
            real_command=str(replacement),
        )

        self.assertEqual(repaired["status"], "repaired")
        state = json.loads(launcher.state_path(self.codex_home).read_text())
        self.assertEqual(state["real_command"], str(replacement))
        self.assertTrue(launcher.status(codex_home=self.codex_home, bin_dir=self.bin_dir)["healthy"])

    def test_dry_run_does_not_create_runtime_paths(self) -> None:
        other_home = self.root / "dry-home"
        other_bin = self.root / "dry-bin"
        result = launcher.install(
            codex_home=other_home,
            bin_dir=other_bin,
            real_command=str(self.real),
            dry_run=True,
        )
        self.assertEqual(result["status"], "planned")
        self.assertFalse(other_home.exists())
        self.assertFalse(other_bin.exists())

    def test_foreign_file_is_never_overwritten(self) -> None:
        self.target.unlink()
        self.target.write_text("user-owned\n", encoding="utf-8")
        before = self.target.read_bytes()
        with self.assertRaises(launcher.CodexLauncherError):
            launcher.install(
                codex_home=self.codex_home,
                bin_dir=self.bin_dir,
                real_command=str(self.real),
            )
        self.assertEqual(self.target.read_bytes(), before)
        self.assertFalse(launcher.state_path(self.codex_home).exists())

    def test_missing_real_cli_has_a_typed_result(self) -> None:
        self.target.unlink()
        with mock.patch.object(launcher.shutil, "which", return_value=None):
            with self.assertRaises(launcher.CodexUnavailableError):
                launcher.install(codex_home=self.codex_home, bin_dir=self.bin_dir)

    def _write_foreign_wrapper(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(launcher.wrapper_bytes())
        path.chmod(0o755)

    def test_binding_skips_a_foreign_install_wrapper_on_path(self) -> None:
        # A second HOME's wrapper earlier on PATH must never become real_command:
        # binding to it makes the launcher exec itself forever.
        foreign_bin = self.root / "other-home" / ".local" / "bin"
        self._write_foreign_wrapper(foreign_bin / "codex")
        real_bin = self.root / "real-bin"
        real_bin.mkdir()
        real_cli = real_bin / "codex"
        real_cli.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        real_cli.chmod(0o755)
        self.target.unlink()
        with mock.patch.dict(
            os.environ, {"PATH": os.pathsep.join([str(foreign_bin), str(real_bin)])}
        ):
            with mock.patch.object(
                launcher.shutil, "which", return_value=str(foreign_bin / "codex")
            ):
                created = launcher.install(codex_home=self.codex_home, bin_dir=self.bin_dir)
        self.assertEqual(created["status"], "created")
        state = json.loads(launcher.state_path(self.codex_home).read_text())
        self.assertEqual(state["real_command"], str(real_cli))

    def test_binding_fails_closed_when_only_wrappers_are_on_path(self) -> None:
        foreign_bin = self.root / "other-home" / ".local" / "bin"
        self._write_foreign_wrapper(foreign_bin / "codex")
        self.target.unlink()
        with mock.patch.dict(os.environ, {"PATH": str(foreign_bin)}):
            with mock.patch.object(
                launcher.shutil, "which", return_value=str(foreign_bin / "codex")
            ):
                with self.assertRaises(launcher.CodexUnavailableError):
                    launcher.install(codex_home=self.codex_home, bin_dir=self.bin_dir)

    def test_explicit_wrapper_real_command_is_rejected(self) -> None:
        foreign = self.root / "elsewhere" / "codex"
        self._write_foreign_wrapper(foreign)
        self.target.unlink()
        with self.assertRaises(launcher.CodexLauncherError):
            launcher.install(
                codex_home=self.codex_home,
                bin_dir=self.bin_dir,
                real_command=str(foreign),
            )


if __name__ == "__main__":
    unittest.main()
