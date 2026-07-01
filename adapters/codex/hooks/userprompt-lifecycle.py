#!/usr/bin/env python3
"""Codex UserPromptSubmit bridge for portable prompt lifecycle signals."""

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


def nested_mapping(payload: dict[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


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


def text_from_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(part for item in value if (part := text_from_value(item)))
    if isinstance(value, dict):
        direct = first_string(value, "prompt", "message", "user_prompt", "userPrompt", "text")
        if direct:
            return direct
        for key in ("content", "messages", "input", "payload", "event", "data"):
            text = text_from_value(value.get(key))
            if text:
                return text
    return ""


def load_payload() -> dict[str, Any]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def cwd(payload: dict[str, Any]) -> str:
    return nested_string(payload, "cwd", "working_directory", "workingDirectory") or os.getcwd()


def session_id(payload: dict[str, Any]) -> str:
    sid = nested_string(payload, "session_id", "sessionID", "thread_id", "threadID")
    session = payload.get("session")
    if not sid and isinstance(session, dict):
        sid = first_string(session, "id")
    return sid or "codex-hook"


def prompt_text(payload: dict[str, Any]) -> str:
    for key in ("prompt", "message", "user_prompt", "userPrompt", "text", "content", "messages", "input", "payload", "event", "data"):
        text = text_from_value(payload.get(key))
        if text:
            return text
    return ""


def run_preflight(*args: str) -> str:
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
    return result.stdout


def emit_context(event_name: str, parts: list[str]) -> None:
    context = "\n".join(part.strip() for part in parts if part.strip())
    if not context:
        return
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event_name, "additionalContext": context}}, ensure_ascii=False))


def main() -> int:
    payload = load_payload()
    current_cwd = cwd(payload)
    sid = session_id(payload)
    prompt = prompt_text(payload)

    parts = [
        run_preflight("status", current_cwd, sid),
        run_preflight("prompt-signal", current_cwd, sid),
        run_preflight("mode", current_cwd, sid),
    ]
    if prompt:
        parts.append(run_preflight("recall", prompt, current_cwd))
    parts.append(run_preflight("briefing", current_cwd))
    run_preflight("turn-nudge", current_cwd, sid)
    emit_context("UserPromptSubmit", parts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
