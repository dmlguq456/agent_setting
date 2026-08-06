#!/usr/bin/env python3

import json
from pathlib import Path
import tempfile
import unittest

import dispatch_continuation_budget as MODULE


class ContinuationBudgetTest(unittest.TestCase):
    def seal(self, value):
        import hashlib
        encoded = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
        value["route_hash"] = "sha256:" + hashlib.sha256(encoded).hexdigest()
        value["route_id"] = "rt-" + value["route_hash"].split(":", 1)[1][:16]
        return value

    def test_bound_route_uses_nodes_plus_unique_retry_boundaries(self):
        with tempfile.TemporaryDirectory() as raw:
            route = Path(raw) / "route.json"
            value = self.seal({
                "schema_version": 2,
                "nodes": [{"id": f"node-{index}"} for index in range(8)],
                "resume_retry_boundaries": [f"node-{index}" for index in range(7)],
            })
            route.write_text(json.dumps(value), encoding="utf-8")
            budget = MODULE.resolve_continuation_budget(
                route_file=route,
                route_id=value["route_id"],
                route_hash=value["route_hash"],
            )
        self.assertEqual(15, budget.limit)
        self.assertEqual("bound-route", budget.source)
        self.assertEqual(8, budget.declared_nodes)
        self.assertEqual(7, budget.retry_slots)

    def test_unbound_or_mismatched_route_keeps_finite_floor(self):
        with tempfile.TemporaryDirectory() as raw:
            route = Path(raw) / "route.json"
            value = self.seal({
                "schema_version": 2,
                "nodes": [{"id": "node"}],
                "resume_retry_boundaries": [],
            })
            route.write_text(json.dumps(value), encoding="utf-8")
            budget = MODULE.resolve_continuation_budget(
                route_file=route, route_id="rt-foreign", route_hash=value["route_hash"]
            )
        self.assertEqual(MODULE.COMPATIBILITY_FLOOR, budget.limit)
        self.assertEqual("compatibility-floor", budget.source)

    def test_positive_explicit_override_replaces_route_value(self):
        budget = MODULE.resolve_continuation_budget(explicit=3)
        self.assertEqual(3, budget.limit)
        self.assertEqual("explicit-owner-override", budget.source)


if __name__ == "__main__":
    unittest.main()
