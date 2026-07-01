#!/usr/bin/env python3
"""Codex headless dispatch registration/launch wrapper."""

from __future__ import annotations

import argparse
import os
import shutil
import shlex
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
    p.add_argument("--sandbox", default="workspace-write")
    p.add_argument("--approval", default="never")
    p.add_argument("--require-hook-trust", action="store_true")
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


def qa_track(capability: str) -> str:
    if capability.startswith("code-") or capability == "autopilot-code":
        return "code"
    if capability in {"autopilot-research"} or capability.startswith("analyze-"):
        return "research"
    if capability in {"autopilot-draft", "autopilot-refine"} or capability.startswith("draft-"):
        return "doc"
    return "general"


def dispatch_prompt(args: argparse.Namespace) -> tuple[str, str]:
    task, source = task_prompt(args)
    track = qa_track(args.capability)
    execution_contract = ""
    if args.capability == "autopilot-code":
        execution_contract = (
            "\nAutopilot-code execution contract:\n"
            "- Before code edits, emit a `spec-significance` verdict.\n"
            "- Run the pipeline in order: code-plan -> code-execute -> code-test -> code-report. Use optional code-refine only when user feedback or QA review requires plan correction.\n"
            "- For each sub-step, read the matching adapters/codex/skills/<step>/SKILL.md when present and run adapters/codex/bin/preflight.sh capability-info <step>.\n"
            "- Pipeline role profiles: run adapters/codex/bin/preflight.sh role planning, role implementation, role verification, and role report to map stages to Codex-native agents.\n"
            "- Planning review: run adapters/codex/bin/preflight.sh mode-info qa/plan-review and adapters/codex/bin/preflight.sh role verification. For thorough/adversarial QA, also use a deep/external reviewer role when available.\n"
            "- Implementation: run adapters/codex/bin/preflight.sh role implementation and obey the requested development mode.\n"
            "- Testing: run adapters/codex/bin/preflight.sh mode-info qa/test, satisfy the reported verification-runner contract, and record evidence under test_logs/.\n"
            "- Reporting: run adapters/codex/bin/preflight.sh role report, then write or update pipeline_summary.md with changed files, verification commands/results, artifact paths, and unsupported Codex tool contracts.\n"
            "- Do not claim independent QA delegation if no separate Codex agent/headless pass actually ran; report inline fallback explicitly.\n"
        )
    return (
        "You are a Codex headless worker launched by the portable agent harness.\n"
        "Follow the Codex adapter contract before doing task work.\n\n"
        "Required bootstrap:\n"
        "- Read adapters/codex/AGENTS.md first.\n"
        f"- Run adapters/codex/bin/preflight.sh route {args.capability} . codex-headless.\n"
        f"- Read adapters/codex/skills/{args.capability}/SKILL.md when present.\n"
        f"- Run adapters/codex/bin/preflight.sh mode-info {args.mode} and read the reported native_mode_path when present.\n"
        f"- Run adapters/codex/bin/preflight.sh qa-policy {args.qa} {track} and obey the reported reviewer, external-adversary, and fallback policy.\n"
        "- If you actually read .agent_reports/spec/prd.md or legacy .claude_reports/spec/prd.md, run adapters/codex/bin/preflight.sh read <prd.md> codex-headless after the read.\n"
        "- Before edits, run adapters/codex/bin/preflight.sh write <file> codex-headless.\n"
        "- Do not use adapters/claude, claude_setting, Claude slash commands, or Claude hook/statusline files as Codex-native input.\n\n"
        "Dispatch metadata:\n"
        f"- capability: {args.capability}\n"
        f"- mode: {args.mode}\n"
        f"- qa: {args.qa}\n"
        f"- worktree: {args.worktree}\n\n"
        f"{execution_contract}"
        "User task:\n"
        f"{task.rstrip()}\n\n"
        "Return a concise Korean report with changed files, verification commands, artifact paths, and any blocked/unsupported Codex tool contracts. "
        "Leave merge and worktree cleanup to the main orchestrator.\n",
        source,
    )


def shell_command(args: argparse.Namespace, prompt_path: Path, log_path: Path) -> str:
    # `codex exec` does not accept --ask-for-approval (top-level `codex` flag
    # only); it runs non-interactively, so the --sandbox policy governs writes.
    # args.approval is retained for CLI compatibility but not passed through.
    cmd = [
        "codex",
        "exec",
        "--cd",
        args.worktree,
        "--sandbox",
        args.sandbox,
        "--json",
        "-",
    ]
    return " ".join(shlex.quote(x) for x in cmd) + f" < {shlex.quote(str(prompt_path))} >> {shlex.quote(str(log_path))} 2>&1"


