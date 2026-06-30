#!/usr/bin/env python3
"""Codex dispatch liveness check using Codex session JSONL mtimes."""

from __future__ import annotations

import json
import os
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


def transcript_cwd(path: Path) -> str | None:
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                if '"cwd"' not in line:
                    continue
                try:
                    payload = (json.loads(line).get("payload") or {})
                except Exception:
                    continue
                cwd = payload.get("cwd")
                if isinstance(cwd, str) and cwd:
                    return cwd
    except OSError:
        return None
    return None


def locate_latest_for_worktree(sessions: Path, worktree: str) -> Path | None:
    if not sessions.is_dir():
        return None
    try:
        candidates = sorted(
            sessions.glob("**/*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return None
    for path in candidates:
        if same_path(transcript_cwd(path) or "", worktree):
            return path
    return None


def main(argv: list[str]) -> int:
    if len(argv) > 2 or (len(argv) == 2 and argv[1] in {"-h", "--help"}):
        return usage()

    agent_home = Path(os.environ.get("AGENT_HOME", os.getcwd()))
    jobs = Path(argv[1]) if len(argv) == 2 else agent_home / ".dispatch" / "jobs.log"
    sessions = Path(os.environ.get("CODEX_SESSIONS", Path.home() / ".codex" / "sessions"))
    stale_min = int(os.environ.get("DISPATCH_STALE_MIN", "15"))

    if not jobs.is_file():
        print(f"(jobs.log missing: {jobs})")
        return 0

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
            transcript = locate_latest_for_worktree(sessions, worktree)
            if transcript is None:
                print(f"DEAD     {label} - Codex session transcript not found for {worktree} [open: {ts}]")
                suspect += 1
                continue
            age = int((now - transcript.stat().st_mtime) // 60)
            if age <= stale_min:
                print(f"ALIVE    {label} (Codex transcript {age}m ago: {transcript})")
                alive += 1
            else:
                print(f"SUSPECT  {label} - Codex transcript {age}m stale [open: {ts}]")
                suspect += 1

    print(f"open {open_n} ; alive {alive} ; suspect/dead {suspect}")
    if suspect:
        print("SUSPECT/DEAD: inspect Codex transcript and dispatch log, then harvest or redispatch.")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
