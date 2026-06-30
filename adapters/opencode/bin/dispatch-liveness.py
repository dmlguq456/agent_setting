#!/usr/bin/env python3
"""OpenCode dispatch liveness check using OpenCode SQLite session state."""

from __future__ import annotations

import os
import sqlite3
import sys
import time
from pathlib import Path


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


def main(argv: list[str]) -> int:
    if len(argv) > 2 or (len(argv) == 2 and argv[1] in {"-h", "--help"}):
        return usage()

    agent_home = Path(os.environ.get("AGENT_HOME", os.getcwd()))
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
            match = locate_latest_for_worktree(con, worktree)
            if match is None:
                print(f"DEAD     {label} - OpenCode session not found for {worktree} [open: {ts}]")
                suspect += 1
                continue
            session_id, session_slug, updated_at = match
            age = int((now - updated_at) // 60)
            detail = f"{session_id}"
            if session_slug:
                detail = f"{session_id}/{session_slug}"
            if age <= stale_min:
                print(f"ALIVE    {label} (OpenCode session {age}m ago: {detail})")
                alive += 1
            else:
                print(f"SUSPECT  {label} - OpenCode session {age}m stale: {detail} [open: {ts}]")
                suspect += 1

    print(f"open {open_n} ; alive {alive} ; suspect/dead {suspect}")
    if suspect:
        print("SUSPECT/DEAD: inspect OpenCode session export/DB and dispatch log, then harvest or redispatch.")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
