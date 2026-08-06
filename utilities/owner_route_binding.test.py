#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "owner_route_binding", ROOT / "utilities" / "owner_route_binding.py"
)
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


class OwnerRouteBindingTest(unittest.TestCase):
    def route(self, cwd: str) -> dict:
        return {
            "schema_version": 2,
            "route_id": "rt-test",
            "route_hash": "sha256:test",
            "cwd": cwd,
            "capability": "autopilot-code",
            "capability_mode": "dev",
            "effective_intensity": "strong",
            "owner_dispatch_depth": 1,
            "dispatch_evidence": {
                "tuples": [
                    {
                        "status": "supported",
                        "parent_harness": "codex",
                    }
                ]
            },
            "nodes": [{"id": "test", "runtime_requirements": []}],
        }

    def test_owner_binding_is_node_less_and_sealed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "route.json"
            route = self.route(td)
            path.write_text(json.dumps(route), encoding="utf-8")
            with mock.patch.object(M.ROUTE, "verify_route", return_value=route):
                result = M.validate_owner_route_binding(
                    path,
                    worktree=td,
                    capability="autopilot-code",
                    capability_mode="dev",
                    intensity="strong",
                    harness="codex",
                )
            self.assertEqual(result.route_id, "rt-test")
            self.assertFalse(hasattr(result, "route_node"))

    def test_owner_harness_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "route.json"
            route = self.route(td)
            path.write_text(json.dumps(route), encoding="utf-8")
            with mock.patch.object(M.ROUTE, "verify_route", return_value=route):
                with self.assertRaisesRegex(
                    M.OwnerRouteBindingError, "owner-route-harness-mismatch"
                ):
                    M.validate_owner_route_binding(
                        path,
                        worktree=td,
                        capability="autopilot-code",
                        capability_mode="dev",
                        intensity="strong",
                        harness="claude",
                    )

    def test_loopback_requirement_fails_closed(self):
        route = {"nodes": [{"id": "gate", "runtime_requirements": ["loopback-listen"]}]}
        with self.assertRaisesRegex(
            M.OwnerRouteBindingError, "loopback-only-unsupported"
        ):
            M.validate_runtime_requirements(route, "gate")

    def test_three_wrappers_project_owner_binding(self):
        for adapter in ("codex", "claude", "opencode"):
            text = (
                ROOT / "adapters" / adapter / "bin" / "dispatch-headless.py"
            ).read_text(encoding="utf-8")
            self.assertIn("AGENT_OWNER_ROUTE_FILE", (ROOT / "utilities" / "owner_route_binding.py").read_text(encoding="utf-8"))
            self.assertIn("args.owner_route_binding.route_file", text)
            self.assertIn('f",owner_route_file={args.owner_route_binding.route_file}"', text)
            self.assertIn('"AGENT_ROUTE_NODE": args.route_node or ""', text)


if __name__ == "__main__":
    unittest.main()
