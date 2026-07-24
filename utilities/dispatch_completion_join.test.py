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


if __name__ == "__main__":
    unittest.main()
