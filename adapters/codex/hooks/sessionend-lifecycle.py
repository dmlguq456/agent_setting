#!/usr/bin/env python3
"""Codex SessionEnd/Stop bridge for portable memory lifecycle signals."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PREFLIGHT = ROOT / "adapters" / "codex" / "bin" / "preflight.sh"


def first_string(mapping: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def load_payload() -> dict[str, Any]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def nested_string(payload: dict[str, Any], *keys: str) -> str:
    direct = first_string(payload, *keys)
    if direct:
        return direct
    for key in ("context", "workspace", "session", "payload", "event", "input", "data"):
        value = payload.get(key)
        if isinstance(value, dict):
            found = nested_string(value, *keys)
            if found:
                return found
    return ""


def cwd(payload: dict[str, Any]) -> str:
    return nested_string(payload, "cwd", "working_directory", "workingDirectory") or os.getcwd()


def session_id(payload: dict[str, Any]) -> str:
    sid = nested_string(payload, "session_id", "sessionID", "thread_id", "threadID")
    session = payload.get("session")
    if not sid and isinstance(session, dict):
        sid = first_string(session, "id")
    return sid or "codex-hook"


def run_preflight(*args: str) -> None:
    env = os.environ.copy()
    env.setdefault("AGENT_HOME", str(ROOT))
    result = subprocess.run(
        [str(PREFLIGHT), *args],
        cwd=str(ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.stderr:
        sys.stderr.write(result.stderr)


def spawn_preflight(*args: str) -> None:
    env = os.environ.copy()
    env.setdefault("AGENT_HOME", str(ROOT))
    env.setdefault("CODEX_SESSION_END_BACKGROUND", "1")
    subprocess.Popen(
        [str(PREFLIGHT), *args],
        cwd=str(ROOT),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )


def hook_event(payload: dict[str, Any]) -> str:
    event = os.environ.get("CODEX_HOOK_EVENT", "")
    if event:
        return event
    return nested_string(payload, "hook_event_name", "hookEventName", "event_name", "eventName")


def main() -> int:
    payload = load_payload()
    event_cwd = cwd(payload)
    event_session_id = session_id(payload)
    if hook_event(payload).lower() == "stop":
        # Codex Stop is turn-scoped and timeout-bound. The session-end pipeline can
        # legitimately run a distillation worker, so detach it and return silently.
        spawn_preflight("session-end", event_cwd, event_session_id)
    else:
        run_preflight("session-end", event_cwd, event_session_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
