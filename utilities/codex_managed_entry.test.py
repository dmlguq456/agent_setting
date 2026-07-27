#!/usr/bin/env python3

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "utilities" / "codex-managed-entry.py"


class ManagedEntryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / "codex-home"
        self.state = self.base / "state"
        self.workspace = self.base / "workspace"
        for path in (self.home, self.state, self.workspace):
            path.mkdir()
        os.chmod(self.home, 0o700)
        os.chmod(self.state, 0o700)
        (self.home / "auth.json").write_text("{}\n", encoding="utf-8")
        self.fake_codex = self.base / "fake-codex.py"
        self.fake_codex.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import signal, socket, sys, time
                listen = sys.argv[sys.argv.index('--listen') + 1]
                path = listen[len('unix://'):] if listen.startswith('unix://') else listen
                server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                server.bind(path)
                server.listen(1)
                stop = False
                def end(*_args):
                    global stop
                    stop = True
                signal.signal(signal.SIGTERM, end)
                while not stop:
                    time.sleep(0.02)
                server.close()
                """
            ),
            encoding="utf-8",
        )
        self.fake_codex.chmod(0o755)
        self.client = self.base / "client.py"
        self.result = self.base / "client-result.json"
        self.client.write_text(
            textwrap.dedent(
                """\
                import json, os, pathlib, sys
                remote, result = sys.argv[1:]
                value = {
                    'remote': remote,
                    'gateway': os.environ.get('AGENT_CODEX_MANAGED_GATEWAY'),
                    'parent_runtime': os.environ.get('AGENT_CODEX_MANAGED_PARENT_RUNTIME'),
                    'control': os.environ.get('AGENT_CODEX_MANAGED_CONTROL_SOCKET'),
                    'codex_home': os.environ.get('CODEX_HOME'),
                    'agent_home': os.environ.get('AGENT_HOME'),
                }
                pathlib.Path(result).write_text(json.dumps(value), encoding='utf-8')
                """
            ),
            encoding="utf-8",
        )

    def command(self) -> list[str]:
        client_command = (
            f"{sys.executable} {self.client} {{remote}} {self.result}"
        )
        return [
            sys.executable,
            str(ENTRY),
            "--codex",
            str(self.fake_codex),
            "--codex-home",
            str(self.home),
            "--state-dir",
            str(self.state),
            "--workspace",
            str(self.workspace),
            "--client-command",
            client_command,
        ]

    def test_new_session_opt_in_exports_managed_contract_and_cleans_sockets(self) -> None:
        result = subprocess.run(
            self.command(), text=True, capture_output=True, timeout=15
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        value = json.loads(self.result.read_text(encoding="utf-8"))
        self.assertEqual(value["gateway"], "1")
        self.assertEqual(value["parent_runtime"], "codex")
        self.assertEqual(value["codex_home"], str(self.home))
        self.assertEqual(value["agent_home"], str(ROOT))
        self.assertEqual(
            value["remote"], f"unix://{self.state / 'managed-tui.sock'}"
        )
        self.assertEqual(
            value["control"], str(self.state / "managed-control.sock")
        )
        for name in (
            "app-server.sock",
            "managed-tui.sock",
            "managed-control.sock",
        ):
            self.assertFalse((self.state / name).exists())

    def test_nonprivate_state_dir_fails_before_process_start(self) -> None:
        os.chmod(self.state, 0o755)
        result = subprocess.run(
            self.command(), text=True, capture_output=True, timeout=5
        )
        self.assertEqual(result.returncode, 65)
        self.assertIn("state-dir-permissions-unsafe", result.stderr)
        self.assertFalse(self.result.exists())


if __name__ == "__main__":
    unittest.main()
