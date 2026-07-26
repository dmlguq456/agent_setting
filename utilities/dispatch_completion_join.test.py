#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest
import sys


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "dispatch_completion_join", HERE / "dispatch_completion_join.py"
)
JOIN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = JOIN
SPEC.loader.exec_module(JOIN)


def row(
    status: str,
    attempt: str,
    parent: str,
    slug: str,
    sentinel: str = "",
    *,
    launch_outcome: str = "",
    process_metadata: dict[str, str] | None = None,
) -> str:
    meta = (
        "attempt_schema_version=2,dispatch_depth=2,transport=headless,"
        "execution_surface=registered-headless,registered_worker=1,"
        f"attempt_id={attempt},parent_attempt_id={parent},note={sentinel}"
    )
    if launch_outcome or (status == "done" and not process_metadata):
        meta += f",launch_outcome={launch_outcome or 'never-launched'}"
    for key, value in (process_metadata or {}).items():
        meta += f",{key}={value}"
    return f"2026-07-23T00:00:00Z\t{status}\t/repo\t/wt\t{slug}\t{meta}\n"


def session_row(
    status: str,
    attempt: str,
    parent_session: str,
    slug: str,
    *,
    native: bool = True,
) -> str:
    meta = (
        "attempt_schema_version=2,dispatch_depth=1,transport=headless,"
        "execution_surface=registered-headless,registered_worker=1,"
        "launch_claimed=1,"
        f"attempt_id={attempt},parent_sid={parent_session}"
    )
    if native:
        meta += ",parent_completion_delivery=codex-stop-hook"
    if status == "done":
        meta += ",launch_outcome=never-launched"
    return f"2026-07-23T00:00:00Z\t{status}\t/repo\t/wt\t{slug}\t{meta}\n"


def parallel_row(
    *,
    attempt: str,
    parent: str,
    node: str,
    group: str,
    declared_size: int,
    route_id: str,
    route_file: Path,
) -> str:
    return row(
        "open",
        attempt,
        parent,
        node,
        process_metadata={
            "worktree": str(route_file.parent),
            "route_file": str(route_file),
            "route_id": route_id,
            "route_node": node,
            "parallel_group": group,
            "replica_group": group,
            "reservation_kind": "parallel-batch",
            "batch_declared_size": str(declared_size),
            "batch_group": group,
            "batch_route_id": route_id,
            "batch_parent_attempt_id": parent,
            "batch_attempt_id": attempt,
            "batch_route_node": node,
        },
    )


class DispatchCompletionJoinTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.jobs = self.root / "jobs.log"
        self.live = self.root / "live.sh"
        self.live.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.live.chmod(0o755)

    def test_parallel_batch_waits_for_every_exact_child_and_ignores_foreign(self):
        parent = "att-parent"
        self.jobs.write_text(
            row("open", "att-a", parent, "a", "RAW_CHILD_SENTINEL")
            + row("open", "att-b", parent, "b")
            + row("open", "att-foreign", "att-other", "foreign"),
            encoding="utf-8",
        )

        def close_in_order() -> None:
            time.sleep(0.08)
            with self.jobs.open("a", encoding="utf-8") as handle:
                handle.write(row("done", "att-a", parent, "a"))
            time.sleep(0.14)
            with self.jobs.open("a", encoding="utf-8") as handle:
                handle.write(row("done", "att-b", parent, "b"))

        thread = threading.Thread(target=close_in_order)
        thread.start()
        started = time.monotonic()
        receipt = JOIN.join_batch(
            jobs=self.jobs,
            parent_attempt_id=parent,
            interval=0.02,
            timeout=2,
            liveness_command=[str(self.live)],
        )
        thread.join(timeout=2)
        elapsed = time.monotonic() - started
        self.assertGreaterEqual(elapsed, 0.18)
        self.assertEqual(receipt["state"], "ready")
        self.assertEqual(
            {child["attempt_id"] for child in receipt["children"]},
            {"att-a", "att-b"},
        )
        self.assertNotIn("RAW_CHILD_SENTINEL", json.dumps(receipt))

    def test_terminal_liveness_resumes_for_typed_harvest(self):
        terminal = self.root / "terminal.sh"
        terminal.write_text("#!/bin/sh\nexit 3\n", encoding="utf-8")
        terminal.chmod(0o755)
        self.jobs.write_text(
            row(
                "open",
                "att-a",
                "att-parent",
                "a",
                launch_outcome="reaped-before-publish",
            ),
            encoding="utf-8",
        )
        receipt = JOIN.join_batch(
            jobs=self.jobs,
            parent_attempt_id="att-parent",
            interval=0.02,
            timeout=1,
            liveness_command=[str(terminal)],
        )
        self.assertEqual(receipt["state"], "ready")
        self.assertEqual(receipt["children"][0]["reason"], "terminal-observed")
        self.assertEqual(
            JOIN.pending_attempt_ids(
                JOIN.current_children(self.jobs, "att-parent")
            ),
            set(),
        )

    def test_running_registry_state_is_probed_as_open(self):
        probe = self.root / "probe.sh"
        probe.write_text(
            "#!/bin/sh\nawk -F '\\t' '$2 == \"open\" { found=1 } END { exit(found ? 3 : 9) }' \"$1\"\n",
            encoding="utf-8",
        )
        probe.chmod(0o755)
        self.jobs.write_text(
            row(
                "running",
                "att-a",
                "att-parent",
                "a",
                launch_outcome="reaped-before-publish",
            ),
            encoding="utf-8",
        )
        receipt = JOIN.join_batch(
            jobs=self.jobs,
            parent_attempt_id="att-parent",
            interval=0.02,
            timeout=1,
            liveness_command=[str(probe)],
        )
        self.assertEqual(receipt["state"], "ready")
        self.assertEqual(receipt["children"][0]["reason"], "terminal-observed")

    def test_done_row_waits_for_exact_process_to_exit(self):
        proc = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        def stop_process() -> None:
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=5)

        self.addCleanup(stop_process)
        raw = Path(f"/proc/{proc.pid}/stat").read_text(encoding="utf-8")
        start = raw[raw.rfind(")") + 2 :].split()[19]
        process_metadata = {
            "pid": str(proc.pid),
            "pid_start": start,
            "pgid": str(proc.pid),
            "pid_observer_ns": os.readlink("/proc/self/ns/pid"),
        }
        self.jobs.write_text(
            row(
                "done",
                "att-a",
                "att-parent",
                "a",
                process_metadata=process_metadata,
            ),
            encoding="utf-8",
        )
        draining = JOIN.join_batch(
            jobs=self.jobs,
            parent_attempt_id="att-parent",
            interval=0.02,
            timeout=0.08,
            liveness_command=[str(self.live)],
        )
        self.assertEqual(draining["state"], "timeout")
        self.assertEqual(draining["children"][0]["reason"], "process-alive")
        proc.terminate()
        proc.wait(timeout=5)
        ready = JOIN.join_batch(
            jobs=self.jobs,
            parent_attempt_id="att-parent",
            interval=0.02,
            timeout=1,
            liveness_command=[str(self.live)],
        )
        self.assertEqual(ready["state"], "ready")

    def test_timeout_is_one_bounded_receipt(self):
        self.jobs.write_text(
            row("open", "att-a", "att-parent", "a", "RAW_TIMEOUT_SENTINEL"),
            encoding="utf-8",
        )
        receipt = JOIN.join_batch(
            jobs=self.jobs,
            parent_attempt_id="att-parent",
            interval=0.02,
            timeout=0.08,
            liveness_command=[str(self.live)],
        )
        self.assertEqual(receipt["state"], "timeout")
        self.assertEqual(receipt["children"][0]["readiness"], "pending")
        self.assertNotIn("RAW_TIMEOUT_SENTINEL", json.dumps(receipt))

    def test_expected_attempt_set_fails_closed(self):
        self.jobs.write_text(row("done", "att-a", "att-parent", "a"), encoding="utf-8")
        with self.assertRaises(JOIN.JoinContractError):
            JOIN.join_batch(
                jobs=self.jobs,
                parent_attempt_id="att-parent",
                expected_attempts={"att-a", "att-missing"},
                liveness_command=[str(self.live)],
            )

    def test_supervisor_phase_state_is_atomic_bounded_and_parent_scoped(self):
        state = self.root / "runtime" / "parent.json"
        JOIN.write_supervisor_state(state, "att-parent", {"att-b", "att-a"})
        self.assertEqual(
            JOIN.read_supervisor_state(state, "att-parent"),
            {"att-a", "att-b"},
        )
        self.assertEqual(state.stat().st_mode & 0o777, 0o600)
        self.assertIsNone(JOIN.read_supervisor_state(state, "att-foreign"))
        state.write_text('{"schema_version":1,"parent_attempt_id":"att-parent"}', encoding="utf-8")
        self.assertIsNone(JOIN.read_supervisor_state(state, "att-parent"))
        JOIN.remove_supervisor_state(state)
        self.assertFalse(state.exists())

    def test_session_children_select_only_stamped_exact_direct_rows(self):
        session = "thread-exact"
        depth_two = row("open", "att-depth-two", "att-parent", "depth-two")
        depth_two = depth_two.replace(
            "parent_attempt_id=att-parent", f"parent_sid={session}"
        )
        self.jobs.write_text(
            session_row("open", "att-native", session, "native")
            + session_row("open", "att-foreign", "thread-foreign", "foreign")
            + session_row("open", "att-legacy", session, "legacy", native=False)
            + depth_two,
            encoding="utf-8",
        )
        rows = JOIN.current_session_children(self.jobs, session)
        self.assertEqual([item.attempt_id for item in rows], ["att-native"])

    def test_session_batch_waits_for_every_exact_child(self):
        session = "thread-parent"
        self.jobs.write_text(
            session_row("open", "att-a", session, "a")
            + session_row("open", "att-b", session, "b")
            + session_row("open", "att-foreign", "thread-other", "foreign"),
            encoding="utf-8",
        )

        def close_batch() -> None:
            time.sleep(0.06)
            with self.jobs.open("a", encoding="utf-8") as handle:
                handle.write(session_row("done", "att-a", session, "a"))
            time.sleep(0.06)
            with self.jobs.open("a", encoding="utf-8") as handle:
                handle.write(session_row("done", "att-b", session, "b"))

        thread = threading.Thread(target=close_batch)
        thread.start()
        receipt = JOIN.join_session_batch(
            jobs=self.jobs,
            parent_session_id=session,
            interval=0.02,
            timeout=1,
            liveness_command=[str(self.live)],
        )
        thread.join(timeout=1)
        self.assertEqual(receipt["state"], "ready")
        self.assertEqual(receipt["parent_session_id"], session)
        self.assertEqual(
            {child["attempt_id"] for child in receipt["children"]},
            {"att-a", "att-b"},
        )

    def test_parent_session_state_is_atomic_bounded_and_hashed(self):
        session = "thread-private"
        state = JOIN.parent_session_state_path(self.jobs, session)
        self.assertNotIn(session, state.name)
        JOIN.register_parent_session_attempt(state, session, "att-a")
        JOIN.register_parent_session_attempt(state, session, "att-b")
        pending = JOIN.read_parent_session_batch_state(state, session)
        self.assertIsNotNone(pending)
        self.assertEqual(set(pending.attempt_ids), {"att-a", "att-b"})
        self.assertEqual(set(pending.delivered_attempt_ids), set())
        JOIN.write_parent_session_state(
            state,
            session,
            {"att-b", "att-a"},
            attempt_ids={"att-b", "att-a"},
        )
        self.assertEqual(
            JOIN.read_parent_session_state(state, session),
            {"att-a", "att-b"},
        )
        self.assertEqual(state.stat().st_mode & 0o777, 0o600)
        self.assertIsNone(JOIN.read_parent_session_state(state, "thread-foreign"))
        with self.assertRaises(JOIN.JoinContractError):
            JOIN.consume_parent_session_attempt(
                state,
                session,
                "att-a",
                before_consume=lambda: False,
            )
        self.assertEqual(
            JOIN.read_parent_session_state(state, session),
            {"att-a", "att-b"},
        )
        self.assertTrue(JOIN.consume_parent_session_attempt(state, session, "att-a"))
        self.assertEqual(JOIN.read_parent_session_state(state, session), {"att-b"})
        self.assertTrue(JOIN.consume_parent_session_attempt(state, session, "att-b"))
        self.assertFalse(state.exists())

    def test_supervised_command_classifier_admits_only_exact_phase_actions(self):
        open_attempts = {"att-a", "att-b"}
        harvest = JOIN.classify_supervised_shell_command(
            base=JOIN.ROOT,
            command=(
                "adapters/codex/bin/preflight.sh harvest "
                "--attempt-id att-a --status open"
            ),
            open_attempt_ids=open_attempts,
            parent_slug="owner",
        )
        self.assertEqual(harvest, JOIN.SupervisorShellAction("harvest", "att-a"))
        dispatch = JOIN.classify_supervised_shell_command(
            base=JOIN.ROOT,
            command=(
                "python3 utilities/dispatch-node.py --route /tmp/route.json "
                "--node implement --adapter claude --action start --slug worker-b "
                "--parent owner -- --jobs /tmp/jobs.log"
            ),
            open_attempt_ids=open_attempts,
            parent_slug="owner",
        )
        self.assertEqual(dispatch, JOIN.SupervisorShellAction("dispatch"))
        batch = JOIN.classify_supervised_shell_command(
            base=JOIN.ROOT,
            command=(
                "adapters/codex/bin/preflight.sh dispatch-batch "
                "--route /tmp/route.json --replica-group plan "
                "--action start --slug-prefix review --parent owner "
                "--jobs /tmp/jobs.log"
            ),
            open_attempt_ids=open_attempts,
            parent_slug="owner",
        )
        self.assertEqual(batch, JOIN.SupervisorShellAction("dispatch-batch"))
        for command in (
            "adapters/codex/bin/preflight.sh harvest --attempt-id att-c --status open",
            "adapters/codex/bin/preflight.sh harvest --attempt-id att-a --status open; git status",
            (
                "utilities/dispatch-node.py --route /tmp/route.json --node implement "
                "--adapter codex --action start --slug worker-b --parent foreign"
            ),
            (
                "/tmp/python3 utilities/dispatch-node.py --route /tmp/route.json "
                "--node implement --adapter codex --action start --slug worker-b "
                "--parent owner"
            ),
            "git status --short",
            (
                "adapters/codex/bin/preflight.sh dispatch-batch "
                "--route /tmp/route.json --replica-group plan --action start "
                "--slug-prefix review --parent foreign"
            ),
            (
                "adapters/codex/bin/preflight.sh dispatch-batch "
                "--route /tmp/route.json --replica-group plan --action start "
                "--slug-prefix review --parent owner --jobs /tmp/a.log "
                "--jobs /tmp/b.log"
            ),
        ):
            with self.subTest(command=command):
                self.assertIsNone(
                    JOIN.classify_supervised_shell_command(
                        base=JOIN.ROOT,
                        command=command,
                        open_attempt_ids=open_attempts,
                        parent_slug="owner",
                    )
                )

    def test_strict_supervisor_admits_only_one_missing_leg_of_three_way_group(self):
        parent = "att-parent"
        route_id = "route-n3"
        group = "frame"
        route_file = self.root / "route.json"
        route_file.write_text(
            json.dumps(
                {
                    "route_id": route_id,
                    "nodes": [
                        {
                            "id": node,
                            "dispatch_depth": 2,
                            "parallel_group": group,
                            "replica_group": group,
                        }
                        for node in ("frame-a", "frame-b", "frame-c")
                    ],
                }
            ),
            encoding="utf-8",
        )

        def command() -> str:
            return (
                "adapters/codex/bin/preflight.sh dispatch-batch "
                f"--route {route_file} --parallel-group {group} --action start "
                f"--slug-prefix frame --parent owner --jobs {self.jobs}"
            )

        rows = [
            parallel_row(
                attempt=f"att-{suffix}",
                parent=parent,
                node=f"frame-{suffix}",
                group=group,
                declared_size=3,
                route_id=route_id,
                route_file=route_file,
            )
            for suffix in ("a", "b", "c")
        ]

        self.jobs.write_text(rows[0], encoding="utf-8")
        self.assertIsNone(
            JOIN.classify_supervised_shell_command(
                base=JOIN.ROOT,
                command=command(),
                open_attempt_ids={"att-a"},
                parent_slug="owner",
                jobs=self.jobs,
                parent_attempt_id=parent,
                route_file=route_file,
                route_id=route_id,
            )
        )

        self.jobs.write_text("".join(rows[:2]), encoding="utf-8")
        self.assertEqual(
            JOIN.classify_supervised_shell_command(
                base=JOIN.ROOT,
                command=command(),
                open_attempt_ids={"att-a", "att-b"},
                parent_slug="owner",
                jobs=self.jobs,
                parent_attempt_id=parent,
                route_file=route_file,
                route_id=route_id,
            ),
            JOIN.SupervisorShellAction("dispatch-batch"),
        )

        self.jobs.write_text("".join(rows), encoding="utf-8")
        self.assertIsNone(
            JOIN.classify_supervised_shell_command(
                base=JOIN.ROOT,
                command=command(),
                open_attempt_ids={"att-a", "att-b", "att-c"},
                parent_slug="owner",
                jobs=self.jobs,
                parent_attempt_id=parent,
                route_file=route_file,
                route_id=route_id,
            )
        )

    def test_strict_supervisor_rejects_direct_dispatch_of_parallel_leg(self):
        parent = "att-parent"
        route_id = "route-n2"
        group = "plan"
        route_file = self.root / "route.json"
        route_file.write_text(
            json.dumps(
                {
                    "route_id": route_id,
                    "nodes": [
                        {
                            "id": node,
                            "dispatch_depth": 2,
                            "parallel_group": group,
                            "replica_group": group,
                        }
                        for node in ("plan-a", "plan-b")
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.jobs.write_text(
            parallel_row(
                attempt="att-a",
                parent=parent,
                node="plan-a",
                group=group,
                declared_size=2,
                route_id=route_id,
                route_file=route_file,
            ),
            encoding="utf-8",
        )
        command = (
            f"python3 utilities/dispatch-node.py --route {route_file} "
            "--node plan-b --adapter claude --action start --slug plan-b "
            f"--parent owner -- --jobs {self.jobs}"
        )
        self.assertIsNone(
            JOIN.classify_supervised_shell_command(
                base=JOIN.ROOT,
                command=command,
                open_attempt_ids={"att-a"},
                parent_slug="owner",
                jobs=self.jobs,
                parent_attempt_id=parent,
                route_file=route_file,
                route_id=route_id,
            )
        )


if __name__ == "__main__":
    unittest.main()
