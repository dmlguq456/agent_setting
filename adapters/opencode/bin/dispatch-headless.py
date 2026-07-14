#!/usr/bin/env python3
"""OpenCode headless dispatch registration/launch wrapper."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import os
import re
import shutil
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INTENSITY_LEVELS = {"direct", "quick", "standard", "strong", "thorough", "adversarial"}
QA_LEVELS = {"quick", "light", "standard", "thorough", "adversarial"}
# Verification rigor is derived from intensity — CONVENTIONS §1.1 mapping table (SoT).
# `--qa` is no longer a user-facing axis; optional, derived from --intensity when omitted.
# The jobs.log `qa=` field is retained (derived value) for fleet-collector compatibility.
QA_FROM_INTENSITY = {
    "direct": "light",
    "quick": "quick",
    "standard": "standard",
    "strong": "standard",
    "thorough": "thorough",
    "adversarial": "adversarial",
}

# SD-15 (OPERATIONS §5.10 ⑨): immediate limit/auth failure patterns — homomorphic port of the Claude
# wrapper's DEATH_PATTERNS. `opencode run --format json` surfaces provider limit/auth
# failures as text/JSON in the log; a raw tail substring scan matches either. Runtime-
# currentness (2026-07, anomalyco/opencode#8203·#11104·#34886·#15890): OpenCode prints
# "Provider Rate Limit exceeded [retrying in Ns attempt #N]", "API rate limited (429)",
# and "Rate limited. Quick retry in 1s…". ⚠️ ADAPTATION CONSTRAINT: `opencode run` has a
# known bug (#8203) where it *hangs* on API errors instead of exiting — the launch
# early-exit watch (which requires the child to exit) only catches the clean-exit path;
# hang-on-limit is caught later by dispatch-liveness.py's log scan (both share this list).
DEATH_PATTERNS = [
    ("session-limit", r"hit your (?:session|usage) limit|session limit reached"),
    ("usage-limit", r"usage[_ ]limit[_ ]reached|usage limit reached|weekly limit|"
     r"rate limit(?:ed)?|provider rate limit|exceeded retry limit|\b429\b"),
    ("auth", r"invalid api key|authentication_error|not logged in|please run /login|unauthorized|\b401\b"),
    ("credit", r"credit balance is too low|insufficient (?:credit|quota|funds)"),
]
_RESET_RE = re.compile(
    r"resets?(?:\s+at)?\s+([0-9]{1,2}:[0-9]{2}\s*(?:am|pm)?|[0-9]{1,2}\s*(?:am|pm))",
    re.I,
)


def scan_death(text: str) -> tuple[str, str] | None:
    """Return (reason, reset) if the log text shows a limit/auth death, else None.

    reset is a best-effort human string ('3pm', '15:45', ...) or '' when absent.
    Homomorphic with the Claude wrapper's scan_death and dispatch-liveness.py LIMIT_RE.
    """
    low = text.lower()
    reason = ""
    for name, pat in DEATH_PATTERNS:
        if re.search(pat, low):
            reason = name
            break
    if not reason:
        return None
    m = _RESET_RE.search(text)
    reset = re.sub(r"\s+", "", m.group(1)) if m else ""
    return reason, reset


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
    p.add_argument("--qa", default=None)  # optional/derived from --intensity (CONVENTIONS §1.1)
    p.add_argument("--intensity", default="standard")
    p.add_argument("--depth", type=int, default=1)
    p.add_argument("--parent", dest="parent_slug")
    p.add_argument(
        "--parent-session-id",
        default=os.environ.get("AGENT_DISPATCH_PARENT_SESSION_ID")
        or os.environ.get("OPENCODE_SESSION_ID")
        or os.environ.get("CODEX_THREAD_ID")
        or os.environ.get("CLAUDE_CODE_SESSION_ID"),
    )
    p.add_argument("--worker-role")
    p.add_argument("--owner", dest="capability_owner")
    p.add_argument(
        "--owner-harness",
        default=os.environ.get("AGENT_DISPATCH_OWNER_HARNESS") or "opencode",
    )
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
    p.add_argument(
        "--early-exit-watch",
        type=float,
        default=float(os.environ.get("OPENCODE_DISPATCH_EARLY_EXIT_WATCH", "8")),
        help="SD-15: seconds to watch a just-launched child for a limit/auth early death "
        "(0 disables). On detection the jobs.log row is closed done,note=dead-<reason>. "
        "Note: OpenCode may hang on limit (#8203) rather than exit; hangs are caught by "
        "dispatch-liveness's log scan, not this watch.",
    )
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
            "- Choose the stage graph from intensity before QA. direct has no plan stage; quick is a depth-1 one-shot worker that uses micro-plan plus plan-check-lite and focused verification; standard+ uses owner-plan plus optional bounded depth2 verifier/planner, synth, and durable execute/test/report.\n"
            f"- Run adapters/opencode/bin/preflight.sh qa-policy {args.qa} code and obey assurance_scope, stage_graph_selector, reviewer_counts, and independent delegation policy before claiming QA coverage.\n"
            "- Plan-check is required for quick+ but stays small; do not run independent QA after every stage by default.\n"
            "- standard+ may use bounded depth-2 planner/verifier workers when separable; thorough/adversarial expands to multi-axis/adversary workers. Synthesize short reports; depth 3+ is forbidden.\n"
        )
    return (
        "Run the requested portable harness work.\n"
        f"capability={args.capability}\nmode={args.mode}\nqa={args.qa}\n"
        f"intensity={args.intensity}\ndepth={args.depth}\nparent={args.parent_slug or '-'}\n"
        f"parent_session_id={args.parent_session_id or '-'}\n"
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
    pipe = f"capability={args.capability},mode={args.mode},qa={args.qa},intensity={args.intensity},depth={args.depth},harness=opencode"
    if args.parent_slug:
        pipe += f",parent={args.parent_slug}"
    if args.parent_session_id:
        pipe += f",parent_sid={args.parent_session_id}"
    if args.worker_role:
        pipe += f",worker_role={args.worker_role}"
    if args.capability_owner:
        pipe += f",owner={args.capability_owner}"
    if args.owner_harness:
        pipe += f",owner_harness={args.owner_harness}"
    settings = args.resolved_model_settings
    pipe += f",model_source={settings['source']},model_role={settings['role']},model={settings['model']},variant={settings['variant']}"
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    # SD-15: serialize with the same flock close_job_row uses so a concurrent close
    # (row-rewrite) and this append cannot interleave and drop rows.
    with jobs_lock(jobs):
        with jobs.open("a", encoding="utf-8") as f:
            f.write(f"{ts}\topen\t{repo}\t{args.worktree}\t{args.slug}\t{pipe}\n")


def close_job_row(jobs: Path, slug: str, worktree: str, reason: str, reset: str) -> bool:
    """SD-15: flip this dispatch's own open row to done with a dead-<reason> note.

    Matches by (slug, worktree, status==open) under the same flock append_job uses.
    Appends note=dead-<reason>[,reset=<reset>] to the pipe column. Idempotent: returns
    False if no matching open row is found. Homomorphic with the Claude/codex wrappers.
    """
    if not jobs.is_file():
        return False
    with jobs_lock(jobs):
        lines = jobs.read_text(encoding="utf-8").splitlines(keepends=True)
        changed = False
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 6:
                continue
            ts, status, repo, wt, row_slug, pipe = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
            if status != "open" or row_slug != slug or wt != worktree:
                continue
            pipe += f",note=dead-{reason}"
            if reset:
                pipe += f",reset={reset}"
            lines[i] = f"{ts}\tdone\t{repo}\t{wt}\t{row_slug}\t{pipe}\n"
            changed = True
            break
        if changed:
            jobs.write_text("".join(lines), encoding="utf-8")
        return changed


def write_reset_cache(agent_home: Path, harness: str, reason: str, reset: str) -> None:
    """SD-15↔SD-16: cache the last known limit reset for usage-check.sh to read.

    File `.dispatch/usage-reset.<harness>` holds one line: `<iso-ts> <reason> <reset>`.
    Best-effort — a cache write failure never blocks dispatch bookkeeping.
    """
    try:
        cache = agent_home / ".dispatch" / f"usage-reset.{harness}"
        cache.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        cache.write_text(f"{ts} {reason} {reset}\n", encoding="utf-8")
    except OSError:
        pass


def watch_early_death(
    proc: subprocess.Popen, log_path: Path, watch_secs: float
) -> tuple[str, str] | None:
    """SD-15: poll a just-launched child for a limit/auth early death.

    Returns (reason, reset) if the child exits within watch_secs AND its log tail matches
    a DEATH_PATTERN; otherwise None. ADAPTATION note: `opencode run` may hang on API
    errors (#8203) instead of exiting — a hang leaves proc.poll() None so this returns
    None and the row stays open; dispatch-liveness.py's log scan then catches it as DEAD.
    Only the clean-exit-on-limit path is closed here.
    """
    if watch_secs <= 0:
        return None
    deadline = time.monotonic() + watch_secs
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            break
        time.sleep(0.5)
    if proc.poll() is None:
        return None  # still alive/hanging past the watch window — not a clean early death
    try:
        tail = log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
    except OSError:
        return None
    return scan_death(tail)


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



def validate_preflight(kind: str, command: str, value: str, reason: str) -> int:
    result = subprocess.run(
        [str(ROOT / "adapters" / "opencode" / "bin" / "preflight.sh"), command, value],
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


def validate_dispatch_metadata(args: argparse.Namespace) -> int:
    rc = validate_preflight("capability", "capability-info", args.capability, "invalid-dispatch-capability")
    if rc != 0:
        return rc
    rc = validate_preflight("mode", "mode-info", args.mode, "invalid-dispatch-mode")
    if rc != 0:
        return rc
    if args.qa is None:
        args.qa = QA_FROM_INTENSITY.get(args.intensity, "standard")
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
    if args.depth == 2 and args.intensity in {"direct", "quick"}:
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
    jobs_override = args.jobs or os.environ.get("AGENT_DISPATCH_JOBS")
    jobs = Path(jobs_override) if jobs_override else agent_home / ".dispatch" / "jobs.log"
    log_dir = Path(args.log_dir) if args.log_dir else agent_home / ".dispatch" / "logs"
    prompt_text, prompt_source = prompt(args)
    prompt_path = log_dir / f"{args.slug}.opencode.prompt.txt"
    log_path = log_dir / f"{args.slug}.opencode.jsonl"
    command = shell_command(args, prompt_path, log_path)

    if action in ("register", "start"):
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_text, encoding="utf-8")
        append_job(jobs, args)
    if action == "start":
        proc = subprocess.Popen(["sh", "-c", command], start_new_session=True, env={
            **os.environ,
            "AGENT_DISPATCH_CHILD": "1",
            "AGENT_DISPATCH_DEPTH": str(args.depth),
            "AGENT_DISPATCH_INTENSITY": args.intensity,
            "AGENT_DISPATCH_PARENT_SLUG": args.parent_slug or "",
            "AGENT_DISPATCH_PARENT_SESSION_ID": args.parent_session_id or "",
            "AGENT_DISPATCH_WORKER_ROLE": args.worker_role or "",
            "AGENT_DISPATCH_OWNER": args.capability_owner or "",
            "AGENT_DISPATCH_OWNER_HARNESS": args.owner_harness or "",
            # Headless liveness contract: the OpenCode runtime child exposes
            # the dispatch slug to the plugin, which records a plugin-load
            # marker at init and touches <log_dir>/<slug>.heartbeat on every
            # session.idle event. dispatch-liveness.py inspects both as a
            # secondary alive signal independent of the OpenCode SQLite mtime.
            "OPENCODE_DISPATCH_SLUG": args.slug,
        })
        # SD-15 (OPERATIONS §5.10 ⑨): watch briefly for a clean-exit limit/auth death.
        # A hang-on-limit (#8203) escapes this watch and is caught by liveness log scan.
        death = watch_early_death(proc, log_path, args.early_exit_watch)
        if death:
            reason, reset = death
            close_job_row(jobs, args.slug, args.worktree, reason, reset)
            write_reset_cache(agent_home, "opencode", reason, reset)
            args.early_death = (reason, reset)

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
    print(f"parent_session_id={args.parent_session_id or '-'}")
    print(f"worker_role={args.worker_role or '-'}")
    print(f"owner={args.capability_owner or '-'}")
    print(f"owner_harness={args.owner_harness or '-'}")
    print(f"agent={args.agent}")
    settings = args.resolved_model_settings
    print(f"model_source={settings['source']}")
    print(f"model_role={settings['role']}")
    print(f"model={settings['model']}")
    print(f"variant={settings['variant']}")
    print(f"job_registry={jobs}")
    print(f"registered={1 if action in ('register', 'start') else 0}")
    print(f"started={1 if action == 'start' else 0}")
    early_death = getattr(args, "early_death", None)
    if early_death:
        reason, reset = early_death
        print(f"early_death={reason}")
        print(f"early_death_reset={reset or '-'}")
        print(f"row_closed=done,note=dead-{reason}")
    else:
        print("early_death=-")
    print(f"prompt_source={prompt_source}")
    print(f"prompt_file={prompt_path}")
    print(f"log_file={log_path}")
    print(f"command={command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
