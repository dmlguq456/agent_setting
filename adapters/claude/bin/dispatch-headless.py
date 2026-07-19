#!/usr/bin/env python3
"""Claude headless dispatch registration/launch wrapper."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import json
import os
import re
import signal
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "utilities"))
from dispatch_contract import (  # noqa: E402
    DispatchContractError,
    anchored_capacity_failure,
    claim_attempt_row,
    close_attempt_row,
    completion_marker_gate,
    ensure_global_registry_writable,
    new_attempt_id,
    resolve_global_registry,
    validate_nested_eligibility,
)
from worker_bootstrap import (  # noqa: E402
    assigned_contract,
    profile_worker_type,
    render_worker_bootstrap,
    resolve_worker_type,
)
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

# SD-15 (OPERATIONS §5.10 ⑨): immediate limit/auth failure patterns shared
# between launch-time early-exit detection and the liveness/wait DEAD verdict.
# Each tuple is (reason, lowercase substring regex); the first match wins.
# utilities/dispatch-liveness.sh intentionally duplicates the list as LIMIT_RE
# across the Python/shell runtime boundary; keep the two synchronized.
DEATH_PATTERNS = [
    ("capacity", r"(?:selected\s+)?model\b.{0,80}\b(?:is\s+)?at capacity\b"),
    ("network-operation-not-permitted", r"operation not permitted|network is unreachable|network access denied"),
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


def scan_anchored_death(text: str) -> tuple[str, str] | None:
    """Inspect only terse terminal CLI lines, never completion-report prose."""
    for line in [line.strip() for line in text.splitlines() if line.strip()][-3:]:
        if len(line) > 200:
            continue
        death = scan_death(line)
        if death:
            if death[0] == "capacity" and not anchored_capacity_failure(line):
                continue
            return death
    return None


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
    p.add_argument(
        "--parent-cwd",
        default=os.environ.get("AGENT_DISPATCH_PARENT_CWD") or None,
    )
    p.add_argument("--worker-role")
    p.add_argument("--worker-type", choices=("owner", "stage", "review", "support"))
    p.add_argument("--owner", dest="capability_owner")
    p.add_argument("--route-file")
    p.add_argument("--route-id")
    p.add_argument("--route-hash")
    p.add_argument("--route-node")
    p.add_argument("--registry-digest")
    p.add_argument("--write-scope")
    p.add_argument("--completion-gate")
    p.add_argument("--harness-affinity")
    p.add_argument(
        "--owner-harness",
        default=os.environ.get("AGENT_DISPATCH_OWNER_HARNESS")
        or ("codex" if os.environ.get("CODEX_THREAD_ID") else "claude"),
    )
    p.add_argument("--prompt-file")
    p.add_argument("--prompt-text")
    p.add_argument("--jobs")
    p.add_argument("--attempt-id")
    p.add_argument("--broker-request-id")
    p.add_argument("--fallback-ordinal", type=int, default=0)
    p.add_argument("--capacity-retry", type=int, choices=(0, 1), default=0)
    p.add_argument("--prior-attempt-id")
    p.add_argument("--cooled-model")
    p.add_argument("--selection-source")
    p.add_argument("--launch-authority", choices=("conductor", "ancestor-broker"), default="conductor")
    p.add_argument("--parent-harness", default=os.environ.get("AGENT_DISPATCH_CURRENT_HARNESS") or os.environ.get("AGENT_DISPATCH_OWNER_HARNESS") or "claude")
    p.add_argument("--parent-transport", default=os.environ.get("AGENT_DISPATCH_CURRENT_TRANSPORT") or "unknown")
    p.add_argument("--parent-sandbox", default=os.environ.get("AGENT_DISPATCH_CURRENT_SANDBOX") or "unknown")
    # default None (not "unknown"): an explicitly supplied `--nested-eligibility
    # unknown` must stay distinguishable from an absent flag — explicit evidence,
    # even unknown, is never overwritten by the internal probe.
    p.add_argument("--nested-eligibility", choices=("supported", "unsupported", "unknown"), default=None)
    p.add_argument("--eligibility-source", default="")
    p.add_argument("--eligibility-failure-class", default="")
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


def resolve_artifact_root(worktree: str) -> str:
    result = subprocess.run(
        [str(ROOT / "utilities" / "artifact-root.sh"), worktree],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    value = result.stdout.strip()
    if result.returncode != 0 or not value or not Path(value).is_absolute():
        detail = (result.stderr or result.stdout or "invalid artifact root").strip()
        raise ValueError(detail)
    return value


def dispatch_prompt(args: argparse.Namespace) -> tuple[str, str]:
    task, source = task_prompt(args)
    args.worker_type = resolve_worker_type(
        explicit=args.worker_type,
        depth=args.depth,
        worker_role=args.worker_role,
        route_node=args.route_node,
        profile_type=profile_worker_type(ROOT, args.profile),
    )
    bootstrap = render_worker_bootstrap(ROOT, args.worker_type)
    args.assigned_contract = assigned_contract(
        capability=args.capability,
        worker_type=args.worker_type,
        worker_role=args.worker_role,
        route_node=args.route_node,
    )
    profile_note = (
        f"masked specialization profile={args.profile}; its CLAUDE.md contains only the runtime attach layer and selected specialization"
        if args.profile
        else "profile=-"
    )
    heartbeat = ""
    if args.attempt_id and args.route_id and args.route_node:
        base = (
            f"python3 {shlex.quote(str(ROOT / 'utilities/dispatch-progress.py'))} heartbeat "
            f"--attempt-id {shlex.quote(args.attempt_id)} "
            f"--route-id {shlex.quote(args.route_id)} "
            f"--route-node {shlex.quote(args.route_node)} "
            "--jobs \"$AGENT_DISPATCH_JOBS\""
        )
        heartbeat = (
            "Stage progress contract (SD-58):\n"
            f"- Emit analysis on entry: {base} --phase analysis --kind registry --evidence analysis-entered\n"
            "- After a real tool call, write, test, or artifact update, run the same command with phase tool|file-write|test|artifact and kind tool|file|test|artifact plus a deterministic id/signature.\n"
            "- Repeated prose or an unchanged phase/evidence pair is not progress. Emit terminal only after the assigned artifact is durable.\n\n"
        )
    return (
        f"{bootstrap}\n"
        "Dispatch metadata:\n"
        f"- capability: {args.capability}\n"
        f"- mode: {args.mode}\n"
        f"- qa: {args.qa}\n"
        f"- intensity: {args.intensity}\n"
        f"- depth: {args.depth}\n"
        f"- worker_type: {args.worker_type}\n"
        f"- assigned_contract: {args.assigned_contract}\n"
        f"- parent: {args.parent_slug or '-'}\n"
        f"- parent_session_id: {args.parent_session_id or '-'}\n"
        f"- worker_role: {args.worker_role or '-'}\n"
        f"- owner: {args.capability_owner or '-'}\n"
        f"- owner_harness: {args.owner_harness or '-'}\n"
        f"- worktree: {args.worktree}\n"
        f"- artifact_root: {args.artifact_root}\n"
        f"- route_state: {'consume the immutable record already validated by the wrapper' if args.route_file else 'validated dispatch metadata'}\n"
        f"- {profile_note}\n\n"
        "Claude realization:\n"
        "- The wrapper validates route/scope and the masked profile before launch. Re-run route validation only for a safety recheck.\n"
        f"- Read only the exposed {args.assigned_contract} Skill, named artifacts, and selected specialization. General Claude custom subagents may still inherit project CLAUDE.md; do not manually load a full harness bootstrap.\n"
        "- Owner workers use the inherited registry, launch checked adapter wrappers directly, poll in this turn, harvest artifacts, and close rows; stage/review/support workers do not dispatch.\n\n"
        f"{heartbeat}"
        "Assignment:\n"
        f"{task.rstrip()}\n\n"
        "End with the kernel's exact three-line handoff and nothing after it.\n",
        source,
    )


def shell_command(args: argparse.Namespace, prompt_path: Path, log_path: Path) -> str:
    # `claude -p` reads the prompt from stdin when no positional prompt is
    # given and prints the response non-interactively, mirroring the codex
    # wrapper's file-piped `codex exec ... < prompt_path` invocation.
    cmd = ["claude", "-p", "--add-dir", args.artifact_root]
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


def _effective_parent_cwd(args):
    """Where the DISPATCHING session lives — not merely where the wrapper ran.

    Orchestrators routinely `cd` into the task worktree before dispatching, so a raw
    getcwd() records the child's own worktree — a path that can never anchor the
    parent session row in Fleet (observed: codex depth-1 dispatches stayed orphan,
    2026-07-16). When the launch cwd sits inside the task worktree and that worktree
    is linked, back-map to the primary checkout instead; explicit --parent-cwd or
    AGENT_DISPATCH_PARENT_CWD still wins via args.parent_cwd.
    """
    cwd = os.path.realpath(args.parent_cwd or os.getcwd())
    try:
        wt = os.path.realpath(args.worktree)
    except (OSError, TypeError):
        return cwd
    if args.parent_cwd is None and (cwd == wt or cwd.startswith(wt + os.sep)):
        try:
            out = subprocess.check_output(
                ["git", "-C", wt, "worktree", "list", "--porcelain"],
                text=True, stderr=subprocess.DEVNULL)
            first = next((ln.split(" ", 1)[1] for ln in out.splitlines()
                          if ln.startswith("worktree ")), None)
            if first and os.path.realpath(first) != wt:
                return os.path.realpath(first)
        except (OSError, subprocess.SubprocessError, IndexError):
            pass
    return cwd


def append_job(jobs: Path, args: argparse.Namespace) -> bool:
    repo = subprocess.check_output(["git", "-C", args.worktree, "rev-parse", "--show-toplevel"], text=True).strip()
    pipe = f"capability={args.capability},mode={args.mode},qa={args.qa},intensity={args.intensity},depth={args.depth},harness=claude"
    if args.parent_slug:
        pipe += f",parent={args.parent_slug}"
    if args.parent_session_id:
        pipe += f",parent_sid={args.parent_session_id}"
    if args.parent_slug or args.parent_session_id:
        # OPERATIONS §5.10 pipe contract lists parent_cwd; without it a cross-harness
        # child whose parent_sid is synthetic can never nest in Fleet (2026-07-15).
        pipe += f",parent_cwd={_effective_parent_cwd(args)}"
    if args.worker_role:
        pipe += f",worker_role={args.worker_role}"
    pipe += f",worker_type={args.worker_type}"
    if args.capability_owner:
        pipe += f",owner={args.capability_owner}"
    if args.owner_harness:
        pipe += f",owner_harness={args.owner_harness}"
    if args.depth >= 2:
        pipe += (
            f",parent_harness={args.parent_harness},parent_transport={args.parent_transport}"
            f",parent_sandbox={args.parent_sandbox},child_harness=claude"
            f",nested_eligibility={args.nested_eligibility},eligibility_source={args.eligibility_source}"
            f",eligibility_failure_class={args.eligibility_failure_class or '-'}"
            f",eligibility_probe={getattr(args, 'eligibility_probe', None) or '-'}"
        )
    for key in ("route_file", "route_id", "route_hash", "route_node", "registry_digest", "write_scope", "completion_gate", "harness_affinity"):
        value = getattr(args, key)
        if value:
            pipe += f",{key}={value}"
    settings = args.resolved_model_settings
    pipe += f",model_source={settings['source']},model_role={settings['role']},model={settings['model']},effort={settings['effort']}"
    if args.profile:
        pipe += f",profile={args.profile}"
    pipe += f",artifact_root={args.artifact_root},log_file={args.log_path}"
    if args.attempt_id:
        pipe += f",attempt_id={args.attempt_id},launch_authority={args.launch_authority},fallback_ordinal={args.fallback_ordinal}"
    if args.capacity_retry:
        pipe += (
            f",capacity_retry=1,prior_attempt_id={args.prior_attempt_id}"
            f",cooled_model={args.cooled_model},selection_source={args.selection_source}"
        )
    if args.broker_request_id:
        pipe += f",broker_request_id={args.broker_request_id}"
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    row = f"{ts}\topen\t{repo}\t{args.worktree}\t{args.slug}\t{pipe}"
    exclusive = ({"route_id": args.route_id, "route_node": args.route_node,
                  "capacity_retry": "1"} if args.capacity_retry else None)
    return claim_attempt_row(
        jobs, args.attempt_id, row, launch=args.action == "start",
        exclusive_metadata=exclusive,
    )


def close_job_row(jobs: Path, slug: str, worktree: str, reason: str, reset: str, attempt_id: str | None = None) -> bool:
    """SD-15: flip this dispatch's own open row to done with a dead-<reason> note.

    Matches by (slug, worktree, status==open) under the same flock the writer uses,
    so a concurrent conductor appending other rows is serialized. Appends
    note=dead-<reason>[,reset=<reset>] to the pipe column (kv style). Idempotent:
    returns False if no matching open row is found.
    """
    if attempt_id:
        evidence = {"reset": reset} if reset else {}
        if reason == "capacity":
            evidence.update(failure_class="capacity", detected_by="anchored-early-exit")
        return close_attempt_row(jobs, attempt_id, f"dead-{reason}", evidence=evidence)
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
            if attempt_id and f"attempt_id={attempt_id}" not in pipe.split(","):
                continue
            pipe += f",note=dead-{reason}"
            if reason == "capacity":
                pipe += ",failure_class=capacity,detected_by=anchored-early-exit"
            if reset:
                pipe += f",reset={reset}"
            lines[i] = f"{ts}\tdone\t{repo}\t{wt}\t{row_slug}\t{pipe}\n"
            changed = True
            break
        if changed:
            jobs.write_text("".join(lines), encoding="utf-8")
        return changed


def annotate_job_row(jobs: Path, slug: str, worktree: str, extra_kv: str, attempt_id: str | None = None) -> bool:
    """Append `,<extra_kv>` to the pipe column of this dispatch's open row.

    Same match keys and flock discipline as close_job_row. Used right after
    launch to record the child pid (`pid=<n>`, OPERATIONS §5.10 job registry)
    so dispatch-liveness judges the child by process instead of transcript
    mtime — a conductor sharing the child's worktree keeps the transcript
    directory fresh and masks an exited child behind ALIVE (shared-worktree
    aliasing, observed 2026-07-13).
    """
    if not jobs.is_file():
        return False
    with jobs_lock(jobs):
        lines = jobs.read_text(encoding="utf-8").splitlines(keepends=True)
        for i, line in enumerate(lines):
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 6:
                continue
            ts, status, repo, wt, row_slug, pipe = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
            if status != "open" or row_slug != slug or wt != worktree:
                continue
            if attempt_id and f"attempt_id={attempt_id}" not in pipe.split(","):
                continue
            lines[i] = f"{ts}\t{status}\t{repo}\t{wt}\t{row_slug}\t{pipe},{extra_kv}\n"
            jobs.write_text("".join(lines), encoding="utf-8")
            return True
    return False


def process_start_ticks(pid: int) -> str:
    try:
        return (Path("/proc") / str(pid) / "stat").read_text(encoding="utf-8").split()[21]
    except (OSError, IndexError):
        return ""


def seed_launch_heartbeat(args: argparse.Namespace, jobs: Path, pid: int, start: str) -> str:
    if not (args.attempt_id and args.route_id and args.route_node):
        return "not-route-bound"
    result = subprocess.run(
        [sys.executable, str(ROOT / "utilities/dispatch-progress.py"), "heartbeat",
         "--attempt-id", args.attempt_id, "--route-id", args.route_id,
         "--route-node", args.route_node, "--jobs", str(jobs),
         "--phase", "launch", "--kind", "registry",
         "--evidence", f"pid={pid};start={start or '-'}"],
        cwd=ROOT, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        check=False,
    )
    return "ok" if result.returncode == 0 else "failed"


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

    Returns (reason, reset) if the child exits within watch_secs and its log tail
    matches a DEATH_PATTERN. SD-59 capacity is the one proactive exception: an
    anchored live capacity line interrupts the exact process group for failover.
    Otherwise returns None. Polls in 0.5s steps.
    """
    if watch_secs <= 0:
        return None
    deadline = time.monotonic() + watch_secs
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            break
        try:
            live_tail = log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
        except OSError:
            live_tail = ""
        live_death = scan_anchored_death(live_tail)
        if live_death and live_death[0] == "capacity":
            try:
                os.killpg(proc.pid, signal.SIGINT)
                proc.wait(timeout=2)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                pass
            return live_death
        time.sleep(0.5)
    if proc.poll() is None:
        return None  # still alive past the watch window — not an early death
    try:
        tail = log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
    except OSError:
        return None
    death = scan_anchored_death(tail)
    if death:
        return death
    if proc.returncode:
        return f"launch-exit-{proc.returncode}", ""
    return None


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


