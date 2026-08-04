#!/usr/bin/env python3
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
import warnings
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "utilities"), str(ROOT / "tools")]

import dispatch_summary as S  # noqa: E402
from fleet import titles  # noqa: E402

warnings.filterwarnings("ignore", category=ResourceWarning)


class DispatchSummaryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_env = os.environ.copy()
        os.environ.update({
            "FLEET_TITLE_STATE_DIR": str(Path(self.tmp.name) / "titles"),
            "AGENT_MODEL_GOVERNOR_ROOT": str(Path(self.tmp.name) / "governor"),
            "AGENT_MODEL_WORKER_TOTAL": "5",
            "AGENT_MODEL_WORKER_START_BUDGET": "20",
            "FLEET_TITLE_CONCURRENCY": "4",
            "FLEET_TITLE_MAX_STARTS": "4",
            "FLEET_TITLE_COMMAND": shlex.join([
                sys.executable, "-c",
                "print('TITLE: Dispatch Summary Owner\\nNOW: 분사 작업 요약을 갱신하고 있습니다')",
            ]),
        })
        os.environ.pop("FLEET_TITLE_DISABLE", None)
        os.environ.pop("FLEET_TITLE_REFRESH", None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.old_env)
        self.tmp.cleanup()

    def test_supervisor_generates_initial_and_final_sidecar_without_fleet(self):
        attempt = "att-summary-live"
        log = Path(self.tmp.name) / f"owner.{attempt}.codex.jsonl"
        log.write_text(json.dumps({
            "type": "item.completed",
            "item": {"type": "agent_message", "text": "start summary owner"},
        }) + "\n", encoding="utf-8")
        child = subprocess.Popen([
            sys.executable, "-c",
            "import pathlib,sys,time,json; time.sleep(.4); "
            "p=pathlib.Path(sys.argv[1]); "
            "f=p.open('a'); f.write(json.dumps({'type':'item.completed','item':"
            "{'type':'agent_message','text':'finish summary owner'}})+'\\n'); "
            "f.close(); time.sleep(.25)",
            str(log),
        ], start_new_session=True)
        start = S.process_observation(child.pid)[1]
        self.assertTrue(start)
        rc = S.supervise(
            attempt_id=attempt, harness="codex", transcript=log,
            target_pid=child.pid, target_start=start,
            poll=0.05, initial_delay=0, periodic_debounce=90,
            final_grace=8, log_quiet=0.05,
        )
        child.wait(timeout=5)
        self.assertEqual(rc, 0)
        sidecar = titles.read(S.summary_sid(attempt), harness="codex")
        self.assertEqual(sidecar["title"], "Dispatch Summary Owner")
        self.assertEqual(sidecar["summary"], "분사 작업 요약을 갱신하고 있습니다")
        self.assertEqual(sidecar["offset"], log.stat().st_size)
        state = json.loads(S.owner_state_path("codex", attempt).read_text())
        self.assertEqual(state["status"], "terminal")
        self.assertTrue(state["final_refresh_complete"])

    def test_reconcile_reattaches_only_one_live_exact_attempt(self):
        attempt = "att-summary-recover"
        worker = subprocess.Popen(["sleep", "60"], start_new_session=True)
        owner = subprocess.Popen(["sleep", "60"], start_new_session=True)
        try:
            start = S.process_observation(worker.pid)[1]
            log = Path(self.tmp.name) / f"owner.{attempt}.claude.jsonl"
            log.write_text('{"message":"recover summary"}\n', encoding="utf-8")
            jobs = Path(self.tmp.name) / "jobs.log"
            jobs.write_text(
                "2026-08-04T00:00:00Z\topen\t/repo\t/wt\towner\t"
                "attempt_schema_version=2,dispatch_depth=1,transport=headless,"
                "execution_surface=registered-headless,registered_worker=1,"
                "fallback_hop=same-harness-headless,worker_type=owner,"
                f"attempt_id={attempt},harness=claude,pid={worker.pid},"
                f"pid_start={start},log_file={log}\n",
                encoding="utf-8",
            )
            owner_start = S.process_observation(owner.pid)[1]
            observer_namespace = S.process_namespace_identity()
            attached = {
                "summary_owner": S.OWNER_KIND,
                "summary_sid": S.summary_sid(attempt),
                "summary_owner_pid": str(owner.pid),
                "summary_owner_pid_start": owner_start,
                "summary_owner_pid_observer_ns": observer_namespace,
                "summary_state_file": str(S.owner_state_path("claude", attempt)),
            }
            state_path = S.owner_state_path("claude", attempt)
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps({
                "schema_version": S.OWNER_SCHEMA,
                "status": "active",
                "attempt_id": attempt,
                "harness": "claude",
                "pid": owner.pid,
                "proc_start": owner_start,
                "observer_namespace": observer_namespace,
            }))
            with mock.patch.object(S, "launch_summary_owner", return_value=attached) as launch:
                first = S.ensure_attempt_owner(jobs, attempt)
                second = S.ensure_attempt_owner(jobs, attempt)
            self.assertEqual(first["state"], "started")
            self.assertEqual(second, {"state": "existing", "reason": "owner-live"})
            launch.assert_called_once()
            self.assertIn("summary_owner=dispatch-v1", jobs.read_text())
        finally:
            for process in (worker, owner):
                if process.poll() is None:
                    process.kill()
                process.wait()

    def test_all_three_wrappers_attach_owner_at_pre_release_boundary(self):
        for harness in ("claude", "codex", "opencode"):
            source = (ROOT / "adapters" / harness / "bin" / "dispatch-headless.py").read_text()
            self.assertIn("from dispatch_summary import launch_summary_owner", source)
            self.assertIn("pre_release=lambda identity: launch_summary_owner", source)
            self.assertIn(f'harness="{harness}"', source)
        opencode = (ROOT / "adapters" / "opencode" / "bin" / "dispatch-headless.py").read_text()
        self.assertIn("if args.attempt_id else", opencode)


if __name__ == "__main__":
    unittest.main(verbosity=2)
