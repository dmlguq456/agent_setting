#!/usr/bin/env python3
"""OpenCode headless dispatch registration/launch wrapper."""

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
    p.add_argument("--agent", default="build")
    p.add_argument("--model-role", default=os.environ.get("OPENCODE_DISPATCH_MODEL_ROLE"))
    p.add_argument("--model", default=os.environ.get("OPENCODE_DISPATCH_MODEL"))
    p.add_argument("--variant", default=os.environ.get("OPENCODE_DISPATCH_VARIANT"))
    p.add_argument(
        "--inherit-model-settings",
        action="store_true",
        help="do not override model/variant; inherit the active OpenCode config for this dispatch",
    )
    p.add_argument("--prompt-file")
    p.add_argument("--prompt-text")
    p.add_argument("--jobs")
    p.add_argument("--log-dir")
    return p


def fail(reason: str, code: int, **fields: str) -> int:
    print("check=failed")
    print(f"reason={reason}")
    for key, value in fields.items():
        print(f"{key}={value}")
    return code


class ModelSelectionError(ValueError):
    def __init__(self, reason: str, detail: str):
        super().__init__(detail)
        self.reason = reason


def role_map(role: str) -> dict[str, str]:
    result = subprocess.run(
        [str(ROOT / "adapters" / "opencode" / "bin" / "preflight.sh"), "role", role],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise ModelSelectionError("invalid-dispatch-model-role", detail or f"preflight role lookup failed for {role}")
    fields: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            fields[key] = value
    return fields


def resolve_model_settings(args: argparse.Namespace) -> dict[str, str]:
    if args.inherit_model_settings:
        if args.model_role or args.model or args.variant:
            raise ModelSelectionError(
                "invalid-dispatch-model-selection",
                "--inherit-model-settings is mutually exclusive with --model-role, --model, and --variant",
            )
        return {"source": "inherit", "role": "inherit", "model": "inherit", "variant": "inherit"}
    if args.model_role and (args.model or args.variant):
        raise ModelSelectionError(
            "invalid-dispatch-model-selection",
            "--model-role is mutually exclusive with --model and --variant",
        )
    if args.model_role:
        fields = role_map(args.model_role)
        model = fields.get("model")
        variant = fields.get("variant")
        if not model or not variant:
            raise ModelSelectionError("invalid-dispatch-model-role", "role map did not return model and variant")
        if model == "opencode-default" or variant == "runtime-default":
            raise ModelSelectionError(
                "invalid-dispatch-model-role",
                f"model role {args.model_role!r} resolved to runtime defaults; configure AGENT_MODEL_* and AGENT_VARIANT_* or pass --model/--variant",
            )
        return {"source": "role", "role": args.model_role, "model": model, "variant": variant}
    if not args.model and not args.variant:
        raise ModelSelectionError(
            "missing-dispatch-model-selection",
            "main dispatch must choose --model-role, --model with --variant, or --inherit-model-settings",
        )
    if not args.model or not args.variant:
        raise ModelSelectionError(
            "invalid-dispatch-model-selection",
            "--model and --variant must be provided together",
        )
    return {"source": "explicit", "role": "-", "model": args.model, "variant": args.variant}


def prompt(args: argparse.Namespace) -> tuple[str, str]:
    if args.prompt_file and args.prompt_text:
        raise ValueError("--prompt-file and --prompt-text are mutually exclusive")
    if args.prompt_file:
        path = Path(args.prompt_file)
        return path.read_text(encoding="utf-8"), str(path)
    if args.prompt_text:
        return args.prompt_text, "inline"
    extra = ""
    if args.capability == "autopilot-code":
        extra = (
            "\nAutopilot-code execution contract:\n"
            "- Choose the stage graph from intensity before QA. direct has no plan stage; quick uses micro-plan plus plan-check-lite; standard+ uses durable plan/execute/test/report.\n"
            "- Plan-check is required for quick+ but stays small; do not run independent QA after every stage by default.\n"
            "- thorough/adversarial may use bounded depth-2 planner/verifier/adversary workers and must synthesize short reports; depth 3+ is forbidden.\n"
        )
    return (
        "Run the requested portable harness work.\n"
        f"capability={args.capability}\nmode={args.mode}\nqa={args.qa}\n"
        f"intensity={args.intensity}\ndepth={args.depth}\nparent={args.parent_slug or '-'}\n"
        f"worktree={args.worktree}\n"
        f"{extra}",
        "generated",
    )

def shell_command(args: argparse.Namespace, prompt_path: Path, log_path: Path) -> str:
    cmd = [
        "opencode",
        "run",
        "--dir",
        args.worktree,
        "--format",
        "json",
        "--agent",
        args.agent,
    ]
    if args.resolved_model_settings["source"] != "inherit":
        cmd += [
            "--model",
            args.resolved_model_settings["model"],
            "--variant",
            args.resolved_model_settings["variant"],
        ]
    prompt_arg = f'"$(cat -- {shlex.quote(str(prompt_path))})"'
    return " ".join(shlex.quote(x) for x in cmd) + f" {prompt_arg} >> {shlex.quote(str(log_path))} 2>&1"


def append_job(jobs: Path, args: argparse.Namespace) -> None:
    jobs.parent.mkdir(parents=True, exist_ok=True)
    repo = subprocess.check_output(["git", "-C", args.worktree, "rev-parse", "--show-toplevel"], text=True).strip()
    pipe = f"capability={args.capability},mode={args.mode},qa={args.qa},intensity={args.intensity},depth={args.depth}"
    if args.parent_slug:
        pipe += f",parent={args.parent_slug}"
    if args.worker_role:
        pipe += f",worker_role={args.worker_role}"
    if args.capability_owner:
        pipe += f",owner={args.capability_owner}"
    settings = args.resolved_model_settings
    pipe += f",model_source={settings['source']},model_role={settings['role']},model={settings['model']},variant={settings['variant']}"
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with jobs.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\topen\t{repo}\t{args.worktree}\t{args.slug}\t{pipe}\n")


def resolve_agent_home() -> Path:
    env_home = os.environ.get("AGENT_HOME")
    if env_home and (Path(env_home) / "core" / "CORE.md").is_file():
        return Path(env_home)
    return ROOT


def check_runtime_projection(worktree: str) -> int:
    result = subprocess.run(
        [str(ROOT / "adapters" / "opencode" / "bin" / "preflight.sh"), "headless", "--check", worktree],
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


def validate_dispatch_metadata(args: argparse.Namespace) -> int:
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
    rc = validate_dispatch_metadata(args)
    if rc != 0:
        return rc
    try:
        args.resolved_model_settings = resolve_model_settings(args)
    except ModelSelectionError as e:
        fields = {"detail": str(e)}
        if args.model_role:
            fields["model_role"] = args.model_role
        return fail(e.reason, 64, **fields)
    if args.start and shutil.which("opencode") is None:
        return fail("opencode-command-unavailable", 69, worktree=args.worktree)
    if args.start:
        rc = check_runtime_projection(args.worktree)
        if rc != 0:
            return rc

    agent_home = resolve_agent_home()
    jobs = Path(args.jobs) if args.jobs else agent_home / ".dispatch" / "jobs.log"
    log_dir = Path(args.log_dir) if args.log_dir else agent_home / ".dispatch" / "logs"
    prompt_text, prompt_source = prompt(args)
    prompt_path = log_dir / f"{args.slug}.opencode.prompt.txt"
    log_path = log_dir / f"{args.slug}.opencode.jsonl"
    command = shell_command(args, prompt_path, log_path)

    if action in ("register", "start"):
        append_job(jobs, args)
    if action == "start":
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_text, encoding="utf-8")
        subprocess.Popen(["sh", "-c", command], start_new_session=True, env={
            **os.environ,
            "AGENT_DISPATCH_DEPTH": str(args.depth),
            "AGENT_DISPATCH_INTENSITY": args.intensity,
            "AGENT_DISPATCH_PARENT_SLUG": args.parent_slug or "",
            "AGENT_DISPATCH_WORKER_ROLE": args.worker_role or "",
            "AGENT_DISPATCH_OWNER": args.capability_owner or "",
        })

    print("adapter=opencode")
    print("runtime_surface=opencode-run-headless")
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
    print(f"agent={args.agent}")
    settings = args.resolved_model_settings
    print(f"model_source={settings['source']}")
    print(f"model_role={settings['role']}")
    print(f"model={settings['model']}")
    print(f"variant={settings['variant']}")
    print(f"job_registry={jobs}")
    print(f"registered={1 if action in ('register', 'start') else 0}")
    print(f"started={1 if action == 'start' else 0}")
    print(f"prompt_source={prompt_source}")
    print(f"prompt_file={prompt_path}")
    print(f"log_file={log_path}")
    print(f"command={command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
