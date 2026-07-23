#!/usr/bin/env python3

import os
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTERS = {
    "codex": (
        ROOT / "adapters/codex/bin/dispatch-headless.py",
        ["--model", "gpt-test", "--reasoning", "low"],
        "codex.prompt.txt",
    ),
    "claude": (
        ROOT / "adapters/claude/bin/dispatch-headless.py",
        ["--model", "claude-test", "--effort", "low"],
        "claude.prompt.txt",
    ),
    "opencode": (
        ROOT / "adapters/opencode/bin/dispatch-headless.py",
        ["--model", "provider/test", "--variant", "low"],
        "opencode.prompt.txt",
    ),
}


class WorkerDispatchPromptTest(unittest.TestCase):
    def setUp(self):
        self.parents = []

    def tearDown(self):
        for proc in self.parents:
            if proc.poll() is None:
                proc.kill()
            proc.wait()

    def test_custom_assignment_is_wrapped_for_every_adapter(self):
        for harness, (wrapper, model, suffix) in ADAPTERS.items():
            with self.subTest(harness=harness), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo = root / "repo"
                repo.mkdir()
                subprocess.run(["git", "init", "-q", str(repo)], check=True)
                subprocess.run(
                    ["git", "-C", str(repo), "config", "user.email", "fixture@example.com"],
                    check=True,
                )
                subprocess.run(
                    ["git", "-C", str(repo), "config", "user.name", "Fixture"],
                    check=True,
                )
                (repo / "x").write_text("x", encoding="utf-8")
                subprocess.run(["git", "-C", str(repo), "add", "x"], check=True)
                subprocess.run(["git", "-C", str(repo), "commit", "-qm", "init"], check=True)
                artifact_root = root / ".agent_reports"
                artifact_root.mkdir()
                logs = root / "logs"
                jobs = root / "jobs.log"
                if harness in {"codex", "claude"}:
                    parent = subprocess.Popen(["sleep", "60"])
                    self.parents.append(parent)
                    start = (Path("/proc") / str(parent.pid) / "stat").read_text().split()[21]
                    jobs.write_text(
                        f"2026-07-23T00:00:00Z\topen\t{repo}\t{repo}\towner\t"
                        "attempt_schema_version=2,dispatch_depth=1,transport=headless,"
                        "execution_surface=registered-headless,registered_worker=1,"
                        "fallback_hop=same-harness-headless,worker_type=owner,"
                        f"attempt_id=att-prompt-parent,pid={parent.pid},pid_start={start}\n"
                    )
                slug = f"{harness}-typed"
                command = [
                    sys.executable,
                    str(wrapper),
                    "--register",
                    "--worktree",
                    str(repo),
                    "--slug",
                    slug,
                    "--capability",
                    "autopilot-code",
                    "--mode",
                    "dev/backend",
                    "--intensity",
                    "standard",
                    "--dispatch-depth",
                    "2",
                    "--parent",
                    "owner",
                    "--worker-type",
                    "stage",
                    "--assigned-contract",
                    "code-test",
                    "--prompt-text",
                    "CUSTOM ASSIGNMENT",
                    "--jobs",
                    str(jobs),
                    "--log-dir",
                    str(logs),
                    *model,
                ]
                env = {
                    **os.environ,
                    "AGENT_HOME": str(ROOT),
                    "AGENT_ARTIFACT_ROOT": str(artifact_root),
                    "OPENCODE_CONFIG_CONTENT": "{}",
                }
                env.pop("AGENT_DISPATCH_JOBS", None)
                if harness in {"codex", "claude"}:
                    env["AGENT_DISPATCH_ATTEMPT_ID"] = "att-prompt-parent"
                result = subprocess.run(command, text=True, capture_output=True, env=env)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                prompt = (logs / f"{slug}.{suffix}").read_text(encoding="utf-8")
                self.assertEqual(prompt.count("# Portable Worker Kernel"), 1)
                self.assertEqual(prompt.count("# Worker Type:"), 1)
                self.assertIn("# Worker Type: Stage", prompt)
                self.assertIn("- assigned_contract: code-test", prompt)
                self.assertNotIn("- worker_role:", prompt)
                self.assertIn("CUSTOM ASSIGNMENT", prompt)
                self.assertIn("artifact: <canonical path | ->", prompt)
                self.assertIn("verdict: PASS | FAIL | BLOCKED", prompt)
                self.assertIn("blocker: none | <one line>", prompt)
                self.assertNotIn("Read $AGENT_HOME/adapters/codex/AGENTS.md first", prompt)
                self.assertNotIn("Return a concise report with changed files", prompt)

    def test_route_bound_stage_prompts_name_deterministic_heartbeat_consumer(self):
        for harness, (wrapper, model, _suffix) in ADAPTERS.items():
            with self.subTest(harness=harness):
                spec=importlib.util.spec_from_file_location(f"dispatch_{harness}",wrapper)
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                args=module.parser().parse_args([
                    "--worktree","/work/repo","--slug","stage","--capability","code-test",
                    "--mode","dev/backend","--intensity","standard","--dispatch-depth","2",
                    "--parent","owner","--worker-type","stage",
                    "--assigned-contract","code-test","--prompt-text","TASK",*model,
                ])
                args.attempt_id="att-promptheartbeat01";args.route_id="rt-prompt";args.route_node="test"
                args.artifact_root="/artifacts"
                render=module.prompt if harness=="opencode" else module.dispatch_prompt
                prompt,_=render(args)
                self.assertIn("Stage progress contract (SD-58)",prompt)
                self.assertIn("att-promptheartbeat01",prompt)
                self.assertIn("rt-prompt",prompt)
                self.assertIn("--phase analysis",prompt)
                self.assertIn("unchanged phase/evidence pair is not progress",prompt)
                heartbeat_path=(
                    ROOT/"utilities/dispatch-progress.py"
                    if harness=="claude"
                    else ROOT/f"adapters/{harness}/bin/preflight.sh"
                )
                self.assertIn(str(heartbeat_path),prompt)


if __name__ == "__main__":
    unittest.main()
