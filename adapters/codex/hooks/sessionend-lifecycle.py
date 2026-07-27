#!/usr/bin/env python3
"""Codex SessionEnd/Stop bridge for portable memory lifecycle signals."""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PREFLIGHT = ROOT / "adapters" / "codex" / "bin" / "preflight.sh"
sys.path.insert(0, str(ROOT / "utilities"))
from codex_hook_definition_age import prove_parent_definition  # noqa: E402
from dispatch_completion_join import (  # noqa: E402
    JoinContractError,
    current_session_children,
    join_session_batch,
    parent_session_state_path,
    read_parent_session_batch_state,
    remove_parent_session_state,
    write_parent_session_state,
)

# Keep one minute below the outer Stop command timeout in hooks.json so the
# bridge can emit a typed receipt or recovery instruction before Codex kills it.
STOP_JOIN_TIMEOUT_MAX = 7140.0
LEGACY_STOP_JOIN_TIMEOUT_MAX = 540.0


def first_string(mapping: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def load_payload() -> dict[str, Any]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def nested_string(payload: dict[str, Any], *keys: str) -> str:
    direct = first_string(payload, *keys)
    if direct:
        return direct
    for key in ("context", "workspace", "session", "payload", "event", "input", "data"):
        value = payload.get(key)
        if isinstance(value, dict):
            found = nested_string(value, *keys)
            if found:
                return found
    return ""


def nested_bool(payload: dict[str, Any], *keys: str) -> bool:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, bool):
            return value
    for key in ("context", "workspace", "session", "payload", "event", "input", "data"):
        value = payload.get(key)
        if isinstance(value, dict) and nested_bool(value, *keys):
            return True
    return False


def cwd(payload: dict[str, Any]) -> str:
    return nested_string(payload, "cwd", "working_directory", "workingDirectory") or os.getcwd()


def session_id(payload: dict[str, Any]) -> str:
    sid = nested_string(payload, "session_id", "sessionID", "thread_id", "threadID")
    session = payload.get("session")
    if not sid and isinstance(session, dict):
        sid = first_string(session, "id")
    return sid or "codex-hook"


def run_preflight(*args: str, quiet: bool = False) -> None:
    env = os.environ.copy()
    env.setdefault("AGENT_HOME", str(ROOT))
    result = subprocess.run(
        [str(PREFLIGHT), *args],
        cwd=str(ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.stderr and not quiet:
        sys.stderr.write(result.stderr)


def spawn_preflight(*args: str) -> None:
    env = os.environ.copy()
    env.setdefault("AGENT_HOME", str(ROOT))
    env.setdefault("CODEX_SESSION_END_BACKGROUND", "1")
    subprocess.Popen(
        [str(PREFLIGHT), *args],
        cwd=str(ROOT),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )


def hook_event(payload: dict[str, Any]) -> str:
    event = os.environ.get("CODEX_HOOK_EVENT", "")
    if event:
        return event
    return nested_string(payload, "hook_event_name", "hookEventName", "event_name", "eventName")


def is_worker_session() -> bool:
    return (
        os.environ.get("AGENT_SESSION_ROLE", "").lower() == "worker"
        or os.environ.get("AGENT_DISPATCH_CHILD") == "1"
        or bool(os.environ.get("AGENT_DISPATCH_DEPTH"))
        or os.environ.get("CLAUDE_CODE_CHILD_SESSION") == "1"
        or bool(os.environ.get("OPENCODE_DISPATCH_SLUG"))
        or os.environ.get("FLEET_TITLE_REFRESH") == "1"
        or os.environ.get("MEM_DISTILL") == "1"
    )


def dispatch_jobs_path() -> Path:
    override = os.environ.get("AGENT_DISPATCH_JOBS")
    if override:
        return Path(override)
    agent_home = os.environ.get("AGENT_HOME")
    if agent_home and (Path(agent_home) / "core" / "CORE.md").is_file():
        return Path(agent_home) / ".dispatch" / "jobs.log"
    return ROOT / ".dispatch" / "jobs.log"


def bounded_float(name: str, default: float, maximum: float) -> float:
    try:
        value = float(os.environ.get(name, str(default)))
    except ValueError:
        return default
    if not math.isfinite(value):
        return default
    return min(maximum, max(0.0, value))


def stop_join_budget(event_session_id: str) -> tuple[float, str, str]:
    """Keep the inner join within the Stop definition loaded by this parent.

    A parent that predates the current hooks.json may still hold a native Stop
    receipt stamped before the definition changed. Its Codex process retained
    the legacy 600-second outer timeout, even though this script is loaded from
    the current checkout. Fail closed to the legacy 540-second inner budget so
    Codex cannot kill the hook before it emits typed recovery feedback.
    """

    proof = prove_parent_definition(event_session_id)
    requested = bounded_float(
        "CODEX_STOP_JOIN_TIMEOUT", 7140.0, STOP_JOIN_TIMEOUT_MAX
    )
    if proof.eligible:
        return requested, "two-hour", proof.reason
    return (
        min(requested, LEGACY_STOP_JOIN_TIMEOUT_MAX),
        "compatibility",
        proof.reason,
    )


def emit_stop_block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}, separators=(",", ":")))


