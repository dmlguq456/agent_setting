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
            W.resolve_worker_type(explicit=None, depth=2, worker_role="code-test"),
            "stage",
        )
        self.assertEqual(
            W.resolve_worker_type(explicit=None, depth=2, worker_role="external-adversary"),
            "review",
        )
        self.assertEqual(W.resolve_worker_type(explicit=None, depth=2), "support")

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
                worker_role=None,
                route_node="test",
            ),
            "code-test",
        )
        self.assertEqual(
            W.assigned_contract(
                capability="autopilot-code",
                worker_type="owner",
                worker_role=None,
                route_node=None,
            ),
            "autopilot-code",
        )


if __name__ == "__main__":
    unittest.main()
