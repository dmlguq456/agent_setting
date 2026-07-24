#!/usr/bin/env python3
"""Claude hook parity tests for runtime-supervised registered parents."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "registered-parent-park.py"
PARENT = "att-claude-owner"
CHILD = "att-claude-child-a"
SLUG = "owner"


class RegisteredParentParkTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.jobs = self.base / "jobs.log"
        self.state = self.base / "state.json"
        self.route_id = "rt-claude-park"
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
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.jobs.write_text(
            "2026-07-23T00:00:00Z\topen\t/repo\t/wt\tchild-a\t"
            "attempt_schema_version=2,dispatch_depth=2,transport=headless,"
            "execution_surface=registered-headless,registered_worker=1,"
            f"attempt_id={CHILD},parent_attempt_id={PARENT},"
            f"route_id={self.route_id},route_file={self.route},"
            "route_node=implement\n",
            encoding="utf-8",
        )

    def write_state(self, delivered: list[str]) -> None:
        self.state.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "parent_attempt_id": PARENT,
                    "delivered_attempt_ids": delivered,
                }
            ),
            encoding="utf-8",
        )

    def invoke(
        self,
        tool_name: str,
        command: str | None = None,
        *,
        mode: str = "supervised",
    ) -> dict[str, object] | None:
        payload: dict[str, object] = {
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": {},
            "cwd": str(ROOT),
        }
        if command is not None:
            payload["tool_input"] = {"command": command}
        result = subprocess.run(
            ["python3", str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
            env={
                **os.environ,
                "AGENT_HOME": str(ROOT),
                "AGENT_DISPATCH_JOBS": str(self.jobs),
                "AGENT_DISPATCH_COMPLETION_MODE": mode,
                "AGENT_DISPATCH_ATTEMPT_ID": PARENT,
                "AGENT_DISPATCH_COMPLETION_STATE_FILE": str(self.state),
                "AGENT_DISPATCH_SELF_SLUG": SLUG,
                "AGENT_ROUTE_FILE": str(self.route),
                "AGENT_ROUTE_ID": self.route_id,
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout else None

    def assert_denied(self, tool_name: str, command: str | None = None) -> None:
        result = self.invoke(tool_name, command)
        self.assertIsNotNone(result)
        output = result["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn("runtime-supervised-parent", output["permissionDecisionReason"])

    def test_undelivered_batch_allows_only_another_exact_sibling_start(self) -> None:
        self.write_state([])
        dispatch = (
            f"python3 utilities/dispatch-node.py --route {self.route} "
            "--node test --adapter codex --action start --slug child-b "
            f"--parent owner -- --jobs {self.jobs} "
            f"--parent-attempt-id {PARENT}"
        )
        self.assertIsNone(self.invoke("Bash", dispatch))
        self.assert_denied("Read")
        self.assert_denied("Bash", "git status --short")
        self.assert_denied("Bash", dispatch.replace("--parent owner", "--parent foreign"))
        self.assert_denied(
            "Bash",
            f"adapters/codex/bin/preflight.sh harvest --attempt-id {CHILD} --status open",
        )

    def test_delivered_batch_allows_only_exact_harvest(self) -> None:
        self.write_state([CHILD])
        self.assertIsNone(
            self.invoke(
                "Bash",
                f"adapters/codex/bin/preflight.sh harvest --attempt-id {CHILD} --status open",
            )
        )
        self.assert_denied("Bash", f"utilities/dispatch-wait.sh --attempt-id {CHILD} --max 600")
        self.assert_denied(
            "Bash",
            "utilities/dispatch-node.py --route /tmp/route.json --node test "
            "--adapter claude --action start --slug child-b --parent owner",
        )

    def test_missing_state_is_recovery_only_and_non_supervised_is_inactive(self) -> None:
        self.assertFalse(self.state.exists())
        self.assertIsNone(
            self.invoke(
                "Bash",
                f"adapters/codex/bin/preflight.sh harvest --attempt-id {CHILD} --status open",
            )
        )
        self.assert_denied(
            "Bash",
            "utilities/dispatch-node.py --route /tmp/route.json --node test "
            "--adapter claude --action start --slug child-b --parent owner",
        )
        self.assertIsNone(self.invoke("Read", mode="poll"))

    def test_replica_batch_requires_one_exact_leg_and_rejects_repeat(self) -> None:
        replica_metadata = (
            "attempt_schema_version=2,dispatch_depth=2,transport=headless,"
            "execution_surface=registered-headless,registered_worker=1,"
            f"attempt_id={CHILD},parent_attempt_id={PARENT},"
            f"route_id={self.route_id},route_file={self.route},route_node=plan-a,"
            "replica_group=plan,reservation_kind=replica-batch,"
            "batch_declared_size=2,batch_group=plan,"
            f"batch_route_id={self.route_id},batch_parent_attempt_id={PARENT},"
            f"batch_attempt_id={CHILD},batch_route_node=plan-a"
        )
        self.jobs.write_text(
            "2026-07-23T00:00:00Z\topen\t/repo\t/wt\tplan-a\t"
            + replica_metadata
            + "\n",
            encoding="utf-8",
        )
        self.write_state([])
        batch = (
            "adapters/codex/bin/preflight.sh dispatch-batch "
            f"--route {self.route} --replica-group plan --action start "
            f"--slug-prefix owner --parent owner --jobs {self.jobs}"
        )
        self.assertIsNone(self.invoke("Bash", batch))
        self.assert_denied("Bash", batch.replace("--replica-group plan", "--replica-group foreign"))
        foreign_jobs = self.base / "foreign.log"
        foreign_jobs.write_text("", encoding="utf-8")
        self.assert_denied("Bash", batch.replace(str(self.jobs), str(foreign_jobs)))

        second = replica_metadata.replace(CHILD, "att-claude-child-b").replace(
            "route_node=plan-a", "route_node=plan-b"
        ).replace("batch_route_node=plan-a", "batch_route_node=plan-b")
        with self.jobs.open("a", encoding="utf-8") as handle:
            handle.write(
                "2026-07-23T00:00:01Z\topen\t/repo\t/wt\tplan-b\t"
                + second
                + "\n"
            )
        self.assert_denied("Bash", batch)


if __name__ == "__main__":
    unittest.main()
