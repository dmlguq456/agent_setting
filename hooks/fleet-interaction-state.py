#!/usr/bin/env python3
"""Publish privacy-minimal Claude interaction waits for Fleet.

This side-effect hook accepts the Claude hook payload but delegates state
semantics to the runtime-neutral ``fleet.interaction`` codec. It never returns
a Claude decision and never writes stdout.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


def _worker_session():
    return (
        os.environ.get("AGENT_SESSION_ROLE", "").lower() == "worker"
        or os.environ.get("AGENT_DISPATCH_CHILD") == "1"
        or bool(os.environ.get("AGENT_DISPATCH_DEPTH"))
        or bool(os.environ.get("OPENCODE_DISPATCH_SLUG"))
        or os.environ.get("FLEET_TITLE_REFRESH") == "1"
        or os.environ.get("MEM_DISTILL") == "1"
    )


def _payload():
    try:
        value = json.load(sys.stdin)
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def main():
    try:
        payload = _payload()
        if _worker_session() or payload.get("agent_id"):
            return 0
        session_id = payload.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            return 0
        from fleet import interaction

        action = sys.argv[1] if len(sys.argv) > 1 else ""
        if action == "clear":
            interaction.clear_wait(session_id, "claude")
            return 0
        if action != "set" or len(sys.argv) != 4 or sys.argv[2] != "--kind":
            return 0
        kind = sys.argv[3]
        source = {
            "decision": "claude-asktool",
            "permission": "claude-permission",
        }.get(kind)
        if source:
            interaction.set_wait(session_id, "claude", kind, source)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
