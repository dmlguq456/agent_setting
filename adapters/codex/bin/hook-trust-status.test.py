#!/usr/bin/env python3
"""Tests for authoritative Codex hook current-hash trust inspection."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import sys


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "hook_trust_status", HERE / "hook-trust-status.py"
)
TRUST = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = TRUST
SPEC.loader.exec_module(TRUST)


class FakeServer:
    def __init__(self, result):
        self.result = result
        self.closed = False

    def request(self, method, _params):
        if method == "initialize":
            return {}
        if method == "hooks/list":
            return self.result
        raise AssertionError(method)

    def notify(self, method):
        if method != "initialized":
            raise AssertionError(method)

    def close(self):
        self.closed = True


class HookTrustStatusTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.hooks = self.root / "hooks.json"
        self.hooks.write_text(
            json.dumps(
                {
                    "hooks": {
                        "Stop": [
                            {
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "python stop.py",
                                        "timeout": 600,
                                    }
                                ]
                            }
                        ],
                        "PreToolUse": [
                            {
                                "matcher": "*",
                                "hooks": [
                                    {"type": "command", "command": "python guard.py"}
                                ],
                            }
                        ],
                    }
                }
            ),
            encoding="utf-8",
        )

    def result(self, stop_status="trusted", include_pretool=True):
        hooks = [
            {
                "sourcePath": str(self.hooks),
                "eventName": "stop",
                "enabled": True,
                "trustStatus": stop_status,
            }
        ]
        if include_pretool:
            hooks.append(
                {
                    "sourcePath": str(self.hooks),
                    "eventName": "pre_tool_use",
                    "enabled": True,
                    "trustStatus": "trusted",
                }
            )
        return {"data": [{"cwd": str(self.root), "hooks": hooks}]}

    def inspect(self, result):
        fake = FakeServer(result)
        with mock.patch.object(TRUST, "AppServer", return_value=fake):
            value = TRUST.inspect_trust(
                hooks_file=self.hooks,
                cwd=self.root,
                command=["codex", "app-server"],
            )
        self.assertTrue(fake.closed)
        return value

    def test_all_current_hashes_are_authoritatively_trusted(self):
        trusted, reason, events = self.inspect(self.result())
        self.assertTrue(trusted)
        self.assertEqual(reason, "current-hash-trusted")
        self.assertEqual(events, ["pre_tool_use", "stop"])

    def test_modified_current_hash_requires_review(self):
        trusted, reason, events = self.inspect(self.result(stop_status="modified"))
        self.assertFalse(trusted)
        self.assertEqual(reason, "current-hash-not-trusted")
        self.assertEqual(events, ["stop"])

    def test_discovery_set_mismatch_fails_closed(self):
        trusted, reason, events = self.inspect(self.result(include_pretool=False))
        self.assertFalse(trusted)
        self.assertEqual(reason, "definition-set-mismatch")
        self.assertEqual(events, ["pre_tool_use", "stop"])


if __name__ == "__main__":
    unittest.main()
