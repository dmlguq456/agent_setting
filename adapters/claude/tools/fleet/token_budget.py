"""Portable token/context telemetry primitives.

This module keeps *active context* separate from cumulative session counters.
The distinction matters because legacy ``Session.tokens`` has different meanings
across collectors and is therefore not a valid policy signal.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


CODEX_BASELINE_TOKENS = 12_000
DEFAULT_TIGHT_PCT = 70
DEFAULT_CRITICAL_PCT = 85
DEFAULT_MAX_AGE_SECONDS = 86_400

_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$")


def _counter(value) -> Optional[int]:
    if isinstance(value, (int, float)) and value >= 0:
        return int(value)
    return None


@dataclass
class TokenTelemetry:
    """Normalized read-only session telemetry; ``None`` means not exposed."""

    adapter: str = "portable"
    status: str = "unknown"
    reason: Optional[str] = None
    session_id: Optional[str] = None
    signal_source: Optional[str] = None
    signal_age_seconds: Optional[int] = None
    active_context_tokens: Optional[int] = None
    context_window_tokens: Optional[int] = None
    context_used_pct: Optional[int] = None
    session_input_tokens: Optional[int] = None
    session_cached_input_tokens: Optional[int] = None
    session_output_tokens: Optional[int] = None
    session_reasoning_output_tokens: Optional[int] = None
    session_total_tokens: Optional[int] = None

    def to_dict(self) -> dict:
        return asdict(self)


def codex_context_used_pct(active_context_tokens, context_window_tokens) -> Optional[int]:
    """Mirror Codex's 12k reserve formula used by the native TUI."""

    active = _counter(active_context_tokens)
    window = _counter(context_window_tokens)
    if active is None or window is None or window <= CODEX_BASELINE_TOKENS:
        return None
    effective_window = window - CODEX_BASELINE_TOKENS
    used = max(0, active - CODEX_BASELINE_TOKENS)
    return min(99, round(100.0 * used / effective_window))


def policy_band(context_used_pct, tight_pct=DEFAULT_TIGHT_PCT,
                critical_pct=DEFAULT_CRITICAL_PCT) -> str:
    """Return ``unknown|normal|tight|critical`` for a normalized context %."""

    if not isinstance(tight_pct, int) or not isinstance(critical_pct, int):
        raise ValueError("thresholds must be integers")
    if not 0 < tight_pct < critical_pct <= 100:
        raise ValueError("thresholds must satisfy 0 < tight < critical <= 100")
    if not isinstance(context_used_pct, (int, float)):
        return "unknown"
    if context_used_pct >= critical_pct:
        return "critical"
    if context_used_pct >= tight_pct:
        return "tight"
    return "normal"


def telemetry_from_explicit(*, adapter="portable", session_id=None,
                            active_context_tokens=None, context_window_tokens=None,
                            session_input_tokens=None, session_cached_input_tokens=None,
                            session_output_tokens=None,
                            session_reasoning_output_tokens=None,
                            session_total_tokens=None) -> TokenTelemetry:
    active = _counter(active_context_tokens)
    window = _counter(context_window_tokens)
    telemetry = TokenTelemetry(
        adapter=adapter,
        status="observed" if active is not None and window is not None else "unknown",
        reason=None if active is not None and window is not None else "missing-context-signal",
        session_id=session_id,
        signal_source="explicit",
        active_context_tokens=active,
        context_window_tokens=window,
        session_input_tokens=_counter(session_input_tokens),
        session_cached_input_tokens=_counter(session_cached_input_tokens),
        session_output_tokens=_counter(session_output_tokens),
        session_reasoning_output_tokens=_counter(session_reasoning_output_tokens),
        session_total_tokens=_counter(session_total_tokens),
    )
    if adapter == "codex":
        telemetry.context_used_pct = codex_context_used_pct(active, window)
    elif active is not None and window:
        telemetry.context_used_pct = min(99, round(100.0 * active / window))
    if telemetry.context_used_pct is None:
        telemetry.status = "unknown"
        telemetry.reason = "invalid-context-window"
    return telemetry


