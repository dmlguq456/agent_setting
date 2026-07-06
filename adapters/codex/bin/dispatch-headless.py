#!/usr/bin/env python3
"""Codex headless dispatch registration/launch wrapper."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import os
import shutil
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QA_LEVELS = {"quick", "light", "standard", "thorough", "adversarial"}
INTENSITY_LEVELS = {"direct", "quick", "standard", "strong", "thorough", "adversarial"}


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
    p.add_argument("--intensity", default="standard")
    p.add_argument("--depth", type=int, default=1)
    p.add_argument("--parent", dest="parent_slug")
    p.add_argument("--worker-role")
    p.add_argument("--owner", dest="capability_owner")
    p.add_argument("--prompt-file")
    p.add_argument("--prompt-text")
    p.add_argument("--jobs")
    p.add_argument("--log-dir")
    p.add_argument("--sandbox", default="workspace-write")
    p.add_argument(
        "--approval",
        choices=("untrusted", "on-request", "never", "inherit"),
        default=os.environ.get("CODEX_DISPATCH_APPROVAL", "never"),
    )
    p.add_argument("--model-role", default=os.environ.get("CODEX_DISPATCH_MODEL_ROLE"))
    p.add_argument("--model", default=os.environ.get("CODEX_DISPATCH_MODEL"))
    p.add_argument("--reasoning", default=os.environ.get("CODEX_DISPATCH_REASONING"))
    p.add_argument(
        "--inherit-model-settings",
        action="store_true",
        help="do not override model/reasoning; inherit the active Codex config for this dispatch",
    )
    p.add_argument("--require-hook-trust", action="store_true")
    p.add_argument("--profile")
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
        f"intensity={args.intensity}\ndepth={args.depth}\nparent={args.parent_slug or '-'}\n"
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


def toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def role_map(role: str) -> dict[str, str]:
    result = subprocess.run(
        [str(ROOT / "adapters" / "codex" / "bin" / "preflight.sh"), "role", role],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise ValueError(detail or f"preflight role lookup failed for {role}")
    fields: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            fields[key] = value
    return fields


class ModelSelectionError(ValueError):
    def __init__(self, reason: str, detail: str):
        super().__init__(detail)
        self.reason = reason


def resolve_model_settings(args: argparse.Namespace) -> dict[str, str]:
    if args.inherit_model_settings:
        if args.model_role or args.model or args.reasoning:
            raise ModelSelectionError(
                "invalid-dispatch-model-selection",
                "--inherit-model-settings is mutually exclusive with --model-role, --model, and --reasoning",
            )
        return {"source": "inherit", "role": "inherit", "model": "inherit", "reasoning": "inherit"}
    if args.model_role and (args.model or args.reasoning):
        raise ModelSelectionError(
            "invalid-dispatch-model-selection",
            "--model-role is mutually exclusive with --model and --reasoning",
        )
    if args.model_role:
        fields = role_map(args.model_role)
        model = fields.get("model")
        reasoning = fields.get("reasoning")
        if not model or not reasoning:
            raise ModelSelectionError("invalid-dispatch-model-role", "role map did not return model and reasoning")
        if model in {"role-set", "role-profile", "unconfigured"}:
            raise ModelSelectionError(
                "invalid-dispatch-model-role",
                f"model role {args.model_role!r} resolved to non-runnable model={model}",
            )
        return {"source": "role", "role": args.model_role, "model": model, "reasoning": reasoning}
    if not args.model and not args.reasoning:
        raise ModelSelectionError(
            "missing-dispatch-model-selection",
            "main dispatch must choose --model-role, --model with --reasoning, or --inherit-model-settings",
        )
    if not args.model or not args.reasoning:
        raise ModelSelectionError(
            "invalid-dispatch-model-selection",
            "--model and --reasoning must be provided together",
        )
    return {"source": "explicit", "role": "-", "model": args.model, "reasoning": args.reasoning}


def dispatch_prompt(args: argparse.Namespace) -> tuple[str, str]:
    task, source = task_prompt(args)
    track = qa_track(args.capability)
    execution_contract = ""
    if args.capability == "autopilot-code":
        execution_contract = (
            "\nAutopilot-code execution contract:\n"
            "- Before code edits, emit a `spec-significance` verdict.\n"
            "- Select the stage graph from `intensity` before using QA. `direct` has no code-plan/plan-check/durable plan artifact; `quick` uses an inline micro-plan plus plan-check-lite; `standard+` uses the durable code-plan -> code-execute -> code-test -> code-report loop.\n"
            "- For each durable sub-step that is actually used, read the matching adapters/codex/skills/<step>/SKILL.md when present and run adapters/codex/bin/preflight.sh capability-info <step>.\n"
            "- Pipeline role profiles: for standard+ stages, run adapters/codex/bin/preflight.sh role planning, role implementation, role verification, and role report to map stages to Codex-native agents.\n"
            "- Plan-check is required for quick+ but stays small: requirements coverage, over/under-scoping, executable verification, and missed spec-significant risk. Do not run independent QA after every stage by default.\n"
            "- When the selected graph calls for independent plan review, run adapters/codex/bin/preflight.sh mode-info qa/plan-review and adapters/codex/bin/preflight.sh role verification before claiming that review.\n"
            "- Pipeline intensity controls ceremony. For thorough/adversarial intensity, a depth-1 capability owner may dispatch bounded depth-2 planner/verifier/adversary workers and must synthesize short reports; depth 3+ is forbidden.\n"
            "- Implementation: run adapters/codex/bin/preflight.sh role implementation for standard+ implementation stages and obey the requested development mode.\n"
            "- Testing: run adapters/codex/bin/preflight.sh mode-info qa/test when concrete verification commands are used, satisfy the reported verification-runner contract, and record evidence under test_logs/ for standard+ work cycles.\n"
            "- Reporting: direct/quick return a concise report; standard+ runs adapters/codex/bin/preflight.sh role report, then writes or updates pipeline_summary.md with changed files, verification commands/results, artifact paths, and unsupported Codex tool contracts.\n"
            "- Do not claim independent QA delegation if no separate Codex agent/headless pass actually ran; report inline fallback explicitly.\n"
        )
    return (
        "You are a Codex headless worker launched by the portable agent harness.\n"
        "Follow the Codex adapter contract before doing task work.\n\n"
        "Required bootstrap:\n"
        "- Read adapters/codex/AGENTS.md first.\n"
        "- Run adapters/codex/bin/preflight.sh status . codex-headless and inspect workflow, artifact, git, worktree, and headless-job risk fields.\n"
        "- Run adapters/codex/bin/preflight.sh prompt-signal . codex-headless to mirror the Codex UserPromptSubmit routing signal.\n"
        "- Run adapters/codex/bin/preflight.sh mode . codex-headless to mirror the tracked/untracked workflow guard.\n"
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
        f"- intensity: {args.intensity}\n"
        f"- depth: {args.depth}\n"
        f"- parent: {args.parent_slug or '-'}\n"
        f"- worker_role: {args.worker_role or '-'}\n"
        f"- owner: {args.capability_owner or '-'}\n"
        f"- worktree: {args.worktree}\n\n"
        f"{execution_contract}"
        "User task:\n"
        f"{task.rstrip()}\n\n"
        "Return a concise Korean report with changed files, verification commands, artifact paths, and any blocked/unsupported Codex tool contracts. "
        "Leave merge and worktree cleanup to the main orchestrator.\n",
        source,
    )


def shell_command(args: argparse.Namespace, prompt_path: Path, log_path: Path) -> str:
    cmd = [
        "codex",
        "exec",
        "--cd",
        args.worktree,
        "--sandbox",
        args.sandbox,
    ]
    if args.resolved_model_settings["source"] != "inherit":
        model = args.resolved_model_settings["model"]
        reasoning = args.resolved_model_settings["reasoning"]
        cmd += [
            "--model",
            model,
            "-c",
            f"model_reasoning_effort={toml_string(reasoning)}",
        ]
    if args.approval != "inherit":
        cmd += [
            "-c",
            f"approval_policy={toml_string(args.approval)}",
        ]
    cmd += [
        "--json",
        "-",
    ]
    return " ".join(shlex.quote(x) for x in cmd) + f" < {shlex.quote(str(prompt_path))} >> {shlex.quote(str(log_path))} 2>&1"


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
    pipe = f"capability={args.capability},mode={args.mode},qa={args.qa},intensity={args.intensity},depth={args.depth}"
    if args.parent_slug:
        pipe += f",parent={args.parent_slug}"
    if args.worker_role:
        pipe += f",worker_role={args.worker_role}"
    if args.capability_owner:
        pipe += f",owner={args.capability_owner}"
    settings = args.resolved_model_settings
    pipe += f",model_source={settings['source']},model_role={settings['role']},model={settings['model']},reasoning={settings['reasoning']}"
    if args.approval != "inherit":
        pipe += f",approval={args.approval}"
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
    if args.intensity not in INTENSITY_LEVELS:
        return fail(
            "invalid-dispatch-intensity",
            64,
            intensity=args.intensity,
            allowed_intensity="direct,quick,standard,strong,thorough,adversarial",
        )
    if args.depth not in (1, 2):
        return fail("invalid-dispatch-depth", 64, depth=str(args.depth), allowed_depth="1,2")
    if args.depth == 2 and not args.parent_slug:
        return fail("missing-dispatch-parent", 64, depth=str(args.depth))
    if args.depth == 2 and args.intensity not in {"thorough", "adversarial"}:
        return fail("invalid-depth-two-intensity", 64, depth=str(args.depth), intensity=args.intensity)
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
    try:
        args.resolved_model_settings = resolve_model_settings(args)
    except ModelSelectionError as e:
        fields = {"detail": str(e)}
        if args.model_role:
            fields["model_role"] = args.model_role
        return fail(e.reason, 64, **fields)
    if args.start and shutil.which("codex") is None:
        return fail("codex-command-unavailable", 69, worktree=args.worktree)
    profile_home: Path | None = None
    if args.start:
        rc = check_runtime_projection(args.worktree, args.require_hook_trust)
        if rc != 0:
            return rc
        if args.profile:
            home_root = resolve_agent_home() / ".dispatch" / "homes"
            build_home = resolve_agent_home() / "tools" / "profile" / "build-home.py"
            check_result = subprocess.run(
                ["python3", str(build_home), args.profile, "--check"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if check_result.returncode != 0:
                if check_result.stdout:
                    print(check_result.stdout, end="")
                if check_result.stderr:
                    print(check_result.stderr, end="", file=sys.stderr)
                return fail("invalid-dispatch-profile", 3, profile=args.profile)
            build_result = subprocess.run(
                ["python3", str(build_home), args.profile, "--instance", args.slug, "--home-root", str(home_root)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if build_result.returncode != 0:
                if build_result.stdout:
                    print(build_result.stdout, end="")
                if build_result.stderr:
                    print(build_result.stderr, end="", file=sys.stderr)
                return fail("profile-build-failed", 3, profile=args.profile)
            profile_home = home_root / f"{args.slug}.{args.profile}"

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
        dispatch_env = {
            **os.environ,
            "AGENT_DISPATCH_DEPTH": str(args.depth),
            "AGENT_DISPATCH_INTENSITY": args.intensity,
            "AGENT_DISPATCH_PARENT_SLUG": args.parent_slug or "",
            "AGENT_DISPATCH_WORKER_ROLE": args.worker_role or "",
            "AGENT_DISPATCH_OWNER": args.capability_owner or "",
        }
        if profile_home is not None:
            dispatch_env["CODEX_HOME"] = str(profile_home)
        subprocess.Popen(["sh", "-c", command], start_new_session=True, env=dispatch_env)

    print("adapter=codex")
    print("runtime_surface=codex-exec-headless")
    print(f"status={action}")
    print(f"worktree={args.worktree}")
    print(f"slug={args.slug}")
    print(f"capability={args.capability}")
    print(f"mode={args.mode}")
    print(f"qa={args.qa}")
    print(f"intensity={args.intensity}")
    print(f"depth={args.depth}")
    print(f"parent={args.parent_slug or '-'}")
    print(f"worker_role={args.worker_role or '-'}")
    print(f"owner={args.capability_owner or '-'}")
    settings = args.resolved_model_settings
    print(f"model_source={settings['source']}")
    print(f"model_role={settings['role']}")
    print(f"model={settings['model']}")
    print(f"reasoning={settings['reasoning']}")
    print(f"approval={args.approval}")
    print(f"profile={args.profile or '-'}")
    print(f"job_registry={jobs}")
    print(f"registry_lock={jobs}.lock")
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
