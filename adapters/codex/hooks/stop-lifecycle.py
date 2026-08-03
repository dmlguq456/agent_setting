#!/usr/bin/env python3
"""Silent Codex Stop boundary with no completion or lifecycle authority."""

import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


def _worker():
    return (
        os.environ.get("AGENT_SESSION_ROLE", "").lower() == "worker"
        or os.environ.get("AGENT_DISPATCH_CHILD") == "1"
        or bool(os.environ.get("AGENT_DISPATCH_DEPTH"))
        or bool(os.environ.get("OPENCODE_DISPATCH_SLUG"))
        or os.environ.get("FLEET_TITLE_REFRESH") == "1"
        or os.environ.get("MEM_DISTILL") == "1"
    )


def _sid(value):
    if not isinstance(value, dict):
        return ""
    for key in ("session_id", "sessionID", "thread_id", "threadID"):
        item = value.get(key)
        if isinstance(item, str) and item:
            return item
    item = value.get("session")
    if isinstance(item, dict) and isinstance(item.get("id"), str):
        return item["id"]
    for key in ("context", "workspace", "payload", "event", "input", "data"):
        item = _sid(value.get(key))
        if item:
            return item
    return ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        session_id = "" if _worker() else _sid(payload)
        if session_id:
            from fleet import interaction

            interaction.clear_wait(session_id, "codex")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
