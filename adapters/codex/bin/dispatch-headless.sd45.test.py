#!/usr/bin/env python3
import argparse,importlib.util,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[3]
S=importlib.util.spec_from_file_location("route",ROOT/"utilities/capability-route.py"); R=importlib.util.module_from_spec(S); S.loader.exec_module(R)
WH_S=importlib.util.spec_from_file_location("codex_dispatch_headless",Path(__file__).with_name("dispatch-headless.py")); WH=importlib.util.module_from_spec(WH_S); WH_S.loader.exec_module(WH)


def probe_args(**overrides):
    base = dict(
        depth=2, action="start", nested_eligibility="unknown", eligibility_source="",
        eligibility_failure_class="", parent_harness="claude", parent_transport="headless",
        parent_sandbox="default", launch_authority="conductor", worktree="/tmp/fixture-worktree",
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def fake_probe_result(**row):
    return mock.Mock(stdout=json.dumps(row), returncode=0 if row.get("status") == "supported" else 69)


class CodexSD45InternalProbe(unittest.TestCase):
    def test_absent_evidence_binds_supported_and_marks_internal(self):
        args = probe_args()
        row = dict(parent_harness="claude", parent_transport="headless", parent_sandbox="default",
                   child_harness="codex", launch_authority="conductor", status="supported",
                   probe_source="direct-auth+headless-check", failure_class="")
        with mock.patch.object(WH.subprocess, "run", return_value=fake_probe_result(**row)) as run:
            WH.bind_internal_eligibility_probe(args)
        run.assert_called_once()
        self.assertIn("--child-harness", run.call_args.args[0])
        self.assertEqual(args.nested_eligibility, "supported")
        self.assertEqual(args.eligibility_source, "direct-auth+headless-check")
        self.assertEqual(args.eligibility_probe, "internal")
        WH.validate_nested_eligibility(
            depth=args.depth, action=args.action, parent_harness=args.parent_harness,
            parent_transport=args.parent_transport, parent_sandbox=args.parent_sandbox,
            child_harness="codex", launch_authority=args.launch_authority,
            status=args.nested_eligibility, source=args.eligibility_source,
        )  # must not raise

    def test_unsupported_probe_result_fails_closed_with_no_launch(self):
        args = probe_args()
        row = dict(parent_harness="claude", parent_transport="headless", parent_sandbox="default",
                   child_harness="codex", launch_authority="conductor", status="unsupported",
                   probe_source="direct-headless-check", failure_class="exit-1")
        with mock.patch.object(WH.subprocess, "run", return_value=fake_probe_result(**row)):
            WH.bind_internal_eligibility_probe(args)
        self.assertEqual(args.nested_eligibility, "unsupported")
        self.assertEqual(args.eligibility_probe, "internal")
        with self.assertRaises(WH.DispatchContractError) as ctx:
            WH.validate_nested_eligibility(
                depth=args.depth, action=args.action, parent_harness=args.parent_harness,
                parent_transport=args.parent_transport, parent_sandbox=args.parent_sandbox,
                child_harness="codex", launch_authority=args.launch_authority,
                status=args.nested_eligibility, source=args.eligibility_source,
            )
        self.assertEqual(ctx.exception.reason, "nested-child-spawn-unsupported")

    def test_explicit_evidence_skips_internal_probe(self):
        args = probe_args(nested_eligibility="unsupported", eligibility_source="caller-supplied")
        args.eligibility_probe = "-"
        with mock.patch.object(WH.subprocess, "run") as run:
            WH.bind_internal_eligibility_probe(args)
        run.assert_not_called()
        self.assertEqual(args.eligibility_probe, "-")
        self.assertEqual(args.nested_eligibility, "unsupported")

    def test_unknown_parent_identity_skips_probe_and_stays_fail_closed(self):
        args = probe_args(parent_sandbox="unknown")
        args.eligibility_probe = "-"
        with mock.patch.object(WH.subprocess, "run") as run:
            WH.bind_internal_eligibility_probe(args)
        run.assert_not_called()
        self.assertEqual(args.eligibility_probe, "-")
        self.assertEqual(args.nested_eligibility, "unknown")

    def test_malformed_json_leaves_unknown_and_fails_closed(self):
        args = probe_args()
        with mock.patch.object(WH.subprocess, "run", return_value=mock.Mock(stdout="not json", returncode=1)):
            WH.bind_internal_eligibility_probe(args)
        self.assertEqual(args.nested_eligibility, "unknown")
        self.assertEqual(args.eligibility_probe, "internal")

    def test_identity_mismatched_probe_row_leaves_unknown_and_fails_closed(self):
        args = probe_args()
        row = dict(parent_harness="opencode", parent_transport="headless", parent_sandbox="default",
                   child_harness="codex", launch_authority="conductor", status="supported",
                   probe_source="direct-auth+headless-check", failure_class="")
        with mock.patch.object(WH.subprocess, "run", return_value=fake_probe_result(**row)):
            WH.bind_internal_eligibility_probe(args)
        self.assertEqual(args.nested_eligibility, "unknown")
        self.assertEqual(args.eligibility_probe, "internal")

    def test_depth1_never_probes(self):
        args = probe_args(depth=1)
        with mock.patch.object(WH.subprocess, "run") as run:
            WH.bind_internal_eligibility_probe(args)
        run.assert_not_called()

    def test_register_action_never_probes(self):
        args = probe_args(action="register")
        with mock.patch.object(WH.subprocess, "run") as run:
            WH.bind_internal_eligibility_probe(args)
        run.assert_not_called()


class CodexSandboxMountShape(unittest.TestCase):
    def args(self, transport):
        return argparse.Namespace(
            sandbox="workspace-write",
            launch_lifecycle="foreground-scoped",
            depth=2,
            parent_harness="codex",
            parent_transport=transport,
            parent_sandbox="workspace-write",
        )

    def test_tracked_file_shape_fails_before_sandbox_launch(self):
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.dict(os.environ, {"AGENT_DISPATCH_CHILD": "1"}):
            worktree = Path(tmp)
            target = worktree / ".codex"
            target.write_text("")
            invalid = WH.invalid_codex_mount_target(
                self.args("codex-exec-headless"), worktree
            )
        self.assertEqual(invalid, target)

    def test_canonical_nested_headless_disables_inner_mount_sandbox(self):
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.dict(os.environ, {"AGENT_DISPATCH_CHILD": "1"}):
            worktree = Path(tmp)
            (worktree / ".codex").write_text("")
            args = self.args("headless")
            self.assertEqual(WH.effective_runtime_sandbox(args), "danger-full-access")
            self.assertIsNone(WH.invalid_codex_mount_target(args, worktree))

    def test_directory_shape_is_valid_with_workspace_sandbox(self):
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.dict(os.environ, {"AGENT_DISPATCH_CHILD": "1"}):
            worktree = Path(tmp)
            (worktree / ".codex").mkdir()
            self.assertIsNone(
                WH.invalid_codex_mount_target(
                    self.args("codex-exec-headless"), worktree
                )
            )

    def test_dry_run_rejects_file_before_registry_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            worktree = base / "repo"
            worktree.mkdir()
            subprocess.run(["git", "init", "-q", str(worktree)], check=True)
            (worktree / ".codex").write_text("")
            jobs = base / "jobs.log"
            result = subprocess.run(
                [
                    sys.executable, str(ROOT / "adapters/codex/bin/dispatch-headless.py"),
                    "--dry-run", "--worktree", str(worktree), "--slug", "mount-shape",
                    "--capability", "autopilot-code", "--mode", "debug",
                    "--model", "gpt-test", "--reasoning", "low",
                    "--jobs", str(jobs),
                ],
                text=True,
                capture_output=True,
                env={**os.environ, "AGENT_HOME": str(ROOT)},
            )
            self.assertEqual(result.returncode, 65, result.stdout + result.stderr)
            output = result.stdout + result.stderr
            self.assertIn("invalid-worktree-codex-mount-target", output)
            self.assertIn("child_spawned=0", output)
            self.assertFalse(jobs.exists())


class CodexSD45(unittest.TestCase):
 def test_route_consumer_and_scope_refusal(self):
  with tempfile.TemporaryDirectory() as td:
   base=Path(td); repo=base/"repo"; repo.mkdir(); subprocess.run(["git","init","-q",str(repo)],check=True); subprocess.run(["git","-C",str(repo),"config","user.email","fixture@example.com"],check=True); subprocess.run(["git","-C",str(repo),"config","user.name","Fixture"],check=True); (repo/"x").write_text("x"); subprocess.run(["git","-C",str(repo),"add","x"],check=True); subprocess.run(["git","-C",str(repo),"commit","-qm","init"],check=True)
   art=base/".agent_reports"; art.mkdir(); gate={"spec_read":{"satisfied":True,"source":"codex-fixture"},"drift_verdict":"within-spec","workflow_mode":"tracked","artifact_guard":{"satisfied":True,"source":"codex-fixture"}}
   dispatch={"tuples":[{"parent_harness":"codex","parent_transport":"headless","parent_sandbox":"fixture","child_harness":"codex","launch_authority":"conductor","status":"supported","probe_source":"codex-fixture","probe_time":"2026-07-16T00:00:00Z","failure_class":""}],"native_subagent":[]}; route=R.compile_route("autopilot-code","dev","strong",repo,art,signals=["shared-contract"],transport="headless",tracking="tracked",tracked_gate_evidence=gate,dispatch_evidence=dispatch); path=base/"route.json"; path.write_text(json.dumps(route)); node=next(x for x in route["nodes"] if x["id"]=="execute"); jobs=base/"jobs.log"; logs=base/"logs"
   args=[sys.executable,str(ROOT/"adapters/codex/bin/dispatch-headless.py"),"--register","--worktree",str(repo),"--slug","codex-sd45","--capability","autopilot-code","--mode","dev/backend","--qa","standard","--intensity","strong","--depth","2","--parent","owner","--route-file",str(path),"--route-id",route["route_id"],"--route-hash",route["route_hash"],"--route-node","execute","--registry-digest",route["registry_digest"],"--write-scope",";".join(node["write_scope"]),"--completion-gate",node["completion_gate"],"--model","gpt-test","--reasoning","low","--jobs",str(jobs),"--log-dir",str(logs)]
   env={**os.environ,"AGENT_HOME":str(ROOT),"AGENT_ARTIFACT_ROOT":str(art)}; ok=subprocess.run(args,text=True,capture_output=True,env=env); self.assertEqual(ok.returncode,0,ok.stderr); prompt=(logs/"codex-sd45.codex.prompt.txt").read_text(); self.assertIn("consume the assigned route only",prompt); self.assertNotIn("preflight.sh route autopilot-code",prompt)
   bad=args.copy(); bad[bad.index(";".join(node["write_scope"]))]="spec/**"; denied=subprocess.run(bad,text=True,capture_output=True,env=env); self.assertEqual(denied.returncode,65); self.assertIn("route-node-scope-mismatch",denied.stderr)
   legacy=[sys.executable,str(ROOT/"adapters/codex/bin/dispatch-headless.py"),"--dry-run","--worktree",str(repo),"--slug","codex-legacy-scope","--capability","autopilot-code","--mode","dev/backend","--qa","standard","--write-scope","source/**","--model","gpt-test","--reasoning","low"]
   compatible=subprocess.run(legacy,text=True,capture_output=True,env=env); self.assertEqual(compatible.returncode,0,compatible.stderr); self.assertIn("status=dry-run",compatible.stdout)


def _prompt_args(**overrides):
    base = dict(
        worker_type="owner", intensity="strong", worktree="/tmp/fixture-worktree",
        route_id=None, route_node=None, attempt_id=None, route_file=None,
        worker_role=None, profile=None, capability="autopilot-code", mode="dev",
        qa="thorough", depth=1, parent_slug=None, parent_session_id=None,
        capability_owner=None, owner_harness=None, write_scope=None,
        agent_home=Path("/tmp/fixture-agent-home"), artifact_root="/tmp/fixture-artifacts",
    )
    base.update(overrides)
    return argparse.Namespace(**base)


class CodexSD71SyncWaitClause(unittest.TestCase):
    """SD-71: the standard top-of-prompt clause (core/OPERATIONS.md §5.10) is an
    auxiliary layer only — Codex gets no --disallowedTools equivalent (parity
    honesty: Codex's fatal-async policy differs and is out of this cycle's
    proven scope), but the owner prompt clause itself is harness-neutral."""

    def test_owner_prompt_carries_standard_synchronous_wait_clause(self):
        args = _prompt_args()
        with mock.patch.object(WH, "task_prompt", return_value=("do the thing", "cli")):
            prompt, _source = WH.dispatch_prompt(args)
        self.assertTrue(prompt.startswith(
            "No asynchronous Monitor/wakeup/scheduling waits; poll synchronously with"))
        self.assertIn("dispatch-wait.sh", prompt)
        self.assertIn("auxiliary layer only", prompt)

    def test_stage_prompt_never_carries_the_clause(self):
        args = _prompt_args(worker_type=None, intensity="strong", depth=2,
                            route_id="rt-fixture", route_node="execute", attempt_id="att-fixture",
                            worker_role="code-execute")
        with mock.patch.object(WH, "task_prompt", return_value=("do the thing", "cli")):
            prompt, _source = WH.dispatch_prompt(args)
        self.assertNotIn("No asynchronous Monitor/wakeup/scheduling waits", prompt)

    def test_owner_direct_intensity_never_carries_the_clause(self):
        args = _prompt_args(intensity="direct")
        with mock.patch.object(WH, "task_prompt", return_value=("do the thing", "cli")):
            prompt, _source = WH.dispatch_prompt(args)
        self.assertNotIn("No asynchronous Monitor/wakeup/scheduling waits", prompt)


if __name__=="__main__": unittest.main()
