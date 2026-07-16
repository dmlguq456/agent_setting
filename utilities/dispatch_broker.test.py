#!/usr/bin/env python3
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
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

    def route_v1(self, parent, child):
        # Hand-forced v1 record (compile_route only produces v2 now) --
        # needed by tests that specifically exercise v1's env-trusting,
        # instance-bound behavior (§1.6b). Mirrors capability_route.test.py's
        # test_v1_record_keeps_instance_binding_rules construction.
        path = self.route(parent, child)
        route = json.loads(path.read_text(encoding="utf-8"))
        route["broker_contract_version"] = 1
        for row in route.get("dispatch_evidence", {}).get("tuples", []):
            if row.get("launch_authority") == "ancestor-broker":
                row["broker_instance"] = self.meta["broker_instance"]
        for node in route.get("nodes", []):
            for hop in node.get("dispatch_fallback", []):
                for row in hop.get("candidates", []):
                    if row.get("launch_authority") == "ancestor-broker":
                        row["broker_instance"] = self.meta["broker_instance"]
        route["route_hash"] = ROUTE.route_hash(route)
        route["route_id"] = "rt-" + route["route_hash"].split(":", 1)[1][:16]
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

    def chain(self, parent, child, slug=None, broker_root=None, instance=None, route_path=None):
        route = route_path or self.route(parent, child)
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
        return FALLBACK.broker_envelope(args, route, node, row, ordinal, live_instance=self.meta["broker_instance"])

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

    def fake_agent_home(self) -> Path:
        # A minimal AGENT_HOME whose claude adapter is a fake, controllable
        # sleeping process instead of the real dispatch-headless.py -- used to
        # exercise HOL-blocking / parallel-recovery scenarios without ever
        # spawning a real claude/codex/opencode session (§4.0).
        home = self.base / "fake-agent-home"
        (home / "core").mkdir(parents=True)
        (home / "core" / "CORE.md").write_text("fixture\n", encoding="utf-8")
        adapter_dir = home / "adapters" / "claude" / "bin"
        adapter_dir.mkdir(parents=True)
        script = adapter_dir / "dispatch-headless.py"
        script.write_text(
            "#!/usr/bin/env python3\n"
            "import argparse, json, os, time\n"
            "from pathlib import Path\n"
            "p = argparse.ArgumentParser()\n"
            "p.add_argument('--slug', required=True)\n"
            "args, _ = p.parse_known_args()\n"
            "artifact_root = Path(os.environ['AGENT_ARTIFACT_ROOT'])\n"
            "config_path = artifact_root / 'sleep-seconds.json'\n"
            "seconds = 0.0\n"
            "if config_path.is_file():\n"
            "    seconds = float(json.loads(config_path.read_text()).get(args.slug, 0.0))\n"
            "(artifact_root / f'started-{args.slug}.marker').write_text('1')\n"
            "time.sleep(seconds)\n"
            "(artifact_root / f'done-{args.slug}.marker').write_text('1')\n",
            encoding="utf-8",
        )
        os.chmod(script, 0o755)
        return home

    def fixture_broker_request(self, slug, broker_root, broker_instance):
        # Build a route+envelope bound to an arbitrary (fixture) broker
        # root/instance rather than self.broker_root -- needed because
        # self.route()/self.request() hardcode the setUp broker.
        rows = [
            {
                "parent_harness": "claude",
                "parent_transport": "headless",
                "parent_sandbox": "fixture",
                "child_harness": "claude",
                "launch_authority": "ancestor-broker",
                "status": "supported",
                "probe_source": "fixture-broker",
                "probe_time": "2026-07-15T00:00:00Z",
                "failure_class": "",
                "broker_root": str(broker_root),
                "broker_instance": broker_instance,
            }
        ]
        evidence = {"tuples": rows, "native_subagent": []}
        gate = {
            "spec_read": {"satisfied": True, "source": "fixture"},
            "drift_verdict": "within-spec",
            "workflow_mode": "tracked",
            "artifact_guard": {"satisfied": True, "source": "fixture"},
        }
        route = ROUTE.compile_route(
            "autopilot-code", "dev", "strong", self.repo, self.artifact,
            signals=["shared-contract"], transport="headless", tracking="tracked",
            tracked_gate_evidence=gate, dispatch_evidence=evidence,
        )
        path = self.base / f"route-fixture-{slug}.json"
        path.write_text(json.dumps(route), encoding="utf-8")
        node = route["nodes"][0]
        row = node["dispatch_fallback"][0]["candidates"][0]
        args = SimpleNamespace(
            action="register", slug=slug, parent="fixture-owner", mode="dev/backend",
            worker_role=None, model_role="deep maker", prompt_file=None,
            route=path, jobs=self.jobs,
        )
        return FALLBACK.broker_envelope(args, route, node, row, 1, live_instance=broker_instance)

    def submit_to(self, request, broker_root, broker_instance, env_overrides=None):
        env = self.environment(instance=broker_instance)
        env["AGENT_DISPATCH_BROKER_ROOT"] = str(broker_root)
        if env_overrides:
            env.update(env_overrides)
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "utilities/dispatch-broker.py"),
                "request",
                "--root",
                str(broker_root),
                "--jobs",
                str(self.jobs),
            ],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            env=env,
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
        # SD-54 (§1.6a): per-request lock + lease-renewal makes the inflight
        # rejection deterministic. The claim/running transition (in the lock)
        # is fast; the target subprocess.run (outside the lock) is slow enough
        # that the second submission reliably observes the lease as live and
        # is rejected with broker-request-inflight rather than being
        # reconciled against the registry row (which would prematurely
        # terminate the request while the first target is still running).
        # A fake, deliberately-slow target (fixture broker, §4.0) is used so
        # the overlap is deterministic rather than a race against however
        # fast the real --register action happens to complete.
        fake_home = self.fake_agent_home()
        fixture_broker_root = self.base / "fixture-broker-concurrent"
        (self.artifact / "sleep-seconds.json").write_text(
            json.dumps({"concurrent-duplicate": 2}), encoding="utf-8"
        )
        env = dict(os.environ)
        for key in ("AGENT_SESSION_ROLE", "AGENT_DISPATCH_CHILD", "AGENT_DISPATCH_BROKER_INSTANCE", "AGENT_DISPATCH_BROKER_ROOT", "AGENT_DISPATCH_JOBS"):
            env.pop(key, None)
        env["AGENT_HOME"] = str(fake_home)
        ensured = subprocess.run(
            [
                sys.executable, str(ROOT / "utilities/dispatch-broker.py"), "ensure",
                "--root", str(fixture_broker_root), "--jobs", str(self.jobs),
            ],
            text=True, capture_output=True, check=True, env=env,
        )
        meta = dict(line.split("=", 1) for line in ensured.stdout.splitlines() if "=" in line)
        try:
            request = self.fixture_broker_request("concurrent-duplicate", fixture_broker_root, meta["broker_instance"])
            command = [
                sys.executable,
                str(ROOT / "utilities/dispatch-broker.py"),
                "request",
                "--root",
                str(fixture_broker_root),
                "--jobs",
                str(self.jobs),
            ]
            submit_env = self.environment(instance=meta["broker_instance"])
            submit_env["AGENT_DISPATCH_BROKER_ROOT"] = str(fixture_broker_root)
            processes = [
                subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=submit_env)
                for _ in range(2)
            ]
            # communicate() must run concurrently, not sequentially -- a list
            # comprehension would block on process[0] before process[1] even
            # receives its stdin, defeating the overlap this fixture needs.
            outcomes = [None, None]

            def run(index, process):
                outcomes[index] = process.communicate(json.dumps(request), timeout=15) + (process.returncode,)

            threads = [threading.Thread(target=run, args=(i, p)) for i, p in enumerate(processes)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=20)
            results = outcomes
            replies = [json.loads(stdout) for stdout, _stderr, _rc in results]
            ok_replies = [reply for reply in replies if reply.get("ok")]
            rejected = [reply for reply in replies if not reply.get("ok")]
            self.assertEqual(len(ok_replies), 1, replies)
            self.assertEqual(len(rejected), 1, replies)
            self.assertEqual(rejected[0].get("reason"), "broker-request-inflight", rejected)
            # the fake fixture target never writes the real jobs registry --
            # the invariant here is a single terminal state for the shared
            # request_id/attempt_id, asserted above via ok_replies/rejected.
            self.assertFalse(self.jobs.exists())
        finally:
            subprocess.run(
                [
                    sys.executable, str(ROOT / "utilities/dispatch-broker.py"), "stop",
                    "--root", str(fixture_broker_root), "--jobs", str(self.jobs),
                ],
                text=True, capture_output=True, check=False, env=env,
            )

    def test_resubmit_while_running_with_registry_row_is_inflight(self):
        # SD-54 §1.3e / plan-check B3: SD-52 writes the registry row BEFORE spawn,
        # so a resubmit of a still-running request WILL find a row. The inflight
        # check must therefore precede the registry reconcile -- otherwise the
        # resubmit reconciles against that row and terminates the request while
        # its target is still executing (terminal immutability + AC2 both break).
        # Reverting the order leaves every other fixture green, so this one is the
        # only guard.
        home = self.base / "b3-home"
        (home / "core").mkdir(parents=True)
        (home / "core" / "CORE.md").write_text("fixture\n", encoding="utf-8")
        adapter_dir = home / "adapters" / "claude" / "bin"
        adapter_dir.mkdir(parents=True)
        script = adapter_dir / "dispatch-headless.py"
        script.write_text(
            "#!/usr/bin/env python3\n"
            "import argparse, os, time\n"
            "from pathlib import Path\n"
            "p=argparse.ArgumentParser()\n"
            "p.add_argument('--slug'); p.add_argument('--jobs'); p.add_argument('--attempt-id', dest='att')\n"
            "a,_=p.parse_known_args()\n"
            # the canonical spawn-time row -- exactly what makes the B3 race reachable
            "row='2026-07-16T00:00:00Z\\trunning\\t2\\towner\\t'+a.slug+'\\tattempt_id='+a.att+',note=live'\n"
            "Path(a.jobs).parent.mkdir(parents=True, exist_ok=True)\n"
            "with open(a.jobs,'a') as fh: fh.write(row+'\\n')\n"
            "art=Path(os.environ['AGENT_ARTIFACT_ROOT'])\n"
            "(art/('started-'+a.slug+'.marker')).write_text('1')\n"
            "time.sleep(6)\n"
            "(art/('done-'+a.slug+'.marker')).write_text('1')\n",
            encoding="utf-8",
        )
        os.chmod(script, 0o755)
        broker_root = self.base / "b3-broker"
        env = dict(os.environ)
        for key in ("AGENT_SESSION_ROLE", "AGENT_DISPATCH_CHILD", "AGENT_DISPATCH_BROKER_INSTANCE",
                    "AGENT_DISPATCH_BROKER_ROOT", "AGENT_DISPATCH_JOBS"):
            env.pop(key, None)
        env["AGENT_HOME"] = str(home)
        ensured = subprocess.run(
            [sys.executable, str(ROOT / "utilities/dispatch-broker.py"), "ensure",
             "--root", str(broker_root), "--jobs", str(self.jobs)],
            text=True, capture_output=True, check=True, env=env,
        )
        meta = dict(line.split("=", 1) for line in ensured.stdout.splitlines() if "=" in line)
        try:
            request = self.fixture_broker_request("b3", broker_root, meta["broker_instance"])
            results = {}
            first = threading.Thread(target=lambda: results.__setitem__(
                "first", self.submit_to(request, broker_root, meta["broker_instance"])))
            first.start()
            started = self.artifact / "started-b3.marker"
            deadline = time.monotonic() + 15
            while not started.exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertTrue(started.exists(), "target never started")
            time.sleep(0.4)  # let the row land

            second = self.submit_to(request, broker_root, meta["broker_instance"])
            reply = json.loads(second.stdout)
            # the target must still be running -- otherwise this asserts nothing
            self.assertFalse((self.artifact / "done-b3.marker").exists())
            self.assertFalse(reply.get("ok"), reply)
            self.assertEqual(reply.get("reason"), "broker-request-inflight", reply)
            first.join(timeout=30)
        finally:
            subprocess.run(
                [sys.executable, str(ROOT / "utilities/dispatch-broker.py"), "stop",
                 "--root", str(broker_root), "--jobs", str(self.jobs)],
                text=True, capture_output=True, check=False, env=env,
            )

    def test_slow_target_does_not_block_other_requests(self):
        # SD-54 acceptance ①: a slow target must not block a second,
        # independent request from launching, running, and completing.
        fake_home = self.fake_agent_home()
        fixture_broker_root = self.base / "fixture-broker"
        (self.artifact / "sleep-seconds.json").write_text(
            json.dumps({"slow": 5, "fast": 0}), encoding="utf-8"
        )
        env = dict(os.environ)
        for key in ("AGENT_SESSION_ROLE", "AGENT_DISPATCH_CHILD", "AGENT_DISPATCH_BROKER_INSTANCE", "AGENT_DISPATCH_BROKER_ROOT", "AGENT_DISPATCH_JOBS"):
            env.pop(key, None)
        env["AGENT_HOME"] = str(fake_home)
        ensured = subprocess.run(
            [
                sys.executable, str(ROOT / "utilities/dispatch-broker.py"), "ensure",
                "--root", str(fixture_broker_root), "--jobs", str(self.jobs),
            ],
            text=True, capture_output=True, check=True, env=env,
        )
        meta = dict(line.split("=", 1) for line in ensured.stdout.splitlines() if "=" in line)
        try:
            slow_request = self.fixture_broker_request("slow", fixture_broker_root, meta["broker_instance"])
            fast_request = self.fixture_broker_request("fast", fixture_broker_root, meta["broker_instance"])

            results = {}
            slow_thread = threading.Thread(
                target=lambda: results.__setitem__(
                    "slow", self.submit_to(slow_request, fixture_broker_root, meta["broker_instance"])
                )
            )
            slow_thread.start()

            # Barrier: wait until the slow target has actually entered its
            # execution window (the per-request lock is held/released fast;
            # without this, a resurrected global lock could still pass).
            started_marker = self.artifact / "started-slow.marker"
            deadline = time.monotonic() + 10
            while not started_marker.exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertTrue(started_marker.exists(), "slow target did not start in time")

            fast_result = self.submit_to(fast_request, fixture_broker_root, meta["broker_instance"])
            self.assertEqual(fast_result.returncode, 0, fast_result.stdout + fast_result.stderr)
            fast_reply = json.loads(fast_result.stdout)
            self.assertTrue(fast_reply.get("ok"), fast_reply)
            self.assertEqual(fast_reply["state"]["status"], "done")

            # Decisive evidence of HOL-blocking resolution: fast completed
            # while slow's target is still sleeping.
            self.assertFalse((self.artifact / "done-slow.marker").exists())

            slow_thread.join(timeout=30)
            self.assertIn("slow", results)
            slow_result = results["slow"]
            self.assertEqual(slow_result.returncode, 0, slow_result.stdout + slow_result.stderr)
            slow_reply = json.loads(slow_result.stdout)
            self.assertTrue(slow_reply.get("ok"), slow_reply)
            self.assertEqual(slow_reply["state"]["status"], "done")
            self.assertTrue((self.artifact / "done-slow.marker").exists())
        finally:
            subprocess.run(
                [
                    sys.executable, str(ROOT / "utilities/dispatch-broker.py"), "stop",
                    "--root", str(fixture_broker_root), "--jobs", str(self.jobs),
                ],
                text=True, capture_output=True, check=False, env=env,
            )

    def test_fenced_recovery_holds_under_parallel_inflight(self):
        # SD-54 acceptance ③ under parallel load: a claim-crash recovery for
        # one request must not be corrupted by, or corrupt, a concurrently
        # submitted, unrelated request handled by the same broker.
        victim = self.request("codex", "claude", "fenced-victim")
        normalized = BROKER.validate_request(
            victim, self.jobs, self.broker_root, self.meta["broker_instance"],
        )
        digest = "sha256:" + BROKER.hashlib.sha256(BROKER.canonical(normalized)).hexdigest()
        state = {
            "schema_version": 1,
            "request_id": victim["request_id"],
            "attempt_id": victim["attempt_id"],
            "request_hash": digest,
            "request": normalized,
            "status": "claimed",
            "broker_instance": self.meta["broker_instance"],
            "fencing_token": self.meta["broker_instance"],
            "lease_expires_epoch": time.time() + 60,
            "created_at": BROKER.utcnow(),
            "updated_at": BROKER.utcnow(),
        }
        BROKER.atomic_json(self.broker_root / "requests" / f"{victim['request_id']}.json", state)

        parallel_results = {}

        def submit_parallel():
            parallel_results["reply"] = self.chain("codex", "claude", slug="fenced-parallel")

        parallel_thread = threading.Thread(target=submit_parallel)
        parallel_thread.start()

        self.restart_broker(crash=True)
        parallel_thread.join(timeout=15)
        self.assertIn("reply", parallel_results)

        recovered = self.submit(victim)
        self.assertEqual(recovered.returncode, 0, recovered.stdout + recovered.stderr)
        reply = json.loads(recovered.stdout)
        self.assertEqual(reply["state"]["broker_instance"], self.meta["broker_instance"])
        self.assertEqual(reply["state"].get("recovered_after_fence"), True)

        rows = self.jobs.read_text(encoding="utf-8").splitlines()
        victim_rows = [line for line in rows if "\tfenced-victim\t" in line]
        self.assertEqual(len(victim_rows), 1)
        parallel_rows = [line for line in rows if "\tfenced-parallel\t" in line]
        self.assertLessEqual(len(parallel_rows), 1)

    def test_v2_record_survives_broker_rollover(self):
        # SD-55 acceptance (1): v2 hop resolves the live instance at submit
        # time, so a rollover (restart with a new instance id) must not
        # degrade the ordinal-1 hop, and the immutable record's hash must be
        # untouched (identity moved out of the record entirely).
        self.assertTrue(str(Path(self.broker_root).resolve()).startswith(str(self.base.resolve())))
        old_instance = self.meta["broker_instance"]
        route_path = self.route("codex", "codex")
        route_before = json.loads(route_path.read_text(encoding="utf-8"))
        self.assertEqual(route_before.get("broker_contract_version"), 2)
        route_hash_before = route_before["route_hash"]

        self.restart_broker(crash=False)
        self.assertNotEqual(self.meta["broker_instance"], old_instance)

        # Deliberately inject the stale pre-rollover instance into the
        # conductor's env (§2.3's exact target scenario) and confirm the v2
        # hop ignores it and resolves live instead.
        result = self.chain("codex", "codex", instance=old_instance, route_path=route_path)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("check=ok", result.stdout)
        self.assertIn("selected_hop=same-harness-headless", result.stdout)
        self.assertIn("fallback_ordinal=1", result.stdout)
        self.assertNotIn("check=degraded", result.stdout)
        self.assertIn(f"broker_instance={self.meta['broker_instance']}", result.stdout)

        reloaded = json.loads(route_path.read_text(encoding="utf-8"))
        self.assertEqual(reloaded["route_hash"], route_hash_before)

    def test_v2_record_without_live_broker_fails_closed(self):
        # SD-55 acceptance (3): a v2 hop whose broker cannot be reached must
        # fail closed with `broker-unavailable`, and -- because the status-only
        # design (§2.2) never runs `ensure` from this caller -- must never
        # create a broker as a side effect.
        never_root = self.base / "never-broker"
        route_path = self.route("codex", "claude")
        route = json.loads(route_path.read_text(encoding="utf-8"))
        for row in route["dispatch_evidence"]["tuples"]:
            row["broker_root"] = str(never_root)
        for node in route["nodes"]:
            for hop in node.get("dispatch_fallback", []):
                for candidate in hop.get("candidates", []):
                    candidate["broker_root"] = str(never_root)
        route["route_hash"] = ROUTE.route_hash(route)
        route["route_id"] = "rt-" + route["route_hash"].split(":", 1)[1][:16]
        never_path = self.base / "route-never-broker.json"
        never_path.write_text(json.dumps(route), encoding="utf-8")

        result = self.chain("codex", "claude", broker_root=never_root, route_path=never_path)
        self.assertEqual(result.returncode, 76, result.stdout + result.stderr)
        self.assertIn("reason=broker-unavailable", result.stdout)
        self.assertIn("child_spawned=0", result.stdout)
        self.assertFalse(self.jobs.exists())
        self.assertFalse((never_root / "broker.json").exists())

        # variant: a fixture broker that *was* alive is now stopped.
        stopped_root = self.base / "stopped-broker"
        clean_env = dict(os.environ)
        for key in ("AGENT_SESSION_ROLE", "AGENT_DISPATCH_CHILD", "AGENT_DISPATCH_BROKER_INSTANCE", "AGENT_DISPATCH_BROKER_ROOT", "AGENT_DISPATCH_JOBS"):
            clean_env.pop(key, None)
        subprocess.run(
            [sys.executable, str(ROOT / "utilities/dispatch-broker.py"), "ensure",
             "--root", str(stopped_root), "--jobs", str(self.jobs)],
            text=True, capture_output=True, check=True, env=clean_env,
        )
        subprocess.run(
            [sys.executable, str(ROOT / "utilities/dispatch-broker.py"), "stop",
             "--root", str(stopped_root), "--jobs", str(self.jobs)],
            text=True, capture_output=True, check=False, env=clean_env,
        )
        deadline = time.monotonic() + 3
        while (stopped_root / "broker.sock").exists() and time.monotonic() < deadline:
            time.sleep(0.02)

        route2 = json.loads(route_path.read_text(encoding="utf-8"))
        for row in route2["dispatch_evidence"]["tuples"]:
            row["broker_root"] = str(stopped_root)
        for node in route2["nodes"]:
            for hop in node.get("dispatch_fallback", []):
                for candidate in hop.get("candidates", []):
                    candidate["broker_root"] = str(stopped_root)
        route2["route_hash"] = ROUTE.route_hash(route2)
        route2["route_id"] = "rt-" + route2["route_hash"].split(":", 1)[1][:16]
        stopped_path = self.base / "route-stopped-broker.json"
        stopped_path.write_text(json.dumps(route2), encoding="utf-8")

        result2 = self.chain("codex", "claude", broker_root=stopped_root, route_path=stopped_path)
        self.assertEqual(result2.returncode, 76, result2.stdout + result2.stderr)
        self.assertIn("reason=broker-unavailable", result2.stdout)
        self.assertIn("child_spawned=0", result2.stdout)
        self.assertFalse(self.jobs.exists())

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
        # v1-locked (§1.6b analog): explicit --broker-root override against a
        # missing root is v1's "broker-unavailable" path. Under v2 default,
        # an explicit override that disagrees with the route's own
        # broker_root is a distinct broker-root-mismatch case (fixture 4/10).
        missing = self.base / "missing-broker"
        route_path = self.route_v1("codex", "claude")
        result = self.chain("codex", "claude", broker_root=missing, route_path=route_path)
        self.assertEqual(result.returncode, 76, result.stdout + result.stderr)
        self.assertIn("reason=broker-unavailable", result.stdout)
        self.assertIn("child_spawned=0", result.stdout)
        self.assertFalse(self.jobs.exists())

    def test_tampered_inherited_instance_fails_closed(self):
        # ★ v1-locked (§1.6b / plan-check M1): once SD-55 lands, v2 hop
        # deliberately ignores AGENT_DISPATCH_BROKER_INSTANCE (§2.3) --
        # locking this test to a v1 record keeps it testing v1's env-trust
        # contract instead of silently degrading into a false pass.
        route_path = self.route_v1("codex", "claude")
        result = self.chain("codex", "claude", instance="brk-tampered", route_path=route_path)
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
            "broker_instance": self.meta["broker_instance"],
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