def handle_stop(event_cwd: str, event_session_id: str) -> None:
    """Park an interactive parent outside the model until its exact batch settles."""

    jobs = dispatch_jobs_path()
    try:
        state_path = parent_session_state_path(jobs, event_session_id)
        state = read_parent_session_batch_state(state_path, event_session_id)
        if state is not None:
            attempts = set(state.attempt_ids)
            rows = current_session_children(
                jobs,
                event_session_id,
                expected_attempts=attempts,
            )
        else:
            if state_path.exists():
                raise JoinContractError("parent-session-state-invalid")
            rows = current_session_children(jobs, event_session_id)
            attempts = {row.attempt_id for row in rows}
        if not rows:
            remove_parent_session_state(state_path)
            spawn_preflight("session-end", event_cwd, event_session_id)
            return

        attempt_list = ",".join(sorted(attempts))
        harvest_targets = ",".join(
            f"{row.attempt_id}:all"
            for row in sorted(rows, key=lambda item: item.attempt_id)
        )
        delivered = set(state.delivered_attempt_ids) if state is not None else set()
        if attempts.issubset(delivered):
            emit_stop_block(
                "codex-stop-parent: the native completion receipt was already delivered "
                f"for exact attempt(s) {attempt_list}; run only exact preflight harvest "
                f"with attempt:status target(s) {harvest_targets}, then continue the task. "
                "Do not wait or inspect raw output."
            )
            return

        join_timeout, wait_generation, definition_reason = stop_join_budget(
            event_session_id
        )
        receipt = join_session_batch(
            jobs=jobs,
            parent_session_id=event_session_id,
            expected_attempts=attempts,
            interval=bounded_float("CODEX_STOP_JOIN_INTERVAL", 2.0, 10.0),
            timeout=join_timeout,
        )
        if receipt.get("state") == "ready":
            raw_children = receipt.get("children")
            observed = (
                {
                    child.get("attempt_id")
                    for child in raw_children
                    if isinstance(child, dict)
                    and isinstance(child.get("attempt_id"), str)
                }
                if isinstance(raw_children, list)
                else set()
            )
            if observed != attempts:
                raise JoinContractError("stop-receipt-attempt-set-mismatch")
            write_parent_session_state(
                state_path,
                event_session_id,
                attempts,
                attempt_ids=attempts,
            )
            emit_stop_block(
                "codex-stop-parent: exact registered child batch is ready outside the "
                f"model; receipt state=ready attempt(s)={attempt_list}. Run only exact "
                f"preflight harvest for attempt:status target(s) {harvest_targets}, then "
                "continue the task. "
                "Do not wait or inspect raw child output."
            )
            return
        if receipt.get("state") == "timeout":
            emit_stop_block(
                "codex-stop-parent: exact registered child batch is still running after "
                f"the bounded {wait_generation} native wait "
                f"({definition_reason}); attempt(s)={attempt_list}. Automatic "
                "completion delivery is no longer active after this single recovery "
                "continuation; operator re-entry is required after the batch completes. "
                "End this continuation without any tool call and do not start a model or "
                "tool polling loop."
            )
            return
        raise JoinContractError("stop-receipt-state-invalid")
    except JoinContractError as exc:
        emit_stop_block(
            "codex-stop-parent: native completion delivery failed closed "
            f"({exc}). Do not run unrelated tools; reconcile the exact registered "
            "attempts through the operator recovery path."
        )


def finish_stop_reentry(event_cwd: str, event_session_id: str) -> None:
    """End a runtime-created Stop continuation without another block or join."""

    jobs = dispatch_jobs_path()
    try:
        state_path = parent_session_state_path(jobs, event_session_id)
        state = read_parent_session_batch_state(state_path, event_session_id)
        if state is not None:
            rows = current_session_children(
                jobs,
                event_session_id,
                expected_attempts=set(state.attempt_ids),
            )
        else:
            if state_path.exists():
                return
            rows = current_session_children(jobs, event_session_id)
        if rows:
            return
        remove_parent_session_state(state_path)
        spawn_preflight("session-end", event_cwd, event_session_id)
    except JoinContractError:
        # A continuation must never recursively block. Invalid state remains
        # available for the explicit operator recovery path on a later turn.
        return


def main() -> int:
    payload = load_payload()
    # Worker shutdown owns no automatic sync or curator lifecycle. Return before
    # the Stop bridge can detach another process (D-42).
    if is_worker_session():
        return 0
    event_cwd = cwd(payload)
    event_session_id = session_id(payload)
    event = hook_event(payload).lower()
    if event == "stop":
        # A blocking Stop result is itself replayed as a new model continuation.
        # Codex marks that replay with stop_hook_active. Blocking that replay
        # again creates an unbounded Stop -> continuation -> Stop cycle.
        if nested_bool(payload, "stop_hook_active", "stopHookActive"):
            finish_stop_reentry(event_cwd, event_session_id)
            return 0
        # Stop owns interactive registered-child waiting. It emits a continuation
        # only for one typed receipt (or a bounded retry/recovery instruction).
        # Distillation remains detached, but only after no native child is open.
        handle_stop(event_cwd, event_session_id)
    elif event == "sessionend":
        run_preflight("material-route", "clear", "--session", event_session_id, quiet=True)
        run_preflight("session-end", event_cwd, event_session_id)
    else:
        run_preflight("session-end", event_cwd, event_session_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
