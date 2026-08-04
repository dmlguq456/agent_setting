#!/usr/bin/env python3
"""Acceptance suite for the portable tracked-workflow continuation contract.

Every test here maps to one clause of `core/WORKFLOW.md §0.6` / `OPERATIONS §5.12`,
and the BC_ResNet_tf cases are the regression pilot: a run that finished training
while nothing owned evaluation must now either be refused at compile or carried
forward by the supervisor.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools"))

import workflow_state as WS  # noqa: E402
import capability_topology as TOPO  # noqa: E402


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolve annotations through sys.modules, so register before exec.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SUP = _load("workflow_supervisor", "utilities/workflow-supervisor.py")
ROUTE = _load("capability_route", "utilities/capability-route.py")
RUNNER_CLI = ROOT / "utilities" / "resource-runner.py"

GATE = {
    "spec_read": {"satisfied": True, "source": "fixture-prd-sha256"},
    "drift_verdict": "within-spec",
    "workflow_mode": "tracked",
    "artifact_guard": {"satisfied": True, "source": "fixture-prechecked"},
}


def nested_tuple(parent="claude", child="codex"):
    sandbox = ROUTE.WRAPPER_PARENT_SANDBOXES[parent][0]
    return {
        "parent_harness": parent, "parent_transport": "headless",
        "parent_sandbox": sandbox, "child_harness": child,
        "launch_authority": "conductor", "status": "supported",
        "probe_source": "fixture-probe", "probe_time": "2026-08-04T00:00:00Z",
        "failure_class": "",
    }


def dispatch_evidence():
    return {"tuples": [nested_tuple("claude", "claude"), nested_tuple("claude", "codex")],
            "native_subagent": []}


def compile_fixture(capability, capability_mode, cwd, signals):
    return ROUTE.compile_route(
        capability, capability_mode, "standard", cwd, cwd,
        predicates=[], signals=signals, transport="headless",
        transport_evidence="fixture", inline_reason=None, tracking="tracked",
        tracked_gate_evidence=copy.deepcopy(GATE),
        dispatch_evidence=dispatch_evidence(),
    )


class WorkflowFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.workflow_root = self.base / "workflow"
        self._previous = os.environ.get("AGENT_WORKFLOW_ROOT")
        os.environ["AGENT_WORKFLOW_ROOT"] = str(self.workflow_root)
        self.addCleanup(self._restore)
        self.addCleanup(self.tmp.cleanup)

    def _restore(self):
        if self._previous is None:
            os.environ.pop("AGENT_WORKFLOW_ROOT", None)
        else:
            os.environ["AGENT_WORKFLOW_ROOT"] = self._previous

    # -- fixtures -------------------------------------------------------------
    def write_route(self, nodes, route_id="rt-fixture0000000", route_hash="sha256:fixture"):
        route = {
            "schema_version": 2, "route_id": route_id, "route_hash": route_hash,
            "capability": "autopilot-lab", "capability_mode": "setup",
            "effective_intensity": "standard", "cwd": str(self.base),
            "human_gates": [], "human_gate_bindings": [], "nodes": nodes,
        }
        path = self.base / f"{route_id}.json"
        path.write_text(json.dumps(route, indent=2), encoding="utf-8")
        return route, path

    def two_stage_route(self, continuation=None, human_gate=None):
        nodes = [
            {"id": "run", "kind": "resource-runner", "depends_on": [],
             "outputs": ["run.json"], "write_scope": ["run.json"],
             "completion_gate": "fixture-run",
             "continuation": continuation or {"kind": "supervised"}},
            {"id": "verify", "kind": "review-worker", "depends_on": ["run"],
             "outputs": ["reviews/verdict.json"], "write_scope": ["reviews/**"],
             "completion_gate": "fixture-verify", "dispatch_depth": 2,
             "terminal": True, "terminal_gate": "fixture-verify"},
        ]
        route, path = self.write_route(nodes)
        if human_gate:
            route["human_gates"] = [human_gate]
            route["human_gate_bindings"] = [
                {"gate": human_gate, "node": "verify", "position": "entry"}]
            path.write_text(json.dumps(route, indent=2), encoding="utf-8")
        return route, path

    def resource_registry(self, *, exit_code=0, pid=None, starttime=None,
                          command_hash=None, status="running", sentinel=True):
        """A registry row plus a real sentinel, so evidence is genuinely readable."""
        registry = self.base / "resource-runs.json"
        sentinel_path = self.base / "run.log.exit"
        if sentinel and exit_code is not None:
            sentinel_path.write_text(str(exit_code), encoding="utf-8")
        row = {
            "run_id": "fixture-run", "pid": pid if pid is not None else 999999999,
            "starttime": starttime or "1",
            "command_hash": command_hash or "0" * 64,
            "process_group": pid if pid is not None else 999999999,
            "cwd": str(self.base), "log": str(self.base / "run.log"),
            "sentinel": str(sentinel_path), "command": ["true"],
            "route": None, "node": "run", "status": status,
            "started_at": time.time() - 60,
        }
        registry.write_text(json.dumps({"schema_version": 1, "runs": {"fixture-run": row}},
                                       indent=2), encoding="utf-8")
        return registry

    def arm(self, route_path, registry, *, node="run", command=None, extra=()):
        marker = self.base / "successor-started"
        # The successor is detached, so it can outlive the fixture teardown; a missing
        # temp dir then is teardown noise, not a defect.
        argv = command or [
            sys.executable, "-c",
            f"import contextlib\nwith contextlib.suppress(OSError):\n"
            f"    open({str(marker)!r},'a').write('x')",
        ]
        args = [
            "arm", "--route", str(route_path), "--node", node,
            "--predecessor-kind", "resource", "--predecessor-id", "fixture-run",
            "--resource-registry", str(registry),
            "--successor-command", json.dumps(argv),
            *extra,
        ]
        SUP.main(args)
        return marker


# ---------------------------------------------------------------------------
# A. the portable state machine
# ---------------------------------------------------------------------------
class TestStateMachine(WorkflowFixture):
    def test_complete_is_reachable_only_through_terminal_verify(self):
        self.assertTrue(WS.can_transition("TERMINAL_VERIFY", "COMPLETE"))
        for state in ("RUNNING", "STAGE_SUCCEEDED", "NEXT_REGISTERED", "NEXT_RUNNING",
                      "READY", "CREATED"):
            self.assertFalse(WS.can_transition(state, "COMPLETE"),
                             f"{state} must not reach COMPLETE directly")

    def test_human_gate_never_advances_automatically(self):
        for target in ("STAGE_SUCCEEDED", "NEXT_REGISTERED", "NEXT_RUNNING",
                       "TERMINAL_VERIFY", "COMPLETE"):
            self.assertFalse(WS.can_transition("BLOCKED_HUMAN_GATE", target))
        self.assertTrue(WS.can_transition("BLOCKED_HUMAN_GATE", "RUNNING"))

    def test_terminal_states_are_absorbing(self):
        for state in ("COMPLETE", "FAILED_TERMINAL", "CANCELLED"):
            self.assertEqual(WS.vocabulary()["transitions"][state], ())

    def test_journal_is_the_source_of_truth_after_a_crash(self):
        ledger = WS.WorkflowLedger("rt-crash0000000000", "sha256:x")
        ledger.record("a", "RUNNING")
        ledger.record("a", "STAGE_SUCCEEDED")
        ledger.state_path.unlink()
        recovered = ledger.state()
        self.assertEqual(recovered["nodes"]["a"]["state"], "STAGE_SUCCEEDED")
        self.assertTrue(ledger.state_path.is_file())

    def test_torn_journal_line_is_dropped_not_guessed(self):
        ledger = WS.WorkflowLedger("rt-torn00000000000", "sha256:x")
        ledger.record("a", "RUNNING")
        with ledger.journal_path.open("a", encoding="utf-8") as handle:
            handle.write('{"node": "b", "state": "STAGE_SUC')
        self.assertEqual(set(ledger.state()["nodes"]), {"a"})

    def test_illegal_node_transition_is_refused(self):
        ledger = WS.WorkflowLedger("rt-illegal00000000", "sha256:x")
        ledger.record("a", "FAILED_TERMINAL")
        with self.assertRaises(WS.WorkflowStateError):
            ledger.record("a", "STAGE_SUCCEEDED")


# ---------------------------------------------------------------------------
# B. supervisor advance semantics
# ---------------------------------------------------------------------------
class TestSupervisorAdvance(WorkflowFixture):
    def test_successful_stage_registers_the_next_stage_exactly_once(self):
        route, path = self.two_stage_route()
        registry = self.resource_registry(exit_code=0)
        marker = self.arm(path, registry)
        ledger = SUP.ledger_for(route)
        first = SUP.poll_once(route, ledger)
        second = SUP.poll_once(route, ledger)
        third = SUP.poll_once(route, ledger)
        self.assertEqual(first[0]["action"], "advanced")
        self.assertEqual([row["successor"] for row in first[0]["successors"]], ["verify"])
        self.assertTrue(first[0]["successors"][0]["created"])
        self.assertEqual(second[0]["action"], "settled")
        self.assertEqual(third[0]["action"], "settled")
        for _ in range(50):
            if marker.exists():
                break
            time.sleep(0.05)
        self.assertTrue(marker.exists(), "the successor must actually start")
        self.assertEqual(marker.read_text(), "x", "the successor must start exactly once")
        self.assertEqual(len(ledger.claims()), 1)

    def test_failed_stage_does_not_run_downstream(self):
        route, path = self.two_stage_route()
        registry = self.resource_registry(exit_code=1)
        marker = self.arm(path, registry)
        ledger = SUP.ledger_for(route)
        result = SUP.poll_once(route, ledger)
        self.assertEqual(result[0]["action"], "halt-failed")
        self.assertEqual(ledger.state()["nodes"]["run"]["state"], "FAILED_RETRYABLE")
        self.assertEqual(ledger.claims(), {})
        time.sleep(0.2)
        self.assertFalse(marker.exists())
        self.assertEqual(SUP.poll_once(route, ledger)[0]["action"], "halted")

    def test_absent_exit_sentinel_is_never_read_as_success(self):
        route, path = self.two_stage_route()
        registry = self.resource_registry(exit_code=None, sentinel=False)
        self.arm(path, registry)
        ledger = SUP.ledger_for(route)
        result = SUP.poll_once(route, ledger)
        self.assertEqual(result[0]["action"], "halt-failed")
        self.assertEqual(ledger.claims(), {})

    def test_pid_reuse_is_distinguished_from_a_clean_exit(self):
        """A live PID whose start time differs is a different process, not our run."""
        route, path = self.two_stage_route()
        # os.getpid() is alive but its start time will not be "1".
        registry = self.resource_registry(exit_code=None, sentinel=False,
                                          pid=os.getpid(), starttime="1")
        self.arm(path, registry)
        ledger = SUP.ledger_for(route)
        result = SUP.poll_once(route, ledger)
        evidence = result[0]["evidence"]
        self.assertEqual(evidence["liveness"], "stale")
        self.assertEqual(evidence["reason"], "process-identity-mismatch")
        self.assertEqual(result[0]["action"], "halt-failed")
        # The same row with an absent PID is `exited`, a materially different verdict.
        other = self.resource_registry(exit_code=0, pid=999999998, starttime="7")
        row = json.loads(other.read_text())["runs"]["fixture-run"]
        self.assertEqual(SUP.RR.classify_identity(row)[0], "exited")

    def test_concurrent_supervisors_start_one_successor(self):
        route, path = self.two_stage_route()
        registry = self.resource_registry(exit_code=0)
        marker = self.arm(path, registry)

        # Four genuinely separate supervisor processes, racing on the same route.
        command = [sys.executable, str(ROOT / "utilities" / "workflow-supervisor.py"),
                   "poll", "--route", str(path)]
        environment = {**os.environ, "AGENT_WORKFLOW_ROOT": str(self.workflow_root)}
        workers = [subprocess.Popen(command, env=environment, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE) for _ in range(4)]
        outcomes = [worker.communicate() for worker in workers]
        for worker, (_out, err) in zip(workers, outcomes):
            self.assertEqual(worker.returncode, 0, err.decode())
        advanced = [json.loads(out)["results"][0]["action"] for out, _err in outcomes]
        self.assertEqual(advanced.count("advanced"), 1,
                         f"exactly one supervisor may advance, saw {advanced}")
        for _ in range(50):
            if marker.exists():
                break
            time.sleep(0.05)
        ledger = SUP.ledger_for(route)
        self.assertEqual(len(ledger.claims()), 1)
        self.assertEqual(marker.read_text(), "x",
                         "four concurrent supervisors must create one downstream job")

    def test_restart_resumes_from_the_last_confirmed_stage(self):
        route, path = self.two_stage_route()
        registry = self.resource_registry(exit_code=0)
        marker = self.arm(path, registry)
        SUP.poll_once(route, SUP.ledger_for(route))
        for _ in range(50):
            if marker.exists():
                break
            time.sleep(0.05)
        # A restarted supervisor has no in-memory state: it must rebuild from disk.
        restarted = _load("workflow_supervisor_restart", "utilities/workflow-supervisor.py")
        fresh_route = restarted.load_route(path)
        result = restarted.poll_once(fresh_route, restarted.ledger_for(fresh_route))
        self.assertEqual(result[0]["action"], "settled")
        self.assertEqual(marker.read_text(), "x")
        self.assertEqual(len(restarted.ledger_for(fresh_route).claims()), 1)

    def test_a_human_gate_can_never_be_supervised_into_advancing(self):
        """No arming path exists for a human gate, and a blocked workflow stays blocked."""
        route, path = self.two_stage_route(
            continuation={"kind": "human-gate", "gate": "run-authorization"},
            human_gate="run-authorization")
        registry = self.resource_registry(exit_code=0)
        with self.assertRaisesRegex(SUP.SupervisorError, "supervisor governs only"):
            self.arm(path, registry, extra=["--successor-external"])
        SUP.main(["gate", "--route", str(path), "--gate", "run-authorization", "--block"])
        ledger = SUP.ledger_for(route)
        self.assertEqual(ledger.state()["workflow_state"], "BLOCKED_HUMAN_GATE")
        self.assertEqual(SUP.poll_once(route, ledger), [])
        self.assertEqual(ledger.claims(), {})
        self.assertEqual(ledger.state()["workflow_state"], "BLOCKED_HUMAN_GATE")
        SUP.main(["gate", "--route", str(path), "--gate", "run-authorization",
                  "--release", "--by", "fixture-user"])
        self.assertEqual(ledger.state()["workflow_state"], "RUNNING")

    def test_monitor_continuation_waits_for_a_matched_condition(self):
        route, path = self.two_stage_route(
            continuation={"kind": "monitor", "monitor": "external-check"})
        registry = self.resource_registry(exit_code=0)
        evidence_path = self.base / "monitor.json"
        evidence_path.write_text(json.dumps({"condition": "pending"}), encoding="utf-8")
        marker = self.arm(path, registry,
                          extra=["--monitor-evidence", str(evidence_path)])
        ledger = SUP.ledger_for(route)
        self.assertEqual(SUP.poll_once(route, ledger)[0]["action"], "wait-monitor")
        self.assertEqual(ledger.claims(), {})
        evidence_path.write_text(json.dumps({"condition": "matched"}), encoding="utf-8")
        self.assertEqual(SUP.poll_once(route, ledger)[0]["action"], "advanced")
        for _ in range(50):
            if marker.exists():
                break
            time.sleep(0.05)
        self.assertTrue(marker.exists())

    def test_declared_artifact_absence_halts_the_advance(self):
        route, path = self.two_stage_route()
        registry = self.resource_registry(exit_code=0)
        self.arm(path, registry, extra=["--artifact-base", str(self.base)])
        ledger = SUP.ledger_for(route)
        result = SUP.poll_once(route, ledger)
        self.assertEqual(result[0]["action"], "halt-missing-artifact")
        self.assertEqual(ledger.claims(), {})

    def test_arm_refuses_a_continuation_with_no_way_to_start_the_successor(self):
        _route, path = self.two_stage_route()
        registry = self.resource_registry(exit_code=0)
        with self.assertRaises(SUP.SupervisorError) as caught:
            SUP.main(["arm", "--route", str(path), "--node", "run",
                      "--predecessor-kind", "resource", "--predecessor-id", "fixture-run",
                      "--resource-registry", str(registry)])
        self.assertIn("successor-command", str(caught.exception))

    def test_arm_refuses_a_terminal_node(self):
        _route, path = self.two_stage_route()
        registry = self.resource_registry(exit_code=0)
        with self.assertRaises(SUP.SupervisorError):
            SUP.main(["arm", "--route", str(path), "--node", "verify",
                      "--predecessor-kind", "resource", "--predecessor-id", "fixture-run",
                      "--resource-registry", str(registry),
                      "--successor-command", '["true"]'])


# ---------------------------------------------------------------------------
# C. completion is terminal-node bound
# ---------------------------------------------------------------------------
class TestCompletion(WorkflowFixture):
    def test_workflow_does_not_complete_before_its_terminal_node(self):
        route, path = self.two_stage_route()
        registry = self.resource_registry(exit_code=0)
        self.arm(path, registry)
        ledger = SUP.ledger_for(route)
        SUP.poll_once(route, ledger)
        self.assertNotEqual(ledger.state()["workflow_state"], "COMPLETE")

        class Args:
            route = str(path)

        self.assertEqual(SUP.cmd_complete(Args()), 3)
        self.assertNotEqual(ledger.state()["workflow_state"], "COMPLETE")

    def test_derive_workflow_state_requires_verified_terminal_gates(self):
        nodes = {"run": {"state": "STAGE_SUCCEEDED"}, "verify": {"state": "STAGE_SUCCEEDED"}}
        self.assertEqual(
            WS.derive_workflow_state(nodes, ["verify"], terminal_gates_passed=False),
            "TERMINAL_VERIFY")
        self.assertEqual(
            WS.derive_workflow_state(nodes, ["verify"], terminal_gates_passed=True),
            "COMPLETE")

    def test_failure_outranks_downstream_success(self):
        nodes = {"run": {"state": "FAILED_RETRYABLE"}, "verify": {"state": "STAGE_SUCCEEDED"}}
        self.assertEqual(
            WS.derive_workflow_state(nodes, ["verify"], terminal_gates_passed=True),
            "FAILED_RETRYABLE")


# ---------------------------------------------------------------------------
# D. status projection and resource visibility
# ---------------------------------------------------------------------------
class TestStatusProjection(WorkflowFixture):
    def test_status_exposes_workflow_stage_resource_and_failure(self):
        route, path = self.two_stage_route()
        registry = self.resource_registry(exit_code=0)
        self.arm(path, registry)
        ledger = SUP.ledger_for(route)
        SUP.poll_once(route, ledger)
        captured = subprocess.run(
            [sys.executable, str(ROOT / "utilities" / "workflow-supervisor.py"),
             "status", "--route", str(path), "--json"],
            capture_output=True, text=True,
            env={**os.environ, "AGENT_WORKFLOW_ROOT": str(self.workflow_root)})
        self.assertEqual(captured.returncode, 0, captured.stderr)
        payload = json.loads(captured.stdout)
        for field in ("workflow_state", "current_stage", "next_stage", "terminal_nodes",
                      "terminal_gates", "resource_children", "failure_reason",
                      "updated_at", "human_gate_bindings", "claims"):
            self.assertIn(field, payload)
        self.assertEqual(payload["terminal_nodes"], ["verify"])
        self.assertEqual(payload["next_stage"], ["verify"])
        self.assertEqual([child["run_id"] for child in payload["resource_children"]],
                         ["fixture-run"])

    def test_resource_child_is_listed_even_when_the_global_index_misses_it(self):
        route, path = self.two_stage_route()
        registry = self.resource_registry(exit_code=0)
        self.arm(path, registry)
        children = SUP.resource_children(route, SUP.ledger_for(route))
        self.assertEqual([child["run_id"] for child in children], ["fixture-run"])


# ---------------------------------------------------------------------------
# E. resource-runner lifecycle
# ---------------------------------------------------------------------------
class TestResourceLifecycle(WorkflowFixture):
    def run_registry(self):
        return self.base / "runs.json"

    def test_reap_persists_terminal_status_exit_code_and_ended_at(self):
        registry = self.run_registry()
        sentinel = self.base / "job.log.exit"
        sentinel.write_text("0", encoding="utf-8")
        registry.write_text(json.dumps({"schema_version": 1, "runs": {"job": {
            "run_id": "job", "pid": 999999997, "starttime": "5",
            "command_hash": "a" * 64, "process_group": 999999997,
            "cwd": str(self.base), "log": str(self.base / "job.log"),
            "sentinel": str(sentinel), "command": ["true"], "status": "running",
        }}}), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(RUNNER_CLI), "--registry", str(registry),
             "reap", "--run-id", "job"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "succeeded")
        self.assertEqual(payload["exit_code"], 0)
        self.assertEqual(payload["workflow_state"], "STAGE_SUCCEEDED")
        self.assertIsNotNone(payload["ended_at"])
        stored = json.loads(registry.read_text())["runs"]["job"]
        self.assertEqual(stored["status"], "succeeded")

    def test_no_stale_running_survives_an_observation(self):
        registry = self.run_registry()
        registry.write_text(json.dumps({"schema_version": 1, "runs": {"job": {
            "run_id": "job", "pid": 999999996, "starttime": "5",
            "command_hash": "b" * 64, "process_group": 999999996,
            "cwd": str(self.base), "log": str(self.base / "job.log"),
            "sentinel": str(self.base / "absent.exit"), "command": ["true"],
            "status": "running",
        }}}), encoding="utf-8")
        subprocess.run([sys.executable, str(RUNNER_CLI), "--registry", str(registry),
                        "status", "--run-id", "job"], capture_output=True, text=True, check=True)
        stored = json.loads(registry.read_text())["runs"]["job"]
        self.assertEqual(stored["status"], "failed")
        self.assertEqual(stored["failure_class"], "no-exit-sentinel")

    def test_sentinel_wrapper_persists_the_payload_exit_status(self):
        registry = self.run_registry()
        log = self.base / "direct.log"
        sentinel = Path(str(log) + ".exit")
        runner = _load("resource_runner_direct", "utilities/resource-runner.py")
        with open(log, "ab") as stream:
            proc = subprocess.Popen(
                ["/bin/sh", "-c", runner.SENTINEL_SCRIPT, "resource-runner",
                 "sh", "-c", "exit 7"],
                cwd=self.base, env={**os.environ, "AGENT_RESOURCE_SENTINEL": str(sentinel)},
                stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        identity = None
        for _ in range(50):
            identity = SUP.RR.proc_identity(proc.pid)
            if identity:
                break
            time.sleep(0.01)
        self.assertIsNotNone(identity)
        proc.wait(timeout=30)
        for _ in range(100):
            if sentinel.is_file():
                break
            time.sleep(0.02)
        self.assertEqual(sentinel.read_text().strip(), "7",
                         "the wrapper must persist the payload exit status")
        registry.write_text(json.dumps({"schema_version": 1, "runs": {"job": {
            **identity, "run_id": "job", "process_group": proc.pid,
            "cwd": str(self.base), "log": str(log), "sentinel": str(sentinel),
            "command": ["sh", "-c", "exit 7"], "status": "running",
            "parent_attempt_id": "att-fixture", "workflow_state": "RUNNING",
        }}}), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(RUNNER_CLI), "--registry", str(registry),
             "reap", "--run-id", "job"], capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["exit_code"], 7)
        self.assertEqual(payload["failure_class"], "exit-7")
        self.assertEqual(payload["parent_attempt_id"], "att-fixture")


# ---------------------------------------------------------------------------
# F. the graph contract itself, and the BC_ResNet_tf regression
# ---------------------------------------------------------------------------
class TestGraphContract(unittest.TestCase):
    def setUp(self):
        self.registry = TOPO.load_registry()

    def recipe(self, capability, mode):
        return TOPO.resolve_recipe(self.registry, capability, mode)

    def test_every_recipe_declares_a_terminal_and_full_continuations(self):
        for recipe in self.registry["recipes"]:
            nodes = recipe["standard_plus"]["nodes"]
            dependents = {node["id"]: [] for node in nodes}
            for node in nodes:
                for dep in node.get("depends_on", []):
                    dependents[dep].append(node["id"])
            sinks = [node for node in nodes if not dependents[node["id"]]]
            self.assertTrue(sinks, recipe["capability"])
            for node in sinks:
                self.assertTrue(node.get("terminal"), (recipe["capability"], node["id"]))
                self.assertNotEqual(node["kind"], "resource-runner")
            for node in nodes:
                if dependents[node["id"]]:
                    self.assertIn(node["continuation"]["kind"],
                                  self.registry["continuation_kinds"],
                                  (recipe["capability"], node["id"]))

    def test_bc_resnet_shape_is_refused_at_registry_validation(self):
        """The original lab-setup graph — training as the last node — no longer compiles."""
        broken = copy.deepcopy(self.registry)
        recipe = next(r for r in broken["recipes"]
                      if r["capability"] == "autopilot-lab" and "setup" in r["modes"])
        nodes = recipe["standard_plus"]["nodes"]
        recipe["standard_plus"]["nodes"] = [n for n in nodes
                                            if n["id"] not in ("run-verify", "handoff")]
        full_run = next(n for n in recipe["standard_plus"]["nodes"] if n["id"] == "full-run")
        full_run.pop("continuation", None)
        full_run["terminal"] = True
        full_run["terminal_gate"] = full_run["completion_gate"]
        recipe["conditional_extensions"][0]["after"] = ["full-run"]
        recipe["completion_gates"] = [g for g in recipe["completion_gates"]
                                      if g not in ("lab-run-verify", "lab-setup-handoff")]
        recipe["resume_retry_boundaries"] = [b for b in recipe["resume_retry_boundaries"]
                                             if b not in ("run-verify", "handoff")]
        with self.assertRaises(TOPO.TopologyError) as caught:
            TOPO.validate_registry(broken)
        self.assertIn("detached resource run can never be the workflow terminal",
                      str(caught.exception))

    def test_a_detached_node_may_not_claim_a_non_supervised_continuation(self):
        broken = copy.deepcopy(self.registry)
        recipe = next(r for r in broken["recipes"]
                      if r["capability"] == "autopilot-lab" and "eval" in r["modes"])
        node = next(n for n in recipe["standard_plus"]["nodes"] if n["id"] == "eval-run")
        node["continuation"] = {"kind": "inline-next"}
        with self.assertRaisesRegex(TOPO.TopologyError, "cannot continue itself"):
            TOPO.validate_registry(broken)

    def test_a_stage_with_no_continuation_is_refused(self):
        broken = copy.deepcopy(self.registry)
        recipe = next(r for r in broken["recipes"] if r["capability"] == "autopilot-code")
        node = next(n for n in recipe["standard_plus"]["nodes"] if n["id"] == "execute")
        node.pop("continuation")
        with self.assertRaisesRegex(TOPO.TopologyError, "requires a continuation"):
            TOPO.validate_registry(broken)

    def test_an_unbound_human_gate_is_refused(self):
        broken = copy.deepcopy(self.registry)
        recipe = next(r for r in broken["recipes"] if r["capability"] == "autopilot-ship")
        recipe["human_gates"] = ["deploy-authorization", "invented-gate"]
        with self.assertRaisesRegex(TOPO.TopologyError, "bind to exactly one node"):
            TOPO.validate_registry(broken)

    def test_lab_setup_graph_carries_the_run_through_verification_to_handoff(self):
        recipe = self.recipe("autopilot-lab", "setup")
        ids = [node["id"] for node in recipe["standard_plus"]["nodes"]]
        self.assertEqual(ids, ["scaffold", "smoke", "full-run", "run-verify", "handoff"])
        by_id = {node["id"]: node for node in recipe["standard_plus"]["nodes"]}
        self.assertEqual(by_id["smoke"]["continuation"],
                         {"kind": "human-gate", "gate": "full-run-authorization"})
        self.assertEqual(by_id["full-run"]["continuation"], {"kind": "supervised"})
        self.assertTrue(by_id["handoff"]["terminal"])
        self.assertEqual(recipe["conditional_extensions"][0]["after"], ["handoff"])

    def test_lab_eval_resource_node_is_supervised_and_sync_is_terminal(self):
        recipe = self.recipe("autopilot-lab", "eval")
        by_id = {node["id"]: node for node in recipe["standard_plus"]["nodes"]}
        self.assertEqual(by_id["eval-run"]["continuation"], {"kind": "supervised"})
        self.assertTrue(by_id["sync"]["terminal"])

    def test_ship_realizes_its_declared_deploy_authorization(self):
        recipe = self.recipe("autopilot-ship", "default")
        by_id = {node["id"]: node for node in recipe["standard_plus"]["nodes"]}
        self.assertIn("deploy", by_id)
        self.assertIn("post-deploy-verify", by_id)
        self.assertEqual(recipe["human_gate_bindings"],
                         [{"gate": "deploy-authorization", "node": "deploy",
                           "position": "entry"}])
        for reviewer in ("security-review", "release-review"):
            self.assertEqual(by_id[reviewer]["continuation"],
                             {"kind": "human-gate", "gate": "deploy-authorization"})
        self.assertTrue(by_id["post-deploy-verify"]["terminal"])

    def test_code_route_terminal_is_the_report(self):
        recipe = self.recipe("autopilot-code", "dev")
        by_id = {node["id"]: node for node in recipe["standard_plus"]["nodes"]}
        self.assertTrue(by_id["report"]["terminal"])
        self.assertEqual(by_id["execute"]["continuation"], {"kind": "inline-next"})


class TestSealedRoutes(unittest.TestCase):
    """The compiled route must carry the contract, not just the registry."""

    def compile(self, capability, mode, signals):
        with tempfile.TemporaryDirectory() as td:
            return compile_fixture(capability, mode, td, signals)

    def test_lab_setup_route_seals_terminal_handoff_and_supervised_run(self):
        route = self.compile("autopilot-lab", "setup", ["resource-run"])
        contract = route["workflow_contract"]
        self.assertEqual(contract["terminal_nodes"], ["handoff"])
        self.assertEqual(contract["continuations"]["full-run"], "supervised")
        self.assertEqual(contract["continuations"]["smoke"], "human-gate")
        self.assertEqual(route["human_gate_bindings"],
                         [{"gate": "full-run-authorization", "node": "full-run",
                           "position": "entry"}])
        ROUTE.verify_route(route, route["cwd"])

    def test_ship_route_seals_post_deploy_verification(self):
        route = self.compile("autopilot-ship", "default", ["human-gate"])
        self.assertEqual(route["workflow_contract"]["terminal_nodes"],
                         ["post-deploy-verify"])
        ROUTE.verify_route(route, route["cwd"])

    def test_code_route_seals_the_report_terminal(self):
        route = self.compile("autopilot-code", "dev", ["shared-contract"])
        self.assertEqual(route["workflow_contract"]["terminal_nodes"], ["report"])
        ROUTE.verify_route(route, route["cwd"])

    def test_tampered_workflow_contract_fails_verification(self):
        route = self.compile("autopilot-lab", "eval", ["gpu"])
        route["workflow_contract"]["terminal_nodes"] = ["eval-run"]
        route["route_hash"] = ROUTE.route_hash(route)
        route["route_id"] = "rt-" + route["route_hash"].split(":", 1)[1][:16]
        with self.assertRaisesRegex(ValueError, "workflow contract"):
            ROUTE.verify_route(route, route["cwd"])

    def test_direct_route_declares_its_single_terminal(self):
        with tempfile.TemporaryDirectory() as td:
            direct = ROUTE.compile_route(
                "autopilot-code", "dev", "direct", td, td,
                predicates=["atomic-outcome", "known-scope", "no-shared-contract",
                            "no-resource-run", "no-artifact-handoff",
                            "no-independent-verifier", "focused-verification"],
                signals=[], transport=None, inline_reason="atomic-direct",
                tracking="tracked", tracked_gate_evidence=copy.deepcopy(GATE))
            self.assertEqual(direct["workflow_contract"]["terminal_nodes"], ["inline"])
            self.assertEqual(direct["workflow_contract"]["continuations"], {})
            ROUTE.verify_route(direct, td)


class TestCapabilityIntegration(WorkflowFixture):
    """One end-to-end pass per capability family, on the real compiled graphs."""

    def compiled(self, capability, mode, signals):
        route = compile_fixture(capability, mode, str(self.base), signals)
        path = self.base / f"{route['route_id']}.json"
        path.write_text(json.dumps(route, indent=2), encoding="utf-8")
        return route, path

    def test_lab_setup_run_advances_to_verification_exactly_once(self):
        """BC_ResNet_tf pilot: the finished training run now carries itself forward.

        The 2026-08-04 failure was that training and its hard-negative loop finished and
        nothing owned what came next. On the real `autopilot-lab --mode setup` graph the
        supervisor must now advance `full-run` into `run-verify` — once, and only on
        genuine terminal evidence.
        """
        route, path = self.compiled("autopilot-lab", "setup", ["resource-run"])
        self.assertEqual(route["workflow_contract"]["terminal_nodes"], ["handoff"])
        registry = self.resource_registry(exit_code=0)
        marker = self.arm(path, registry, node="full-run")
        ledger = SUP.ledger_for(route)
        result = SUP.poll_once(route, ledger)
        self.assertEqual(result[0]["action"], "advanced")
        self.assertEqual([row["successor"] for row in result[0]["successors"]],
                         ["run-verify"])
        for _ in range(50):
            if marker.exists():
                break
            time.sleep(0.05)
        self.assertEqual(marker.read_text(), "x")
        self.assertEqual(SUP.poll_once(route, ledger)[0]["action"], "settled")
        self.assertEqual(marker.read_text(), "x")
        # Training succeeding is not the workflow succeeding.
        self.assertNotEqual(ledger.state()["workflow_state"], "COMPLETE")

    def test_lab_eval_run_advances_into_metrics(self):
        route, path = self.compiled("autopilot-lab", "eval", ["gpu"])
        registry = self.resource_registry(exit_code=0)
        self.arm(path, registry, node="eval-run")
        result = SUP.poll_once(route, SUP.ledger_for(route))
        self.assertEqual([row["successor"] for row in result[0]["successors"]], ["metrics"])

    def test_code_stages_are_inline_and_a_failed_registered_attempt_is_not_success(self):
        """Code stages continue in-payload; a supervisor must refuse to fake that.

        The failure evidence path still has to be exact, because the same registered
        attempt rows feed every capability that *does* supervise.
        """
        route, path = self.compiled("autopilot-code", "dev", ["shared-contract"])
        registry = self.resource_registry(exit_code=0)
        for node in ("execute", "test", "plan"):
            with self.assertRaisesRegex(SUP.SupervisorError, "supervisor governs only"):
                self.arm(path, registry, node=node)
        self.assertEqual(SUP.ledger_for(route).claims(), {})

        jobs = self.base / "jobs.log"
        def row(status, note, failure_class):
            meta = (f"attempt_id=att-code,route_node=execute,note={note},"
                    f"failure_class={failure_class}")
            return "\t".join(["2026-08-04T00:00:00Z", status, "repo", str(self.base),
                              "slug", meta])
        jobs.write_text(row("done", "dead-limit", "capacity") + "\n", encoding="utf-8")
        evidence = SUP.registered_evidence({"predecessor_id": "att-code", "jobs": str(jobs)})
        self.assertTrue(evidence["terminal"])
        self.assertFalse(evidence["succeeded"])
        jobs.write_text(row("done", "completed-marker", "pass") + "\n", encoding="utf-8")
        self.assertTrue(SUP.registered_evidence(
            {"predecessor_id": "att-code", "jobs": str(jobs)})["succeeded"])
        jobs.write_text(row("open", "", "") + "\n", encoding="utf-8")
        self.assertFalse(SUP.registered_evidence(
            {"predecessor_id": "att-code", "jobs": str(jobs)})["terminal"])

    def test_ship_readiness_stops_at_the_deploy_authorization(self):
        route, path = self.compiled("autopilot-ship", "default", ["human-gate"])
        registry = self.resource_registry(exit_code=0)
        with self.assertRaisesRegex(SUP.SupervisorError, "supervisor governs only"):
            self.arm(path, registry, node="release-review")
        SUP.main(["gate", "--route", str(path), "--gate", "deploy-authorization", "--block"])
        ledger = SUP.ledger_for(route)
        self.assertEqual(ledger.state()["workflow_state"], "BLOCKED_HUMAN_GATE")
        self.assertEqual(ledger.claims(), {})

    def test_generic_monitor_workflow_advances_only_on_a_matched_condition(self):
        """A composed observe → condition → approved-action → verify graph."""
        compose = _load("compose_route", "utilities/compose-route.py")
        topology = TOPO.load_registry()
        units = [
            {"id": "observe", "unit": "qa/data-curate", "kind": "map-worker",
             "write_scope": ["shards/observe/**"], "outputs": ["shards/observe/state.json"],
             "gate": "note-scan", "continuation": {"kind": "monitor",
                                                   "monitor": "external-state-change"}},
            {"id": "act", "unit": "dev/backend", "depends_on": ["observe"],
             "write_scope": ["source/**"], "outputs": ["source-diff"],
             "gate": "code-execute"},
            {"id": "verify", "unit": "qa/test", "depends_on": ["act"],
             "write_scope": ["reviews/monitor/**"],
             "outputs": ["reviews/monitor-verdict.json"], "gate": "code-test"},
        ]
        recipe = compose.build_recipe(
            "autopilot-code", "dev", units, topology_class="staged",
            quick_write_scope=["source/**"],
            quick_model_profile=topology["owner_profile_by_intensity"]["quick"],
            gate_index=compose.unit_io_gate_index(topology),
            human_gate_bindings=[{"gate": "approved-action", "node": "act",
                                  "position": "entry"}],
        )
        by_id = {node["id"]: node for node in recipe["standard_plus"]["nodes"]}
        # An entry gate on the action node outranks the declared monitor: an approved
        # action is a human decision, not an automatic consequence of a match.
        self.assertEqual(by_id["observe"]["continuation"],
                         {"kind": "human-gate", "gate": "approved-action"})
        self.assertTrue(by_id["verify"]["terminal"])

        unattended = copy.deepcopy(units)
        recipe = compose.build_recipe(
            "autopilot-code", "dev", unattended, topology_class="staged",
            quick_write_scope=["source/**"],
            quick_model_profile=topology["owner_profile_by_intensity"]["quick"],
            gate_index=compose.unit_io_gate_index(topology),
        )
        route = ROUTE.compile_composed_route(
            recipe, "dev", "standard", str(self.base), str(self.base),
            predicates=[], signals=["independent-verifier"], transport="headless",
            transport_evidence="fixture", tracking="tracked",
            tracked_gate_evidence=copy.deepcopy(GATE),
            dispatch_evidence=dispatch_evidence())
        self.assertEqual(route["workflow_contract"]["continuations"]["observe"], "monitor")
        self.assertEqual(route["workflow_contract"]["terminal_nodes"], ["verify"])
        path = self.base / f"{route['route_id']}.json"
        path.write_text(json.dumps(route, indent=2), encoding="utf-8")
        registry = self.resource_registry(exit_code=0)
        condition = self.base / "condition.json"
        condition.write_text(json.dumps({"condition": "pending"}), encoding="utf-8")
        marker = self.arm(path, registry, node="observe",
                          extra=["--monitor-evidence", str(condition)])
        ledger = SUP.ledger_for(route)
        self.assertEqual(SUP.poll_once(route, ledger)[0]["action"], "wait-monitor")
        condition.write_text(json.dumps({"condition": "matched"}), encoding="utf-8")
        self.assertEqual(SUP.poll_once(route, ledger)[0]["action"], "advanced")
        for _ in range(50):
            if marker.exists():
                break
            time.sleep(0.05)
        self.assertEqual(marker.read_text(), "x")


class TestRouteClosure(unittest.TestCase):
    """A cycle that edits the registry must still be able to close its own route."""

    def compile(self, cwd):
        return compile_fixture("autopilot-code", "dev", cwd, ["shared-contract"])

    def test_a_registry_edit_does_not_orphan_the_route_that_made_it(self):
        with tempfile.TemporaryDirectory() as td:
            route = self.compile(td)
            path = Path(td) / "route.json"
            ROUTE.write_once(path, route)
            stale = dict(route, registry_digest="sha256:" + "0" * 64)
            stale["route_hash"] = ROUTE.route_hash(stale)
            stale["route_id"] = "rt-" + stale["route_hash"].split(":", 1)[1][:16]
            stale_path = Path(td) / "stale-route.json"
            ROUTE.write_once(stale_path, stale)

            # Anything that could launch or mutate still refuses the stale route.
            with self.assertRaisesRegex(ValueError, "stale registry digest"):
                ROUTE.verify_route(stale)

            verified = ROUTE.verify_route(stale, allow_stale_registry=True)
            self.assertFalse(verified["_registry_current"])
            outcome, created = ROUTE.close_route(verified, stale_path, "deadbeef", "superseded")
            self.assertTrue(created)
            self.assertIs(outcome["registry_current"], False)
            self.assertEqual(outcome["route_id"], stale["route_id"])

            fresh, _created = ROUTE.close_route(
                ROUTE.verify_route(route, allow_stale_registry=True), path, "deadbeef", "done")
            self.assertIs(fresh["registry_current"], True)

            rows = {row["route_id"]: row for row in ROUTE.route_status(td)}
            self.assertTrue(all(row["closed"] for row in rows.values()))
            self.assertIs(rows[stale["route_id"]]["registry_current"], False)

    def test_a_tampered_route_is_never_closable(self):
        with tempfile.TemporaryDirectory() as td:
            route = self.compile(td)
            route["nodes"][0]["write_scope"] = ["source/**"]
            with self.assertRaisesRegex(ValueError, "stale or modified route hash"):
                ROUTE.verify_route(route, allow_stale_registry=True)


class TestParentResumeOncePerBatch(unittest.TestCase):
    """Managed completion resumes the parent thread once per batch, not per child."""

    def test_a_batch_receipt_is_consumed_exactly_once(self):
        join = _load("dispatch_completion_join", "utilities/dispatch_completion_join.py")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "parent-session.json"
            session = "session-fixture"
            for attempt in ("att-one", "att-two"):
                join.register_parent_session_attempt(path, session, attempt)
            state = join.read_parent_session_batch_state(path, session)
            self.assertEqual(set(state.attempt_ids), {"att-one", "att-two"})
            join.write_parent_session_state(path, session, {"att-one", "att-two"},
                                            attempt_ids={"att-one", "att-two"})
            self.assertTrue(join.consume_parent_session_attempt(path, session, "att-one"))
            self.assertFalse(join.consume_parent_session_attempt(path, session, "att-one"),
                             "a delivered receipt may not wake the parent twice")
            self.assertTrue(join.consume_parent_session_attempt(path, session, "att-two"))
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main(verbosity=1)
