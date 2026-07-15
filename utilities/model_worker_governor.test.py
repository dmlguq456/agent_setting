#!/usr/bin/env python3

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PATH = Path(__file__).with_name("model-worker-governor.py")
SPEC = importlib.util.spec_from_file_location("model_worker_governor", PATH)
GOVERNOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GOVERNOR)


class GovernorTest(unittest.TestCase):
    def test_caps_release_and_kill_switch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tokens = [GOVERNOR.acquire(temp_dir, "dispatch") for _ in range(3)]
            with self.assertRaisesRegex(ValueError, "class cap"):
                GOVERNOR.acquire(temp_dir, "dispatch")
            GOVERNOR.release(temp_dir, tokens.pop())
            tokens.append(GOVERNOR.acquire(temp_dir, "dispatch"))
            Path(temp_dir, "KILL_SWITCH").touch()
            with self.assertRaisesRegex(ValueError, "kill switch"):
                GOVERNOR.acquire(temp_dir, "title")

    def test_fifty_attempts_are_bounded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            admitted = 0
            for _ in range(50):
                try:
                    GOVERNOR.acquire(temp_dir, "dispatch")
                    admitted += 1
                except ValueError:
                    pass
            self.assertEqual(admitted, 3)

    def test_check_does_not_consume_start_budget(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for _ in range(10):
                GOVERNOR.check(temp_dir, "dispatch", budget=1)
            token = GOVERNOR.acquire(temp_dir, "dispatch", budget=1)
            GOVERNOR.release(temp_dir, token)
            with self.assertRaisesRegex(ValueError, "start budget"):
                GOVERNOR.acquire(temp_dir, "dispatch", budget=1)

    def test_artifact_root_is_the_worker_writable_default(self):
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.dict(
            os.environ,
            {"AGENT_ARTIFACT_ROOT": temp_dir},
            clear=False,
        ):
            os.environ.pop("AGENT_MODEL_GOVERNOR_ROOT", None)
            self.assertEqual(
                GOVERNOR.default_root(),
                Path(temp_dir) / ".runtime" / "model-worker-governor",
            )


if __name__ == "__main__":
    unittest.main()
