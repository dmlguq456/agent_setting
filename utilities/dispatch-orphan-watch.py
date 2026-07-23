#!/usr/bin/env python3
"""Watch one exact owner PID and reconcile only a true post-exit orphan."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys
import time

from dispatch_contract import process_start_ticks
from dispatch_completion_join import remove_supervisor_state


OPEN = {"open", "running"}


def process_start(pid: int) -> str | None:
    return process_start_ticks(pid)


def attempt_status(jobs: Path, attempt_id: str) -> str | None:
    try:
        lines = jobs.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for line in lines:
        fields = line.split("\t")
        if len(fields) != 6:
            continue
        meta = dict(part.split("=", 1) for part in fields[5].split(",") if "=" in part)
        if meta.get("attempt_id") == attempt_id:
            return fields[1]
    return None


def reconcile(args) -> int:
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
    if re.fullmatch(r"att-[A-Za-z0-9._-]{1,240}", args.attempt_id):
        remove_supervisor_state(
            args.agent_home
            / ".dispatch"
            / "supervisor-state"
            / f"{args.attempt_id}.json"
        )
    return result.returncode


def watch(args) -> int:
    while True:
        status = attempt_status(args.jobs, args.attempt_id)
        if status not in OPEN:
            # A prior watcher may have closed the owner and died before its
            # child cascade. orphan-status is idempotent and only continues a
            # row already typed dead-parent-orphaned.
            return reconcile(args) if status == "done" else 0
        if process_start(args.pid) != args.pid_start:
            break
        time.sleep(args.interval)
    return reconcile(args)


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
