#!/usr/bin/env python3
"""Regression for compose-on-demand assembly (utilities/compose-route.py).

Covers the compose -> compile -> verify round trip plus the fail-closed cases a
compose-on-demand caller can hit: unknown unit, gate that no contract backs,
gate that names the wrong unit, ambiguous gate auto-derive, and a gate-evidence
fabrication attempt. The dispatch evidence is a fixture supported-conductor
tuple (the release smoke test keeps a live nested probe), so the round trip
does not depend on live auth.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "utilities" / "compose-route.py"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "utilities" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = _load("compose_route", "compose-route.py")
R = _load("route", "capability-route.py")

FIXTURE_EVIDENCE = {
    "tuples": [{
        "parent_harness": "claude", "parent_transport": "headless",
        "parent_sandbox": "workspace-write", "child_harness": "claude",
        "launch_authority": "conductor", "status": "supported",
        "probe_source": "fixture-probe", "probe_time": "2026-07-22T00:00:00Z",
        "failure_class": "",
    }],
    "native_subagent": [],
}
# A two-node analyze-project compose: research survey feeding a claim reviewer.
UNITS = [
    {"id": "survey", "unit": "research/research-survey",
     "write_scope": ["analysis_project/code/**"], "gate": "research-retrieval"},
    {"id": "claim", "unit": "research/claim-verify", "depends_on": ["survey"],
     "write_scope": ["reviews/claims/**"], "gate": "research-claims"},
]


class TestComposeRoute(unittest.TestCase):
    def _gate_index(self):
        return C.unit_io_gate_index(C._load_topology().load_registry())

    def _run(self, units, *, tracking="tracked", spec_read="canonical-sha",
             workflow_mode="tracked", output=None, capability_mode="code"):
        """Invoke the compose-route.py CLI as a real caller would."""
        with tempfile.TemporaryDirectory() as tmp:
            evidence_path = Path(tmp) / "evidence.json"
            evidence_path.write_text(json.dumps(FIXTURE_EVIDENCE), encoding="utf-8")
            command = [
                sys.executable, str(COMPOSE),
                "--capability", "analyze-project", "--capability-mode", capability_mode,
                "--units-json", json.dumps(units),
                "--cwd", str(ROOT), "--artifact-root", tmp,
                "--tracking", tracking, "--spec-read", spec_read,
                "--drift-verdict", "within-spec", "--workflow-mode", workflow_mode,
                "--artifact-guard", "conductor-prechecked",
                "--dispatch-evidence", str(evidence_path),
            ]
            if output is not None:
                command += ["--output", output]
            result = subprocess.run(command, text=True, capture_output=True, check=False)
            return result

    # --- build_recipe: the assembly logic this tool owns ------------------
    def test_build_recipe_derives_role_kind_gate_and_inputs(self):
        recipe = C.build_recipe(
            "analyze-project", "code", UNITS,
            topology_class="staged", quick_write_scope=[], gate_index=self._gate_index(),
        )
        nodes = {n["id"]: n for n in recipe["standard_plus"]["nodes"]}
        # role is derived from unit frontmatter (never caller-supplied).
        self.assertEqual(nodes["survey"]["role"], "deep maker")
        self.assertEqual(nodes["claim"]["role"], "fast fact-checker")
        # kind is derived from worker_type: stage -> pipeline-stage, review -> review-worker.
        self.assertEqual(nodes["survey"]["kind"], "pipeline-stage")
        self.assertEqual(nodes["claim"]["kind"], "review-worker")
        # a dependent node inherits its upstream write scope as inputs.
        self.assertEqual(nodes["claim"]["inputs"], ["analysis_project/code/**"])
        # every node is a dispatch-depth-2 unit; the quick block excludes spec scopes.
        self.assertTrue(all(n["dispatch_depth"] == 2 for n in nodes.values()))
        self.assertEqual(recipe["standard_plus"]["max_dispatch_depth"], 2)
        self.assertEqual(recipe["standard_plus"]["owner_dispatch_depth"], 1)

    def test_build_recipe_auto_derives_single_unit_io_gate(self):
        recipe = C.build_recipe(
            "analyze-project", "code",
            [{"id": "review", "unit": "qa/plan-review", "write_scope": ["reviews/plan/**"]}],
            topology_class="staged", quick_write_scope=[], gate_index=self._gate_index(),
        )
        # qa/plan-review names exactly one unit-io gate, so no explicit gate is needed.
        self.assertEqual(recipe["standard_plus"]["nodes"][0]["completion_gate"], "code-plan-check")

    # --- compose -> compile -> verify round trip -------------------------
    def test_round_trip_seals_and_verifies(self):
        with tempfile.TemporaryDirectory() as out_dir:
            output = str(Path(out_dir) / "route.json")
            result = self._run(UNITS, output=output)
            self.assertEqual(result.returncode, 0, result.stderr)
            route = json.loads(result.stdout)
            self.assertIs(route["composed"], True)
            self.assertEqual(route["effective_intensity"], "standard")
            self.assertEqual(route["capability"], "analyze-project")
            self.assertFalse(route["spec_touch"])
            self.assertEqual([n["id"] for n in route["nodes"]], ["survey", "claim"])
            # the sealed file is byte-identical to stdout and passes verify.
            self.assertEqual(json.loads(Path(output).read_text()), route)
            R.verify_route(route, ROOT)

    # --- fail-closed cases -----------------------------------------------
    def test_unknown_unit_fails_closed(self):
        result = self._run([{"id": "x", "unit": "research/does-not-exist",
                             "write_scope": ["analysis_project/code/**"], "gate": "research-retrieval"}])
        self.assertEqual(result.returncode, 64)
        self.assertIn("unknown unit", result.stderr)

    def test_gate_without_contract_fails_closed(self):
        result = self._run([{"id": "x", "unit": "research/research-survey",
                             "write_scope": ["analysis_project/code/**"], "gate": "no-such-gate"}])
        self.assertEqual(result.returncode, 64)
        self.assertIn("completion_gate_contracts", result.stderr)

    def test_gate_naming_wrong_unit_fails_closed_at_compile(self):
        # code-plan-check is a real unit-io gate, but it names qa/plan-review, not the node's unit.
        result = self._run([{"id": "x", "unit": "research/research-survey",
                             "write_scope": ["analysis_project/code/**"], "gate": "code-plan-check"}])
        self.assertEqual(result.returncode, 64)
        self.assertIn("must name the carrying node's unit", result.stderr)

    def test_ambiguous_gate_auto_derive_fails_closed(self):
        # research/research-survey backs five unit-io gates, so auto-derive is refused.
        result = self._run([{"id": "x", "unit": "research/research-survey",
                             "write_scope": ["analysis_project/code/**"]}])
        self.assertEqual(result.returncode, 64)
        self.assertIn("multiple gates", result.stderr)

    def test_unsatisfied_tracked_gate_is_not_fabricated(self):
        # --spec-read false means the tracked spec-read gate is unmet; the tool must
        # pass it through unchanged (never fabricate satisfied), so compile fails closed.
        result = self._run(UNITS, spec_read="false")
        self.assertEqual(result.returncode, 64)
        self.assertIn("spec_read", result.stderr)

    def test_workflow_mode_mismatch_fails_closed(self):
        result = self._run(UNITS, tracking="tracked", workflow_mode="untracked")
        self.assertEqual(result.returncode, 64)


if __name__ == "__main__":
    unittest.main()
