#!/usr/bin/env python3
"""Codex PostToolUse bridge for portable design post-write checks."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PREFLIGHT = ROOT / "adapters" / "codex" / "bin" / "preflight.sh"
DESIGN_RE = re.compile(r"(designs?/|/design/|spec/design|preview\.html$|slides?\.html$|03_components|scaffolds/)")


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
    raw = first_string(payload, "cwd", "working_directory", "workingDirectory")
    return Path(raw) if raw else Path.cwd()


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


def patch_text(payload: dict[str, Any], args: dict[str, Any]) -> str:
    return first_string(args, "patch", "patchText", "patch_text", "input") or first_string(
        payload, "patch", "patchText", "patch_text", "input", "text"
    )


def target_files(payload: dict[str, Any]) -> list[str]:
    name = tool_name(payload)
    args = tool_input(payload)
    base = cwd(payload)

    if name in {"Write", "write", "Edit", "edit", "MultiEdit", "multi_edit", "multiedit"}:
        file = normalize(base, first_string(args, "file_path", "filePath", "path", "file"))
        return [file] if file else []

    if is_patch_tool(name):
        return patch_files(base, patch_text(payload, args))

    return []


def is_design_html(file: str) -> bool:
    return bool(re.search(r"\.html?$", file, re.IGNORECASE) and DESIGN_RE.search(file.replace(os.sep, "/")))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0

    env = os.environ.copy()
    env.setdefault("AGENT_HOME", str(ROOT))
    rc = 0

    for file in target_files(payload):
        if not is_design_html(file):
            continue
        result = subprocess.run(
            [str(PREFLIGHT), "design", file],
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
        rc = max(rc, result.returncode)

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
