#!/usr/bin/env python3
"""Run the D-42 daily memory-curator catch-up with project cursors.

This orchestrator owns only deterministic discovery, event windows, cursor
durability, and receipts. Semantic actions come from the same no-tools curator
worker used by the session-end dispatcher and remain bounded by the shared
applier plus mem.py's project/pending/graveyard gates.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MEM = ROOT / "tools" / "memory" / "mem.py"
DEFAULT_DISPATCHER = ROOT / "hooks" / "mem-distill-dispatch.sh"
EXCLUDED_DIRS = {".git", "node_modules", "backup", "backups"}


def parse_time(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value)
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed.replace(microsecond=0)


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(value, fh, sort_keys=True, ensure_ascii=False, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


def load_json(path: Path, default: dict) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else default
    except (OSError, json.JSONDecodeError):
        return default


def is_excluded(name: str) -> bool:
    lower = name.lower()
    return name in EXCLUDED_DIRS or name.startswith("_layer2") or lower.startswith("backup")


def discover_projects(roots: list[Path], max_depth: int = 3) -> list[Path]:
    found: set[Path] = set()
    for root in roots:
        try:
            root = root.expanduser().resolve()
        except OSError:
            continue
        if not root.is_dir():
            continue
        if (root / ".git").exists():
            found.add(root)
        for current, dirs, _files in os.walk(root):
            cur = Path(current)
            try:
                depth = len(cur.relative_to(root).parts)
            except ValueError:
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if not is_excluded(d)]
            if depth >= max_depth:
                dirs[:] = []
            if (cur / ".git").exists():
                found.add(cur)
                dirs[:] = []
    return sorted(found, key=lambda p: str(p))[:200]


def run(argv: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=str(cwd), env=env, capture_output=True,
                          text=True, timeout=timeout)


def project_key(mem: Path, cwd: Path, env: dict[str, str]) -> str:
    try:
        result = run([sys.executable, str(mem), "project-key"], cwd=cwd, env=env)
    except subprocess.TimeoutExpired:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def cursor_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def bounded_error(result: subprocess.CompletedProcess | None, fallback: str) -> str:
    if result is None:
        return fallback
    text = (result.stderr or result.stdout or fallback).strip().replace("\x00", "")
    return text[-500:]


def main(argv: list[str] | None = None) -> int:
    state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    default_dir = state_home / "agent-memory"
    parser = argparse.ArgumentParser(description="D-42 daily memory curator")
    parser.add_argument("--root", action="append", default=[])
    parser.add_argument("--project", action="append", default=[])
    parser.add_argument("--worker", default=os.environ.get("MEM_DISTILL_WORKER", ""))
    parser.add_argument("--mem", default=str(DEFAULT_MEM))
    parser.add_argument("--dispatcher", default=str(DEFAULT_DISPATCHER))
    parser.add_argument("--state", default=os.environ.get(
        "MEM_DAILY_CURATOR_STATE", str(default_dir / "daily-curator-state.json")))
    parser.add_argument("--report", default=os.environ.get(
        "MEM_DAILY_CURATOR_REPORT", str(default_dir / "daily-curator-last.json")))
    parser.add_argument("--lookback-hours", type=int, default=36)
    parser.add_argument("--max-records", type=int, default=100)
    parser.add_argument("--max-workers", type=int, default=int(os.environ.get(
        "MEM_DAILY_CURATOR_MAX_WORKERS", "8")))
    parser.add_argument("--now", help="Fixed local ISO timestamp for deterministic tests")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if not 1 <= args.lookback_hours <= 24 * 30:
        parser.error("--lookback-hours must be between 1 and 720")
    if not 1 <= args.max_records <= 100:
        parser.error("--max-records must be between 1 and 100")
    if not 1 <= args.max_workers <= 32:
        parser.error("--max-workers must be between 1 and 32")

    mem = Path(args.mem).resolve()
    dispatcher = Path(args.dispatcher).resolve()
    state_path = Path(args.state).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = state_path.with_suffix(state_path.suffix + ".lock")

    try:
        through_dt = parse_time(args.now) if args.now else dt.datetime.now().replace(microsecond=0)
    except ValueError as exc:
        parser.error(f"invalid --now: {exc}")
    through = through_dt.isoformat(timespec="seconds")
    started = dt.datetime.now().replace(microsecond=0).isoformat(timespec="seconds")
    run_id = through_dt.strftime("%Y%m%dT%H%M%S")

    if args.project:
        projects = sorted({Path(p).expanduser().resolve() for p in args.project})
        roots = []
    else:
        configured = args.root
        if not configured:
            configured = [p for p in os.environ.get(
                "MEM_DAILY_CURATOR_ROOTS", "/home/nas/user/Uihyeop").split(os.pathsep) if p]
            configured.append(str(ROOT))
        roots = [Path(p) for p in configured]
        projects = discover_projects(roots)

    report = {
        "schema": 1,
        "run_id": run_id,
        "started_at": started,
        "through": through,
        "dry_run": args.dry_run,
        "projects": [],
    }
    failures = 0
    worker_runs = 0

    with lock_path.open("a+", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            report["status"] = "busy"
            atomic_json(report_path, report)
            return 75

        state = load_json(state_path, {"schema": 1, "projects": {}})
        if state.get("schema") != 1 or not isinstance(state.get("projects"), dict):
            state = {"schema": 1, "projects": {}}
        seen_keys: set[str] = set()

        for cwd in projects[:200]:
            result = {"cwd": str(cwd), "through": through, "actions": []}
            if not cwd.is_dir():
                result.update(status="failed", phase="discovery", error="project path missing")
                report["projects"].append(result)
                failures += 1
                continue

            env = os.environ.copy()
            env["MEM_PY"] = str(mem)
            key = project_key(mem, cwd, env)
            if not key:
                result.update(status="failed", phase="project-key", error="project key unavailable")
                report["projects"].append(result)
                failures += 1
                continue
            if key in seen_keys:
                continue
            seen_keys.add(key)
            cid = cursor_id(key)
            entry = state["projects"].get(cid, {})
            since = entry.get("last_success_at")
            try:
                since_dt = parse_time(since) if since else through_dt - dt.timedelta(hours=args.lookback_hours)
            except (TypeError, ValueError):
                since_dt = through_dt - dt.timedelta(hours=args.lookback_hours)
            if since_dt >= through_dt:
                since_dt = through_dt - dt.timedelta(seconds=1)
            since = since_dt.isoformat(timespec="seconds")
            result.update(project_key=key, cursor_id=cid, since=since)

            try:
                recent_proc = run(
                    [sys.executable, str(mem), "curate-recent", "--since", since,
                     "--until", through, "--limit", str(args.max_records), "--json"],
                    cwd=cwd, env=env,
                )
            except subprocess.TimeoutExpired:
                result.update(status="failed", phase="recent-scan",
                              error="curate-recent timed out")
                report["projects"].append(result)
                failures += 1
                continue
            if recent_proc.returncode != 0:
                result.update(status="failed", phase="recent-scan",
                              error=bounded_error(recent_proc, "curate-recent failed"))
                report["projects"].append(result)
                failures += 1
                continue
            try:
                recent = json.loads(recent_proc.stdout)
            except json.JSONDecodeError:
                result.update(status="failed", phase="recent-scan", error="invalid recent JSON")
                report["projects"].append(result)
                failures += 1
                continue
            result["recent_count"] = recent.get("count", 0)
            if recent.get("project_key") != key:
                result.update(status="failed", phase="recent-scan", error="project key mismatch")
                report["projects"].append(result)
                failures += 1
                continue
            if recent.get("journal_gap"):
                result.update(
                    status="failed", phase="journal-gap",
                    error=("daily cursor predates retained write events; "
                           f"earliest={recent.get('earliest_retained_ts') or 'unknown'}"),
                )
                report["projects"].append(result)
                failures += 1
                continue
            if recent.get("truncated") or recent.get("oversized"):
                result.update(status="failed", phase="overflow",
                              error=(f"recent records exceed limit {args.max_records}"
                                     if recent.get("truncated") else
                                     "one or more recent record bodies exceed 8000 characters"))
                report["projects"].append(result)
                failures += 1
                continue

            if not recent.get("records") or args.dry_run:
                result.update(status="dry-run" if args.dry_run else "no-change",
                              phase="complete", applied_count=0)
                if not args.dry_run:
                    try:
                        sync_proc = run(
                            [sys.executable, str(mem), "sync", "--mirror-only", "--strict"],
                            cwd=cwd, env=env, timeout=60,
                        )
                    except subprocess.TimeoutExpired:
                        result.update(status="failed", phase="mirror-sync",
                                      error="mirror sync timed out")
                        report["projects"].append(result)
                        failures += 1
                        continue
                    if sync_proc.returncode != 0:
                        result.update(status="failed", phase="mirror-sync",
                                      error=bounded_error(sync_proc, "mirror sync failed"))
                        report["projects"].append(result)
                        failures += 1
                        continue
                    result["mirror_sync"] = "ok"
                    state["projects"][cid] = {
                        "project_key": key, "cwd": str(cwd),
                        "last_success_at": through, "last_run_id": run_id,
                    }
                    atomic_json(state_path, state)
                report["projects"].append(result)
                continue

            if not args.worker:
                result.update(status="failed", phase="unsupported-worker",
                              error="no MEM_DISTILL_WORKER configured")
                report["projects"].append(result)
                failures += 1
                continue
            if worker_runs >= args.max_workers:
                result.update(status="failed", phase="worker-budget",
                              error=f"daily worker budget {args.max_workers} exhausted")
                report["projects"].append(result)
                failures += 1
                continue
            worker_runs += 1

            recent_fd, recent_name = tempfile.mkstemp(prefix="daily-recent-", suffix=".json",
                                                       dir=state_path.parent)
            receipt_fd, receipt_name = tempfile.mkstemp(prefix="daily-receipt-", suffix=".json",
                                                         dir=state_path.parent)
            os.close(receipt_fd)
            try:
                with os.fdopen(recent_fd, "w", encoding="utf-8") as fh:
                    json.dump(recent, fh, sort_keys=True, ensure_ascii=False)
                    fh.write("\n")
                Path(receipt_name).unlink(missing_ok=True)
                dispatch_env = env.copy()
                dispatch_env.update({
                    "MEM_DISTILL_ENABLE": "1",
                    "MEM_DAILY_CURATE_ENABLE": "1",
                    "MEM_DISTILL_WORKER": args.worker,
                    "MEM_APPLIER": str(ROOT / "tools" / "memory" / "apply-distill-actions.py"),
                })
                project_run = f"{run_id}-{cid}"
                dispatch_proc = run(
                    ["bash", str(dispatcher), "daily", project_run, str(cwd),
                     recent_name, receipt_name],
                    cwd=cwd, env=dispatch_env,
                    timeout=int(os.environ.get("MEM_DAILY_CURATE_TIMEOUT", "660")),
                )
                receipt = load_json(Path(receipt_name), {})
                result["actions"] = receipt.get("applied", [])[:100]
                result["applied_count"] = receipt.get("applied_count", len(result["actions"]))
                result["mirror_sync"] = receipt.get("mirror_sync", "unknown")
                if dispatch_proc.returncode != 0 or receipt.get("status") != "ok":
                    result.update(status="failed", phase=receipt.get("phase", "dispatch"),
                                  error=bounded_error(dispatch_proc, "daily dispatch failed"))
                    report["projects"].append(result)
                    failures += 1
                    continue
            except subprocess.TimeoutExpired:
                result.update(status="failed", phase="timeout", error="daily curator timed out")
                report["projects"].append(result)
                failures += 1
                continue
            finally:
                Path(recent_name).unlink(missing_ok=True)
                Path(receipt_name).unlink(missing_ok=True)

            result.update(status="ok", phase="complete")
            state["projects"][cid] = {
                "project_key": key, "cwd": str(cwd),
                "last_success_at": through, "last_run_id": run_id,
            }
            if len(state["projects"]) > 512:
                ordered = sorted(state["projects"].items(),
                                 key=lambda item: item[1].get("last_success_at", ""), reverse=True)
                state["projects"] = dict(ordered[:512])
            atomic_json(state_path, state)
            report["projects"].append(result)

    report["status"] = "failed" if failures else ("no-projects" if not report["projects"] else "ok")
    report["failed_count"] = failures
    report["project_count"] = len(report["projects"])
    report["applied_count"] = sum(int(p.get("applied_count", 0)) for p in report["projects"])
    report["worker_runs"] = worker_runs
    atomic_json(report_path, report)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
