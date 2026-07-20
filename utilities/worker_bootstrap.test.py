#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path

import worker_bootstrap as W

ROOT = Path(__file__).resolve().parents[1]


class WorkerBootstrapTest(unittest.TestCase):
    def test_deterministic_fallback_types(self):
        self.assertEqual(W.resolve_worker_type(explicit=None, depth=1), "owner")
        self.assertEqual(
            W.resolve_worker_type(explicit=None, depth=2, route_node="test"),
            "stage",
        )
        self.assertEqual(
            W.resolve_worker_type(explicit=None, depth=2, route_node="plan-review"),
            "review",
        )
        self.assertEqual(W.resolve_worker_type(explicit=None, depth=2), "support")

    def test_worker_role_is_only_a_legacy_fallback(self):
        self.assertEqual(
            W.resolve_worker_type(
                explicit="support",
                depth=2,
                worker_role="external-adversary",
                route_node="review",
            ),
            "support",
        )
        self.assertEqual(
            W.resolve_worker_type(explicit=None, depth=2, worker_role="code-test"),
            "stage",
        )

    def test_explicit_and_profile_precedence(self):
        self.assertEqual(
            W.resolve_worker_type(
                explicit="review", depth=1, profile_type="stage"
            ),
            "review",
        )
        self.assertEqual(
            W.resolve_worker_type(explicit=None, depth=1, profile_type="support"),
            "support",
        )

    def test_render_has_one_kernel_one_type_and_exact_handoff(self):
        rendered = W.render_worker_bootstrap(ROOT, "stage")
        self.assertEqual(rendered.count("# Portable Worker Kernel"), 1)
        self.assertEqual(rendered.count("# Worker Type:"), 1)
        self.assertIn(W.handoff_template(), rendered)
        self.assertNotIn("# Worker Type: Owner", rendered)
        self.assertNotIn("# Worker Type: Review", rendered)

    def test_profile_type_scalar(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "profiles").mkdir()
            (root / "profiles" / "x.yaml").write_text(
                "name: x\nworker_type: review\n", encoding="utf-8"
            )
            self.assertEqual(W.profile_worker_type(root, "x"), "review")

    def test_assigned_stage_contract(self):
        self.assertEqual(
            W.assigned_contract(
                capability="autopilot-code",
                worker_type="stage",
                route_node="test",
                completion_gate="code-test",
                root=ROOT,
            ),
            "code-test",
        )
        self.assertEqual(
            W.assigned_contract(
                capability="autopilot-code",
                worker_type="owner",
                route_node=None,
                root=ROOT,
            ),
            "autopilot-code",
        )
        self.assertEqual(
            W.assigned_contract(
                capability="autopilot-design",
                worker_type="support",
                route_node="refs",
                completion_gate="design-refs",
                root=ROOT,
            ),
            "design-refs",
        )
        self.assertEqual(
            W.assigned_contract(
                capability="autopilot-spec",
                worker_type="support",
                route_node="research",
                completion_gate="spec-research",
                root=ROOT,
            ),
            "autopilot-spec",
        )

    def test_topology_kind_maps_only_to_bootstrap_type(self):
        self.assertEqual(W.worker_type_for_kind("capability-owner"), "owner")
        self.assertEqual(W.worker_type_for_kind("pipeline-stage"), "stage")
        self.assertEqual(W.worker_type_for_kind("review-worker"), "review")
        self.assertEqual(W.worker_type_for_kind("map-worker"), "support")
        with self.assertRaises(ValueError):
            W.worker_type_for_kind("resource-runner")


if __name__ == "__main__":
    unittest.main()
