#!/usr/bin/env python3

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "hooks" / "material-route-guard.py"
ROUTER = ROOT / "utilities" / "capability-route.py"
PREDICATES = (
    "atomic-outcome",
    "known-scope",
    "no-shared-contract",
    "no-resource-run",
    "no-artifact-handoff",
    "no-independent-verifier",
    "focused-verification",
)


class MaterialRouteGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "project"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Test"], check=True)
        (self.repo / "app.py").write_text("print('one')\n", encoding="utf-8")
        (self.repo / "README.md").write_text("one\n", encoding="utf-8")
        (self.repo / "settings.json").write_text("{}\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "initial"], check=True)
        self.artifacts = self.base / "artifacts"
        self.artifacts.mkdir()
        self.route = self.artifacts / "route.json"
        self.home = self.base / "agent-home"
        (self.home / "core").mkdir(parents=True)
        (self.home / "core" / "CORE.md").write_text("core\n", encoding="utf-8")
        (self.home / "utilities").symlink_to(ROOT / "utilities", target_is_directory=True)
        command = [
            sys.executable, str(ROUTER), "compile",
            "--capability", "autopilot-code",
            "--capability-mode", "dev",
            "--intensity", "direct",
            "--cwd", str(self.repo),
            "--artifact-root", str(self.artifacts),
        ]
        for predicate in PREDICATES:
            command += ["--predicate", predicate]
        command += [
            "--transport", "interactive",
            "--inline-reason", "atomic-direct",
            "--tracking", "untracked",
            "--spec-read", "not-applicable",
            "--drift-verdict", "no-project-spec",
            "--workflow-mode", "untracked",
            "--artifact-guard", "preflight-passed",
            "--output", str(self.route),
        ]
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.route_id = json.loads(self.route.read_text())["route_id"]

    def guard(self, *args: str, session: str = "session-a", env: dict[str, str] | None = None):
        return subprocess.run(
            [
                sys.executable, str(GUARD), "--agent-home", str(self.home),
                "check", *args, "--cwd", str(self.repo), "--session", session,
            ],
            text=True,
            capture_output=True,
            env={**os.environ, **(env or {})},
        )

    def bind(self, session: str = "session-a") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable, str(GUARD), "--agent-home", str(self.home),
                "bind", "--route", str(self.route), "--cwd", str(self.repo),
                "--session", session,
            ],
            text=True,
            capture_output=True,
        )

    def reset(self) -> None:
        subprocess.run(["git", "-C", str(self.repo), "reset", "--hard", "-q", "HEAD"], check=True)

    def test_source_edit_denies_silent_no_route_and_accepts_bound_route(self) -> None:
        denied = self.guard("--tool", "Edit", "--file", str(self.repo / "app.py"))
        self.assertEqual(denied.returncode, 2)
        self.assertIn("silent no-route", denied.stderr)
        self.assertEqual(self.bind().returncode, 0)
        allowed = self.guard("--tool", "Edit", "--file", str(self.repo / "app.py"))
        self.assertEqual(allowed.returncode, 0, allowed.stderr)

    def test_docs_config_scratch_and_foreign_session_behavior(self) -> None:
        config_script = self.repo / "config" / "bootstrap.sh"
        config_script.parent.mkdir()
        config_script.write_text("true\n", encoding="utf-8")
        for path in (
            self.repo / "README.md",
            self.repo / "settings.json",
            config_script,
            self.base / "scratch.py",
        ):
            result = self.guard("--tool", "Write", "--file", str(path))
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.bind("session-a").returncode, 0)
        denied = self.guard(
            "--tool", "Edit", "--file", str(self.repo / "app.py"), session="session-b"
        )
        self.assertEqual(denied.returncode, 2)

    def test_stale_source_commit_and_tampered_record_are_denied(self) -> None:
        self.assertEqual(self.bind().returncode, 0)
        subprocess.run(["git", "-C", str(self.repo), "commit", "--allow-empty", "-qm", "advance"], check=True)
        stale = self.guard("--tool", "Edit", "--file", str(self.repo / "app.py"))
        self.assertEqual(stale.returncode, 2)
        self.assertIn("route-source-commit-stale", stale.stderr)
        subprocess.run(["git", "-C", str(self.repo), "reset", "--hard", "-q", "HEAD^"], check=True)
        value = json.loads(self.route.read_text())
        value["route_id"] = "rt-tampered"
        self.route.write_text(json.dumps(value), encoding="utf-8")
        tampered = self.guard("--tool", "Edit", "--file", str(self.repo / "app.py"))
        self.assertEqual(tampered.returncode, 2)
        self.assertIn("route-record-verification-failed", tampered.stderr)

    def test_route_symlink_is_not_accepted_as_authority(self) -> None:
        linked_route = self.artifacts / "linked-route.json"
        linked_route.symlink_to(self.route)
        result = subprocess.run(
            [
                sys.executable, str(GUARD), "--agent-home", str(self.home),
                "bind", "--route", str(linked_route), "--cwd", str(self.repo),
                "--session", "linked-route-session",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("route-file-unsafe", result.stderr)

    def test_worker_route_environment_is_valid_without_session_marker(self) -> None:
        allowed = self.guard(
            "--tool", "Edit", "--file", str(self.repo / "app.py"),
            session="worker-session",
            env={
                "AGENT_ROUTE_FILE": str(self.route),
                "AGENT_ROUTE_ID": self.route_id,
                "AGENT_ROUTE_NODE": "inline",
            },
        )
        self.assertEqual(allowed.returncode, 0, allowed.stderr)

    def test_commit_chokepoint_source_docs_rename_and_all(self) -> None:
        (self.repo / "app.py").write_text("print('two')\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "app.py"], check=True)
        denied = self.guard("--tool", "Bash", "--command", "git commit -m source")
        self.assertEqual(denied.returncode, 2)
        self.assertEqual(self.bind().returncode, 0)
        self.assertEqual(
            self.guard("--tool", "Bash", "--command", "git commit -m source").returncode,
            0,
        )

        self.reset()
        (self.repo / "README.md").write_text("two\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "README.md"], check=True)
        self.assertEqual(
            self.guard("--tool", "Bash", "--command", "git commit -m docs", session="fresh").returncode,
            0,
        )

        self.reset()
        subprocess.run(["git", "-C", str(self.repo), "mv", "app.py", "renamed.py"], check=True)
        self.assertEqual(
            self.guard("--tool", "Bash", "--command", "git commit -m rename", session="fresh").returncode,
            0,
        )

        self.reset()
        (self.repo / "app.py").write_text("print('three')\n", encoding="utf-8")
        denied_all = self.guard(
            "--tool", "Bash", "--command", "git commit -am tracked", session="fresh"
        )
        self.assertEqual(denied_all.returncode, 2)
        nested = self.guard(
            "--tool", "Bash", "--command", "bash -c 'git commit -am nested'", session="fresh"
        )
        self.assertEqual(nested.returncode, 2)

        self.reset()
        (self.repo / "app.py").write_text("print('staged elsewhere')\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "app.py"], check=True)
        (self.repo / "README.md").write_text("docs only target\n", encoding="utf-8")
        only_docs = self.guard(
            "--tool", "Bash", "--command", "git commit --only=README.md -m docs",
            session="fresh",
        )
        self.assertEqual(only_docs.returncode, 0, only_docs.stderr)

        only_source = self.guard(
            "--tool", "Bash", "--command", "git commit --only=app.py -m source",
            session="fresh",
        )
        self.assertEqual(only_source.returncode, 2)

    def test_new_source_file_in_repo_is_material(self) -> None:
        denied = self.guard(
            "--tool", "Write", "--file", str(self.repo / "new" / "feature.py")
        )
        self.assertEqual(denied.returncode, 2)

    def test_posttool_compile_binds_and_session_end_clears(self) -> None:
        spoof_payload = {
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {
                "command": f"echo {ROUTER} compile --output {self.route}"
            },
            "cwd": str(self.repo),
            "session_id": "spoof-session",
        }
        subprocess.run(
            [sys.executable, str(GUARD)], input=json.dumps(spoof_payload), text=True,
            capture_output=True, env={**os.environ, "AGENT_HOME": str(self.home)}, check=True,
        )
        spoofed = self.guard(
            "--tool", "Edit", "--file", str(self.repo / "app.py"), session="spoof-session"
        )
        self.assertEqual(spoofed.returncode, 2)

        command = f"python3 {ROUTER} compile --output {self.route}"
        payload = {
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": str(self.repo),
            "session_id": "hook-session",
        }
        result = subprocess.run(
            [sys.executable, str(GUARD)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env={**os.environ, "AGENT_HOME": str(self.home)},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        allowed = self.guard(
            "--tool", "Edit", "--file", str(self.repo / "app.py"), session="hook-session"
        )
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        end_payload = {"hook_event_name": "SessionEnd", "session_id": "hook-session"}
        subprocess.run(
            [sys.executable, str(GUARD)], input=json.dumps(end_payload), text=True,
            capture_output=True, env={**os.environ, "AGENT_HOME": str(self.home)}, check=True,
        )
        denied = self.guard(
            "--tool", "Edit", "--file", str(self.repo / "app.py"), session="hook-session"
        )
        self.assertEqual(denied.returncode, 2)

    def test_claude_hook_protocol_and_source_registration(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": str(self.repo / "app.py")},
            "cwd": str(self.repo),
            "session_id": "unbound-hook-session",
        }
        denied = subprocess.run(
            [sys.executable, str(GUARD)], input=json.dumps(payload), text=True,
            capture_output=True, env={**os.environ, "AGENT_HOME": str(self.home)},
        )
        self.assertEqual(denied.returncode, 0, denied.stderr)
        decision = json.loads(denied.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("silent no-route", decision["permissionDecisionReason"])

        notebook_payload = {
            **payload,
            "tool_name": "NotebookEdit",
            "tool_input": {"notebook_path": str(self.repo / "analysis.ipynb")},
        }
        notebook_denied = subprocess.run(
            [sys.executable, str(GUARD)], input=json.dumps(notebook_payload), text=True,
            capture_output=True, env={**os.environ, "AGENT_HOME": str(self.home)},
        )
        self.assertEqual(notebook_denied.returncode, 0, notebook_denied.stderr)
        self.assertEqual(
            json.loads(notebook_denied.stdout)["hookSpecificOutput"]["permissionDecision"],
            "deny",
        )

        settings = json.loads((ROOT / "adapters" / "claude" / "settings.json").read_text())
        expected = {
            "PreToolUse": {"Edit|Write|MultiEdit|NotebookEdit", "Bash"},
            "PostToolUse": {"Bash"},
            "SessionEnd": {"*"},
        }
        for event, matchers in expected.items():
            observed = {
                group.get("matcher")
                for group in settings["hooks"][event]
                if any(
                    "material-route-guard.py" in hook.get("command", "")
                    for hook in group.get("hooks", [])
                )
            }
            self.assertEqual(observed, matchers)
        projection = ROOT / "adapters" / "claude" / "hooks" / "material-route-guard.py"
        self.assertTrue(projection.is_symlink())
        self.assertEqual(projection.resolve(), GUARD.resolve())


if __name__ == "__main__":
    unittest.main()