def bind_internal_eligibility_probe(args: argparse.Namespace) -> None:
    """SD-66 fix-forward: run the nested-eligibility probe in-wrapper when a
    depth-2 ``--start`` carries no explicit evidence, instead of failing
    closed on missing flags a caller never had reason to supply by hand.

    Triggers only when both evidence options are still at their parser
    default (``unknown``/empty) and the parent identity needed to run the
    probe is fully known. Explicit supported/unsupported/unknown/partial
    evidence, depth-1, and dry-run/register never reach this function's
    trigger path (callers gate on depth/action before calling it). The probe's
    own JSON status is trusted only when every identity field it echoes back
    matches the request; a malformed/mismatched/erroring probe leaves
    ``nested_eligibility`` at its unknown default so `validate_nested_eligibility`
    still fails closed.
    """
    if args.depth < 2 or args.action != "start":
        return
    if getattr(args, "nested_eligibility_explicit", False):
        return
    if args.nested_eligibility != "unknown" or args.eligibility_source:
        return
    if not all((args.parent_harness, args.parent_transport, args.parent_sandbox, args.launch_authority)):
        return
    if "unknown" in (args.parent_harness, args.parent_transport, args.parent_sandbox):
        return
    args.eligibility_probe = "internal"
    probe = ROOT / "utilities" / "nested-dispatch-eligibility.py"
    result = subprocess.run(
        [
            sys.executable, str(probe),
            "--parent-harness", args.parent_harness,
            "--parent-transport", args.parent_transport,
            "--parent-sandbox", args.parent_sandbox,
            "--child-harness", "claude",
            "--launch-authority", args.launch_authority,
            "--worktree", args.worktree,
            "--json",
        ],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    try:
        row = json.loads(result.stdout)
    except (ValueError, TypeError):
        return
    if (
        row.get("parent_harness") != args.parent_harness
        or row.get("parent_transport") != args.parent_transport
        or row.get("parent_sandbox") != args.parent_sandbox
        or row.get("child_harness") != "claude"
        or row.get("launch_authority") != args.launch_authority
        or row.get("status") not in ("supported", "unsupported", "unknown")
    ):
        return
    if row["status"] == "supported" and result.returncode != 0:
        # A failed probe process cannot mint launch-eligible evidence, even if
        # its stdout says supported; checked unsupported/unknown results keep
        # their nonzero-rc path and still fail closed downstream.
        return
    args.nested_eligibility = row["status"]
    args.eligibility_source = row.get("probe_source") or ""
    args.eligibility_failure_class = row.get("failure_class") or ""


def validate_route_record(args: argparse.Namespace) -> int:
    routed = any((args.route_id, args.route_hash, args.route_node, args.registry_digest))
    if routed and not args.route_file:
        return fail("route-record-required", 65, route_id=args.route_id or "-")
    if not args.route_file:
        return 0
    required = ("route_id", "route_hash", "route_node", "registry_digest", "write_scope")
    missing = [name for name in required if not getattr(args, name)]
    if missing: return fail("route-metadata-missing", 65, fields=",".join(missing))
    command = [sys.executable, str(ROOT/"utilities"/"worker-route-guard.py"), "validate",
        "--route", args.route_file, "--node", args.route_node, "--cwd", args.worktree,
        "--artifact-root", args.artifact_root, "--capability", args.capability,
        "--intensity", args.intensity, "--write-scope", args.write_scope,
        "--route-id", args.route_id, "--route-hash", args.route_hash,
        "--registry-digest", args.registry_digest]
    if args.attempt_id:
        command += ["--current-attempt", args.attempt_id]
    result=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if result.returncode:
        if result.stdout: print(result.stdout,end="")
        if result.stderr: print(result.stderr,end="",file=sys.stderr)
        return fail("worker-route-validation-failed",result.returncode,route_file=args.route_file)
    args.route_validation=result.stdout.strip()
    try:
        completion_marker_gate(args.route_file, args.route_node, args.action, args.agent_home)
    except DispatchContractError as e:
        return fail(e.reason, 65, detail=e.detail, child_spawned="0")
    return 0


def main(argv: list[str]) -> int:
    args = parser().parse_args(argv[1:])
    args.nested_eligibility_explicit = args.nested_eligibility is not None
    if args.nested_eligibility is None:
        args.nested_eligibility = "unknown"
    if args.capacity_retry and not all(
        (args.prior_attempt_id, args.cooled_model, args.selection_source)
    ):
        return fail("capacity-retry-evidence-missing", 64, child_spawned="0")
    if not Path(args.worktree).is_absolute():
        return fail("worktree-must-be-absolute", 64, worktree=args.worktree)
    args.worktree = str(Path(args.worktree).resolve())
    action = "start" if args.start else "register" if args.register else "dry-run"
    args.action = action
    if args.broker_request_id or args.launch_authority == "ancestor-broker":
        return fail("launch-broker-retired", 76, child_spawned="0")
    args.agent_home = resolve_agent_home()
    worktree = Path(args.worktree)
    if not worktree.is_dir():
        return fail("worktree-not-found", 66, worktree=args.worktree)
    if subprocess.run(
        ["git", "-C", args.worktree, "rev-parse", "--is-inside-work-tree"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        return fail("not-a-git-worktree", 65, worktree=args.worktree)
    try:
        args.artifact_root = resolve_artifact_root(args.worktree)
    except ValueError as e:
        return fail("artifact-root-resolution-failed", 64, detail=str(e), worktree=args.worktree)
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
    args.eligibility_probe = "-"
    bind_internal_eligibility_probe(args)
    try:
        validate_nested_eligibility(
            depth=args.depth, action=action, parent_harness=args.parent_harness,
            parent_transport=args.parent_transport, parent_sandbox=args.parent_sandbox,
            child_harness="claude", launch_authority=args.launch_authority,
            status=args.nested_eligibility, source=args.eligibility_source,
        )
    except DispatchContractError as e:
        return fail(
            e.reason, 69, detail=e.detail,
            parent_harness=args.parent_harness or "-",
            parent_transport=args.parent_transport or "-",
            parent_sandbox=args.parent_sandbox or "-",
            child_harness="claude",
            launch_authority=args.launch_authority,
            nested_eligibility=args.nested_eligibility,
            eligibility_source=args.eligibility_source or "-",
            eligibility_failure_class=args.eligibility_failure_class or "-",
            eligibility_probe=args.eligibility_probe,
        )
    rc=validate_route_record(args)
    if rc != 0: return rc
    try:
        args.resolved_model_settings = resolve_model_settings(args)
    except ModelSelectionError as e:
        fields = {"detail": str(e)}
        if args.model_role:
            fields["model_role"] = args.model_role
        return fail(e.reason, 64, **fields)
    if args.start and shutil.which("claude") is None:
        return fail("claude-command-unavailable", 69, worktree=args.worktree)

    agent_home = args.agent_home
    try:
        registry = resolve_global_registry(agent_home, args.jobs, args.depth, action)
        jobs = registry.path
        args.attempt_id = new_attempt_id(args.attempt_id) if action in ("register", "start") else args.attempt_id
        if action in ("register", "start"):
            ensure_global_registry_writable(jobs)
    except DispatchContractError as e:
        return fail(e.reason, 73, detail=e.detail, child_spawned="0")
    log_dir = Path(args.log_dir) if args.log_dir else agent_home / ".dispatch" / "logs"
    home_root = agent_home / ".dispatch" / "homes"
    instance_dir = home_root / f"{args.slug}.{args.profile}" if args.profile else None

    prompt_text, prompt_source = dispatch_prompt(args)
    prompt_path = log_dir / f"{args.slug}.claude.prompt.txt"
    log_name = (f"{args.slug}.{args.attempt_id}.claude.log"
                if args.route_id and args.attempt_id else f"{args.slug}.claude.log")
    log_path = log_dir / log_name
    args.log_path = log_path
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
        if action == "start":
            governor = ROOT / "utilities" / "model-worker-governor.py"
            governor_root = Path(
                os.environ.get("AGENT_MODEL_GOVERNOR_ROOT")
                or Path(args.artifact_root) / ".runtime" / "model-worker-governor"
            )
            gate = subprocess.run([sys.executable, str(governor), "--root", str(governor_root), "check", "--class", "dispatch"])
            if gate.returncode != 0:
                return fail("model-worker-governor-denied", 75)
        args.attempt_claimed = append_job(jobs, args)
    else:
        args.attempt_claimed = False

    if action == "start" and args.attempt_claimed:
        env = {key: value for key, value in os.environ.items() if not key.startswith("AGENT_DISPATCH_BROKER_")}
        env.update({
            "AGENT_SESSION_ROLE": "worker",
            "CLAUDE_CODE_CHILD_SESSION": "1",
            "AGENT_DISPATCH_CHILD": "1",
            "AGENT_DISPATCH_DEPTH": str(args.depth),
            "AGENT_DISPATCH_PARENT_CWD": (_effective_parent_cwd(args) if (args.parent_slug or args.parent_session_id) else ""),
            "AGENT_DISPATCH_INTENSITY": args.intensity,
            # This session's own slug — the conductor Stop gate / dispatch-wait
            # identify "open child rows whose parent= equals MY slug" and cannot
            # do so from AGENT_DISPATCH_PARENT_SLUG (which points at the parent).
            "AGENT_DISPATCH_SELF_SLUG": args.slug,
            "AGENT_DISPATCH_PARENT_SLUG": args.parent_slug or "",
            "AGENT_DISPATCH_PARENT_SESSION_ID": args.parent_session_id or "",
            "AGENT_DISPATCH_WORKER_ROLE": args.worker_role or "",
            "AGENT_DISPATCH_WORKER_TYPE": args.worker_type,
            "AGENT_DISPATCH_OWNER": args.capability_owner or "",
            "AGENT_DISPATCH_OWNER_HARNESS": args.owner_harness or "",
            "AGENT_ARTIFACT_ROOT": args.artifact_root,
            "AGENT_ROUTE_FILE": args.route_file or "",
            "AGENT_ROUTE_ID": args.route_id or "",
            "AGENT_ROUTE_NODE": args.route_node or "",
            "AGENT_MODEL_GOVERNOR_ROOT": str(governor_root),
            "AGENT_DISPATCH_JOBS": str(jobs),
            "AGENT_DISPATCH_CURRENT_HARNESS": "claude",
            "AGENT_DISPATCH_CURRENT_TRANSPORT": "headless",
            "AGENT_DISPATCH_CURRENT_SANDBOX": "adapter-default",
        })
        if args.profile:
            env["CLAUDE_CONFIG_DIR"] = str(instance_dir)
        try:
            proc = subprocess.Popen(
                [sys.executable, str(governor), "--root", str(governor_root),
                 "run", "--class", "dispatch", "--", "sh", "-c", command],
                env=env,
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            close_job_row(jobs, args.slug, args.worktree, "launch-error", "", args.attempt_id)
            return fail("child-launch-failed", 70, detail=str(exc), attempt_id=args.attempt_id)
        # Shared-worktree aliasing (OPERATIONS §5.10 signal order ①): record
        # the child pid so liveness can use a process signal. Conductor activity
        # in the same worktree can contaminate transcript mtime.
        start_ticks = process_start_ticks(proc.pid)
        launch_identity = f"pid={proc.pid}" + (f",pid_start={start_ticks}" if start_ticks else "")
        if args.depth >= 2 and os.environ.get("AGENT_DISPATCH_CHILD") == "1":
            launch_identity += ",pid_scope=namespace-local"
        annotate_job_row(jobs, args.slug, args.worktree, launch_identity, args.attempt_id)
        args.child_pid = proc.pid
        args.child_pid_start = start_ticks
        args.launch_heartbeat = seed_launch_heartbeat(args, jobs, proc.pid, start_ticks)
        # SD-15 (OPERATIONS §5.10 ⑨): watch briefly for a limit/auth early death so
        # a limit-killed launch closes its own row now instead of lingering `open`
        # until liveness SUSPECT catches it minutes later.
        death = watch_early_death(proc, log_path, args.early_exit_watch)
        if death:
            reason, reset = death
            close_job_row(jobs, args.slug, args.worktree, reason, reset, args.attempt_id)
            if reason != "capacity":
                write_reset_cache(agent_home, "claude", reason, reset)
            args.early_death = (reason, reset)

    print("adapter=claude")
    print("runtime_surface=claude-print-headless")
    print(f"status={action}")
    print(f"worktree={args.worktree}")
    print(f"artifact_root={args.artifact_root}")
    print("artifact_write_scope=canonical-only")
    print(f"slug={args.slug}")
    print(f"capability={args.capability}")
    print(f"mode={args.mode}")
    print(f"qa={args.qa}")
    print(f"intensity={args.intensity}")
    print(f"depth={args.depth}")
    print(f"eligibility_probe={getattr(args, 'eligibility_probe', None) or '-'}")
    print(f"parent={args.parent_slug or '-'}")
    print(f"parent_session_id={args.parent_session_id or '-'}")
    print(f"worker_role={args.worker_role or '-'}")
    print(f"worker_type={args.worker_type}")
    print(f"owner={args.capability_owner or '-'}")
    print(f"owner_harness={args.owner_harness or '-'}")
    print(f"route_file={args.route_file or '-'}")
    print(f"route_validation={getattr(args, 'route_validation', None) or '-'}")
    settings = args.resolved_model_settings
    print(f"model_source={settings['source']}")
    print(f"model_role={settings['role']}")
    print(f"model={settings['model']}")
    print(f"effort={settings['effort']}")
    print(f"profile={args.profile or '-'}")
    print(f"instance_home={instance_dir if instance_dir else '-'}")
    print(f"job_registry={jobs}")
    print("broker_lifecycle=retired")
    print(f"registry_authority={registry.source}")
    print(f"attempt_id={args.attempt_id or '-'}")
    print(f"launch_authority={args.launch_authority}")
    print(f"fallback_ordinal={args.fallback_ordinal}")
    print(f"registry_lock={jobs}.lock")
    print(f"duplicate_attempt={0 if args.attempt_claimed or action == 'dry-run' else 1}")
    print(f"registered={1 if args.attempt_claimed else 0}")
    print(f"started={1 if action == 'start' and args.attempt_claimed else 0}")
    print(f"child_pid={getattr(args, 'child_pid', None) or '-'}")
    print(f"child_pid_start={getattr(args, 'child_pid_start', None) or '-'}")
    print(f"launch_heartbeat={getattr(args, 'launch_heartbeat', 'not-started')}")
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
