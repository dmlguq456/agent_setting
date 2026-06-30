#!/usr/bin/env python3
"""Codex PostToolUse bridge for portable spec read markers."""

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


def tool_name(payload: dict[str, Any]) -> str:
    tool = nested_mapping(payload, "tool")
    return first_string(payload, "tool_name", "toolName", "matcher") or first_string(tool, "name")


def tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    return nested_mapping(payload, "tool_input", "toolInput", "input", "arguments", "args", "params")


def cwd(payload: dict[str, Any]) -> Path:
    raw = first_string(payload, "cwd", "working_directory", "workingDirectory")
    return Path(raw) if raw else Path.cwd()


def normalize(base: Path, raw: str) -> str:
    if not raw or raw == "/dev/null":
        return ""
    path = Path(raw)
    if not path.is_absolute():
        path = base / path
    return str(path)


def read_target(payload: dict[str, Any]) -> str:
    name = tool_name(payload)
    if name not in {"Read", "read"}:
        return ""
    args = tool_input(payload)
    return normalize(cwd(payload), first_string(args, "file_path", "filePath", "path", "file"))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0

    file = read_target(payload)
    if not file:
        return 0

    session_id = first_string(payload, "session_id", "sessionID", "thread_id", "threadID") or "codex-hook"
    env = os.environ.copy()
    env.setdefault("AGENT_HOME", str(ROOT))
    result = subprocess.run(
        [str(PREFLIGHT), "read", file, session_id],
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
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
