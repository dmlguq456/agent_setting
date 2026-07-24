#!/usr/bin/env python3
"""Watch one exact owner PID and reconcile its registry row after exit."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys
import time

from dispatch_contract import parse_registry_metadata, process_start_ticks
from dispatch_completion_join import remove_supervisor_state
from dispatch_supervisor_terminal import (
    classify_supervisor_log,
    reconcile_supervisor_terminal,
)


OPEN = {"open", "running"}


def process_start(pid: int) -> str | None:
    return process_start_ticks(pid)


def attempt_record(
    jobs: Path, attempt_id: str
) -> tuple[str | None, dict[str, str]]:
    try:
        lines = jobs.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None, {}
    for line in lines:
        fields = line.split("\t")
        if len(fields) != 6:
            continue
        meta = parse_registry_metadata(fields[5])
        if meta.get("attempt_id") == attempt_id:
            return fields[1], meta
    return None, {}


def attempt_status(jobs: Path, attempt_id: str) -> str | None:
    return attempt_record(jobs, attempt_id)[0]


def _run_registry(operation: str, args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().with_name("dispatch-registry.py")),
            operation,
            "--attempt", args.attempt_id,
            "--jobs", str(args.jobs),
            "--agent-home", str(args.agent_home),
            "--apply",
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _remove_supervisor_state(args) -> None:
    if re.fullmatch(r"att-[A-Za-z0-9._-]{1,240}", args.attempt_id):
        remove_supervisor_state(
            args.agent_home
            / ".dispatch"
            / "supervisor-state"
            / f"{args.attempt_id}.json"
        )


def reconcile_orphan_cascade(args) -> int:
    result = _run_registry("orphan-status", args)
    _remove_supervisor_state(args)
    return result.returncode


def reconcile_exact_exit(args) -> int:
    """Close any exact dead owner, even when it failed before child launch.

    Preserve orphan semantics first so unfinished children are cascaded. For a
    registered supervisor, classify its terminal envelope next so capacity,
    authentication, and protocol failures retain their typed reason. Finally,
    use the general exact-PID reconciler for legacy rows without a supervisor
    envelope. Every transition remains exact-attempt and conditionally atomic.
    """

    orphan_result = _run_registry("orphan-status", args)
    status, metadata = attempt_record(args.jobs, args.attempt_id)

    has_supervisor_envelope = bool(
        metadata.get("harness") or metadata.get("log_file")
    )
    if status in OPEN and has_supervisor_envelope:
        terminal = classify_supervisor_log(
            metadata.get("log_file"), metadata.get("harness", "unknown")
        )
        try:
            reconcile_supervisor_terminal(args.jobs, args.attempt_id, terminal)
        except Exception:
            _remove_supervisor_state(args)
            return 70
        status = attempt_status(args.jobs, args.attempt_id)

    exact_result = None
    if status in OPEN:
        exact_result = _run_registry("reconcile", args)
        status = attempt_status(args.jobs, args.attempt_id)

    _remove_supervisor_state(args)
    if status not in OPEN:
        return 0
    if exact_result is not None and exact_result.returncode:
        return exact_result.returncode
    return orphan_result.returncode or 70


def watch(args) -> int:
    while True:
        status = attempt_status(args.jobs, args.attempt_id)
        if status not in OPEN:
            # A prior watcher may have closed the owner and died before its
            # child cascade. orphan-status is idempotent and only continues a
            # row already typed dead-parent-orphaned.
            return reconcile_orphan_cascade(args) if status == "done" else 0
        if process_start(args.pid) != args.pid_start:
            break
        time.sleep(args.interval)
    return reconcile_exact_exit(args)


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
