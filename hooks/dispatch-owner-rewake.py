#!/usr/bin/env python3
"""Wake an interactive Claude parent once when its exact headless owner finishes."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
from typing import Any


ATTEMPT = re.compile(r"att-[A-Za-z0-9._-]{1,240}\Z")
DEFAULT_INTERVAL_SECONDS = 20
DEFAULT_MAX_SECONDS = 21_600


@dataclass(frozen=True)
class Launch:
    attempt_id: str
    jobs: Path
    session_id: str


def _stdout(response: object) -> str:
    if not isinstance(response, dict):
        return ""
    value = response.get("stdout")
    return value if isinstance(value, str) else ""


def _fields(output: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for line in output.splitlines():
        key, separator, value = line.partition("=")
        if not separator or not re.fullmatch(r"[a-z][a-z0-9_.-]*", key):
            continue
        result.setdefault(key, []).append(value)
    return result


def _single(fields: dict[str, list[str]], key: str) -> str | None:
    values = fields.get(key, [])
    return values[0] if len(values) == 1 else None


def parse_launch(payload: object) -> Launch | None:
    """Accept only a successful exact depth-1 owner start from this session."""

    if not isinstance(payload, dict):
        return None
    if payload.get("hook_event_name") != "PostToolUse" or payload.get("tool_name") != "Bash":
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    command = tool_input.get("command")
    if not isinstance(command, str) or "dispatch-owner" not in command:
        return None
    fields = _fields(_stdout(payload.get("tool_response")))
    required_memberships = {
        "check": "ok",
        "status": "start",
        "dispatch_depth": "1",
        "worker_type": "owner",
        "parent_completion_delivery": "claude-parent-runtime",
        "registered": "1",
        "started": "1",
    }
    if any(expected not in fields.get(key, []) for key, expected in required_memberships.items()):
        return None
    attempt_id = _single(fields, "attempt_id")
    jobs_raw = _single(fields, "job_registry")
    parent_session = _single(fields, "parent_session_id")
    payload_session = payload.get("session_id")
    if (
        not isinstance(payload_session, str)
        or not payload_session
        or parent_session != payload_session
        or attempt_id is None
        or ATTEMPT.fullmatch(attempt_id) is None
        or jobs_raw is None
    ):
        return None
    jobs = Path(jobs_raw)
    if not jobs.is_absolute() or jobs.is_symlink() or not jobs.is_file():
        return None
    return Launch(attempt_id=attempt_id, jobs=jobs, session_id=payload_session)


def agent_home() -> Path:
    configured = os.environ.get("AGENT_HOME")
    if configured:
        candidate = Path(configured).expanduser()
        if (candidate / "core" / "CORE.md").is_file():
            return candidate.resolve()
    return Path(__file__).resolve().parents[1]


def _bounded_number(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        return default
    return min(maximum, max(minimum, value))


def wait_for_attempt(launch: Launch, readiness: Path) -> tuple[str, str]:
    interval = _bounded_number(
        "AGENT_CLAUDE_REWAKE_INTERVAL_SECONDS", DEFAULT_INTERVAL_SECONDS, 1, 300
    )
    maximum = _bounded_number(
        "AGENT_CLAUDE_REWAKE_MAX_SECONDS", DEFAULT_MAX_SECONDS, interval, 86_400
    )
    deadline = time.monotonic() + maximum
    command = [
        sys.executable,
        str(readiness),
        "--jobs",
        str(launch.jobs),
        "--attempt-id",
        launch.attempt_id,
    ]
    while True:
        try:
            result = subprocess.run(
                command,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return "bridge-error", type(exc).__name__
        if result.returncode == 0:
            return "ready", "terminal-quiescent"
        if result.returncode == 3:
            return "attention", "terminal-failure-or-unclosed"
        if result.returncode != 2:
            return "bridge-error", f"readiness-exit-{result.returncode}"
        if time.monotonic() >= deadline:
            return "timeout", f"owner-not-quiescent-after-{maximum}s"
        time.sleep(interval)


def receipt(launch: Launch, state: str, reason: str, root: Path) -> str:
    harvest = (
        root / "adapters" / "codex" / "bin" / "preflight.sh"
    )
    return (
        "Runtime owner completion receipt "
        f"schema=1 state={state} attempt_id={launch.attempt_id} reason={reason}. "
        "Do not start or re-arm Background Bash, Monitor, liveness, or dispatch-wait. "
        "Use only the exact checked harvest command: "
        f"{shlex.quote(str(harvest))} harvest --attempt-id "
        f"{shlex.quote(launch.attempt_id)} --mark-done. "
        "Then advance or finish the route without a periodic progress recap."
    )


def main() -> int:
    try:
        payload: Any = json.load(sys.stdin)
    except (OSError, json.JSONDecodeError):
        return 0
    launch = parse_launch(payload)
    if launch is None:
        return 0
    root = agent_home()
    readiness = root / "utilities" / "dispatch-attempt-ready.py"
    if not readiness.is_file():
        print(receipt(launch, "bridge-error", "readiness-helper-missing", root), file=sys.stderr)
        return 2
    state, reason = wait_for_attempt(launch, readiness)
    print(receipt(launch, state, reason, root), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
