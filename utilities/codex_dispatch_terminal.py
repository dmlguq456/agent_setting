#!/usr/bin/env python3
"""Exact Codex dispatch-log terminal handoff inspection.

This parser is intentionally attempt-log scoped. It never searches by cwd,
slug, or newest transcript, so another worker cannot supply terminal evidence
for the registered attempt.
"""

from __future__ import annotations

import json
from pathlib import Path
import re


_HANDOFF_RE = re.compile(
    r"\Aartifact: (?P<artifact>[^\n]+)\n"
    r"verdict: (?P<verdict>PASS|FAIL|BLOCKED)\n"
    r"blocker: (?P<blocker>[^\n]+)\Z"
)
_SANDBOX_INIT_RE = re.compile(
    r"bwrap: Can't bind mount [^\n]+ on [^\n]+/\.codex:"
    r"[^\n]*Unable to mount source on destination: No such file or directory",
    re.I,
)
_MAX_TAIL_BYTES = 1024 * 1024


def _tail_lines(path: Path) -> list[str]:
    size = path.stat().st_size
    start = max(0, size - _MAX_TAIL_BYTES)
    with path.open("rb") as handle:
        handle.seek(start)
        data = handle.read()
    lines = data.splitlines()
    if start and lines:
        lines = lines[1:]
    return [line.decode("utf-8", "replace") for line in lines]


def inspect_terminal_log(path: str | Path | None) -> dict[str, str] | None:
    """Return a validated final handoff, or ``None`` when evidence is ambiguous."""

    if not path:
        return None
    log_path = Path(path)
    try:
        lines = _tail_lines(log_path)
    except OSError:
        return None

    rows: list[dict] = []
    for line in lines:
        try:
            value = json.loads(line)
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            rows.append(value)

    terminal_index = next(
        (
            index
            for index in range(len(rows) - 1, -1, -1)
            if rows[index].get("type") == "turn.completed"
        ),
        None,
    )
    if terminal_index is None:
        return None

    handoff = None
    for row in reversed(rows[:terminal_index]):
        if row.get("type") != "item.completed":
            continue
        item = row.get("item")
        if not isinstance(item, dict) or item.get("type") != "agent_message":
            continue
        text = item.get("text")
        match = _HANDOFF_RE.fullmatch(text.strip()) if isinstance(text, str) else None
        if match:
            handoff = match.groupdict()
        break
    if handoff is None:
        return None

    sandbox_init = False
    for row in rows[:terminal_index]:
        if row.get("type") != "item.completed":
            continue
        item = row.get("item")
        if not isinstance(item, dict) or item.get("type") != "command_execution":
            continue
        output = item.get("aggregated_output")
        if (
            item.get("exit_code") not in (None, 0)
            and isinstance(output, str)
            and _SANDBOX_INIT_RE.search(output)
        ):
            sandbox_init = True
            break

    verdict = handoff["verdict"]
    if verdict == "BLOCKED":
        note = "dead-sandbox-init" if sandbox_init else "dead-worker-blocked"
    elif verdict == "FAIL":
        note = "dead-worker-fail"
    else:
        note = ""
    return {
        **handoff,
        "failure_note": note,
        "failure_class": "sandbox-init" if sandbox_init else verdict.lower(),
        "terminal_event": "turn.completed",
        "log_file": str(log_path),
    }
