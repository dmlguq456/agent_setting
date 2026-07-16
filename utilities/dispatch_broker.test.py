#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "utilities/dispatch-broker.py"
SPEC = importlib.util.spec_from_file_location("dispatch_broker", SCRIPT)
BROKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BROKER)


class RetiredDispatchBrokerTest(unittest.TestCase):
    def command(self, operation: str, root: Path, jobs: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), operation, "--root", str(root), "--jobs", str(jobs), *extra],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_production_operations_are_retired(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "broker"
            jobs = Path(td) / "jobs.log"
            for operation, extra in (
                ("ensure", ()),
                ("request", ()),
                ("serve", ("--instance-id", "brk-retired-fixture")),
            ):
                result = self.command(operation, root, jobs, *extra)
                self.assertEqual(result.returncode, 76, result.stdout + result.stderr)
                self.assertIn("reason=launch-broker-retired", result.stdout)
            self.assertFalse((root / "broker.sock").exists())

    def test_status_and_stop_can_drain_a_legacy_instance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "broker"
            jobs = Path(td) / "jobs.log"
            instance = "brk-retired-fixture"
            server = BROKER.BrokerServer(root, jobs, instance, 5.0)
            thread = threading.Thread(target=server.serve, daemon=True)
            thread.start()
            deadline = time.monotonic() + 3
            while not (root / "broker.sock").exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue((root / "broker.sock").exists())

            status = self.command("status", root, jobs)
            self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
            self.assertIn("broker_lifecycle=retired", status.stdout)
            self.assertIn(f"broker_instance={instance}", status.stdout)

            stopped = self.command("stop", root, jobs)
            self.assertEqual(stopped.returncode, 0, stopped.stdout + stopped.stderr)
            thread.join(timeout=3)
            self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()
