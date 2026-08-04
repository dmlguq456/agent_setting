#!/usr/bin/env python3
"""Codex SessionEnd bridge for synchronous lifecycle cleanup."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PREFLIGHT = ROOT / "adapters" / "codex" / "bin" / "preflight.sh"
UTILITIES = ROOT / "utilities"
if str(UTILITIES) not in sys.path:
    sys.path.insert(0, str(UTILITIES))


def first_string(mapping: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


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


def load_payload() -> dict[str, Any]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def is_worker_session() -> bool:
    return (
        os.environ.get("AGENT_SESSION_ROLE", "").lower() == "worker"
        or os.environ.get("AGENT_DISPATCH_CHILD") == "1"
        or bool(os.environ.get("AGENT_DISPATCH_DEPTH"))
        or bool(os.environ.get("OPENCODE_DISPATCH_SLUG"))
        or os.environ.get("FLEET_TITLE_REFRESH") == "1"
        or os.environ.get("MEM_DISTILL") == "1"
    )


def run_preflight(*args: str, quiet: bool = False) -> None:
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
    if result.stderr and not quiet:
        sys.stderr.write(result.stderr)


def main() -> int:
    # SessionEnd owns final synchronous route/memory cleanup. Stop is a
    # separate short bridge and never enters this code path.
    if is_worker_session():
        return 0
    payload = load_payload()
    event_cwd = nested_string(
        payload, "cwd", "working_directory", "workingDirectory"
    ) or os.getcwd()
    event_session_id = nested_string(
        payload, "session_id", "sessionID", "thread_id", "threadID"
    )
    session = payload.get("session")
    if not event_session_id and isinstance(session, dict):
        event_session_id = first_string(session, "id")
    if event_session_id:
        try:
            tools = ROOT / "tools"
            if str(tools) not in sys.path:
                sys.path.insert(0, str(tools))
            from fleet import interaction
            from session_summary_trigger import launch_trigger

            interaction.clear_wait(event_session_id, "codex")
            launch_trigger("codex", event_session_id, "final")
        except Exception:
            pass
    event_session_id = event_session_id or "codex-hook"
    run_preflight("material-route", "clear", "--session", event_session_id, quiet=True)
    run_preflight("session-end", event_cwd, event_session_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
