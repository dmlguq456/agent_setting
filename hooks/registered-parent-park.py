#!/usr/bin/env python3
"""Claude PreToolUse enforcement for supervised registered-headless owners."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "utilities"))
from dispatch_completion_join import (  # noqa: E402
    JoinContractError,
    classify_supervised_shell_command,
    current_children,
    read_supervisor_state,
)


def deny(reason: str) -> int:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            },
            separators=(",", ":"),
        )
    )
    return 0


def jobs_path() -> Path:
    override = os.environ.get("AGENT_DISPATCH_JOBS")
    if override:
        return Path(override)
    agent_home = os.environ.get("AGENT_HOME")
    if agent_home and (Path(agent_home) / "core" / "CORE.md").is_file():
        return Path(agent_home) / ".dispatch" / "jobs.log"
    return ROOT / ".dispatch" / "jobs.log"


def mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def main() -> int:
    if os.environ.get("AGENT_DISPATCH_COMPLETION_MODE") != "supervised":
        return 0
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return deny("runtime-supervised-parent: native hook payload is invalid")
    if not isinstance(payload, dict):
        return deny("runtime-supervised-parent: native hook payload is invalid")

    parent_attempt = os.environ.get("AGENT_DISPATCH_ATTEMPT_ID", "")
    if not parent_attempt:
        return deny("runtime-supervised-parent: exact parent attempt is missing")
    registry = jobs_path()
    if not registry.is_file():
        return deny("runtime-supervised-parent: canonical child registry is unavailable")
    try:
        rows = current_children(registry, parent_attempt)
    except JoinContractError:
        return deny("runtime-supervised-parent: exact child registry contract is invalid")
    open_attempts = {
        row.attempt_id for row in rows if row.status in {"open", "running"}
    }
    if not open_attempts:
        return 0

    raw_state = os.environ.get("AGENT_DISPATCH_COMPLETION_STATE_FILE", "")
    delivered = read_supervisor_state(
        Path(raw_state) if raw_state else None,
        parent_attempt,
    )
    tool_name = payload.get("tool_name")
    tool_args = mapping(payload.get("tool_input"))
    command = tool_args.get("command")
    action = None
    if tool_name == "Bash" and isinstance(command, str):
        action = classify_supervised_shell_command(
            base=Path(str(payload.get("cwd") or os.getcwd())),
            command=command,
            open_attempt_ids=open_attempts,
            parent_slug=os.environ.get("AGENT_DISPATCH_SELF_SLUG", ""),
        )

    delivered_open = open_attempts.intersection(delivered or set())
    if delivered is None:
        allowed = bool(action and action.kind == "harvest")
    elif delivered_open:
        allowed = bool(
            action
            and action.kind == "harvest"
            and action.attempt_id in delivered_open
        )
    else:
        allowed = bool(action and action.kind == "dispatch")
    if allowed:
        return 0

    attempts = ",".join(sorted(open_attempts))
    return deny(
        "runtime-supervised-parent: open registered child attempt(s) "
        f"{attempts}; a new undelivered batch admits only another exact "
        "parent-bound dispatch-node start, while a delivered batch admits "
        "only exact preflight harvest"
    )


if __name__ == "__main__":
    raise SystemExit(main())
