#!/usr/bin/env python3
"""Regression tests for Codex registered-child parent parking."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "adapters" / "codex" / "hooks" / "pretooluse-write-guard.py"
SESSION = "019f89fa-fixture-parent"
ATTEMPT = "att-fixture-child"
OWNER_ATTEMPT = "att-fixture-owner"
OWNER_SLUG = "owner"


class ParentParkGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.jobs = self.base / "jobs.log"
        self.route_id = "rt-parent-park-fixture"
        self.route = self.base / "route.json"
        self.route.write_text(
            json.dumps(
                {
                    "route_id": self.route_id,
                    "nodes": [
                        {"id": "owner", "dispatch_depth": 1},
                        {"id": "implement", "dispatch_depth": 2},
                        {"id": "test", "dispatch_depth": 2},
                        {
                            "id": "plan-a",
                            "dispatch_depth": 2,
                            "replica_group": "plan",
                        },
                        {
                            "id": "plan-b",
                            "dispatch_depth": 2,
                            "replica_group": "plan",
                        },
                        {
                            "id": "other-a",
                            "dispatch_depth": 2,
                            "replica_group": "other",
                        },
                        {
                            "id": "other-b",
                            "dispatch_depth": 2,
                            "replica_group": "other",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.foreign_route = self.base / "foreign-route.json"
        self.foreign_route.write_text(
            json.dumps({"route_id": "rt-foreign", "nodes": []}),
            encoding="utf-8",
        )
        self.write_row("open", ATTEMPT, parent_sid=SESSION)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_row(
        self,
        state: str,
        attempt: str,
        *,
        parent_sid: str = "",
        parent_attempt_id: str = "",
        append: bool = False,
        process_metadata: dict[str, str] | None = None,
        route_node: str = "",
        replica_group: str = "",
    ) -> None:
        metadata = [
            "attempt_schema_version=2",
            "dispatch_depth=1",
            "transport=headless",
            "execution_surface=registered-headless",
            "registered_worker=1",
            "attempt_id=" + attempt,
        ]
        if parent_sid:
            metadata.append("parent_sid=" + parent_sid)
        if parent_attempt_id:
            metadata.append("parent_attempt_id=" + parent_attempt_id)
        if route_node:
            metadata.extend(
                [
                    "route_id=" + self.route_id,
                    "route_file=" + str(self.route),
                    "route_node=" + route_node,
                ]
            )
        if replica_group:
            metadata.extend(
                [
                    "replica_group=" + replica_group,
                    "reservation_kind=replica-batch",
                    "batch_declared_size=2",
                    "batch_group=" + replica_group,
                    "batch_route_id=" + self.route_id,
                    "batch_parent_attempt_id=" + parent_attempt_id,
                    "batch_attempt_id=" + attempt,
                    "batch_route_node=" + route_node,
                ]
            )
        if state == "done" and not process_metadata:
            metadata.append("launch_outcome=never-launched")
        metadata.extend(
            f"{key}={value}" for key, value in (process_metadata or {}).items()
        )
        row = "\t".join(
            ["2026-07-23T00:00:00Z", state, "/repo", "/repo-wt/child", "child", ",".join(metadata)]
        ) + "\n"
        if append:
            with self.jobs.open("a", encoding="utf-8") as handle:
                handle.write(row)
        else:
            self.jobs.write_text(row, encoding="utf-8")

    def invoke(
        self,
        name: str,
        command: str | None = None,
        *,
        session: str = SESSION,
        extra_env: dict[str, str] | None = None,
    ) -> dict[str, str] | None:
        payload: dict[str, object] = {
            "tool_name": name,
            "tool_input": {},
            "session_id": session,
            "cwd": str(ROOT),
        }
        if command is not None:
            payload["tool_input"] = {"command": command}
        env = {**os.environ, "AGENT_DISPATCH_JOBS": str(self.jobs), "AGENT_HOME": str(ROOT)}
        env.pop("AGENT_DISPATCH_ATTEMPT_ID", None)
        env.pop("AGENT_PARENT_PARK_BYPASS", None)
        if extra_env:
            env.update(extra_env)
        result = subprocess.run(
            ["python3", str(GUARD)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout else None

    def assert_parked(self, name: str, command: str | None = None, **kwargs: object) -> None:
        output = self.invoke(name, command, **kwargs)
        self.assertIsNotNone(output)
        self.assertEqual(output["decision"], "block")
        self.assertIn("parent-parked", output["reason"])
        self.assertIn(ATTEMPT, output["reason"])

    def test_actual_adjacent_session_activity_is_blocked(self) -> None:
        # Reduced forms of every waste class observed in the stopped adjacent
        # Codex parent: raw transcript reads, extraction, source search,
        # artifact census, git inspection, and redundant liveness calls.
        offender_commands = (
            "tail -n 120 /tmp/child.codex.jsonl",
            "python3 -c 'import json' /tmp/child.codex.jsonl",
            "rg -n parent-attempt-not-live adapters utilities",
            "find .agent_reports -maxdepth 4 -type f",
            "git status --short --branch",
            "git diff --stat",
            "adapters/codex/bin/preflight.sh liveness",
            "sed -n '1,200p' /tmp/child.codex.jsonl",
        )
        for command in offender_commands:
            with self.subTest(command=command):
                self.assert_parked("Bash", command)
        self.assert_parked("Read")
        self.assert_parked("update_plan")

    def test_only_exact_long_wait_and_typed_harvest_are_allowed(self) -> None:
        self.assertIsNone(
            self.invoke("Bash", f"utilities/dispatch-wait.sh --attempt-id {ATTEMPT} --max 600")
        )
        self.assertIsNone(
            self.invoke(
                "Bash",
                f"adapters/codex/bin/preflight.sh harvest --attempt-id {ATTEMPT} --status open",
            )
        )
        self.assertIsNone(self.invoke("functions.write_stdin"))
        self.assertIsNone(self.invoke("wait"))
        self.assert_parked("Bash", f"utilities/dispatch-wait.sh --attempt-id {ATTEMPT} --max 40")
        self.assert_parked("Bash", "utilities/dispatch-wait.sh --attempt-id att-other --max 600")
        self.assert_parked(
            "Bash",
            f"utilities/dispatch-wait.sh --attempt-id {ATTEMPT} --max 600; git status",
        )
        self.assert_parked(
            "Bash",
            f"adapters/codex/bin/preflight.sh harvest --attempt-id {ATTEMPT} --status done",
        )

    def test_foreign_and_terminal_rows_do_not_park(self) -> None:
        self.assertIsNone(self.invoke("Bash", "git status --short", session="different-session"))
        self.write_row("done", ATTEMPT, parent_sid=SESSION, append=True)
        self.assertIsNone(self.invoke("Bash", "git status --short"))

    def test_terminal_row_still_parks_until_exact_process_is_reaped(self) -> None:
        proc = subprocess.Popen(["sleep", "30"], start_new_session=True)
        try:
            raw = Path(f"/proc/{proc.pid}/stat").read_text(encoding="utf-8")
            start = raw[raw.rfind(")") + 2 :].split()[19]
            self.write_row(
                "done",
                ATTEMPT,
                parent_sid=SESSION,
                append=True,
                process_metadata={
                    "pid": str(proc.pid),
                    "pid_start": start,
                    "pgid": str(proc.pid),
                    "pid_observer_ns": os.readlink("/proc/self/ns/pid"),
                },
            )
            self.assert_parked("Bash", "git status --short")
            proc.terminate()
            proc.wait(timeout=5)
            self.assertIsNone(self.invoke("Bash", "git status --short"))
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait()

    def test_depth_one_owner_is_bound_by_exact_parent_attempt(self) -> None:
        owner_attempt = "att-owner-exact"
        self.write_row("open", ATTEMPT, parent_attempt_id=owner_attempt)
        self.assert_parked(
            "Bash",
            "tail -n 50 /tmp/child.codex.jsonl",
            session="worker-session",
            extra_env={"AGENT_DISPATCH_ATTEMPT_ID": owner_attempt},
        )
        self.assertIsNone(
            self.invoke(
                "Bash",
                f"utilities/dispatch-wait.sh --attempt-id {ATTEMPT} --max 300",
                session="worker-session",
                extra_env={"AGENT_DISPATCH_ATTEMPT_ID": owner_attempt},
            )
        )

    def supervised_env(self, delivered: list[str]) -> dict[str, str]:
        state = self.base / "supervisor-state.json"
        state.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "parent_attempt_id": OWNER_ATTEMPT,
                    "delivered_attempt_ids": delivered,
                }
            ),
            encoding="utf-8",
        )
        return {
            "AGENT_DISPATCH_COMPLETION_MODE": "supervised",
            "AGENT_DISPATCH_ATTEMPT_ID": OWNER_ATTEMPT,
            "AGENT_DISPATCH_COMPLETION_STATE_FILE": str(state),
            "AGENT_DISPATCH_SELF_SLUG": OWNER_SLUG,
            "AGENT_DISPATCH_JOBS": str(self.jobs),
            "AGENT_ROUTE_FILE": str(self.route),
            "AGENT_ROUTE_ID": self.route_id,
        }

    def test_supervised_delivered_batch_denies_model_wait_and_allows_only_harvest(self) -> None:
        self.write_row("open", ATTEMPT, parent_attempt_id=OWNER_ATTEMPT)
        supervised = self.supervised_env([ATTEMPT])
        wait = self.invoke(
            "Bash",
            f"utilities/dispatch-wait.sh --attempt-id {ATTEMPT} --max 600",
            session="worker-session",
            extra_env=supervised,
        )
        self.assertEqual(wait["decision"], "block")
        self.assertIn("runtime-supervised-parent", wait["reason"])
        transport_wait = self.invoke(
            "wait", session="worker-session", extra_env=supervised
        )
        self.assertEqual(transport_wait["decision"], "block")
        self.assertIsNone(
            self.invoke(
                "Bash",
                f"adapters/codex/bin/preflight.sh harvest --attempt-id {ATTEMPT} --status open",
                session="worker-session",
                extra_env=supervised,
            )
        )
        dispatch = self.invoke(
            "Bash",
            (
                "utilities/dispatch-node.py --route /tmp/route.json --node test "
                "--adapter codex --action start --slug sibling --parent owner"
            ),
            session="worker-session",
            extra_env=supervised,
        )
        self.assertEqual(dispatch["decision"], "block")

    def test_supervised_undelivered_batch_allows_second_sibling_dispatch_only(self) -> None:
        self.write_row(
            "open",
            ATTEMPT,
            parent_attempt_id=OWNER_ATTEMPT,
            route_node="implement",
        )
        supervised = self.supervised_env([])
        exact_dispatch = (
            f"python3 utilities/dispatch-node.py --route {self.route} "
            "--node test --adapter claude --action start --slug sibling-b "
            f"--parent owner -- --jobs {self.jobs} "
            f"--parent-attempt-id {OWNER_ATTEMPT}"
        )
        self.assertIsNone(
            self.invoke(
                "Bash",
                exact_dispatch,
                session="worker-session",
                extra_env=supervised,
            )
        )
        foreign_jobs = self.base / "direct-foreign-jobs.log"
        foreign_jobs.write_text("", encoding="utf-8")
        for name, command in (
            ("Read", None),
            ("Bash", "git status --short"),
            ("Bash", f"utilities/dispatch-wait.sh --attempt-id {ATTEMPT} --max 600"),
            (
                "Bash",
                f"adapters/codex/bin/preflight.sh harvest --attempt-id {ATTEMPT} --status open",
            ),
            (
                "Bash",
                exact_dispatch.replace("--parent owner", "--parent foreign"),
            ),
            (
                "Bash",
                exact_dispatch.replace(str(self.route), str(self.foreign_route)),
            ),
            (
                "Bash",
                exact_dispatch.replace(str(self.jobs), str(foreign_jobs)),
            ),
            (
                "Bash",
                exact_dispatch.replace(OWNER_ATTEMPT, "att-foreign-owner"),
            ),
        ):
            with self.subTest(name=name, command=command):
                blocked = self.invoke(
                    name,
                    command,
                    session="worker-session",
                    extra_env=supervised,
                )
                self.assertEqual(blocked["decision"], "block")
                self.assertIn("runtime-supervised-parent", blocked["reason"])

    def test_supervised_batch_binds_route_group_jobs_parent_and_one_leg_state(self) -> None:
        self.write_row(
            "open",
            ATTEMPT,
            parent_sid="worker-session",
            parent_attempt_id=OWNER_ATTEMPT,
            route_node="plan-a",
            replica_group="plan",
        )
        supervised = self.supervised_env([])

        def batch(route: Path, group: str, jobs: Path) -> str:
            return (
                "adapters/codex/bin/preflight.sh dispatch-batch "
                f"--route {route} --replica-group {group} --action start "
                f"--slug-prefix owner --parent owner --jobs {jobs}"
            )

        exact = batch(self.route, "plan", self.jobs)
        self.assertIsNone(
            self.invoke(
                "Bash",
                exact,
                session="worker-session",
                extra_env=supervised,
            )
        )

        foreign_jobs = self.base / "foreign-jobs.log"
        foreign_jobs.write_text("", encoding="utf-8")
        cases = (
            (batch(self.foreign_route, "plan", self.jobs), supervised),
            (batch(self.route, "other", self.jobs), supervised),
            (batch(self.route, "plan", foreign_jobs), supervised),
            (
                exact,
                {**supervised, "AGENT_DISPATCH_ATTEMPT_ID": "att-foreign-owner"},
            ),
            (exact, {**supervised, "AGENT_ROUTE_ID": "rt-foreign"}),
        )
        for command, env in cases:
            with self.subTest(command=command, parent=env["AGENT_DISPATCH_ATTEMPT_ID"]):
                blocked = self.invoke(
                    "Bash",
                    command,
                    session="worker-session",
                    extra_env=env,
                )
                self.assertEqual(blocked["decision"], "block")
                self.assertIn("runtime-supervised-parent", blocked["reason"])

        self.write_row(
            "open",
            "att-fixture-plan-b",
            parent_sid="worker-session",
            parent_attempt_id=OWNER_ATTEMPT,
            route_node="plan-b",
            replica_group="plan",
            append=True,
        )
        repeated = self.invoke(
            "Bash",
            exact,
            session="worker-session",
            extra_env=supervised,
        )
        self.assertEqual(repeated["decision"], "block")
        self.assertIn("runtime-supervised-parent", repeated["reason"])


if __name__ == "__main__":
    unittest.main()
