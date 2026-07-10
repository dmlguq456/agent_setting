#!/usr/bin/env python3
"""OpenCode dispatch liveness check using OpenCode SQLite session state."""

from __future__ import annotations

import os
import re
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

# SD-15 (OPERATIONS §5.10 ⑨): if an open row's dispatch log shows a limit/auth death
# pattern, judge it DEAD regardless of the SQLite session mtime — this is the axis that
# catches OpenCode's hang-on-limit (#8203), which the wrapper's launch watch cannot.
# Kept in sync with dispatch-headless.py DEATH_PATTERNS (intentional duplication).
LIMIT_RE = re.compile(
    r"hit your (session|usage) limit|session limit reached|usage[_ ]limit[_ ]reached|"
    r"usage limit reached|weekly limit|rate limit(ed)?|provider rate limit|"
    r"exceeded retry limit|[^0-9]429[^0-9]|invalid api key|authentication_error|"
    r"not logged in|please run /login|unauthorized|[^0-9]401[^0-9]|"
    r"credit balance is too low|insufficient (credit|quota|funds)",
    re.I,
)


def log_shows_limit(agent_home: Path, slug: str) -> Path | None:
    """Return the dispatch log path if its tail matches a limit/auth death, else None."""
    if not slug:
        return None
    log_dir = agent_home / ".dispatch" / "logs"
    for lf in sorted(log_dir.glob(f"{slug}.*")):
        if not lf.is_file():
            continue
        try:
            with lf.open("rb") as fh:
                try:
                    fh.seek(-8000, os.SEEK_END)
                except OSError:
                    fh.seek(0)
                tail = fh.read().decode("utf-8", errors="replace")
        except OSError:
            continue
        if LIMIT_RE.search(tail):
            return lf
    return None


def usage() -> int:
    print("usage: dispatch-liveness.py [jobs.log]", file=sys.stderr)
    return 64


