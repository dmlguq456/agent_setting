#!/usr/bin/env python3
"""Claude headless dispatch registration/launch wrapper."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QA_LEVELS = {"quick", "light", "standard", "thorough", "adversarial"}
INTENSITY_LEVELS = {"direct", "quick", "standard", "strong", "thorough", "adversarial"}
# Verification rigor is derived from intensity — CONVENTIONS §1.1 mapping table (SoT).
# `--qa` is no longer a user-facing axis; it is optional and, when omitted, derived here.
# The jobs.log `qa=` field is retained (derived value) for fleet-collector compatibility.
QA_FROM_INTENSITY = {
    "direct": "light",
    "quick": "quick",
    "standard": "standard",
    "strong": "standard",
    "thorough": "thorough",
    "adversarial": "adversarial",
}

# SD-15 (OPERATIONS §5.10 ⑨): limit/auth 즉사 패턴. wrapper 가 launch 직후 조기 exit 를 잡을 때,
# 그리고 dispatch-liveness.sh / dispatch-wait.sh 가 open row 로그를 DEAD 로 판정할 때 공유하는
# 종료-사유 어휘. (reason, 소문자 substring 정규식) — 첫 매치가 사유. shell 쪽 동일 목록은
# utilities/dispatch-liveness.sh 의 LIMIT_RE 가 대응(두 런타임 경계라 의도적 복제, 동기 유지).
DEATH_PATTERNS = [
    ("session-limit", r"hit your (?:session|usage) limit|session limit reached"),
    ("usage-limit", r"usage limit reached|weekly limit|rate limit(?:ed)?|\b429\b"),
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
    Shared contract with dispatch-liveness.sh LIMIT_RE — keep the pattern lists in sync.
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
        or os.environ.get("CODEX_THREAD_ID")
        or os.environ.get("CLAUDE_CODE_SESSION_ID"),
    )
    p.add_argument("--worker-role")
    p.add_argument("--owner", dest="capability_owner")
    p.add_argument(
        "--owner-harness",
        default=os.environ.get("AGENT_DISPATCH_OWNER_HARNESS")
        or ("codex" if os.environ.get("CODEX_THREAD_ID") else "claude"),
    )
    p.add_argument("--prompt-file")
    p.add_argument("--prompt-text")
    p.add_argument("--jobs")
    p.add_argument("--log-dir")
    p.add_argument("--profile", help="profiles/<name>.yaml masked config home to attach via CLAUDE_CONFIG_DIR")
    p.add_argument("--model-role", default=os.environ.get("CLAUDE_DISPATCH_MODEL_ROLE"))
    p.add_argument("--model", default=os.environ.get("CLAUDE_DISPATCH_MODEL"))
    p.add_argument("--effort", default=os.environ.get("CLAUDE_DISPATCH_EFFORT"))
    p.add_argument(
        "--inherit-model-settings",
        action="store_true",
        help="do not override model/effort; inherit the explicitly selected profile or active Claude config",
    )
    p.add_argument(
        "--early-exit-watch",
        type=float,
        default=float(os.environ.get("CLAUDE_DISPATCH_EARLY_EXIT_WATCH", "8")),
        help="SD-15: seconds to watch a just-launched child for a limit/auth early death "
        "(0 disables). On detection the jobs.log row is closed done,note=dead-<reason>.",
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
    result = subprocess.run([str(ROOT / "adapters" / "claude" / "bin" / "model-map.sh"), role], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise ModelSelectionError("invalid-dispatch-model-role", (result.stderr or result.stdout).strip())
    fields = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    return {"model": fields["exact_model_id"], "effort": fields["reasoning"]}


def resolve_model_settings(args: argparse.Namespace) -> dict[str, str]:
    if args.inherit_model_settings:
        if args.model_role or args.model or args.effort:
            raise ModelSelectionError(
                "invalid-dispatch-model-selection",
                "--inherit-model-settings is mutually exclusive with --model-role, --model, and --effort",
            )
        return {"source": "inherit", "role": "inherit", "model": "inherit", "effort": "inherit"}
    if args.model_role and (args.model or args.effort):
        raise ModelSelectionError(
            "invalid-dispatch-model-selection",
            "--model-role is mutually exclusive with --model and --effort",
        )
    if args.model_role:
        fields = role_map(args.model_role)
        return {"source": "role", "role": args.model_role, "model": fields["model"], "effort": fields["effort"]}
    if not args.model and not args.effort:
        raise ModelSelectionError(
            "missing-dispatch-model-selection",
            "main dispatch must choose --model-role, --model with --effort, or --inherit-model-settings",
        )
    if not args.model or not args.effort:
        raise ModelSelectionError(
            "invalid-dispatch-model-selection",
            "--model and --effort must be provided together",
        )
    return {"source": "explicit", "role": "-", "model": args.model, "effort": args.effort}


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
        f"- intensity: {args.intensity}\n"
        f"- depth: {args.depth}\n"
        f"- parent: {args.parent_slug or '-'}\n"
        f"- parent_session_id: {args.parent_session_id or '-'}\n"
        f"- worker_role: {args.worker_role or '-'}\n"
        f"- owner: {args.capability_owner or '-'}\n"
        f"- owner_harness: {args.owner_harness or '-'}\n"
        f"- worktree: {args.worktree}\n"
    )
    if args.depth >= 2:
        role = (args.worker_role or "").strip()
        if role.startswith("code-") or role in {"code-plan", "code-execute", "code-test", "code-report"}:
            depth_note = (
                "Depth contract: you are a depth-2 pipeline stage-worker "
                f"('{role}') dispatched by a depth-1 conductor (2026-07-10 stage-dispatch). "
                "Read your inputs only from the artifact files named in the task (never from "
                "prior-stage conversation); write only your stage's artifact class; source is "
                "mutated by code-execute alone. Do NOT open further headless dispatch (depth 3+ "
                "is forbidden) — internal parallelism uses in-session teams. Return only a short "
                "structured verdict/summary; the conductor reads your artifacts, not your prose.\n"
            )
        else:
            depth_note = (
                "Depth contract: you are a depth-2 review sub-worker dispatched by a depth-1 "
                "owner. Stay within your single assigned role, default to read-only unless the "
                "task grants scoped write, and return a short structured summary. Do NOT open "
                "further headless dispatch; depth 3+ is forbidden.\n"
            )
    else:
        depth_note = (
            "Depth contract: depth 1 is a capability-owner worker. It should open bounded depth-2 "
            "sub-workers for separable standard+ work; for standard+ pipelines it acts as a thin "
            "conductor that dispatches each stage (code-plan/execute/test/report) as its own "
            "depth-2 session with file-only handoff. thorough/adversarial expands review to "
            "multi-axis or adversary workers. Direct/quick stay inline unless explicitly escalated; "
            "depth 3+ is forbidden. "
            "You are a one-shot process: ending your turn ends the process, and background "
            "completion notifications never arrive after that. After dispatching a stage, do NOT "
            "end the turn on a Monitor/notification wait — poll within the same turn using "
            "utilities/dispatch-wait.sh (which reuses dispatch-liveness) until the stage row "
            "leaves 'open', then harvest its artifact verdict and dispatch the next stage. On "
            "SUSPECT/DEAD, diagnose and re-dispatch rather than waiting. After harvesting a "
            "stage (including a DEAD one you re-dispatched), you MUST update its jobs.log row "
            "from 'open' to 'done' in place (OPERATIONS §5.10 registry duty) — rows left open "
            "orphan the pipe for fleet/oncall and block dispatch-wait for your own next stage "
            "(2026-07-11 drill g_stage_dispatch HARD-5 finding).\n"
        )
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
        + depth_note
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
    if args.resolved_model_settings["source"] != "inherit":
        cmd += [
            "--model",
            args.resolved_model_settings["model"],
            "--effort",
            args.resolved_model_settings["effort"],
        ]
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
    pipe = f"capability={args.capability},mode={args.mode},qa={args.qa},intensity={args.intensity},depth={args.depth},harness=claude"
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
    pipe += f",model_source={settings['source']},model_role={settings['role']},model={settings['model']},effort={settings['effort']}"
    if args.profile:
        pipe += f",profile={args.profile}"
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with jobs_lock(jobs):
        with jobs.open("a", encoding="utf-8") as f:
            f.write(f"{ts}\topen\t{repo}\t{args.worktree}\t{args.slug}\t{pipe}\n")


def close_job_row(jobs: Path, slug: str, worktree: str, reason: str, reset: str) -> bool:
    """SD-15: flip this dispatch's own open row to done with a dead-<reason> note.

    Matches by (slug, worktree, status==open) under the same flock the writer uses,
    so a concurrent conductor appending other rows is serialized. Appends
    note=dead-<reason>[,reset=<reset>] to the pipe column (kv style). Idempotent:
    returns False if no matching open row is found.
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

    Returns (reason, reset) if the child exits within watch_secs AND its log tail
    matches a DEATH_PATTERN; otherwise None (still running, or exited cleanly with
    no limit signal — normal harvest owns those). Polls in 0.5s steps.
    """
    if watch_secs <= 0:
        return None
    deadline = time.monotonic() + watch_secs
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            break
        time.sleep(0.5)
    if proc.poll() is None:
        return None  # still alive past the watch window — not an early death
    try:
        tail = log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
    except OSError:
        return None
    return scan_death(tail)


def resolve_agent_home() -> Path:
    # Mirror utilities/agent-home.sh preference order so the wrapper (writer of
    # jobs.log) and the shell readers (dispatch-liveness / dispatch-wait / the
    # conductor Stop gate) agree on ONE registry root. When AGENT_HOME is unset,
    # falling straight back to ROOT (=worktree) split the registry: the wrapper
    # wrote jobs.log under the worktree while the readers looked under
    # $HOME/agent_setting/.dispatch — so the liveness/Stop layer never saw the
    # rows the wrapper appended (SD-14b② registry gap).
    def _valid(p):
        return bool(p) and (Path(p) / "core" / "CORE.md").is_file()

    for cand in (
        os.environ.get("AGENT_HOME"),
        os.environ.get("CLAUDE_HOME"),
        str(Path.home() / "agent_setting"),
        str(Path.home() / ".claude"),
    ):
        if _valid(cand):
            return Path(cand)
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
    try:
        args.resolved_model_settings = resolve_model_settings(args)
    except ModelSelectionError as e:
        fields = {"detail": str(e)}
        if args.model_role:
            fields["model_role"] = args.model_role
        return fail(e.reason, 64, **fields)
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
        env.update({
            "CLAUDE_CODE_CHILD_SESSION": "1",
            "AGENT_DISPATCH_CHILD": "1",
            "AGENT_DISPATCH_DEPTH": str(args.depth),
            "AGENT_DISPATCH_INTENSITY": args.intensity,
            # This session's own slug — the conductor Stop gate / dispatch-wait
            # identify "open child rows whose parent= equals MY slug" and cannot
            # do so from AGENT_DISPATCH_PARENT_SLUG (which points at the parent).
            "AGENT_DISPATCH_SELF_SLUG": args.slug,
            "AGENT_DISPATCH_PARENT_SLUG": args.parent_slug or "",
            "AGENT_DISPATCH_PARENT_SESSION_ID": args.parent_session_id or "",
            "AGENT_DISPATCH_WORKER_ROLE": args.worker_role or "",
            "AGENT_DISPATCH_OWNER": args.capability_owner or "",
            "AGENT_DISPATCH_OWNER_HARNESS": args.owner_harness or "",
        })
        if args.profile:
            env["CLAUDE_CONFIG_DIR"] = str(instance_dir)
        proc = subprocess.Popen(["sh", "-c", command], env=env, start_new_session=True)
        # SD-15 (OPERATIONS §5.10 ⑨): watch briefly for a limit/auth early death so
        # a limit-killed launch closes its own row now instead of lingering `open`
        # until liveness SUSPECT catches it minutes later.
        death = watch_early_death(proc, log_path, args.early_exit_watch)
        if death:
            reason, reset = death
            close_job_row(jobs, args.slug, args.worktree, reason, reset)
            write_reset_cache(agent_home, "claude", reason, reset)
            args.early_death = (reason, reset)

    print("adapter=claude")
    print("runtime_surface=claude-print-headless")
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
    settings = args.resolved_model_settings
    print(f"model_source={settings['source']}")
    print(f"model_role={settings['role']}")
    print(f"model={settings['model']}")
    print(f"effort={settings['effort']}")
    print(f"profile={args.profile or '-'}")
    print(f"instance_home={instance_dir if instance_dir else '-'}")
    print(f"job_registry={jobs}")
    print(f"registry_lock={jobs}.lock")
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
