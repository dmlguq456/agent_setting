#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WATCH = ROOT / "utilities" / "dispatch-orphan-watch.py"


class OrphanWatchTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.home = self.base / "home"
        self.jobs = self.base / "jobs.log"
        self.route_id = "rt-watch"
        self.route = self.base / "route.json"
        self.route.write_text(json.dumps({
            "route_id": self.route_id,
            "nodes": [
                {"id": "plan", "depends_on": []},
                {"id": "execute", "depends_on": ["plan"]},
            ],
        }))
        marker_dir = self.home / ".dispatch" / "completion" / self.route_id
        marker_dir.mkdir(parents=True)
        (marker_dir / "plan.json").write_text(json.dumps({"node_id": "plan"}))
        self.owner = subprocess.Popen(["sleep", "60"])
        self.owner_start = self.proc_start(self.owner.pid)
        self.children = []

    def tearDown(self):
        if self.owner.poll() is None:
            self.owner.kill()
        self.owner.wait()
        for child in self.children:
            if child.poll() is None:
                child.kill()
            child.wait()
        self.temp.cleanup()

    @staticmethod
    def proc_start(pid):
        raw = (Path("/proc") / str(pid) / "stat").read_text()
        return raw[raw.rfind(")") + 2:].split()[19]

    def write_rows(self, completed_owner=False, child=None):
        status = "done" if completed_owner else "open"
        child_pid = child.pid if child is not None else 99999999
        child_start = self.proc_start(child.pid) if child is not None else "1"
        current = (
            "attempt_schema_version=2,transport=headless,"
            "execution_surface=registered-headless,registered_worker=1,"
            "fallback_hop=same-harness-headless"
        )
        self.jobs.write_text(
            f"2026-07-19T00:00:00Z\t{status}\t/r\t/w\towner\t"
            f"{current},dispatch_depth=1,worker_type=owner,attempt_id=att-watch,"
            f"pid={self.owner.pid},pid_start={self.owner_start}\n"
            "2026-07-19T00:00:01Z\topen\t/r\t/w\tchild\t"
            f"{current},dispatch_depth=2,route_id={self.route_id},"
            f"route_file={self.route},route_node=execute,attempt_id=att-child,"
            f"parent=owner,parent_attempt_id=att-watch,pid={child_pid},"
            f"pid_start={child_start}\n"
        )

    def watcher(self):
        return subprocess.Popen([
            sys.executable, str(WATCH),
            "--jobs", str(self.jobs),
            "--agent-home", str(self.home),
            "--attempt-id", "att-watch",
            "--pid", str(self.owner.pid),
            "--pid-start", self.owner_start,
            "--interval", "0.02",
        ])

    def test_owner_exit_reaps_exact_child_group_and_closes_both_rows(self):
        child = subprocess.Popen(["sleep", "60"], start_new_session=True)
        self.children.append(child)
        self.write_rows(child=child)
        watcher = self.watcher()
        time.sleep(0.05)
        self.owner.kill(); self.owner.wait()
        self.assertEqual(watcher.wait(timeout=5), 0)
        text = self.jobs.read_text()
        self.assertIn("\tdone\t/r\t/w\towner\t", text)
        self.assertIn("note=dead-parent-orphaned", text)
        self.assertIn("\tdone\t/r\t/w\tchild\t", text)
        self.assertIn("note=dead-parent-terminated", text)
        self.assertIsNotNone(child.poll())

    def test_terminal_owner_makes_watcher_exit_without_mutation(self):
        self.write_rows(completed_owner=True)
        before = self.jobs.read_text()
        watcher = self.watcher()
        self.assertEqual(watcher.wait(timeout=5), 0)
        self.assertEqual(self.jobs.read_text(), before)


if __name__ == "__main__":
    unittest.main()
