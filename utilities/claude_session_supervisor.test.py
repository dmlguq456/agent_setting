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
SUPERVISOR = ROOT / "utilities" / "claude-session-supervisor.py"
PARENT = "att-parent"


def child_row(status: str = "open") -> str:
    return (
        f"2026-07-23T00:00:00Z\t{status}\t/repo\t/wt\tchild\t"
        "attempt_schema_version=2,dispatch_depth=2,transport=headless,"
        "execution_surface=registered-headless,registered_worker=1,"
        f"attempt_id=att-child,parent_attempt_id={PARENT},note=RAW_CLAUDE_SENTINEL\n"
    )


class ClaudeSessionSupervisorTest(unittest.TestCase):
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
        self.claude = self.base / "fake_claude.py"
        self.join = self.base / "fake_join.py"
        self.claude.write_text(
            textwrap.dedent(
                """\
                import json, os, sys, time
                args = sys.argv[1:]
                resume = '--resume' in args
                key = '--resume' if resume else '--session-id'
                session = args[args.index(key) + 1]
                prompt = sys.stdin.read()
                state_path = os.environ['AGENT_DISPATCH_COMPLETION_STATE_FILE']
                with open(state_path, encoding='utf-8') as state_handle:
                    delivered = json.load(state_handle)['delivered_attempt_ids']
                with open(os.environ['FAKE_TRACE'], 'a', encoding='utf-8') as h:
                    h.write(json.dumps({'event':'turn-start','time':time.monotonic(),
                                        'resume':resume,'session':session,'prompt':prompt,
                                        'args':args,'delivered':delivered}) + '\\n')
                final_first = os.environ.get('FAKE_NO_CHILD') == '1'
                text = ('artifact: -\\nverdict: PASS\\nblocker: none'
                        if resume or final_first else 'runtime_wait: registered-children')
                print(json.dumps({'type':'system','subtype':'init',
                                  'private':'RAW_PARENT_CONTEXT_SENTINEL'}))
                print(json.dumps({'type':'result','subtype':'success','is_error':False,
                                  'result':text}))
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
                with open(trace, 'a', encoding='utf-8') as h:
                    h.write(json.dumps({'event':'join-start','time':time.monotonic()}) + '\\n')
                time.sleep(0.2)
                with open(jobs, 'a', encoding='utf-8') as h:
                    for attempt in attempts:
                        h.write('2026-07-23T00:00:01Z\\tdone\\t/repo\\t/wt\\tchild\\t'
                                'attempt_schema_version=2,dispatch_depth=2,transport=headless,'
                                'execution_surface=registered-headless,registered_worker=1,'
                                f'attempt_id={attempt},parent_attempt_id={parent}\\n')
                with open(trace, 'a', encoding='utf-8') as h:
                    h.write(json.dumps({'event':'join-end','time':time.monotonic()}) + '\\n')
                print(json.dumps({'schema_version':1,'state':'ready','parent_attempt_id':parent,
                    'children':[{'attempt_id':attempt,'status':'done','readiness':'ready',
                                 'reason':'registry-closed'} for attempt in attempts]}))
                """
            ),
            encoding="utf-8",
        )

    def command(self, claude: Path | None = None) -> list[str]:
        return [
            sys.executable,
            str(SUPERVISOR),
            "--worktree", str(self.base),
            "--jobs", str(self.jobs),
            "--parent-attempt-id", PARENT,
            "--state-file", str(self.state),
            "--add-dir", str(self.base),
            "--claude-command", f"{sys.executable} {claude or self.claude}",
            "--join-command", f"{sys.executable} {self.join}",
            "--join-timeout", "2",
            "--join-interval", "0.02",
            "--disallowed-tool", "Monitor",
        ]

    def run_supervisor(self, **extra_env: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            self.command(),
            input="initial assignment",
            text=True,
            capture_output=True,
            env={**os.environ, "FAKE_TRACE": str(self.trace), **extra_env},
            timeout=10,
        )

    def test_resume_uses_same_session_once_after_join(self):
        self.jobs.write_text(child_row(), encoding="utf-8")
        result = self.run_supervisor()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        trace = [json.loads(line) for line in self.trace.read_text().splitlines()]
        self.assertEqual(
            [item["event"] for item in trace],
            ["turn-start", "join-start", "join-end", "turn-start"],
        )
        first, second = trace[0], trace[3]
        self.assertFalse(first["resume"])
        self.assertTrue(second["resume"])
        self.assertEqual(first["session"], second["session"])
        self.assertEqual(first["delivered"], [])
        self.assertEqual(second["delivered"], ["att-child"])
        self.assertNotIn("--no-session-persistence", first["args"])
        self.assertIn("--session-id", first["args"])
        self.assertIn("--resume", second["args"])
        for turn in (first, second):
            self.assertIn("--settings", turn["args"])
            settings = json.loads(
                turn["args"][turn["args"].index("--settings") + 1]
            )
            hook = settings["hooks"]["PreToolUse"][0]["hooks"][0]
            self.assertEqual(hook["type"], "command")
            self.assertIn("hooks/registered-parent-park.py", hook["command"])
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(sum(row.get("type") == "result" for row in rows), 1)
        self.assertEqual(rows[-1]["subtype"], "success")
        self.assertNotIn("RAW_CLAUDE_SENTINEL", result.stdout)
        self.assertNotIn("RAW_PARENT_CONTEXT_SENTINEL", result.stdout)
        self.assertFalse(self.state.exists())
        log = self.base / "attempt.claude.jsonl"
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
        self.assertIn("\tvalid\texact-claude-result\tPASS\tnone\tnone", inspected.stdout)

    def test_no_child_finishes_without_resume(self):
        self.jobs.write_text("", encoding="utf-8")
        result = self.run_supervisor(FAKE_NO_CHILD="1")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        trace = [json.loads(line) for line in self.trace.read_text().splitlines()]
        self.assertEqual(len(trace), 1)
        self.assertFalse(trace[0]["resume"])
        self.assertFalse(self.state.exists())

    def test_missing_result_has_no_false_terminal(self):
        broken = self.base / "broken.py"
        broken.write_text("print('not-json')\n", encoding="utf-8")
        self.jobs.write_text("", encoding="utf-8")
        result = subprocess.run(
            self.command(broken),
            input="initial assignment",
            text=True,
            capture_output=True,
            env={**os.environ, "FAKE_TRACE": str(self.trace)},
            timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('"type":"result"', result.stdout)
        self.assertFalse(self.state.exists())


if __name__ == "__main__":
    unittest.main()
