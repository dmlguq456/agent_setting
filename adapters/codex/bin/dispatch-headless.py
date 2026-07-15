#!/usr/bin/env python3
"""Codex headless dispatch registration/launch wrapper."""

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
sys.path.insert(0, str(ROOT / "utilities"))
from dispatch_contract import (  # noqa: E402
    DispatchContractError,
    ensure_global_registry_writable,
    ensure_launch_broker,
    new_attempt_id,
    resolve_global_registry,
    validate_nested_eligibility,
)
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
INTENSITY_LEVELS = {"direct", "quick", "standard", "strong", "thorough", "adversarial"}

# SD-15 (OPERATIONS §5.10 ⑨): immediate limit/auth failure patterns — homomorphic port of the Claude
# wrapper's DEATH_PATTERNS. codex exec surfaces provider limit/auth failures as JSON
# events (`--json`), but a raw tail substring scan still matches the text inside those
# events, so no JSON parsing is needed (same as the Claude tail scan). Runtime-currentness
# (2026-07, openai/codex#9148·#12677·#11434·#4840): codex prints "exceeded retry limit,
# last status: 429 Too Many Requests" / "usage_limit_reached" and generally exits non-zero
# on retry exhaustion, so the launch early-exit watch is realizable (best-effort). The
# shell/other-adapter counterparts (dispatch-liveness.py LIMIT_RE) keep the same list —
# intentional cross-runtime duplication, keep in sync.
DEATH_PATTERNS = [
    ("network-operation-not-permitted", r"operation not permitted|network is unreachable|network access denied"),
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
    p.add_argument("--owner", dest="capability_owner")
    p.add_argument("--route-file")
    p.add_argument("--route-id")
    p.add_argument("--route-hash")
    p.add_argument("--route-node")
    p.add_argument("--registry-digest")
    p.add_argument("--write-scope")
    p.add_argument("--completion-gate")
    p.add_argument(
        "--owner-harness",
        default=os.environ.get("AGENT_DISPATCH_OWNER_HARNESS") or "codex",
    )
    p.add_argument("--prompt-file")
    p.add_argument("--prompt-text")
    p.add_argument("--jobs")
    p.add_argument("--attempt-id")
    p.add_argument("--broker-request-id")
    p.add_argument("--fallback-ordinal", type=int, default=0)
    p.add_argument("--launch-authority", choices=("conductor", "ancestor-broker"), default="conductor")
    p.add_argument("--parent-harness", default=os.environ.get("AGENT_DISPATCH_CURRENT_HARNESS") or os.environ.get("AGENT_DISPATCH_OWNER_HARNESS") or "codex")
    p.add_argument("--parent-transport", default=os.environ.get("AGENT_DISPATCH_CURRENT_TRANSPORT") or "unknown")
    p.add_argument("--parent-sandbox", default=os.environ.get("AGENT_DISPATCH_CURRENT_SANDBOX") or "unknown")
    p.add_argument("--nested-eligibility", choices=("supported", "unsupported", "unknown"), default="unknown")
    p.add_argument("--eligibility-source", default="")
    p.add_argument("--eligibility-failure-class", default="")
    p.add_argument("--log-dir")
    p.add_argument(
        "--sandbox",
        choices=("read-only", "workspace-write", "danger-full-access"),
        default=os.environ.get("CODEX_DISPATCH_SANDBOX", "workspace-write"),
    )
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
    p.add_argument(
        "--early-exit-watch",
        type=float,
        default=float(os.environ.get("CODEX_DISPATCH_EARLY_EXIT_WATCH", "8")),
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
        [str(ROOT / "adapters" / "codex" / "bin" / "model-map.sh"), role],
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
        model = fields.get("exact_model_id")
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
            "- Select the stage graph from `intensity` before using QA. `direct` has no code-plan/plan-check/durable plan artifact; `quick` is a depth-1 one-shot worker that uses an inline micro-plan plus plan-check-lite and focused verification; `standard+` uses owner-plan plus optional bounded depth2 verifier/planner, synth, then the durable code-execute -> code-test -> code-report loop. Canonical standard+ pipeline: code-plan -> code-execute -> code-test -> code-report.\n"
            "- For each durable sub-step that is actually used, read the matching $AGENT_HOME/adapters/codex/skills/<step>/SKILL.md when present and run $AGENT_HOME/adapters/codex/bin/preflight.sh capability-info <step>.\n"
            "- Pipeline role profiles: for standard+ stages, run $AGENT_HOME/adapters/codex/bin/preflight.sh role planning, role implementation, role verification, and role report to map stages to Codex-native agents.\n"
            "- Plan-check is required for quick+ but stays small: requirements coverage, over/under-scoping, executable verification, and missed spec-significant risk. Do not run independent QA after every stage by default.\n"
            "- When the selected graph calls for independent plan review, run $AGENT_HOME/adapters/codex/bin/preflight.sh mode-info qa/plan-review and $AGENT_HOME/adapters/codex/bin/preflight.sh role verification before claiming that review.\n"
            "- Pipeline intensity controls ceremony. For standard+ intensity, a depth-1 capability owner should dispatch bounded depth-2 planner/verifier workers when the task is separable; thorough/adversarial expands this to multi-axis/adversary workers. Synthesize short reports; depth 3+ is forbidden.\n"
            "- Depth-2 launch recovery: consume the route node's checked fallback with $AGENT_HOME/adapters/codex/bin/preflight.sh dispatch-chain. Every same/cross-harness headless target uses the inherited depth-0 broker binding; do not recursively start adapter CLIs. Do not retry an unchanged failure. Use only inherited $AGENT_DISPATCH_JOBS; cycle-local jobs files are non-authoritative.\n"
            "- Implementation: run $AGENT_HOME/adapters/codex/bin/preflight.sh role implementation for standard+ implementation stages and obey the requested development mode.\n"
            "- Testing: run $AGENT_HOME/adapters/codex/bin/preflight.sh mode-info qa/test when concrete verification commands are used, satisfy the reported verification-runner contract, and record evidence under test_logs/ for standard+ work cycles.\n"
            "- Reporting: direct returns a concise report; quick returns its concise report from the depth-1 one-shot worker; standard+ runs $AGENT_HOME/adapters/codex/bin/preflight.sh role report, then writes or updates pipeline_summary.md with changed files, verification commands/results, artifact paths, and unsupported Codex tool contracts.\n"
            "- Do not claim independent QA delegation if no separate Codex agent/headless pass actually ran; report inline fallback explicitly.\n"
        )
    if args.route_file:
        route_bootstrap = (
            f"- Validate and consume the assigned route only: $AGENT_HOME/adapters/codex/bin/preflight.sh worker-route --route {args.route_file} --node {args.route_node} --cwd {args.worktree} --artifact-root {args.artifact_root} --capability {args.capability} --intensity {args.intensity} --write-scope '{args.write_scope}' --route-id {args.route_id} --route-hash {args.route_hash} --registry-digest {args.registry_digest}.\n"
            "- Do not rerun status -> prompt-signal -> mode -> route and do not reselect capability, intensity, or topology. The validator owns route hash/node/scope, tracked evidence, absolute cwd/canonical root, and git-state safety.\n"
        )
    else:
        route_bootstrap = (
            "- Run $AGENT_HOME/adapters/codex/bin/preflight.sh status . codex-headless and inspect workflow, artifact, git, worktree, and headless-job risk fields.\n"
            "- Run $AGENT_HOME/adapters/codex/bin/preflight.sh prompt-signal . codex-headless to mirror the Codex UserPromptSubmit routing signal.\n"
            "- Run $AGENT_HOME/adapters/codex/bin/preflight.sh mode . codex-headless to mirror the tracked/untracked workflow guard.\n"
            f"- Run $AGENT_HOME/adapters/codex/bin/preflight.sh route {args.capability} . codex-headless.\n"
        )
    return (
        "You are a Codex headless worker launched by the portable agent harness.\n"
        "Follow the Codex adapter contract before doing task work.\n\n"
        "Required bootstrap:\n"
        "- This process is AGENT_SESSION_ROLE=worker. Main-only hook lifecycle (automatic memory/briefing/turn-nudge/session-end curator/title/token context) is disabled; deterministic safety, routing, handoff, liveness, and verification remain active.\n"
        "- Resolve harness files through $AGENT_HOME; the target project need not contain an adapters/ directory.\n"
        "- Read $AGENT_HOME/adapters/codex/AGENTS.md first.\n"
        f"{route_bootstrap}"
        f"- Read $AGENT_HOME/adapters/codex/skills/{args.capability}/SKILL.md when present.\n"
        f"- Run $AGENT_HOME/adapters/codex/bin/preflight.sh mode-info {args.mode} and read the reported native_mode_path under $AGENT_HOME when present.\n"
        f"- Run $AGENT_HOME/adapters/codex/bin/preflight.sh qa-policy {args.qa} {track} and obey the reported reviewer, external-adversary, and fallback policy.\n"
        "- If you actually read .agent_reports/spec/prd.md or legacy .claude_reports/spec/prd.md, run $AGENT_HOME/adapters/codex/bin/preflight.sh read <prd.md> codex-headless after the read.\n"
        "- Before edits, run $AGENT_HOME/adapters/codex/bin/preflight.sh write <file> codex-headless.\n"
        "- Do not use adapters/claude, claude_setting, Claude slash commands, or Claude hook/statusline files as Codex-native input.\n\n"
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
        f"- worktree: {args.worktree}\n\n"
        f"- artifact_root: {args.artifact_root}\n\n"
        f"{execution_contract}"
        "User task:\n"
        f"{task.rstrip()}\n\n"
        "Return a concise report with changed files, verification commands, artifact paths, and any blocked/unsupported Codex tool contracts. "
        "Write every durable agent artifact only under artifact_root; the task worktree's "
        "tracked .agent_reports/.claude_reports snapshot is read-only shadow state. "
        "Leave merge and guarded worktree cleanup to the main orchestrator.\n",
        source,
    )


def shell_command(args: argparse.Namespace, prompt_path: Path, log_path: Path) -> str:
    cmd = [
        "codex",
        "exec",
        "--cd",
        args.worktree,
        "--add-dir",
        args.artifact_root,
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


def append_job(jobs: Path, args: argparse.Namespace) -> None:
    repo = subprocess.check_output(["git", "-C", args.worktree, "rev-parse", "--show-toplevel"], text=True).strip()
    pipe = f"capability={args.capability},mode={args.mode},qa={args.qa},intensity={args.intensity},depth={args.depth},harness=codex"
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
    if args.capability_owner:
        pipe += f",owner={args.capability_owner}"
    if args.owner_harness:
        pipe += f",owner_harness={args.owner_harness}"
    if args.depth >= 2:
        pipe += (
            f",parent_harness={args.parent_harness},parent_transport={args.parent_transport}"
            f",parent_sandbox={args.parent_sandbox},child_harness=codex"
            f",nested_eligibility={args.nested_eligibility},eligibility_source={args.eligibility_source}"
            f",eligibility_failure_class={args.eligibility_failure_class or '-'}"
        )
    for key in ("route_file", "route_id", "route_hash", "route_node", "registry_digest", "write_scope", "completion_gate"):
        value = getattr(args, key)
        if value:
            pipe += f",{key}={value}"
    settings = args.resolved_model_settings
    pipe += f",model_source={settings['source']},model_role={settings['role']},model={settings['model']},reasoning={settings['reasoning']}"
    if args.approval != "inherit":
        pipe += f",approval={args.approval}"
    if args.profile:
        pipe += f",profile={args.profile}"
    pipe += f",artifact_root={args.artifact_root}"
    if args.attempt_id:
        pipe += f",attempt_id={args.attempt_id},launch_authority={args.launch_authority},fallback_ordinal={args.fallback_ordinal}"
    if args.broker_request_id:
        pipe += f",broker_request_id={args.broker_request_id}"
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with jobs_lock(jobs):
        with jobs.open("a", encoding="utf-8") as f:
            f.write(f"{ts}\topen\t{repo}\t{args.worktree}\t{args.slug}\t{pipe}\n")


def close_job_row(jobs: Path, slug: str, worktree: str, reason: str, reset: str, attempt_id: str | None = None) -> bool:
    """SD-15: flip this dispatch's own open row to done with a dead-<reason> note.

    Matches by (slug, worktree, status==open) under the same flock the writer uses,
    so a concurrent conductor appending other rows is serialized. Appends
    note=dead-<reason>[,reset=<reset>] to the pipe column (kv style). Idempotent:
    returns False if no matching open row is found. Homomorphic with the Claude wrapper.
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
            if attempt_id and f"attempt_id={attempt_id}" not in pipe.split(","):
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


def annotate_job_row(jobs: Path, slug: str, worktree: str, extra_kv: str, attempt_id: str | None = None) -> bool:
    """Attach launch identity to the exact open attempt row."""
    if not jobs.is_file():
        return False
    with jobs_lock(jobs):
        lines = jobs.read_text(encoding="utf-8").splitlines(keepends=True)
        for i, line in enumerate(lines):
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 6:
                continue
            ts, status, repo, wt, row_slug, pipe = parts[:6]
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
    matches a DEATH_PATTERN; otherwise None (still running, or exited cleanly with no
    limit signal — normal harvest owns those). Polls in 0.5s steps. ADAPTATION note:
    codex exec exits non-zero on retry exhaustion so this launch-watch axis is realized;
    a runtime that *hangs* on limit instead of exiting (see OpenCode #8203) escapes this
    watch and is caught later by dispatch-liveness's log scan instead.
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
    death = scan_death(tail)
    if death:
        return death
    if proc.returncode:
        return f"launch-exit-{proc.returncode}", ""
    return None


def resolve_agent_home() -> Path:
    env_home = os.environ.get("AGENT_HOME")
    if env_home and (Path(env_home) / "core" / "CORE.md").is_file():
        return Path(env_home)
    maintainer_home = Path.home() / "agent_setting"
    if (maintainer_home / "core" / "CORE.md").is_file():
        return maintainer_home
    return ROOT


def ensure_runtime_home_projection(worktree: Path) -> Path | None:
    """Expose the active Codex session store to Fleet without copying runtime state."""
    runtime_home = Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser().resolve()
    link = worktree / ".dispatch" / "codex-home"
    try:
        link.parent.mkdir(parents=True, exist_ok=True)
        if link.is_symlink():
            link.unlink()
        elif link.exists():
            return None
        link.symlink_to(runtime_home, target_is_directory=True)
        return link
    except OSError:
        return None


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


def validate_route_record(args: argparse.Namespace) -> int:
    routed = any((args.route_id, args.route_hash, args.route_node, args.registry_digest))
    if routed and not args.route_file:
        return fail("route-record-required", 65, route_id=args.route_id or "-")
    if not args.route_file:
        return 0
    required = ("route_id", "route_hash", "route_node", "registry_digest", "write_scope")
    missing = [name for name in required if not getattr(args, name)]
    if missing:
        return fail("route-metadata-missing", 65, fields=",".join(missing))
    command = [sys.executable, str(ROOT / "utilities" / "worker-route-guard.py"), "validate",
        "--route", args.route_file, "--node", args.route_node, "--cwd", args.worktree,
        "--artifact-root", args.artifact_root, "--capability", args.capability,
        "--intensity", args.intensity, "--write-scope", args.write_scope,
        "--route-id", args.route_id, "--route-hash", args.route_hash,
        "--registry-digest", args.registry_digest]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        if result.stdout: print(result.stdout, end="")
        if result.stderr: print(result.stderr, end="", file=sys.stderr)
        return fail("worker-route-validation-failed", result.returncode, route_file=args.route_file)
    args.route_validation = result.stdout.strip()
    return 0


def main(argv: list[str]) -> int:
    args = parser().parse_args(argv[1:])
    if not Path(args.worktree).is_absolute():
        return fail("worktree-must-be-absolute", 64, worktree=args.worktree)
    args.worktree = str(Path(args.worktree).resolve())
    forced_sandbox = os.environ.get("CODEX_DISPATCH_SANDBOX_FORCE")
    if forced_sandbox:
        if forced_sandbox not in ("read-only", "workspace-write", "danger-full-access"):
            return fail("invalid-forced-dispatch-sandbox", 64, sandbox=forced_sandbox)
        args.sandbox = forced_sandbox
    if os.environ.get("CODEX_DISPATCH_PARENT_CURRENT_FORCE") == "1":
        current_thread = os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SESSION_ID")
        if current_thread:
            args.parent_session_id = current_thread
        if args.depth == 1:
            args.parent_slug = None
    action = "start" if args.start else "register" if args.register else "dry-run"
    worktree = Path(args.worktree)
    if not worktree.is_dir():
        return fail("worktree-not-found", 66, worktree=args.worktree)
    if subprocess.run(["git", "-C", args.worktree, "rev-parse", "--is-inside-work-tree"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
        return fail("not-a-git-worktree", 65, worktree=args.worktree)
    try:
        args.artifact_root = resolve_artifact_root(args.worktree)
    except ValueError as e:
        return fail("artifact-root-resolution-failed", 64, detail=str(e), worktree=args.worktree)
    rc = validate_dispatch_inputs(args)
    if rc != 0:
        return rc
    try:
        validate_nested_eligibility(
            depth=args.depth, action=action, parent_harness=args.parent_harness,
            parent_transport=args.parent_transport, parent_sandbox=args.parent_sandbox,
            child_harness="codex", launch_authority=args.launch_authority,
            status=args.nested_eligibility, source=args.eligibility_source,
        )
    except DispatchContractError as e:
        return fail(e.reason, 69, detail=e.detail)
    rc = validate_route_record(args)
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

    runtime_home_projection = None
    if args.start and profile_home is None:
        runtime_home_projection = ensure_runtime_home_projection(worktree)

    agent_home = resolve_agent_home()
    try:
        registry = resolve_global_registry(agent_home, args.jobs, args.depth, action)
        jobs = registry.path
        args.attempt_id = new_attempt_id(args.attempt_id) if action in ("register", "start") else args.attempt_id
        if action in ("register", "start"):
            ensure_global_registry_writable(jobs)
    except DispatchContractError as e:
        return fail(e.reason, 73, detail=e.detail, child_spawned="0")
    try:
        broker = ensure_launch_broker(
            agent_home, jobs, depth=args.depth, action=action, intensity=args.intensity
        )
    except DispatchContractError as e:
        return fail(e.reason, 76, detail=e.detail, child_spawned="0")
    log_dir = Path(args.log_dir) if args.log_dir else agent_home / ".dispatch" / "logs"
    prompt_text, prompt_source = dispatch_prompt(args)
    prompt_path = log_dir / f"{args.slug}.codex.prompt.txt"
    log_path = log_dir / f"{args.slug}.codex.jsonl"
    command = shell_command(args, prompt_path, log_path)

    if action in ("register", "start"):
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_text, encoding="utf-8")
        if action == "start":
            governor = ROOT / "utilities" / "model-worker-governor.py"
            governor_root = Path(
                os.environ.get("AGENT_MODEL_GOVERNOR_ROOT")
                or Path(args.artifact_root) / ".runtime" / "model-worker-governor"
            )
            gate = subprocess.run([sys.executable, str(governor), "--root", str(governor_root), "check", "--class", "dispatch"])
            if gate.returncode != 0:
                return fail("model-worker-governor-denied", 75)
        append_job(jobs, args)
    if action == "start":
        dispatch_env = {
            **os.environ,
            "AGENT_SESSION_ROLE": "worker",
            "AGENT_DISPATCH_CHILD": "1",
            "AGENT_DISPATCH_DEPTH": str(args.depth),
            "AGENT_DISPATCH_INTENSITY": args.intensity,
            "AGENT_DISPATCH_PARENT_SLUG": args.parent_slug or "",
            "AGENT_DISPATCH_PARENT_SESSION_ID": args.parent_session_id or "",
            "AGENT_DISPATCH_PARENT_CWD": (_effective_parent_cwd(args) if (args.parent_slug or args.parent_session_id) else ""),
            "AGENT_DISPATCH_WORKER_ROLE": args.worker_role or "",
            "AGENT_DISPATCH_OWNER": args.capability_owner or "",
            "AGENT_DISPATCH_OWNER_HARNESS": args.owner_harness or "",
            "AGENT_ARTIFACT_ROOT": args.artifact_root,
            "AGENT_ROUTE_FILE": args.route_file or "",
            "AGENT_ROUTE_ID": args.route_id or "",
            "AGENT_ROUTE_NODE": args.route_node or "",
            "AGENT_MODEL_GOVERNOR_ROOT": str(governor_root),
            "AGENT_DISPATCH_JOBS": str(jobs),
            "AGENT_DISPATCH_CURRENT_HARNESS": "codex",
            "AGENT_DISPATCH_CURRENT_TRANSPORT": "headless",
            "AGENT_DISPATCH_CURRENT_SANDBOX": args.sandbox,
        }
        if broker:
            dispatch_env.update({
                "AGENT_DISPATCH_BROKER_ROOT": str(broker.root),
                "AGENT_DISPATCH_BROKER_INSTANCE": broker.instance_id,
                "AGENT_DISPATCH_BROKER_PID": str(broker.pid),
                "AGENT_DISPATCH_BROKER_START_TICKS": broker.start_ticks,
            })
        if profile_home is not None:
            dispatch_env["CODEX_HOME"] = str(profile_home)
        try:
            proc = subprocess.Popen([sys.executable, str(governor), "--root", str(governor_root), "run", "--class", "dispatch", "--", "sh", "-c", command], start_new_session=True, env=dispatch_env)
        except OSError as exc:
            close_job_row(jobs, args.slug, args.worktree, "launch-error", "", args.attempt_id)
            return fail("child-launch-failed", 70, detail=str(exc), attempt_id=args.attempt_id)
        start_ticks = process_start_ticks(proc.pid)
        launch_identity = f"pid={proc.pid}" + (f",pid_start={start_ticks}" if start_ticks else "")
        annotate_job_row(jobs, args.slug, args.worktree, launch_identity, args.attempt_id)
        args.child_pid = proc.pid
        args.child_pid_start = start_ticks
        # SD-15 (OPERATIONS §5.10 ⑨): watch briefly for a limit/auth early death so a
        # limit-killed launch closes its own row now instead of lingering `open` until
        # liveness SUSPECT catches it minutes later.
        death = watch_early_death(proc, log_path, args.early_exit_watch)
        if death:
            reason, reset = death
            close_job_row(jobs, args.slug, args.worktree, reason, reset, args.attempt_id)
            write_reset_cache(agent_home, "codex", reason, reset)
            args.early_death = (reason, reset)

    print("adapter=codex")
    print("runtime_surface=codex-exec-headless")
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
    print(f"parent={args.parent_slug or '-'}")
    print(f"parent_session_id={args.parent_session_id or '-'}")
    print(f"worker_role={args.worker_role or '-'}")
    print(f"owner={args.capability_owner or '-'}")
    print(f"owner_harness={args.owner_harness or '-'}")
    print(f"route_file={args.route_file or '-'}")
    print(f"route_validation={getattr(args, 'route_validation', None) or '-'}")
    settings = args.resolved_model_settings
    print(f"model_source={settings['source']}")
    print(f"model_role={settings['role']}")
    print(f"model={settings['model']}")
    print(f"reasoning={settings['reasoning']}")
    print(f"approval={args.approval}")
    print(f"profile={args.profile or '-'}")
    print(f"runtime_home_projection={runtime_home_projection or '-'}")
    print(f"job_registry={jobs}")
    print(f"broker_root={broker.root if broker else os.environ.get('AGENT_DISPATCH_BROKER_ROOT', '-')}")
    print(f"broker_instance={broker.instance_id if broker else os.environ.get('AGENT_DISPATCH_BROKER_INSTANCE', '-')}")
    print(f"registry_authority={registry.source}")
    print(f"attempt_id={args.attempt_id or '-'}")
    print(f"broker_request_id={args.broker_request_id or '-'}")
    print(f"launch_authority={args.launch_authority}")
    print(f"fallback_ordinal={args.fallback_ordinal}")
    print(f"registry_lock={jobs}.lock")
    print(f"registered={1 if action in ('register', 'start') else 0}")
    print(f"started={1 if action == 'start' else 0}")
    print(f"child_pid={getattr(args, 'child_pid', None) or '-'}")
    print(f"child_pid_start={getattr(args, 'child_pid_start', None) or '-'}")
    print(f"require_hook_trust={1 if args.require_hook_trust else 0}")
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