def same_path(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if a == b:
        return True
    return os.path.abspath(a) == os.path.abspath(b)


def db_path() -> Path:
    explicit = os.environ.get("OPENCODE_DB")
    if explicit:
        return Path(explicit)
    data_home = os.environ.get("OPENCODE_DATA_HOME")
    if data_home:
        return Path(data_home) / "opencode.db"
    return Path.home() / ".local" / "share" / "opencode" / "opencode.db"


def to_seconds(ts: int | float | None) -> float:
    if ts is None:
        return 0.0
    return float(ts) / 1000.0 if ts > 10_000_000_000 else float(ts)


def locate_latest_for_worktree(con: sqlite3.Connection, worktree: str) -> tuple[str, str, float] | None:
    rows = con.execute(
        """
        SELECT
          s.id,
          s.slug,
          s.directory,
          MAX(
            s.time_updated,
            COALESCE((SELECT MAX(time_updated) FROM message WHERE session_id = s.id), 0),
            COALESCE((SELECT MAX(time_updated) FROM part WHERE session_id = s.id), 0),
            COALESCE((SELECT MAX(time_updated) FROM session_message WHERE session_id = s.id), 0),
            COALESCE((SELECT MAX(time_created) FROM session_input WHERE session_id = s.id), 0)
          ) AS last_updated
        FROM session s
        ORDER BY last_updated DESC
        """,
    )
    for row in rows:
        if same_path(row["directory"], worktree):
            return row["id"], row["slug"] or "", to_seconds(row["last_updated"])
    return None


def heartbeat_age_min(agent_home: Path, slug: str, now: float) -> float | None:
    """Return the heartbeat file age in minutes, or None when no heartbeat exists.

    The plugin agent-harness-guards.js touches
    <agent-home>/.dispatch/logs/<slug>.heartbeat on every session.idle event
    when OPENCODE_DISPATCH_SLUG is set (i.e., the session is a dispatched
    headless worker). A missing or aging heartbeat is a secondary liveness
    signal: it never overrides a fresher OpenCode SQLite mtime, but when the
    SQLite mtime is inconclusive or the working session cannot be located, a
    recent heartbeat is evidence the plugin loaded and reached idle.
    """
    if not slug:
        return None
    hb = agent_home / ".dispatch" / "logs" / f"{slug}.heartbeat"
    try:
        mtime = hb.stat().st_mtime
    except OSError:
        return None
    return (now - mtime) / 60.0


def plugin_loaded_for_slug(agent_home: Path, slug: str) -> bool:
    """True when the plugin-load marker for this dispatch slug exists.

    dispatch-headless.py exports OPENCODE_DISPATCH_SLUG to the runtime child;
    agent-harness-guards.js writes <agent-home>/.dispatch/plugin-load.<slug>.mark
    once at plugin init. A missing marker means the plugin did not load in the
    headless runtime — a strong DEAD signal even when the OpenCode SQLite
    session is alive (the session is running but no harness guards are active).
    """
    if not slug:
        return False
    return (agent_home / ".dispatch" / f"plugin-load.{slug}.mark").is_file()


def main(argv: list[str]) -> int:
    if len(argv) > 2 or (len(argv) == 2 and argv[1] in {"-h", "--help"}):
        return usage()

    agent_home = resolve_agent_home()
    jobs = Path(argv[1]) if len(argv) == 2 else agent_home / ".dispatch" / "jobs.log"
    database = db_path()
    stale_min = int(os.environ.get("DISPATCH_STALE_MIN", "15"))

    if not jobs.is_file():
        print(f"(jobs.log missing: {jobs})")
        return 0
    if not database.is_file():
        print(f"OpenCode DB missing: {database}")
        return 69

    con = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row

    now = time.time()
    open_n = alive = suspect = 0
    with jobs.open(encoding="utf-8") as f:
        for raw in f:
            raw = raw.rstrip("\n")
            if not raw:
                continue
            parts = raw.split("\t")
            while len(parts) < 6:
                parts.append("")
            ts, status, _repo, worktree, slug, _pipe = parts[:6]
            if status != "open":
                continue
            open_n += 1
            label = slug or "?"
            # SD-15: scan the dispatch log for a limit/auth death first — definitive and
            # independent of SQLite mtime; this is what catches hang-on-limit (#8203).
            log_hit = log_shows_limit(agent_home, slug)
            if log_hit is not None:
                print(f"DEAD     {label} - log limit/auth pattern ({log_hit}) [open: {ts}]")
                suspect += 1
                continue
            match = locate_latest_for_worktree(con, worktree)
            if match is None:
                # No SQLite session for this worktree. Fall back to the heartbeat
                # side-channel: a recent heartbeat means the plugin is still
                # touching it on session.idle even though the OpenCode session row
                # is gone or unreadable.
                hb_age = heartbeat_age_min(agent_home, slug, now)
                plugin_marker = plugin_loaded_for_slug(agent_home, slug)
                if hb_age is not None and hb_age <= stale_min:
                    print(f"ALIVE    {label} (heartbeat {hb_age:.1f}m ago; plugin_loaded={plugin_marker})")
                    alive += 1
                    continue
                if not plugin_marker:
                    print(f"DEAD     {label} - OpenCode session not found for {worktree} and no plugin-load marker [open: {ts}]")
                else:
                    print(f"DEAD     {label} - OpenCode session not found for {worktree} [open: {ts}]")
                suspect += 1
                continue
            session_id, session_slug, updated_at = match
            age = int((now - updated_at) // 60)
            detail = f"{session_id}"
            if session_slug:
                detail = f"{session_id}/{session_slug}"
            # Cross-check plugin-load marker: a running SQLite session *without*
            # the marker means the headless runtime loaded OpenCode but the
            # harness plugin did not init — guards are not active, so the run is
            # effectively unguarded even if the process is alive.
            plugin_marker = plugin_loaded_for_slug(agent_home, slug)
            if age <= stale_min:
                marker_note = "" if plugin_marker else " plugin_loaded=false"
                print(f"ALIVE    {label} (OpenCode session {age}m ago: {detail}{marker_note})")
                if not plugin_marker and slug:
                    # Alive but unguarded — flag as SUSPECT so main harvests attention.
                    print(f"  note: no plugin-load marker for {slug}; harness guards likely inactive")
                alive += 1
            else:
                hb_age = heartbeat_age_min(agent_home, slug, now)
                if hb_age is not None and hb_age <= stale_min:
                    print(f"ALIVE    {label} (heartbeat {hb_age:.1f}m ago overrides stale SQLite {age}m: {detail})")
                    alive += 1
                else:
                    print(f"SUSPECT  {label} - OpenCode session {age}m stale: {detail} [open: {ts}]")
                    suspect += 1

    print(f"open {open_n} ; alive {alive} ; suspect/dead {suspect}")
    if suspect:
        print("SUSPECT/DEAD: inspect OpenCode session export/DB and dispatch log, then harvest or redispatch.")
        return 3
    return 0


def resolve_agent_home() -> Path:
    env_home = os.environ.get("AGENT_HOME")
    if env_home and (Path(env_home) / "core" / "CORE.md").is_file():
        return Path(env_home)
    return ROOT


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
