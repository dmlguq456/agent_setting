#!/usr/bin/env python3
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("route", ROOT / "utilities/capability-route.py")
ROUTE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ROUTE)
broker_spec = importlib.util.spec_from_file_location("dispatch_broker", ROOT / "utilities/dispatch-broker.py")
BROKER = importlib.util.module_from_spec(broker_spec)
broker_spec.loader.exec_module(BROKER)
fallback_spec = importlib.util.spec_from_file_location("stage_dispatch_fallback", ROOT / "utilities/stage-dispatch-fallback.py")
FALLBACK = importlib.util.module_from_spec(fallback_spec)
fallback_spec.loader.exec_module(FALLBACK)


class DispatchBrokerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "fixture@example.com"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Fixture"], check=True)
        (self.repo / "x").write_text("x", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "x"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "init"], check=True)
        self.artifact = self.base / ".agent_reports"
        self.artifact.mkdir()
        self.jobs = self.base / "jobs.log"
        self.broker_root = self.base / "broker"
        ensured = subprocess.run(
            [
                sys.executable,
                str(ROOT / "utilities/dispatch-broker.py"),
                "ensure",
                "--root",
                str(self.broker_root),
                "--jobs",
                str(self.jobs),
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        self.meta = dict(line.split("=", 1) for line in ensured.stdout.splitlines() if "=" in line)

    def tearDown(self):
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "utilities/dispatch-broker.py"),
                "stop",
                "--root",
                str(self.broker_root),
                "--jobs",
                str(self.jobs),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        deadline = time.monotonic() + 2
        while self.broker_root.joinpath("broker.sock").exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        self.temp.cleanup()

    def tuple(self, parent, child, status):
        return {
            "parent_harness": parent,
            "parent_transport": "headless",
            "parent_sandbox": "fixture",
            "child_harness": child,
            "launch_authority": "ancestor-broker",
            "status": status,
            "probe_source": "fixture-broker",
            "probe_time": "2026-07-15T00:00:00Z",
            "failure_class": "" if status == "supported" else "fixture-ineligible",
            "broker_root": str(self.broker_root),
            "broker_instance": self.meta["broker_instance"],
        }

    def route(self, parent, child):
        rows = [self.tuple(parent, parent, "supported" if parent == child else "unsupported")]
        if child != parent:
            rows.append(self.tuple(parent, child, "supported"))
        evidence = {"tuples": rows, "native_subagent": []}
        gate = {
            "spec_read": {"satisfied": True, "source": "fixture"},
            "drift_verdict": "within-spec",
            "workflow_mode": "tracked",
            "artifact_guard": {"satisfied": True, "source": "fixture"},
        }
        route = ROUTE.compile_route(
            "autopilot-code",
            "dev",
            "strong",
            self.repo,
            self.artifact,
            signals=["shared-contract"],
            transport="headless",
            tracking="tracked",
            tracked_gate_evidence=gate,
            dispatch_evidence=evidence,
        )
        path = self.base / f"route-{parent}-{child}.json"
        path.write_text(json.dumps(route), encoding="utf-8")
        return path

    def environment(self, instance=None):
        return {
            **os.environ,
            "AGENT_HOME": str(ROOT),
            "AGENT_ARTIFACT_ROOT": str(self.artifact),
            "AGENT_DISPATCH_JOBS": str(self.jobs),
            "AGENT_DISPATCH_BROKER_ROOT": str(self.broker_root),
            "AGENT_DISPATCH_BROKER_INSTANCE": instance or self.meta["broker_instance"],
        }

    def chain(self, parent, child, slug=None, broker_root=None, instance=None):
        route = self.route(parent, child)
        command = [
            sys.executable,
            str(ROOT / "utilities/stage-dispatch-fallback.py"),
            "--route",
            str(route),
            "--node",
            "plan",
            "--slug",
            slug or f"{parent}-{child}",
            "--parent",
            f"{parent}-owner",
            "--mode",
            "dev/backend",
            "--model-role",
            "deep maker",
            "--jobs",
            str(self.jobs),
            "--broker-root",
            str(broker_root or self.broker_root),
            "--register",
        ]
        return subprocess.run(command, text=True, capture_output=True, env=self.environment(instance))

    def request(self, parent, child, slug):
        route_path = self.route(parent, child)
        route = json.loads(route_path.read_text(encoding="utf-8"))
        node = route["nodes"][0]
        row = next(
            candidate
            for hop in node["dispatch_fallback"][:2]
            for candidate in hop.get("candidates", [])
            if candidate["status"] == "supported" and candidate["child_harness"] == child
        )
        ordinal = 1 if parent == child else 2
        args = SimpleNamespace(
            action="register",
            slug=slug,
            parent=f"{parent}-owner",
            mode="dev/backend",
            worker_role=None,
            model_role="deep maker",
            prompt_file=None,
            route=route_path,
            jobs=self.jobs,
        )
        return FALLBACK.broker_envelope(args, route, node, row, ordinal)

    def submit(self, request):
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "utilities/dispatch-broker.py"),
                "request",
                "--root",
                str(self.broker_root),
                "--jobs",
                str(self.jobs),
            ],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            env=self.environment(),
        )

    def restart_broker(self, *, crash=False):
        old = dict(self.meta)
        if crash:
            os.kill(int(old["broker_pid"]), signal.SIGKILL)
        else:
            stopped = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "utilities/dispatch-broker.py"),
                    "stop",
                    "--root",
                    str(self.broker_root),
                    "--jobs",
                    str(self.jobs),
                ],
                text=True,
                capture_output=True,
                env=self.environment(),
            )
            self.assertEqual(stopped.returncode, 0, stopped.stdout + stopped.stderr)
        deadline = time.monotonic() + 3
        while BROKER.process_matches(int(old["broker_pid"]), old["broker_start_ticks"]) and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertFalse(BROKER.process_matches(int(old["broker_pid"]), old["broker_start_ticks"]))
        ensured = subprocess.run(
            [
                sys.executable,
                str(ROOT / "utilities/dispatch-broker.py"),
                "ensure",
                "--root",
                str(self.broker_root),
                "--jobs",
                str(self.jobs),
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        self.meta = dict(line.split("=", 1) for line in ensured.stdout.splitlines() if "=" in line)
        self.assertNotEqual(old["broker_instance"], self.meta["broker_instance"])
        return old

    def test_four_parent_child_placements_use_one_external_broker(self):
        for parent, child in (
            ("claude", "claude"),
            ("claude", "codex"),
            ("codex", "claude"),
            ("codex", "codex"),
        ):
            with self.subTest(parent=parent, child=child):
                result = self.chain(parent, child)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn(f"child_harness={child}", result.stdout)
                self.assertIn("launch_authority=ancestor-broker", result.stdout)
                self.assertIn(f"broker_pid={self.meta['broker_pid']}", result.stdout)
                self.assertNotEqual(int(self.meta["broker_pid"]), os.getpid())
        rows = self.jobs.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(rows), 4)
        for parent, child in (
            ("claude", "claude"),
            ("claude", "codex"),
            ("codex", "claude"),
            ("codex", "codex"),
        ):
            row = next(line for line in rows if f"\t{parent}-{child}\t" in line)
            self.assertIn("depth=2", row)
            self.assertIn(f"parent={parent}-owner", row)
            self.assertIn(f"harness={child}", row)
            self.assertIn("launch_authority=ancestor-broker", row)
            self.assertIn("attempt_id=att-", row)
            self.assertIn("broker_request_id=req-", row)

    def test_duplicate_request_is_idempotent(self):
        first = self.chain("codex", "claude", slug="duplicate")
        second = self.chain("codex", "claude", slug="duplicate")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(first.stdout.split("request_id=", 1)[1].splitlines()[0], second.stdout.split("request_id=", 1)[1].splitlines()[0])
        rows = [line for line in self.jobs.read_text(encoding="utf-8").splitlines() if "\tduplicate\t" in line]
        self.assertEqual(len(rows), 1)

    def test_concurrent_duplicate_request_creates_one_attempt(self):
        request = self.request("claude", "codex", "concurrent-duplicate")
        command = [
            sys.executable,
            str(ROOT / "utilities/dispatch-broker.py"),
            "request",
            "--root",
            str(self.broker_root),
            "--jobs",
            str(self.jobs),
        ]
        processes = [
            subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=self.environment())
            for _ in range(2)
        ]
        results = [process.communicate(json.dumps(request), timeout=10) + (process.returncode,) for process in processes]
        for stdout, stderr, returncode in results:
            self.assertEqual(returncode, 0, stdout + stderr)
        rows = [line for line in self.jobs.read_text(encoding="utf-8").splitlines() if "\tconcurrent-duplicate\t" in line]
        self.assertEqual(len(rows), 1)
        self.assertIn(f"attempt_id={request['attempt_id']}", rows[0])

    def test_depth0_can_rotate_to_new_canonical_fixture_registry(self):
        previous_pid = self.meta["broker_pid"]
        replacement_jobs = self.base / "replacement.jobs.log"
        replaced = subprocess.run(
            [
                sys.executable,
                str(ROOT / "utilities/dispatch-broker.py"),
                "ensure",
                "--root",
                str(self.broker_root),
                "--jobs",
                str(replacement_jobs),
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        self.meta = dict(line.split("=", 1) for line in replaced.stdout.splitlines() if "=" in line)
        self.jobs = replacement_jobs
        self.assertNotEqual(previous_pid, self.meta["broker_pid"])
        self.assertEqual(str(replacement_jobs), self.meta["broker_jobs"])

    def test_claim_crash_restarts_only_unregistered_attempt(self):
        request = self.request("codex", "claude", "claim-crash")
        normalized = BROKER.validate_request(
            request,
            self.jobs,
            self.broker_root,
            self.meta["broker_instance"],
        )
        digest = "sha256:" + BROKER.hashlib.sha256(BROKER.canonical(normalized)).hexdigest()
        state = {
            "schema_version": 1,
            "request_id": request["request_id"],
            "attempt_id": request["attempt_id"],
            "request_hash": digest,
            "request": normalized,
            "status": "claimed",
            "broker_instance": self.meta["broker_instance"],
            "fencing_token": self.meta["broker_instance"],
            "lease_expires_epoch": time.time() + 60,
            "created_at": BROKER.utcnow(),
            "updated_at": BROKER.utcnow(),
        }
        BROKER.atomic_json(self.broker_root / "requests" / f"{request['request_id']}.json", state)
        old = self.restart_broker(crash=True)
        recovered = self.submit(request)
        self.assertEqual(recovered.returncode, 0, recovered.stdout + recovered.stderr)
        reply = json.loads(recovered.stdout)
        self.assertEqual(reply["state"]["broker_instance"], self.meta["broker_instance"])
        self.assertEqual(reply["state"].get("recovered_after_fence"), True)
        self.assertEqual(reply["state"]["response"]["recovered_from_registry"], False)
        self.assertEqual(self.meta.get("broker_implementation"), old.get("broker_implementation"))
        rows = [line for line in self.jobs.read_text(encoding="utf-8").splitlines() if "\tclaim-crash\t" in line]
        self.assertEqual(len(rows), 1)

    def test_spawn_crash_recovers_registered_attempt_without_relaunch(self):
        request = self.request("codex", "claude", "spawn-crash")
        first = self.submit(request)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        state_path = self.broker_root / "requests" / f"{request['request_id']}.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["status"] = "running"
        state["broker_instance"] = self.meta["broker_instance"]
        state["lease_expires_epoch"] = time.time() + 60
        state.pop("response", None)
        state_path.write_text(json.dumps(state), encoding="utf-8")
        self.restart_broker(crash=True)
        recovered = self.submit(request)
        self.assertEqual(recovered.returncode, 0, recovered.stdout + recovered.stderr)
        reply = json.loads(recovered.stdout)
        self.assertEqual(reply["state"]["response"]["recovered_from_registry"], True)
        self.assertIn("broker_recovered_from_registry=1", reply["state"]["response"]["stdout"])
        rows = [line for line in self.jobs.read_text(encoding="utf-8").splitlines() if "\tspawn-crash\t" in line]
        self.assertEqual(len(rows), 1)

    def test_zero_staleness_threshold_reports_stale_identity(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "utilities/dispatch-broker.py"),
                "status",
                "--root",
                str(self.broker_root),
                "--jobs",
                str(self.jobs),
                "--stale-seconds",
                "0",
            ],
            text=True,
            capture_output=True,
            env=self.environment(),
        )
        self.assertEqual(result.returncode, 76, result.stdout + result.stderr)
        self.assertIn("reason=broker-stale", result.stdout)

    def test_missing_broker_fails_closed(self):
        missing = self.base / "missing-broker"
        result = self.chain("codex", "claude", broker_root=missing)
        self.assertEqual(result.returncode, 76, result.stdout + result.stderr)
        self.assertIn("reason=broker-unavailable", result.stdout)
        self.assertIn("child_spawned=0", result.stdout)
        self.assertFalse(self.jobs.exists())

    def test_tampered_inherited_instance_fails_closed(self):
        result = self.chain("codex", "claude", instance="brk-tampered")
        self.assertEqual(result.returncode, 76, result.stdout + result.stderr)
        self.assertIn("reason=broker-instance-mismatch", result.stdout)
        self.assertIn("child_spawned=0", result.stdout)
        self.assertFalse(self.jobs.exists())

    def test_unknown_request_fields_are_rejected_without_registry_row(self):
        route_path = self.route("codex", "claude")
        route = json.loads(route_path.read_text(encoding="utf-8"))
        node = route["nodes"][0]
        row = node["dispatch_fallback"][1]["candidates"][0]
        module = importlib.util.spec_from_file_location("fallback", ROOT / "utilities/stage-dispatch-fallback.py")
        # Build the normal envelope through a dry CLI trace, then assert the
        # server rejects an extra arbitrary command field before target launch.
        request_id = "req-" + "a" * 32
        attempt_id = "att-" + "b" * 32
        request = {
            "schema_version": 1,
            "request_id": request_id,
            "attempt_id": attempt_id,
            "action": "register",
            "target_harness": "claude",
            "worktree": str(self.repo),
            "artifact_root": str(self.artifact),
            "jobs": str(self.jobs),
            "slug": "invalid-argv",
            "capability": route["capability"],
            "mode": "dev/backend",
            "intensity": route["effective_intensity"],
            "depth": 2,
            "parent": "owner",
            "worker_role": "code-plan",
            "owner": route["capability"],
            "model_role": "deep maker",
            "route_file": str(route_path),
            "route_id": route["route_id"],
            "route_hash": route["route_hash"],
            "route_node": node["id"],
            "registry_digest": route["registry_digest"],
            "write_scope": ";".join(node["write_scope"]),
            "completion_gate": node["completion_gate"],
            "parent_harness": row["parent_harness"],
            "parent_transport": row["parent_transport"],
            "parent_sandbox": row["parent_sandbox"],
            "requested_launch_authority": row["launch_authority"],
            "fallback_ordinal": 2,
            "probe_source": row["probe_source"],
            "probe_failure_class": "",
            "broker_root": row["broker_root"],
            "broker_instance": row["broker_instance"],
            "argv": ["sh", "-c", "touch forbidden"],
        }
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "utilities/dispatch-broker.py"),
                "request",
                "--root",
                str(self.broker_root),
                "--jobs",
                str(self.jobs),
            ],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            env=self.environment(),
        )
        self.assertEqual(result.returncode, 76, result.stdout + result.stderr)
        reply = json.loads(result.stdout)
        self.assertEqual(reply["reason"], "broker-request-invalid")
        self.assertFalse(self.jobs.exists())


if __name__ == "__main__":
    unittest.main()
