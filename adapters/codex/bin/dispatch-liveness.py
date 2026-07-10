#!/usr/bin/env python3
"""Codex dispatch liveness check using Codex session JSONL mtimes."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

# SD-15 (OPERATIONS §5.10 ⑨): if an open row's dispatch log shows a limit/auth death
# pattern, judge it DEAD regardless of transcript mtime (the wrapper's launch watch may
# have missed it, or the child died — or hung, OpenCode #8203 — after launch). Kept in
# sync with dispatch-headless.py DEATH_PATTERNS (intentional cross-runtime duplication).
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


def parse_profile(pipe: str) -> str | None:
    """Extract profile=<name> from the jobs.log 6th (pipe) field.

    Replicates utilities/dispatch-liveness.sh:23 semantics: last ``profile=``
    occurrence, comma-terminated. Returns None when absent (non-profile job).
    """
    if not pipe or "profile=" not in pipe:
        return None
    name = pipe.split("profile=")[-1].split(",")[0].strip()
    return name or None


def sessions_dir_for(pipe: str, slug: str, agent_home: Path, default_sessions: Path) -> Path:
    """Resolve the Codex session store for one job.

    A ``--profile`` dispatch runs under CODEX_HOME=.dispatch/homes/<slug>.<profile>
    (dispatch-headless.py), so its transcripts land in that home's ``sessions/``,
    not ~/.codex/sessions. Isomorphic to portable dispatch-liveness.sh:22-28 and
    fleet collectors/dispatch.py, adapted to the Codex ``sessions/`` layout (the
    sh helper's ``projects/<enc>`` is Claude-shaped). Non-profile jobs keep the
    default store (byte-behavior for existing callers).
    """
    prof = parse_profile(pipe)
    if prof:
        return agent_home / ".dispatch" / "homes" / f"{slug}.{prof}" / "sessions"
    return default_sessions


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

    agent_home = resolve_agent_home()
    jobs = Path(argv[1]) if len(argv) == 2 else agent_home / ".dispatch" / "jobs.log"
    default_sessions = Path(os.environ.get("CODEX_SESSIONS", Path.home() / ".codex" / "sessions"))
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
            ts, status, _repo, worktree, slug, pipe = parts[:6]
            if status != "open":
                continue
            open_n += 1
            label = slug or "?"
            # SD-15: scan the dispatch log for a limit/auth death first — a limit death is
            # definitive and independent of transcript mtime (catches the hang case too).
            log_hit = log_shows_limit(agent_home, slug)
            if log_hit is not None:
                print(f"DEAD     {label} - log limit/auth pattern ({log_hit}) [open: {ts}]")
                suspect += 1
                continue
            # Resolve per-job: a profile= job lives under its isolated profile home
            # (.dispatch/homes/<slug>.<profile>/sessions), else the default store.
            sessions = sessions_dir_for(pipe, slug, agent_home, default_sessions)
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


def resolve_agent_home() -> Path:
    env_home = os.environ.get("AGENT_HOME")
    if env_home and (Path(env_home) / "core" / "CORE.md").is_file():
        return Path(env_home)
    return ROOT


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
