#!/usr/bin/env python3
"""Claude headless dispatch registration/launch wrapper."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QA_LEVELS = {"quick", "light", "standard", "thorough", "adversarial"}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    action = p.add_mutually_exclusive_group()
    action.add_argument("--dry-run", action="store_true", help="print the command without writing jobs.log")
    action.add_argument("--register", action="store_true", help="append an open job without launching")
    action.add_argument("--start", action="store_true", help="append an open job and launch in background")
    p.add_argument("--worktree", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--capability", required=True)
    p.add_argument("--mode", required=True)
    p.add_argument("--qa", required=True)
    p.add_argument("--prompt-file")
    p.add_argument("--prompt-text")
    p.add_argument("--jobs")
    p.add_argument("--log-dir")
    p.add_argument("--profile", help="profiles/<name>.yaml masked config home to attach via CLAUDE_CONFIG_DIR")
    return p


def fail(reason: str, code: int, **fields: str) -> int:
    print("check=failed")
    print(f"reason={reason}")
    for key, value in fields.items():
        print(f"{key}={value}")
    return code


def task_prompt(args: argparse.Namespace) -> tuple[str, str]:
    if args.prompt_file and args.prompt_text:
        raise ValueError("--prompt-file and --prompt-text are mutually exclusive")
    if args.prompt_file:
        path = Path(args.prompt_file)
        return path.read_text(encoding="utf-8"), str(path)
    if args.prompt_text:
        return args.prompt_text, "inline"
    return (
        "Run the requested portable harness work.\n"
        f"capability={args.capability}\nmode={args.mode}\nqa={args.qa}\n"
        f"worktree={args.worktree}\n",
        "generated",
    )


def dispatch_prompt(args: argparse.Namespace) -> tuple[str, str]:
    task, source = task_prompt(args)
    metadata = (
        "Dispatch metadata:\n"
        f"- capability: {args.capability}\n"
        f"- mode: {args.mode}\n"
        f"- qa: {args.qa}\n"
        f"- worktree: {args.worktree}\n"
    )
    depth1 = "이 세션은 depth-1 worker입니다 — 추가 재분사(claude -p 등 nested dispatch) 금지.\n"
    if args.profile:
        # Unlike the codex wrapper, do not force a preflight/bootstrap chain
        # here: CLAUDE_CONFIG_DIR already points at this dispatch's masked
        # profile home, which loads the L0 core contract and this profile's
        # role fragment (profiles/fragments/<name>.md) on its own. Keep the
        # prompt minimal — task + depth-1 reminder + report request.
        header = (
            "You are a Claude headless worker launched by the portable agent harness "
            f"under masked profile '{args.profile}'.\n"
            "CLAUDE_CONFIG_DIR already points at this profile's masked home — its own "
            "bootstrap covers the L0 core contract and this profile's role fragment. "
            "There is no orchestration section in that bootstrap; do not look for one.\n\n"
        )
    else:
        header = "You are a Claude headless worker launched by the portable agent harness.\n\n"
    return (
        header
        + metadata
        + "\n"
        + depth1
        + "\nUser task:\n"
        + f"{task.rstrip()}\n\n"
        + "Return a concise Korean report with changed files, verification commands/results, "
        "and artifact paths. Leave merge and worktree cleanup to the main orchestrator.\n",
        source,
    )


def shell_command(args: argparse.Namespace, prompt_path: Path, log_path: Path) -> str:
    # `claude -p` reads the prompt from stdin when no positional prompt is
    # given and prints the response non-interactively, mirroring the codex
    # wrapper's file-piped `codex exec ... < prompt_path` invocation.
    cmd = ["claude", "-p"]
    inner = " ".join(shlex.quote(x) for x in cmd)
    return (
        f"cd {shlex.quote(args.worktree)} && "
        f"{inner} < {shlex.quote(str(prompt_path))} >> {shlex.quote(str(log_path))} 2>&1"
    )


@contextmanager
def jobs_lock(jobs: Path):
    jobs.parent.mkdir(parents=True, exist_ok=True)
    lock_path = Path(f"{jobs}.lock")
    with lock_path.open("a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield lock_path
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def append_job(jobs: Path, args: argparse.Namespace) -> None:
    repo = subprocess.check_output(["git", "-C", args.worktree, "rev-parse", "--show-toplevel"], text=True).strip()
    pipe = f"capability={args.capability},mode={args.mode},qa={args.qa}"
    if args.profile:
        pipe += f",profile={args.profile}"
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with jobs_lock(jobs):
        with jobs.open("a", encoding="utf-8") as f:
            f.write(f"{ts}\topen\t{repo}\t{args.worktree}\t{args.slug}\t{pipe}\n")


def resolve_agent_home() -> Path:
    env_home = os.environ.get("AGENT_HOME")
    if env_home and (Path(env_home) / "core" / "CORE.md").is_file():
        return Path(env_home)
    return ROOT


def build_home_gate(agent_home: Path, profile: str, extra: list[str], reason: str) -> int:
    build_home = agent_home / "tools" / "profile" / "build-home.py"
    result = subprocess.run(
        [sys.executable, str(build_home), profile, *extra],
        cwd=agent_home,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode == 0:
        return 0
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return fail(reason, 3, profile=profile)


def main(argv: list[str]) -> int:
    args = parser().parse_args(argv[1:])
    action = "start" if args.start else "register" if args.register else "dry-run"
    worktree = Path(args.worktree)
    if not worktree.is_dir():
        return fail("worktree-not-found", 66, worktree=args.worktree)
    if subprocess.run(
        ["git", "-C", args.worktree, "rev-parse", "--is-inside-work-tree"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        return fail("not-a-git-worktree", 65, worktree=args.worktree)
    if args.qa not in QA_LEVELS:
        return fail(
            "invalid-dispatch-qa",
            64,
            qa=args.qa,
            allowed_qa="quick,light,standard,thorough,adversarial",
        )
    if args.start and shutil.which("claude") is None:
        return fail("claude-command-unavailable", 69, worktree=args.worktree)

    agent_home = resolve_agent_home()
    # Claude and codex share one AGENT_HOME (typically ~/.claude) and therefore
    # the same `.dispatch/jobs.log` registry and `.dispatch/homes/` root
    # whenever AGENT_HOME resolves there. This is a *shared* registry, not two
    # independent ones: it is what lets codex's harness-agnostic
    # dispatch-harvest.py reclaim claude profile instance homes too (cleanup
    # keys off `profile=` in the pipe, not the harness). codex may still pass
    # `--jobs` to point at a repo-relative registry for non-profile runs, but
    # profile dispatch presumes this shared ~/.claude registry so harvest can
    # see every row.
    jobs = Path(args.jobs) if args.jobs else agent_home / ".dispatch" / "jobs.log"
    log_dir = Path(args.log_dir) if args.log_dir else agent_home / ".dispatch" / "logs"
    home_root = agent_home / ".dispatch" / "homes"
    instance_dir = home_root / f"{args.slug}.{args.profile}" if args.profile else None

    prompt_text, prompt_source = dispatch_prompt(args)
    prompt_path = log_dir / f"{args.slug}.claude.prompt.txt"
    log_path = log_dir / f"{args.slug}.claude.log"
    command = shell_command(args, prompt_path, log_path)

    if action in ("register", "start"):
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_text, encoding="utf-8")

    if action == "start" and args.profile:
        # Gate-first, then create -> register -> launch: a --check failure
        # must not leave an instance home behind (no leak on gate failure).
        rc = build_home_gate(agent_home, args.profile, ["--check"], "profile-check-failed")
        if rc != 0:
            return rc
        rc = build_home_gate(
            agent_home,
            args.profile,
            ["--instance", args.slug, "--home-root", str(home_root)],
            "profile-build-failed",
        )
        if rc != 0:
            return rc

    if action in ("register", "start"):
        # Register before launch so harvest can always reclaim the home even
        # if the launch itself never comes up.
        append_job(jobs, args)

    if action == "start":
        env = {**os.environ}
        if args.profile:
            env["CLAUDE_CONFIG_DIR"] = str(instance_dir)
        subprocess.Popen(["sh", "-c", command], env=env, start_new_session=True)

    print("adapter=claude")
    print("runtime_surface=claude-print-headless")
    print(f"status={action}")
    print(f"worktree={args.worktree}")
    print(f"slug={args.slug}")
    print(f"capability={args.capability}")
    print(f"mode={args.mode}")
    print(f"qa={args.qa}")
    print(f"profile={args.profile or '-'}")
    print(f"instance_home={instance_dir if instance_dir else '-'}")
    print(f"job_registry={jobs}")
    print(f"registry_lock={jobs}.lock")
    print(f"registered={1 if action in ('register', 'start') else 0}")
    print(f"started={1 if action == 'start' else 0}")
    print(f"prompt_source={prompt_source}")
    print(f"prompt_file={prompt_path}")
    print(f"log_file={log_path}")
    print(f"command={command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
