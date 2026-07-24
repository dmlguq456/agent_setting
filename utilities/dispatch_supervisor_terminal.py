#!/usr/bin/env python3
"""Typed supervisor terminal classification and exact-attempt reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from dispatch_contract import reconcile_attempt_terminal


CLASSIFIER_SOURCE = "supervisor-terminal-v1"
_MAX_TAIL_BYTES = 1024 * 1024
_HANDOFF_RE = re.compile(
    r"\Aartifact: [^\n]+\n"
    r"verdict: (?P<verdict>PASS|FAIL|BLOCKED)\n"
    r"blocker: (?P<blocker>[^\n]+)\Z"
)
_CAPACITY_RE = re.compile(
    r"(?:reached|hit) your .{0,80}limit|"
    r"session limit|usage limit|weekly limit|rate limit(?:ed)?|"
    r"model.{0,80}at capacity|insufficient quota",
    re.I,
)
_AUTH_RE = re.compile(
    r"authentication_error|invalid api key|not logged in|unauthorized|forbidden",
    re.I,
)
_PROTOCOL_REASON_RE = re.compile(
    r"missing|protocol|schema|shape|json|eof|request-failed|result-invalid|"
    r"thread-start|turn-start-response|join-receipt|contract",
    re.I,
)


@dataclass(frozen=True)
class SupervisorTerminal:
    note: str
    failure_class: str
    terminal_event: str
    reconcile_reason: str
    process_exit: str
    api_status: str = ""

    def evidence(self) -> dict[str, str]:
        values = {
            "classifier_source": CLASSIFIER_SOURCE,
            "detected_by": "completion-supervisor",
            "failure_class": self.failure_class,
            "terminal_event": self.terminal_event,
            "reconcile_reason": self.reconcile_reason,
            "process_exit": self.process_exit,
        }
        if self.api_status:
            values["api_status"] = self.api_status
        return values


def _bounded_strings(value: object) -> list[str]:
    strings: list[str] = []
    pending = [value]
    while pending and len(strings) < 64:
        item = pending.pop()
        if isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item[:64])
        elif isinstance(item, str):
            strings.append(item[:4096])
    return strings


def _api_status(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    pending: list[dict[str, Any]] = [value]
    while pending:
        item = pending.pop()
        for key, raw in item.items():
            if isinstance(raw, dict):
                pending.append(raw)
            elif key in {"api_error_status", "status", "status_code", "http_status"}:
                normalized = str(raw).strip()
                if normalized.isdigit():
                    return normalized
    return ""


def _handoff_terminal(text: object, *, event: str, process_exit: int) -> SupervisorTerminal:
    match = _HANDOFF_RE.fullmatch(text.strip()) if isinstance(text, str) else None
    if match is None:
        return SupervisorTerminal(
            "dead-contract",
            "contract",
            event,
            "final-handoff-invalid",
            str(process_exit),
        )
    verdict = match.group("verdict")
    blocker = match.group("blocker")
    if verdict == "PASS" and blocker != "none":
        return SupervisorTerminal(
            "dead-contract",
            "contract",
            event,
            "pass-blocker-not-none",
            str(process_exit),
        )
    if verdict == "PASS":
        return SupervisorTerminal(
            "completed-supervisor",
            "pass",
            event,
            "exact-final-handoff",
            str(process_exit),
        )
    if verdict == "FAIL":
        return SupervisorTerminal(
            "dead-worker-fail",
            "fail",
            event,
            "worker-reported-fail",
            str(process_exit),
        )
    return SupervisorTerminal(
        "dead-worker-blocked",
        "blocked",
        event,
        "worker-reported-blocked",
        str(process_exit),
    )


def classify_claude_result(
    result: dict[str, Any], process_exit: int
) -> SupervisorTerminal:
    """Classify one final Claude print-mode result without scanning prose success."""

    event = "claude-result"
    is_error = result.get("is_error") is True
    subtype = result.get("subtype")
    if process_exit == 0 and not is_error and subtype in {None, "success"}:
        return _handoff_terminal(
            result.get("result"), event=event, process_exit=process_exit
        )

    status = _api_status(result)
    text = "\n".join(_bounded_strings(result))
    if status == "429":
        return SupervisorTerminal(
            "dead-capacity",
            "capacity",
            event,
            "runtime-capacity-envelope",
            str(process_exit),
            status,
        )
    if status in {"401", "403"}:
        return SupervisorTerminal(
            "dead-auth",
            "auth",
            event,
            "runtime-auth-envelope",
            str(process_exit),
            status,
        )
    if _CAPACITY_RE.search(text):
        return SupervisorTerminal(
            "dead-capacity",
            "capacity",
            event,
            "runtime-capacity-envelope",
            str(process_exit),
            status,
        )
    if _AUTH_RE.search(text):
        return SupervisorTerminal(
            "dead-auth",
            "auth",
            event,
            "runtime-auth-envelope",
            str(process_exit),
            status,
        )
    return SupervisorTerminal(
        "dead-runtime-error",
        "runtime",
        event,
        "runtime-error-envelope",
        str(process_exit),
        status,
    )


def classify_codex_result(final_text: object, process_exit: int = 0) -> SupervisorTerminal:
    if process_exit != 0:
        return SupervisorTerminal(
            "dead-runtime-exit",
            "runtime",
            "turn.completed",
            "app-server-nonzero-exit",
            str(process_exit),
        )
    return _handoff_terminal(
        final_text, event="turn.completed", process_exit=process_exit
    )


def classify_supervisor_error(
    runtime: str,
    reason: str,
    process_exit: int = 70,
) -> SupervisorTerminal:
    failure_class = "protocol" if _PROTOCOL_REASON_RE.search(reason) else "runtime"
    note = "dead-protocol" if failure_class == "protocol" else "dead-runtime-exit"
    return SupervisorTerminal(
        note,
        failure_class,
        "dispatch.supervisor.error",
        reason[:240].replace(",", ";"),
        str(process_exit),
    )


def reconcile_supervisor_terminal(
    jobs: str | Path,
    attempt_id: str,
    terminal: SupervisorTerminal,
) -> str:
    return reconcile_attempt_terminal(
        Path(jobs),
        attempt_id,
        terminal.note,
        evidence=terminal.evidence(),
    )


def _tail_rows(path: Path) -> list[dict[str, Any]]:
    size = path.stat().st_size
    start = max(0, size - _MAX_TAIL_BYTES)
    with path.open("rb") as handle:
        handle.seek(start)
        data = handle.read()
    rows: list[dict[str, Any]] = []
    lines = data.splitlines()
    if start and lines:
        lines = lines[1:]
    for raw in lines:
        try:
            value = json.loads(raw)
        except (UnicodeDecodeError, ValueError):
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def classify_supervisor_log(path: str | Path | None, harness: str) -> SupervisorTerminal:
    """Classify a finished owner's exact log for the post-exit watcher."""

    if not path:
        return classify_supervisor_error(harness, "terminal-log-missing")
    try:
        rows = _tail_rows(Path(path))
    except OSError:
        return classify_supervisor_error(harness, "terminal-log-unreadable")
    for index in range(len(rows) - 1, -1, -1):
        row = rows[index]
        event = row.get("type")
        if event == "result":
            return classify_claude_result(row, 0)
        if event == "turn.completed":
            final_text = None
            for prior in range(index - 1, -1, -1):
                item = rows[prior].get("item")
                if (
                    rows[prior].get("type") == "item.completed"
                    and isinstance(item, dict)
                    and item.get("type") == "agent_message"
                ):
                    final_text = item.get("text")
                    break
            return classify_codex_result(final_text)
        if event == "dispatch.supervisor.error":
            return classify_supervisor_error(
                harness, str(row.get("reason") or "supervisor-error")
            )
    return classify_supervisor_error(harness, "terminal-event-missing")
