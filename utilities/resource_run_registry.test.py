#!/usr/bin/env python3
import json
import os
import tempfile
import unittest
from pathlib import Path

import resource_run_registry as registry


class ResourceRegistryTest(unittest.TestCase):
    def test_live_exited_and_pid_reuse(self):
        row = {"pid": 7, "starttime": "11", "command_hash": "abc"}
        exact = lambda pid: {"pid": pid, "starttime": "11", "command_hash": "abc"}
        reused = lambda pid: {"pid": pid, "starttime": "12", "command_hash": "def"}
        self.assertEqual(registry.classify_identity(row, exact)[0], "working")
        self.assertEqual(registry.classify_identity(row, lambda _pid: None)[0], "exited")
        self.assertEqual(registry.classify_identity(row, reused)[0], "stale")
        unreadable = {**row, "pid": os.getpid()}
        self.assertEqual(registry.classify_identity(
            unreadable, lambda _pid: None)[0], "stale")

    def test_multi_project_index_and_malformed_registry_isolation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            index = root / "index.json"
            good_a = root / "a.json"
            good_b = root / "b.json"
            bad = root / "bad.json"
            identity = {"pid": 7, "starttime": "11", "command_hash": "abc"}
            for path, cwd, run_id in (
                (good_a, "/projects/a", "a1"),
                (good_b, "/projects/b", "b1"),
            ):
                path.write_text(json.dumps({
                    "schema_version": 1,
                    "runs": {run_id: {**identity, "cwd": cwd, "status": "running"}},
                }))
                registry.register_registry(path, index)
            bad.write_text("{")
            # An indexed registry can later become malformed; collection must
            # preserve every other project.
            payload = json.loads(index.read_text())
            payload["registries"]["bad"] = {"path": str(bad)}
            index.write_text(json.dumps(payload))
            rows, diagnostics = registry.scan(index, identity_reader=lambda pid: identity)
            self.assertEqual({row["run_id"] for row in rows}, {"a1", "b1"})
            self.assertEqual({row["cwd"] for row in rows}, {"/projects/a", "/projects/b"})
            self.assertTrue(any(d["kind"] == "malformed-registry" for d in diagnostics))


if __name__ == "__main__":
    unittest.main()
