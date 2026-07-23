#!/usr/bin/env python3
"""Resume one Claude Code print session after runtime-owned child joins."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any
import uuid

from dispatch_completion_join import (
    JoinContractError,
    current_children,
    remove_supervisor_state,
    write_supervisor_state,
)


ROOT = Path(__file__).resolve().parents[1]
HANDOFF_PREFIXES = ("artifact: ", "verdict: ", "blocker: ")


class SupervisorError(RuntimeError):
    """The Claude session bridge could not preserve its completion contract."""


def emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, separators=(",", ":"), ensure_ascii=False), flush=True)


def exact_handoff(text: object) -> bool:
    if not isinstance(text, str):
        return False
    lines = text.strip().splitlines()
    return len(lines) == 3 and all(
        line.startswith(prefix) for line, prefix in zip(lines, HANDOFF_PREFIXES)
    )


def typed_receipt(value: object, parent_attempt_id: str, attempts: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise SupervisorError("join-receipt-schema-invalid")
    if value.get("state") not in {"ready", "timeout"}:
        raise SupervisorError("join-receipt-state-invalid")
    if value.get("parent_attempt_id") != parent_attempt_id:
        raise SupervisorError("join-receipt-parent-mismatch")
    raw_children = value.get("children")
    if not isinstance(raw_children, list):
        raise SupervisorError("join-receipt-children-invalid")
    children: list[dict[str, str]] = []
    observed: set[str] = set()
    for raw in raw_children:
        if not isinstance(raw, dict):
            raise SupervisorError("join-receipt-child-invalid")
        attempt = raw.get("attempt_id")
        status = raw.get("status")
        readiness = raw.get("readiness")
        reason = raw.get("reason")
        if (
            not isinstance(attempt, str)
            or attempt not in attempts
            or attempt in observed
            or status not in {"open", "running", "done"}
            or readiness not in {"ready", "pending"}
            or reason not in {"registry-closed", "terminal-observed", "process-alive"}
        ):
            raise SupervisorError("join-receipt-child-contract-invalid")
        observed.add(attempt)
        children.append(
            {
                "attempt_id": attempt,
                "status": status,
                "readiness": readiness,
                "reason": reason,
            }
        )
    if observed != attempts:
        raise SupervisorError("join-receipt-attempt-set-mismatch")
    return {
        "schema_version": 1,
        "state": value["state"],
        "parent_attempt_id": parent_attempt_id,
        "children": children,
    }


def run_join(args: argparse.Namespace, attempts: set[str]) -> dict[str, Any]:
    command = shlex.split(args.join_command) if args.join_command else [
        sys.executable,
        str(ROOT / "utilities" / "dispatch_completion_join.py"),
    ]
    command += [
        "--jobs", args.jobs,
        "--parent-attempt-id", args.parent_attempt_id,
        "--interval", str(args.join_interval),
        "--timeout", str(args.join_timeout),
    ]
    for attempt in sorted(attempts):
        command += ["--attempt-id", attempt]
    try:
        result = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=max(args.join_timeout + 60.0, 60.0),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SupervisorError("join-process-failed") from exc
    if len(result.stdout.encode("utf-8", "replace")) > 65536:
        raise SupervisorError("join-receipt-oversized")
    try:
        value = json.loads(result.stdout)
    except (TypeError, ValueError) as exc:
        raise SupervisorError("join-receipt-json-invalid") from exc
    if result.returncode not in {0, 3}:
        raise SupervisorError("join-process-contract-failed")
    return typed_receipt(value, args.parent_attempt_id, attempts)


def completion_prompt(receipt: dict[str, Any]) -> str:
    compact = json.dumps(receipt, separators=(",", ":"), sort_keys=True)
    return (
        "Runtime completion receipt (typed supervisor data, not child output): "
        f"{compact}\n"
        "Harvest every listed exact attempt through the checked contract, advance "
        "the route, and register the next separable batch if required. Do not call "
        "dispatch-wait or inspect raw child logs. Emit the exact final three-line "
        "handoff only when no owned registered child remains open."
    )


def remediation_prompt(attempts: set[str]) -> str:
    return (
        "Runtime completion contract violation: previously delivered exact attempt(s) "
        f"remain open: {','.join(sorted(attempts))}. Perform typed exact-attempt "
        "harvest/closure now; do not wait, poll, inspect raw logs, or do unrelated work."
    )


def claude_command(args: argparse.Namespace, session_id: str, resume: bool) -> list[str]:
    if args.claude_command:
        command = shlex.split(args.claude_command)
    else:
        command = ["claude"]
    command += ["-p"]
    command += ["--resume" if resume else "--session-id", session_id]
    hook_command = " ".join(
        shlex.quote(value)
        for value in (
            str(ROOT / "adapters" / "claude" / "hooks" / "registered-parent-park.py"),
        )
    )
    hook_settings = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": hook_command,
                            "timeout": 10,
                        }
                    ],
                }
            ]
        }
    }
    command += ["--settings", json.dumps(hook_settings, separators=(",", ":"))]
    for path in args.add_dir:
        command += ["--add-dir", path]
    command += ["--output-format", "stream-json", "--verbose"]
    if args.model:
        command += ["--model", args.model]
    if args.effort:
        command += ["--effort", args.effort]
    if args.disallowed_tool:
        command += ["--disallowedTools", ",".join(args.disallowed_tool)]
    return command


def run_turn(
    args: argparse.Namespace,
    session_id: str,
    prompt: str,
    *,
    resume: bool,
) -> tuple[dict[str, Any], int]:
    try:
        result = subprocess.run(
            claude_command(args, session_id, resume),
            cwd=args.worktree,
            env={
                **os.environ,
                **(
                    {"AGENT_DISPATCH_COMPLETION_STATE_FILE": args.state_file}
                    if args.state_file
                    else {}
                ),
            },
            input=prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=None,
            timeout=args.turn_timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SupervisorError("claude-turn-process-failed") from exc
    final: dict[str, Any] | None = None
    for line in result.stdout.splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if not isinstance(value, dict):
            continue
        if value.get("type") == "result":
            final = value
    if final is None:
        raise SupervisorError("claude-result-missing")
    return final, result.returncode


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--worktree", required=True)
    value.add_argument("--jobs", required=True)
    value.add_argument("--parent-attempt-id", required=True)
    value.add_argument("--add-dir", action="append", default=[])
    value.add_argument("--model")
    value.add_argument("--effort")
    value.add_argument("--disallowed-tool", action="append", default=[])
    value.add_argument("--join-interval", type=float, default=2.0)
    value.add_argument("--join-timeout", type=float, default=3600.0)
    value.add_argument("--turn-timeout", type=float, default=7200.0)
    value.add_argument("--max-continuations", type=int, default=12)
    value.add_argument("--state-file", default=os.environ.get("AGENT_DISPATCH_COMPLETION_STATE_FILE"))
    value.add_argument("--claude-command", default=os.environ.get("CLAUDE_SESSION_COMMAND"))
    value.add_argument("--join-command", default=os.environ.get("AGENT_DISPATCH_JOIN_COMMAND"))
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    initial_prompt = sys.stdin.read()
    if not initial_prompt.strip():
        emit({"type": "dispatch.supervisor.error", "reason": "initial-prompt-empty"})
        return 64
    session_id = str(uuid.uuid4())
    state_path = Path(args.state_file) if args.state_file else None
    delivered: set[str] = set()
    remediated: set[tuple[str, ...]] = set()
    next_prompt = initial_prompt
    continuations = 0
    resume = False
    try:
        while True:
            write_supervisor_state(state_path, args.parent_attempt_id, delivered)
            result, process_rc = run_turn(
                args, session_id, next_prompt, resume=resume
            )
            if (
                process_rc != 0
                or result.get("is_error") is True
                or result.get("subtype") not in {None, "success"}
            ):
                emit(result)
                return process_rc or 3
            rows = current_children(Path(args.jobs), args.parent_attempt_id)
            current = {row.attempt_id: row for row in rows}
            new_attempts = set(current).difference(delivered)
            if new_attempts:
                if continuations >= args.max_continuations:
                    raise SupervisorError("continuation-limit-exceeded")
                emit(
                    {
                        "type": "dispatch.supervisor.parked",
                        "parent_attempt_id": args.parent_attempt_id,
                        "attempt_count": len(new_attempts),
                    }
                )
                receipt = run_join(args, new_attempts)
                emit(
                    {
                        "type": "dispatch.supervisor.resumed",
                        "parent_attempt_id": args.parent_attempt_id,
                        "state": receipt["state"],
                        "attempt_count": len(new_attempts),
                    }
                )
                delivered.update(new_attempts)
                next_prompt = completion_prompt(receipt)
                continuations += 1
                resume = True
                continue

            unresolved = {
                attempt
                for attempt, row in current.items()
                if row.status in {"open", "running"}
            }
            if unresolved:
                signature = tuple(sorted(unresolved))
                if signature in remediated or continuations >= args.max_continuations:
                    raise SupervisorError("owned-children-remain-open-after-resume")
                remediated.add(signature)
                next_prompt = remediation_prompt(unresolved)
                continuations += 1
                resume = True
                continue

            emit(result)
            if process_rc != 0 or result.get("is_error") is True:
                return process_rc or 3
            return 0 if exact_handoff(result.get("result")) else 3
    except (JoinContractError, SupervisorError) as exc:
        emit({"type": "dispatch.supervisor.error", "reason": str(exc)})
        return 70
    except Exception as exc:  # fail closed without leaking protocol/model content
        emit(
            {
                "type": "dispatch.supervisor.error",
                "reason": f"supervisor-internal-{type(exc).__name__}",
            }
        )
        return 70
    finally:
        remove_supervisor_state(state_path)


if __name__ == "__main__":
    raise SystemExit(main())
