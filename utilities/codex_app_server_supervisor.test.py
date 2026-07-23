#!/usr/bin/env python3

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "utilities" / "codex-app-server-supervisor.py"
PARENT = "att-parent"


def child_row(attempt: str = "att-child", slug: str = "child", status: str = "open") -> str:
    return (
        f"2026-07-23T00:00:00Z\t{status}\t/repo\t/wt\t{slug}\t"
        "attempt_schema_version=2,dispatch_depth=2,transport=headless,"
        "execution_surface=registered-headless,registered_worker=1,"
        f"attempt_id={attempt},parent_attempt_id={PARENT},note=RAW_CHILD_SENTINEL\n"
    )


class CodexAppServerSupervisorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.base)], check=True)
        self.artifact_root = self.base / ".agent_reports"
        self.artifact_root.mkdir()
        self.jobs = self.base / "jobs.log"
        self.state = self.base / "supervisor-state.json"
        self.trace = self.base / "trace.jsonl"
        self.app = self.base / "fake_app.py"
        self.join = self.base / "fake_join.py"
        self.app.write_text(
            textwrap.dedent(
                """\
                import json, os, sys, time
                trace = os.environ['FAKE_TRACE']
                turns = 0
                def record(event, **extra):
                    with open(trace, 'a', encoding='utf-8') as h:
                        h.write(json.dumps({'event': event, 'time': time.monotonic(), **extra}) + '\\n')
                def send(value):
                    print(json.dumps(value), flush=True)
                for line in sys.stdin:
                    value = json.loads(line)
                    method = value.get('method')
                    if method == 'initialize':
                        send({'jsonrpc':'2.0','id':value['id'],'result':{'server':'fake'}})
                    elif method == 'initialized':
                        pass
                    elif method == 'thread/start':
                        send({'jsonrpc':'2.0','id':value['id'],'result':{'thread':{'id':'thread-1'}}})
                    elif method == 'turn/start':
                        turns += 1
                        prompt = value['params']['input'][0]['text']
                        state_path = os.environ.get('AGENT_DISPATCH_COMPLETION_STATE_FILE')
                        with open(state_path, encoding='utf-8') as h:
                            delivered = json.load(h)['delivered_attempt_ids']
                        record('turn-start', turn=turns, prompt=prompt, delivered=delivered)
                        turn_id = f'turn-{turns}'
                        send({'jsonrpc':'2.0','id':value['id'],'result':{'turn':{'id':turn_id}}})
                        final_first = os.environ.get('FAKE_NO_CHILD') == '1'
                        text = ('artifact: -\\nverdict: PASS\\nblocker: none'
                                if turns > 1 or final_first else 'runtime_wait: registered-children')
                        send({'jsonrpc':'2.0','method':'item/completed','params':{
                            'threadId':'thread-1','turnId':turn_id,'completedAtMs':1,
                            'item':{'type':'agentMessage','id':f'msg-{turns}','text':text,
                                    'phase':None,'memoryCitation':None}}})
                        send({'jsonrpc':'2.0','method':'turn/completed','params':{
                            'threadId':'thread-1','turn':{'id':turn_id,'status':'completed'}}})
                """
            ),
            encoding="utf-8",
        )
        self.join.write_text(
            textwrap.dedent(
                """\
                import json, os, sys, time
                trace = os.environ['FAKE_TRACE']
                jobs = sys.argv[sys.argv.index('--jobs') + 1]
                parent = sys.argv[sys.argv.index('--parent-attempt-id') + 1]
                attempts = [sys.argv[i + 1] for i, value in enumerate(sys.argv) if value == '--attempt-id']
                def record(event):
                    with open(trace, 'a', encoding='utf-8') as h:
                        h.write(json.dumps({'event':event,'time':time.monotonic()}) + '\\n')
                record('join-start')
                time.sleep(0.2)
                with open(jobs, 'a', encoding='utf-8') as h:
                    for attempt in attempts:
                        h.write('2026-07-23T00:00:01Z\\tdone\\t/repo\\t/wt\\tchild\\t'
                                'attempt_schema_version=2,dispatch_depth=2,transport=headless,'
                                'execution_surface=registered-headless,registered_worker=1,'
                                f'attempt_id={attempt},parent_attempt_id={parent}\\n')
                record('join-end')
                print(json.dumps({'schema_version':1,'state':'ready','parent_attempt_id':parent,
                    'children':[{'attempt_id':attempt,'status':'done','readiness':'ready',
                                 'reason':'registry-closed'} for attempt in attempts]}))
                """
            ),
            encoding="utf-8",
        )

    def command(self, *, broken_app: Path | None = None) -> list[str]:
        app = broken_app or self.app
        return [
            sys.executable,
            str(SUPERVISOR),
            "--worktree", str(self.base),
            "--jobs", str(self.jobs),
            "--parent-attempt-id", PARENT,
            "--state-file", str(self.state),
            "--sandbox", "danger-full-access",
            "--app-server-command", f"{sys.executable} {app}",
            "--join-command", f"{sys.executable} {self.join}",
            "--join-timeout", "2",
            "--join-interval", "0.02",
        ]

    def run_supervisor(self, **extra_env: str) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "FAKE_TRACE": str(self.trace), **extra_env}
        return subprocess.run(
            self.command(),
            input="initial assignment",
            text=True,
            capture_output=True,
            env=env,
            timeout=10,
        )

    def test_runtime_wait_has_no_model_activity_until_exact_join_is_ready(self):
        self.jobs.write_text(
            child_row("att-child-a", "child-a")
            + child_row("att-child-b", "child-b"),
            encoding="utf-8",
        )
        result = self.run_supervisor()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        trace = [json.loads(line) for line in self.trace.read_text().splitlines()]
        events = [item["event"] for item in trace]
        self.assertEqual(events, ["turn-start", "join-start", "join-end", "turn-start"])
        self.assertEqual(trace[0]["delivered"], [])
        self.assertEqual(
            set(trace[3]["delivered"]), {"att-child-a", "att-child-b"}
        )
        self.assertLess(trace[1]["time"], trace[2]["time"])
        self.assertLessEqual(trace[2]["time"], trace[3]["time"])
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(sum(row.get("type") == "turn.completed" for row in rows), 1)
        self.assertEqual(
            sum(row.get("type") == "dispatch.supervisor.turn.started" for row in rows),
            2,
        )
        final_messages = [
            row["item"]["text"]
            for row in rows
            if row.get("type") == "item.completed"
            and row.get("item", {}).get("type") == "agent_message"
            and "verdict: PASS" in row["item"].get("text", "")
        ]
        self.assertEqual(final_messages, ["artifact: -\nverdict: PASS\nblocker: none"])
        resumed = [row for row in rows if row.get("type") == "dispatch.supervisor.resumed"]
        self.assertEqual(len(resumed), 1)
        self.assertEqual(resumed[0]["attempt_count"], 2)
        terminal = next(i for i, row in enumerate(rows) if row.get("type") == "turn.completed")
        self.assertEqual(rows[terminal - 1]["item"]["type"], "agent_message")
        self.assertIn("verdict: PASS", rows[terminal - 1]["item"]["text"])
        self.assertNotIn("RAW_CHILD_SENTINEL", result.stdout)
        self.assertFalse(self.state.exists())
        log = self.base / "attempt.codex.jsonl"
        log.write_text(result.stdout, encoding="utf-8")
        inspected = subprocess.run(
            [
                sys.executable,
                str(ROOT / "utilities" / "codex_dispatch_terminal.py"),
                "--worktree", str(self.base),
                "--artifact-root-metadata", str(self.artifact_root),
                str(log),
            ],
            text=True,
            capture_output=True,
            env={**os.environ, "AGENT_ARTIFACT_ROOT": str(self.artifact_root)},
        )
        self.assertEqual(inspected.returncode, 0, inspected.stderr + inspected.stdout)
        self.assertIn("\tvalid\texact-turn-completed\tPASS\tnone\tnone", inspected.stdout)

    def test_no_child_finishes_in_one_turn(self):
        self.jobs.write_text("", encoding="utf-8")
        result = self.run_supervisor(FAKE_NO_CHILD="1")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        trace = [json.loads(line) for line in self.trace.read_text().splitlines()]
        self.assertEqual([item["event"] for item in trace], ["turn-start"])
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(sum(row.get("type") == "turn.completed" for row in rows), 1)
        self.assertEqual(
            sum(row.get("type") == "dispatch.supervisor.turn.started" for row in rows),
            1,
        )
        self.assertFalse(self.state.exists())

    def test_protocol_failure_emits_no_false_terminal(self):
        broken = self.base / "broken.py"
        broken.write_text(
            "import json,sys\n"
            "v=json.loads(sys.stdin.readline())\n"
            "print(json.dumps({'id':v['id'],'result':{'ok':1}}),flush=True)\n",
            encoding="utf-8",
        )
        self.jobs.write_text("", encoding="utf-8")
        env = {**os.environ, "FAKE_TRACE": str(self.trace)}
        result = subprocess.run(
            self.command(broken_app=broken),
            input="initial assignment",
            text=True,
            capture_output=True,
            env=env,
            timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('"type":"turn.completed"', result.stdout)
        self.assertFalse(self.state.exists())


if __name__ == "__main__":
    unittest.main()
