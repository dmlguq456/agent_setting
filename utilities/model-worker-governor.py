#!/usr/bin/env python3
"""Shared admission control for repository-launched model workers."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable


CLASS_LIMITS = {"dispatch": 3, "distill": 1, "title": 1, "loop": 2}
START_WINDOW_SECONDS = 600
DEFAULT_TOTAL_LIMIT = 5
DEFAULT_START_BUDGET = 20


def default_root() -> Path:
    """Return a path writable by both the main checkout and linked workers."""
    explicit = os.environ.get("AGENT_MODEL_GOVERNOR_ROOT")
    if explicit:
        return Path(explicit)
    artifact_root = os.environ.get("AGENT_ARTIFACT_ROOT")
    if artifact_root:
        return Path(artifact_root) / ".runtime" / "model-worker-governor"
    resolver = Path(__file__).resolve().with_name("artifact-root.sh")
    if resolver.is_file():
        resolved = subprocess.run(
            [str(resolver), str(Path.cwd())],
            check=False,
            capture_output=True,
            text=True,
        )
        if resolved.returncode == 0 and resolved.stdout.strip():
            return Path(resolved.stdout.strip()) / ".runtime" / "model-worker-governor"
    return Path.home() / ".agent-worker-governor"


def process_starttime(pid: int) -> str | None:
    """Read Linux starttime without being confused by spaces in ``comm``."""
    try:
        raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
        tail = raw[raw.rfind(")") + 2 :].split()
        return tail[19]
    except (OSError, IndexError):
        return None


def _limits(total: int | None, budget: int | None) -> tuple[int, int]:
    total = total if total is not None else int(os.environ.get("AGENT_MODEL_WORKER_TOTAL", DEFAULT_TOTAL_LIMIT))
    budget = budget if budget is not None else int(os.environ.get("AGENT_MODEL_WORKER_START_BUDGET", DEFAULT_START_BUDGET))
    if total < 1 or budget < 1:
        raise ValueError("model-worker limits must be positive")
    return total, budget


def _state_change(root: str | Path, fn: Callable[[dict[str, Any], float], Any]) -> Any:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    state_path = root / "state.json"
    with (root / "lock").open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            data = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {
                "schema_version": 1,
                "leases": {},
                "starts": [],
            }
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"invalid governor state: {exc}") from exc

        now = time.time()
        data["starts"] = [stamp for stamp in data.get("starts", []) if now - stamp < START_WINDOW_SECONDS]
        data["leases"] = {
            token: lease
            for token, lease in data.get("leases", {}).items()
            if process_starttime(int(lease["pid"])) == str(lease["starttime"])
        }
        result = fn(data, now)
        tmp = root / "state.tmp"
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, state_path)
        return result


def _assert_available(
    root: str | Path,
    data: dict[str, Any],
    worker_class: str,
    total: int,
    budget: int,
) -> None:
    root = Path(root)
    if worker_class not in CLASS_LIMITS:
        raise ValueError("unknown worker class")
    if os.environ.get("AGENT_MODEL_WORKERS_DISABLED") == "1" or (root / "KILL_SWITCH").exists():
        raise ValueError("model-worker kill switch active")
    leases = data["leases"]
    if len(leases) >= total:
        raise ValueError("global model-worker cap reached")
    if sum(lease["class"] == worker_class for lease in leases.values()) >= CLASS_LIMITS[worker_class]:
        raise ValueError(f"{worker_class} class cap reached")
    if len(data["starts"]) >= budget:
        raise ValueError("rolling model-worker start budget reached")


def check(root: str | Path, worker_class: str, *, total: int | None = None, budget: int | None = None) -> None:
    """Check admission without consuming a rolling-start budget entry."""
    total, budget = _limits(total, budget)
    _state_change(root, lambda data, now: _assert_available(root, data, worker_class, total, budget))


def acquire(
    root: str | Path,
    worker_class: str,
    pid: int | None = None,
    *,
    total: int | None = None,
    budget: int | None = None,
) -> str:
    total, budget = _limits(total, budget)
    pid = pid or os.getpid()
    starttime = process_starttime(pid)
    if starttime is None:
        raise ValueError("requesting process identity unavailable")

    def operation(data: dict[str, Any], now: float) -> str:
        _assert_available(root, data, worker_class, total, budget)
        token = secrets.token_hex(16)
        data["leases"][token] = {
            "class": worker_class,
            "pid": pid,
            "starttime": starttime,
            "acquired_at": now,
        }
        data["starts"].append(now)
        return token

    return _state_change(root, operation)


def release(root: str | Path, token: str) -> None:
    _state_change(root, lambda data, now: data["leases"].pop(token, None))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(default_root()))
    commands = parser.add_subparsers(dest="command", required=True)
    acquire_parser = commands.add_parser("acquire")
    acquire_parser.add_argument("--class", dest="worker_class", required=True)
    acquire_parser.add_argument("--pid", type=int)
    check_parser = commands.add_parser("check")
    check_parser.add_argument("--class", dest="worker_class", required=True)
    release_parser = commands.add_parser("release")
    release_parser.add_argument("--token", required=True)
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--class", dest="worker_class", required=True)
    run_parser.add_argument("command_argv", nargs=argparse.REMAINDER)
    commands.add_parser("status")
    args = parser.parse_args()

    if args.command == "acquire":
        print(acquire(args.root, args.worker_class, args.pid))
    elif args.command == "check":
        check(args.root, args.worker_class)
        print("governor=available")
    elif args.command == "release":
        release(args.root, args.token)
    elif args.command == "status":
        print(json.dumps(_state_change(args.root, lambda data, now: data), sort_keys=True))
    else:
        command = args.command_argv[1:] if args.command_argv[:1] == ["--"] else args.command_argv
        if not command:
            raise ValueError("worker command is required")
        token = acquire(args.root, args.worker_class)
        try:
            return subprocess.run(command, check=False).returncode
        finally:
            release(args.root, token)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"model-worker-governor: {exc}", file=sys.stderr)
        raise SystemExit(75)
