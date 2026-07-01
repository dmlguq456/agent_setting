#!/usr/bin/env python3
"""Codex PreToolUse bridge for portable write guards."""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PREFLIGHT = ROOT / "adapters" / "codex" / "bin" / "preflight.sh"


def hook_block(reason: str) -> int:
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


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


def tool_name(payload: dict[str, Any]) -> str:
    direct = first_string(payload, "tool_name", "toolName", "matcher")
    if direct:
        return direct
    raw_tool = payload.get("tool")
    if isinstance(raw_tool, str) and raw_tool:
        return raw_tool
    tool = nested_mapping(payload, "tool", "toolUse", "tool_use")
    return first_string(tool, "name", "tool_name", "toolName")


def tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    direct = nested_mapping(payload, "tool_input", "toolInput", "input", "arguments", "args", "params")
    if direct:
        return direct
    tool = nested_mapping(payload, "tool", "toolUse", "tool_use")
    return nested_mapping(tool, "tool_input", "toolInput", "input", "arguments", "args", "params")


def cwd(payload: dict[str, Any]) -> Path:
    raw = nested_string(payload, "cwd", "working_directory", "workingDirectory")
    if raw:
        return Path(raw)
    return Path.cwd()


def normalize(base: Path, raw: str) -> str:
    if not raw or raw == "/dev/null":
        return ""
    path = Path(raw)
    if not path.is_absolute():
        path = base / path
    return str(path)


def patch_files(base: Path, text: str) -> list[str]:
    if not text:
        return []
    files: list[str] = []
    pattern = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$|^\*\*\* Move to: (.+)$", re.MULTILINE)
    for match in pattern.finditer(text):
        raw = match.group(1) or match.group(2) or ""
        file = normalize(base, raw.strip())
        if file:
            files.append(file)
    return files


def is_patch_tool(name: str) -> bool:
    return name in {"apply_patch", "ApplyPatch", "patch", "functions.apply_patch"} or name.endswith(".apply_patch")


def is_shell_tool(name: str) -> bool:
    return name in {"Bash", "bash", "Shell", "shell", "exec_command", "functions.exec_command"} or name.endswith(
        ".exec_command"
    )


def patch_text(payload: dict[str, Any], args: dict[str, Any]) -> str:
    return first_string(args, "patch", "patchText", "patch_text", "input") or first_string(
        payload, "patch", "patchText", "patch_text", "input", "text"
    )


def shell_command(payload: dict[str, Any], args: dict[str, Any]) -> str:
    return first_string(args, "command", "cmd", "script", "input") or first_string(
        payload, "command", "cmd", "script"
    )


def shell_write_files(base: Path, command: str) -> list[str]:
    if not command:
        return []
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return []

    files: list[str] = []
    redirects = {">", ">>", "1>", "1>>", "2>", "2>>", "&>", "&>>", ">|"}
    separators = {"|", "&&", "||", ";"}
    mutation_commands = {"tee", "touch", "cp", "mv", "rm"}

    def add_file(raw: str) -> None:
        file = normalize(base, raw)
        if file:
            files.append(file)

    def split_command_operands(start: int) -> tuple[list[str], int]:
        operands: list[str] = []
        idx = start
        while idx < len(tokens):
            token = tokens[idx]
            if token in separators:
                break
            if token == "--":
                idx += 1
                continue
            if token.startswith("-"):
                idx += 1
                continue
            operands.append(token)
            idx += 1
        return operands, idx

    for idx, token in enumerate(tokens):
        if token in redirects and idx + 1 < len(tokens):
            add_file(tokens[idx + 1])
            continue
        match = re.match(r"^(?:[0-9]?>|[0-9]?>>|&>|&>>|>\|)(.+)$", token)
        if match:
            add_file(match.group(1))

    idx = 0
    while idx < len(tokens):
        command_name = Path(tokens[idx]).name
        if command_name not in mutation_commands:
            idx += 1
            continue

        operands, idx = split_command_operands(idx + 1)
        if command_name == "cp":
            if len(operands) >= 2:
                add_file(operands[-1])
            continue
        for operand in operands:
            add_file(operand)

    return files


def target_files(payload: dict[str, Any]) -> list[str]:
    name = tool_name(payload)
    args = tool_input(payload)
    base = cwd(payload)

    if name in {"Write", "write", "Edit", "edit", "MultiEdit", "multi_edit", "multiedit"}:
        file = normalize(base, first_string(args, "file_path", "filePath", "path", "file"))
        return [file] if file else []

    if is_patch_tool(name):
        return patch_files(base, patch_text(payload, args))

    if is_shell_tool(name):
        return shell_write_files(base, shell_command(payload, args))

    return []


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0

    name = tool_name(payload)
    files = target_files(payload)
    if (name in {"Write", "write", "Edit", "edit", "MultiEdit", "multi_edit", "multiedit"} or is_patch_tool(name)) and not files:
        return hook_block(f"agent harness preflight could not determine target file for Codex tool {name}")

    session_id = nested_string(payload, "session_id", "sessionID", "thread_id", "threadID")
    if not session_id:
        session_id = first_string(nested_mapping(payload, "session"), "id")
    session_id = session_id or "codex-hook"
    env = os.environ.copy()
    env.setdefault("AGENT_HOME", str(ROOT))

    for file in files:
        result = subprocess.run(
            [str(PREFLIGHT), "write", file, session_id],
            cwd=str(ROOT),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            detail = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
            return hook_block(detail or f"agent harness preflight failed for {file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
