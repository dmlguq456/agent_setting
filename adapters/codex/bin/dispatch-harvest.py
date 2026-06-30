#!/usr/bin/env python3
"""Codex dispatch registry harvest/status wrapper."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--jobs")
    p.add_argument("--slug")
    p.add_argument("--worktree")
    p.add_argument("--status", choices=("open", "done", "all"), default="open")
    p.add_argument("--mark-done", action="store_true")
    return p


def emit_header(args: argparse.Namespace, jobs: Path, matched: int, marked_done: int, malformed: int) -> None:
    print("adapter=codex")
    print("runtime_surface=codex-dispatch-harvest")
    print("status=harvest")
    print(f"job_registry={jobs}")
    print(f"selector_slug={args.slug or '*'}")
    print(f"selector_worktree={args.worktree or '*'}")
    print(f"status_filter={args.status}")
    print(f"matched={matched}")
    print(f"marked_done={marked_done}")
    print(f"malformed={malformed}")
    print("merge_action=unsupported")
    print("cleanup_action=unsupported")
    print("note=registry-only; merge remains main/orchestrator")


def matches(args: argparse.Namespace, fields: list[str]) -> bool:
    if len(fields) != 6:
        return False
    _, state, _, worktree, slug, _ = fields
    if args.status != "all" and state != args.status:
        return False
    if args.slug and slug != args.slug:
        return False
    if args.worktree and worktree != args.worktree:
        return False
    return True


def main(argv: list[str]) -> int:
    args = parser().parse_args(argv[1:])
    if args.mark_done and not (args.slug or args.worktree):
        print("check=failed")
        print("reason=selector-required")
        print("hint=pass --slug or --worktree before --mark-done")
        return 64

    agent_home = Path(os.environ.get("AGENT_HOME", os.getcwd()))
    jobs = Path(args.jobs) if args.jobs else agent_home / ".dispatch" / "jobs.log"
    if not jobs.exists():
        emit_header(args, jobs, 0, 0, 0)
        return 0

    original = jobs.read_text(encoding="utf-8").splitlines(keepends=True)
    rewritten: list[str] = []
    matched_jobs: list[list[str]] = []
    matched = 0
    marked_done = 0
    malformed = 0

    for line in original:
        bare = line.rstrip("\n")
        fields = bare.split("\t")
        if len(fields) != 6:
            malformed += 1
            rewritten.append(line)
            continue
        if matches(args, fields):
            matched += 1
            matched_jobs.append(fields.copy())
            if args.mark_done and fields[1] == "open":
                fields[1] = "done"
                marked_done += 1
                line = "\t".join(fields) + "\n"
        rewritten.append(line)

    if args.mark_done:
        jobs.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(jobs.parent), delete=False) as tmp:
            tmp.writelines(rewritten)
            tmp_name = tmp.name
        Path(tmp_name).replace(jobs)

    emit_header(args, jobs, matched, marked_done, malformed)
    for fields in matched_jobs:
        _, state, repo, worktree, slug, pipe = fields
        print(f"job_status={state}")
        print(f"job_repo={repo}")
        print(f"job_worktree={worktree}")
        print(f"job_slug={slug}")
        print(f"job_pipe={pipe}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
