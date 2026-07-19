#!/usr/bin/env python3
"""Watch one exact owner PID and reconcile only a true post-exit orphan."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import time


OPEN = {"open", "running"}


def process_start(pid: int) -> str | None:
    try:
        raw = (Path("/proc") / str(pid) / "stat").read_text(encoding="utf-8")
        tail = raw[raw.rfind(")") + 2:].split()
        return tail[19]
    except (OSError, IndexError):
        return None


def attempt_is_open(jobs: Path, attempt_id: str) -> bool:
    try:
        lines = jobs.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False
    for line in lines:
        fields = line.split("\t")
        if len(fields) != 6:
            continue
        meta = dict(part.split("=", 1) for part in fields[5].split(",") if "=" in part)
        if meta.get("attempt_id") == attempt_id:
            return fields[1] in OPEN
    return False


def watch(args) -> int:
    while True:
        if not attempt_is_open(args.jobs, args.attempt_id):
            return 0
        if process_start(args.pid) != args.pid_start:
            break
        time.sleep(args.interval)
    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().with_name("dispatch-registry.py")),
            "orphan-status",
            "--attempt", args.attempt_id,
            "--jobs", str(args.jobs),
            "--agent-home", str(args.agent_home),
            "--apply",
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=Path, required=True)
    parser.add_argument("--agent-home", type=Path, required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--pid-start", required=True)
    parser.add_argument("--interval", type=float, default=2.0)
    args = parser.parse_args(argv)
    if args.pid <= 0 or args.interval <= 0:
        parser.error("--pid and --interval must be positive")
    args.jobs = args.jobs.resolve()
    args.agent_home = args.agent_home.resolve()
    return watch(args)


if __name__ == "__main__":
    raise SystemExit(main())