def parse_codex_token_count(line: str, *, session_id=None,
                            signal_age_seconds=None) -> TokenTelemetry:
    """Parse one Codex ``token_count`` JSONL event without exposing content."""

    unknown = TokenTelemetry(adapter="codex", session_id=session_id,
                             signal_source="codex-rollout")
    try:
        event = json.loads(line)
    except (TypeError, json.JSONDecodeError):
        unknown.reason = "malformed-token-count"
        return unknown
    payload = event.get("payload") if isinstance(event, dict) else None
    if not isinstance(payload, dict) or payload.get("type") != "token_count":
        unknown.reason = "not-token-count"
        return unknown
    info = payload.get("info") if isinstance(payload, dict) else None
    if not isinstance(info, dict):
        unknown.reason = "missing-token-info"
        return unknown
    last = info.get("last_token_usage") or {}
    total = info.get("total_token_usage") or {}
    telemetry = telemetry_from_explicit(
        adapter="codex",
        session_id=session_id,
        active_context_tokens=last.get("total_tokens"),
        context_window_tokens=info.get("model_context_window"),
        session_input_tokens=total.get("input_tokens"),
        session_cached_input_tokens=total.get("cached_input_tokens"),
        session_output_tokens=total.get("output_tokens"),
        session_reasoning_output_tokens=total.get("reasoning_output_tokens"),
        session_total_tokens=total.get("total_tokens"),
    )
    telemetry.signal_source = "codex-rollout"
    telemetry.signal_age_seconds = _counter(signal_age_seconds)
    return telemetry


def tail_codex_token_count(path: Path, chunk=262_144) -> Optional[str]:
    """Return the last token-count event from a bounded rollout tail."""

    try:
        size = path.stat().st_size
        start = max(0, size - chunk)
        with path.open("rb") as handle:
            handle.seek(start)
            data = handle.read().decode("utf-8", "replace")
    except OSError:
        return None
    lines = data.splitlines()
    if start > 0 and lines:
        lines = lines[1:]
    for line in reversed(lines):
        if '"token_count"' not in line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        payload = event.get("payload") if isinstance(event, dict) else None
        if (isinstance(payload, dict) and payload.get("type") == "token_count"
                and isinstance(payload.get("info"), dict)):
            return line
    return None


def codex_event_epoch(line: str) -> Optional[float]:
    """Return a token-count event timestamp, or ``None`` for legacy rows."""

    try:
        event = json.loads(line)
    except (TypeError, json.JSONDecodeError):
        return None
    value = event.get("timestamp") if isinstance(event, dict) else None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except ValueError:
        return None


def find_codex_rollout(codex_home: Path, session_id: str) -> tuple[Optional[Path], str]:
    """Find exactly one rollout whose filename ends with the exact session id."""

    if not isinstance(session_id, str) or not _SESSION_ID_RE.fullmatch(session_id):
        return None, "invalid-session-id"
    root = codex_home / "sessions"
    try:
        candidates = [
            path for path in root.rglob("rollout-*.jsonl")
            if path.name.endswith("-" + session_id + ".jsonl")
        ]
    except OSError:
        return None, "session-store-unavailable"
    if not candidates:
        return None, "session-not-found"
    if len(candidates) != 1:
        return None, "ambiguous-session"
    return candidates[0], "ok"


def telemetry_from_codex_session(session_id: str, *, codex_home=None,
                                 max_age_seconds=DEFAULT_MAX_AGE_SECONDS,
                                 now=None) -> TokenTelemetry:
    home = Path(codex_home or os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    path, reason = find_codex_rollout(home, session_id)
    if path is None:
        return TokenTelemetry(adapter="codex", session_id=session_id,
                              signal_source="codex-rollout", reason=reason)
    now = time.time() if now is None else now
    try:
        file_age = max(0, int(now - path.stat().st_mtime))
    except OSError:
        return TokenTelemetry(adapter="codex", session_id=session_id,
                              signal_source="codex-rollout", reason="rollout-unreadable")
    line = tail_codex_token_count(path)
    if line is None:
        return TokenTelemetry(adapter="codex", session_id=session_id,
                              signal_source="codex-rollout", signal_age_seconds=file_age,
                              reason="token-count-not-found")
    event_epoch = codex_event_epoch(line)
    age = max(0, int(now - event_epoch)) if event_epoch is not None else file_age
    if max_age_seconds is not None and age > max_age_seconds:
        return TokenTelemetry(adapter="codex", session_id=session_id,
                              signal_source="codex-rollout", signal_age_seconds=age,
                              reason="stale-signal")
    return parse_codex_token_count(line, session_id=session_id,
                                   signal_age_seconds=age)
