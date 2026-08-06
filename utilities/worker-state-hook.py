#!/usr/bin/env python3
"""Runtime-neutral hook bridge for worker ledger writes and compaction."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "utilities" / "worker-state-ledger.py"


def _active() -> bool:
    return (
        os.environ.get("AGENT_DISPATCH_STAGE_AUTHORITY") == "0"
        or bool(os.environ.get("AGENT_DISPATCH_SUBSESSION_ID"))
    )


def _binding() -> tuple[str, str]:
    path = os.environ.get("AGENT_WORKER_STATE_LEDGER", "")
    attempt = os.environ.get("AGENT_DISPATCH_ATTEMPT_ID", "")
    if not path or not attempt:
        raise ValueError("worker sub-session ledger binding missing")
    return path, attempt


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _target_files(payload: dict[str, Any]) -> list[str]:
    cwd = Path(str(payload.get("cwd") or os.getcwd()))
    files: list[str] = []
    for mapping in _walk(payload):
        for key in ("file_path", "filePath", "path", "notebook_path"):
            raw = mapping.get(key)
            if isinstance(raw, str) and raw and raw != "/dev/null":
                path = Path(raw)
                files.append(str((cwd / path).resolve(strict=False) if not path.is_absolute() else path.resolve(strict=False)))
        for key in ("patch", "patchText", "patch_text"):
            patch = mapping.get(key)
            if not isinstance(patch, str):
                continue
            for match in re.finditer(
                r"^\*\*\* (?:Add|Update|Delete) File: (.+)$|^\*\*\* Move to: (.+)$",
                patch, re.MULTILINE,
            ):
                raw = (match.group(1) or match.group(2) or "").strip()
                path = Path(raw)
                files.append(str((cwd / path).resolve(strict=False) if not path.is_absolute() else path.resolve(strict=False)))
    return sorted(set(files))


def _run(action: str, *, file: str = "") -> subprocess.CompletedProcess[str]:
    ledger, attempt = _binding()
    command = [sys.executable, str(LEDGER), action, "--path", ledger, "--attempt-id", attempt]
    if file:
        command += ["--file", file]
    return subprocess.run(command, text=True, capture_output=True, check=False)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("guard-write", "compact-before", "compact-after"))
    args = p.parse_args()
    if not _active():
        return 0
    try:
        if args.action == "guard-write":
            try:
                payload = json.load(sys.stdin)
            except (ValueError, TypeError):
                payload = {}
            files = _target_files(payload if isinstance(payload, dict) else {})
            if not files:
                raise ValueError("worker ledger guard could not determine write target")
            for file in files:
                result = _run("guard-edit", file=file)
                if result.returncode:
                    raise ValueError((result.stderr or result.stdout).strip())
            return 0
        result = _run(args.action)
        if result.returncode:
            raise ValueError((result.stderr or result.stdout).strip())
        if args.action == "compact-after" and result.stdout:
            print(result.stdout, end="")
        return 0
    except ValueError as exc:
        print(f"worker-state-hook: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
