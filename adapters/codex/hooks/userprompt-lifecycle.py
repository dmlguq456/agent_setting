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


def load_payload() -> dict[str, Any]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def cwd(payload: dict[str, Any]) -> str:
    return first_string(payload, "cwd", "working_directory", "workingDirectory") or os.getcwd()


def session_id(payload: dict[str, Any]) -> str:
    return first_string(payload, "session_id", "sessionID", "thread_id", "threadID") or "codex-hook"


def prompt_text(payload: dict[str, Any]) -> str:
    direct = first_string(payload, "prompt", "message", "user_prompt", "userPrompt", "text")
    if direct:
        return direct
    nested = nested_mapping(payload, "input", "payload", "event")
    return first_string(nested, "prompt", "message", "user_prompt", "userPrompt", "text")


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
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)


def main() -> int:
    payload = load_payload()
    current_cwd = cwd(payload)
    sid = session_id(payload)
    prompt = prompt_text(payload)

    run_preflight("mode", current_cwd, sid)
    if prompt:
        run_preflight("recall", prompt, current_cwd)
    run_preflight("briefing", current_cwd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
