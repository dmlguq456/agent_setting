#!/usr/bin/env python3
"""Hold a claimed worker behind a parent-death-safe registry publication gate."""

from __future__ import annotations

import argparse
import ctypes
import os
from pathlib import Path
import signal
import sys

from dispatch_contract import mark_attempt_launch_started


PR_SET_PDEATHSIG = 1


def set_parent_death_signal(signum: int) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(PR_SET_PDEATHSIG, signum, 0, 0, 0) != 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-pid", required=True, type=int)
    parser.add_argument("--gate-fd", required=True, type=int)
    parser.add_argument("--jobs")
    parser.add_argument("--attempt-id")
    parser.add_argument(
        "--post-release-parent-death-signal",
        choices=("none", "term", "kill"),
        default="none",
        help="retain parent-death coupling after publication when lifecycle owns it",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        raise ValueError("launch fence command is required")
    if bool(args.jobs) != bool(args.attempt_id):
        raise ValueError("--jobs and --attempt-id must be provided together")

    set_parent_death_signal(signal.SIGKILL)
    if os.getppid() != args.parent_pid:
        return 70
    try:
        released = os.read(args.gate_fd, 1)
    finally:
        os.close(args.gate_fd)
    if released != b"1":
        return 70
    # Publication is now durable. Detached workers clear parent coupling;
    # foreground-scoped launchers retain an explicit post-release signal.
    post_release_signal = {
        "none": 0,
        "term": signal.SIGTERM,
        "kill": signal.SIGKILL,
    }[args.post_release_parent_death_signal]
    set_parent_death_signal(post_release_signal)
    if post_release_signal and os.getppid() != args.parent_pid:
        return 70
    # Detached fences must clear the short-lived launcher's PDEATHSIG before
    # committing launch_started; if the launcher disappears after this point,
    # the detached fence remains the exact governed process and can still exec.
    # Foreground fences deliberately retain coupling, so parent loss is a
    # terminal launch failure rather than permission to replay the assignment.
    if args.jobs:
        mark_attempt_launch_started(Path(args.jobs), args.attempt_id, os.getpid())
    os.execvpe(command[0], command, os.environ)
    return 70  # pragma: no cover - exec never returns


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"launch-fence: {exc}", file=sys.stderr)
        raise SystemExit(70)