def append_job(jobs: Path, args: argparse.Namespace) -> None:
    jobs.parent.mkdir(parents=True, exist_ok=True)
    repo = subprocess.check_output(["git", "-C", args.worktree, "rev-parse", "--show-toplevel"], text=True).strip()
    pipe = f"capability={args.capability},mode={args.mode},qa={args.qa}"
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with jobs.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\topen\t{repo}\t{args.worktree}\t{args.slug}\t{pipe}\n")


def resolve_agent_home() -> Path:
    env_home = os.environ.get("AGENT_HOME")
    if env_home and (Path(env_home) / "core" / "CORE.md").is_file():
        return Path(env_home)
    return ROOT


def check_runtime_projection(worktree: str, require_hook_trust: bool) -> int:
    command = [str(ROOT / "adapters" / "codex" / "bin" / "preflight.sh"), "headless", "--check"]
    if require_hook_trust:
        command.append("--require-hook-trust")
    command.append(worktree)
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
    return result.returncode


def validate_preflight(kind: str, command: str, value: str, reason: str) -> int:
    result = subprocess.run(
        [str(ROOT / "adapters" / "codex" / "bin" / "preflight.sh"), command, value],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode == 0:
        return 0
    rc = fail(reason, result.returncode or 64, **{kind: value})
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return rc


def validate_dispatch_inputs(args: argparse.Namespace) -> int:
    rc = validate_preflight("capability", "capability-info", args.capability, "invalid-dispatch-capability")
    if rc != 0:
        return rc
    rc = validate_preflight("mode", "mode-info", args.mode, "invalid-dispatch-mode")
    if rc != 0:
        return rc
    if args.qa not in QA_LEVELS:
        return fail(
            "invalid-dispatch-qa",
            64,
            qa=args.qa,
            allowed_qa="quick,light,standard,thorough,adversarial",
        )
    return 0


def main(argv: list[str]) -> int:
    args = parser().parse_args(argv[1:])
    action = "start" if args.start else "register" if args.register else "dry-run"
    worktree = Path(args.worktree)
    if not worktree.is_dir():
        return fail("worktree-not-found", 66, worktree=args.worktree)
    if subprocess.run(["git", "-C", args.worktree, "rev-parse", "--is-inside-work-tree"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
        return fail("not-a-git-worktree", 65, worktree=args.worktree)
    rc = validate_dispatch_inputs(args)
    if rc != 0:
        return rc
    if args.start and shutil.which("codex") is None:
        return fail("codex-command-unavailable", 69, worktree=args.worktree)
    if args.start:
        rc = check_runtime_projection(args.worktree, args.require_hook_trust)
        if rc != 0:
            return rc

    agent_home = resolve_agent_home()
    jobs = Path(args.jobs) if args.jobs else agent_home / ".dispatch" / "jobs.log"
    log_dir = Path(args.log_dir) if args.log_dir else agent_home / ".dispatch" / "logs"
    prompt_text, prompt_source = dispatch_prompt(args)
    prompt_path = log_dir / f"{args.slug}.codex.prompt.txt"
    log_path = log_dir / f"{args.slug}.codex.jsonl"
    command = shell_command(args, prompt_path, log_path)

    if action in ("register", "start"):
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_text, encoding="utf-8")
        append_job(jobs, args)
    if action == "start":
        subprocess.Popen(["sh", "-c", command], start_new_session=True)

    print("adapter=codex")
    print("runtime_surface=codex-exec-headless")
    print(f"status={action}")
    print(f"worktree={args.worktree}")
    print(f"slug={args.slug}")
    print(f"capability={args.capability}")
    print(f"mode={args.mode}")
    print(f"qa={args.qa}")
    print(f"job_registry={jobs}")
    print(f"registered={1 if action in ('register', 'start') else 0}")
    print(f"started={1 if action == 'start' else 0}")
    print(f"require_hook_trust={1 if args.require_hook_trust else 0}")
    print(f"prompt_source={prompt_source}")
    print(f"prompt_file={prompt_path}")
    print(f"log_file={log_path}")
    print(f"command={command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
