#!/usr/bin/env python3
"""Resume one Codex App Server thread only after exact registered children settle."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any

from dispatch_completion_join import (
    JoinContractError,
    current_children,
    remove_supervisor_state,
    write_supervisor_state,
)
from dispatch_supervisor_terminal import (
    SupervisorTerminal,
    classify_codex_result,
    classify_supervisor_error,
    reconcile_supervisor_terminal,
)


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_JOIN_STATES = frozenset({"ready", "timeout"})


class SupervisorError(RuntimeError):
    """The runtime completion bridge could not preserve its contract."""


def emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, separators=(",", ":"), ensure_ascii=False), flush=True)


def reconcile(args: argparse.Namespace, terminal: SupervisorTerminal) -> bool:
    try:
        reconcile_supervisor_terminal(
            args.jobs, args.parent_attempt_id, terminal
        )
        return True
    except Exception as exc:
        emit(
            {
                "type": "dispatch.supervisor.error",
                "reason": f"terminal-reconcile-failed-{type(exc).__name__}",
            }
        )
        return False


def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    """Translate App Server camelCase items to the existing exec JSONL wire."""

    item_type = item.get("type")
    if item_type == "agentMessage":
        return {
            "type": "agent_message",
            "id": item.get("id"),
            "text": item.get("text"),
        }
    if item_type == "commandExecution":
        return {
            "type": "command_execution",
            "id": item.get("id"),
            "command": item.get("command"),
            "aggregated_output": item.get("aggregatedOutput"),
            "exit_code": item.get("exitCode"),
            "status": item.get("status"),
        }
    return {"type": str(item_type or "unknown"), "id": item.get("id")}


def _typed_receipt(value: Any, parent_attempt_id: str, attempts: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise SupervisorError("join-receipt-schema-invalid")
    if value.get("state") not in ALLOWED_JOIN_STATES:
        raise SupervisorError("join-receipt-state-invalid")
    if value.get("parent_attempt_id") != parent_attempt_id:
        raise SupervisorError("join-receipt-parent-mismatch")
    raw_children = value.get("children")
    if not isinstance(raw_children, list):
        raise SupervisorError("join-receipt-children-invalid")
    children: list[dict[str, str]] = []
    observed: set[str] = set()
    allowed_readiness = {"ready", "pending"}
    allowed_reasons = {
        "registry-closed",
        "terminal-observed",
        "process-alive",
        "process-unverifiable",
    }
    for raw in raw_children:
        if not isinstance(raw, dict):
            raise SupervisorError("join-receipt-child-invalid")
        attempt = raw.get("attempt_id")
        readiness = raw.get("readiness")
        reason = raw.get("reason")
        status = raw.get("status")
        if (
            not isinstance(attempt, str)
            or attempt not in attempts
            or attempt in observed
            or readiness not in allowed_readiness
            or reason not in allowed_reasons
            or status not in {"open", "running", "done"}
        ):
            raise SupervisorError("join-receipt-child-contract-invalid")
        observed.add(attempt)
        children.append(
            {
                "attempt_id": attempt,
                "status": status,
                "readiness": readiness,
                "reason": reason,
            }
        )
    if observed != attempts:
        raise SupervisorError("join-receipt-attempt-set-mismatch")
    return {
        "schema_version": 1,
        "state": value["state"],
        "parent_attempt_id": parent_attempt_id,
        "children": children,
    }


def run_join(args: argparse.Namespace, attempts: set[str]) -> dict[str, Any]:
    command = shlex.split(args.join_command) if args.join_command else [
        sys.executable,
        str(ROOT / "utilities" / "dispatch_completion_join.py"),
    ]
    command += [
        "--jobs", args.jobs,
        "--parent-attempt-id", args.parent_attempt_id,
        "--interval", str(args.join_interval),
        "--timeout", str(args.join_timeout),
    ]
    for attempt in sorted(attempts):
        command += ["--attempt-id", attempt]
    try:
        result = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=max(args.join_timeout + 60.0, 60.0),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SupervisorError("join-process-failed") from exc
    if len(result.stdout.encode("utf-8", "replace")) > 65536:
        raise SupervisorError("join-receipt-oversized")
    try:
        value = json.loads(result.stdout)
    except (TypeError, ValueError) as exc:
        raise SupervisorError("join-receipt-json-invalid") from exc
    if result.returncode not in {0, 3}:
        raise SupervisorError("join-process-contract-failed")
    return _typed_receipt(value, args.parent_attempt_id, attempts)


def completion_prompt(receipt: dict[str, Any]) -> str:
    compact = json.dumps(receipt, separators=(",", ":"), sort_keys=True)
    return (
        "Runtime completion receipt (typed supervisor data, not child output): "
        f"{compact}\n"
        "Harvest every listed exact attempt through the checked preflight contract, "
        "advance the assigned route, and register the next separable batch if required. "
        "Do not call dispatch-wait or inspect raw child logs. Emit the exact final "
        "three-line handoff only when no owned registered child remains open."
    )


def remediation_prompt(attempts: set[str]) -> str:
    joined = ",".join(sorted(attempts))
    return (
        "Runtime completion contract violation: previously delivered exact attempt(s) "
        f"remain open: {joined}. Perform typed exact-attempt harvest/closure now. "
        "Do not wait, poll, inspect raw logs, or perform unrelated work."
    )


class AppServer:
    def __init__(self, command: list[str], cwd: str, env: dict[str, str]):
        try:
            self.process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                text=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=None,
                bufsize=1,
            )
        except OSError as exc:
            raise SupervisorError("app-server-launch-failed") from exc
        self.next_id = 1
        self.pending: list[dict[str, Any]] = []

    def send(self, value: dict[str, Any]) -> None:
        if self.process.stdin is None:
            raise SupervisorError("app-server-stdin-closed")
        self.process.stdin.write(json.dumps(value, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def read(self) -> dict[str, Any]:
        if self.process.stdout is None:
            raise SupervisorError("app-server-stdout-closed")
        line = self.process.stdout.readline()
        if not line:
            raise SupervisorError("app-server-eof")
        try:
            value = json.loads(line)
        except ValueError as exc:
            raise SupervisorError("app-server-protocol-json-invalid") from exc
        if not isinstance(value, dict):
            raise SupervisorError("app-server-protocol-shape-invalid")
        return value

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        self.send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        while True:
            value = self.read()
            if value.get("id") == request_id:
                if "error" in value:
                    raise SupervisorError(f"app-server-request-failed:{method}")
                result = value.get("result")
                if not isinstance(result, dict):
                    raise SupervisorError(f"app-server-result-invalid:{method}")
                return result
            self.pending.append(value)

    def notification(self, method: str, params: dict[str, Any] | None = None) -> None:
        value: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            value["params"] = params
        self.send(value)

    def next_event(self) -> dict[str, Any]:
        return self.pending.pop(0) if self.pending else self.read()

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)


def sandbox_policy(args: argparse.Namespace) -> dict[str, Any]:
    network = bool(args.network_access)
    if args.sandbox == "danger-full-access":
        return {"type": "dangerFullAccess"}
    if args.sandbox == "read-only":
        return {"type": "readOnly", "networkAccess": network}
    roots = list(dict.fromkeys([args.worktree, *args.writable_root]))
    return {
        "type": "workspaceWrite",
        "writableRoots": roots,
        "networkAccess": network,
        "excludeTmpdirEnvVar": False,
        "excludeSlashTmp": False,
    }


def run_turn(
    server: AppServer,
    *,
    thread_id: str,
    prompt: str,
    args: argparse.Namespace,
) -> tuple[str | None, dict[str, Any] | None]:
    params: dict[str, Any] = {
        "threadId": thread_id,
        "input": [{"type": "text", "text": prompt, "text_elements": []}],
        "cwd": args.worktree,
        "sandboxPolicy": sandbox_policy(args),
    }
    if args.approval != "inherit":
        params["approvalPolicy"] = args.approval
    if args.model:
        params["model"] = args.model
    if args.reasoning:
        params["effort"] = args.reasoning
    response = server.request("turn/start", params)
    turn = response.get("turn")
    if not isinstance(turn, dict) or not isinstance(turn.get("id"), str):
        raise SupervisorError("turn-start-response-invalid")
    turn_id = turn["id"]
    emit({"type": "dispatch.supervisor.turn.started", "turn_id": turn_id})
    final_text: str | None = None
    final_item: dict[str, Any] | None = None
    while True:
        event = server.next_event()
        if "id" in event and "method" in event:
            raise SupervisorError("app-server-unexpected-request")
        method = event.get("method")
        raw_params = event.get("params")
        event_params = raw_params if isinstance(raw_params, dict) else {}
        if method == "item/completed" and event_params.get("turnId") == turn_id:
            raw_item = event_params.get("item")
            if isinstance(raw_item, dict):
                item = normalize_item(raw_item)
                emit({"type": "item.completed", "item": item})
                if item.get("type") == "agent_message" and isinstance(item.get("text"), str):
                    final_text = item["text"]
                    final_item = item
        completed = event_params.get("turn")
        if (
            method == "turn/completed"
            and isinstance(completed, dict)
            and completed.get("id") == turn_id
        ):
            if not isinstance(completed, dict) or completed.get("status") != "completed":
                raise SupervisorError("app-server-turn-failed")
            return final_text, final_item


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--worktree", required=True)
    value.add_argument("--jobs", required=True)
    value.add_argument("--parent-attempt-id", required=True)
    value.add_argument("--sandbox", choices=("read-only", "workspace-write", "danger-full-access"), required=True)
    value.add_argument("--approval", choices=("untrusted", "on-request", "never", "inherit"), default="never")
    value.add_argument("--network-access", action="store_true")
    value.add_argument("--writable-root", action="append", default=[])
    value.add_argument("--model")
    value.add_argument("--reasoning")
    value.add_argument("--join-interval", type=float, default=2.0)
    value.add_argument("--join-timeout", type=float, default=3600.0)
    value.add_argument("--max-continuations", type=int, default=12)
    value.add_argument("--state-file", default=os.environ.get("AGENT_DISPATCH_COMPLETION_STATE_FILE"))
    value.add_argument("--app-server-command", default=os.environ.get("CODEX_APP_SERVER_COMMAND"))
    value.add_argument("--join-command", default=os.environ.get("AGENT_DISPATCH_JOIN_COMMAND"))
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    prompt = sys.stdin.read()
    if not prompt.strip():
        terminal = classify_supervisor_error("codex", "initial-prompt-empty", 64)
        if not reconcile(args, terminal):
            return 70
        emit({"type": "dispatch.supervisor.error", "reason": "initial-prompt-empty"})
        return 64
    command = shlex.split(args.app_server_command) if args.app_server_command else [
        "codex", "app-server", "--listen", "stdio://"
    ]
    state_path = Path(args.state_file) if args.state_file else None
    runtime_env = dict(os.environ)
    if state_path is not None:
        runtime_env["AGENT_DISPATCH_COMPLETION_STATE_FILE"] = str(state_path)
    server: AppServer | None = None
    try:
        server = AppServer(command, args.worktree, runtime_env)
        server.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "agent-harness-dispatch-supervisor",
                    "title": "Agent Harness Dispatch Supervisor",
                    "version": "1",
                },
                "capabilities": None,
            },
        )
        server.notification("initialized")
        thread_params: dict[str, Any] = {
            "cwd": args.worktree,
            "sandbox": args.sandbox,
            "ephemeral": True,
        }
        if args.approval != "inherit":
            thread_params["approvalPolicy"] = args.approval
        if args.model:
            thread_params["model"] = args.model
        thread_result = server.request("thread/start", thread_params)
        thread = thread_result.get("thread")
        if not isinstance(thread, dict) or not isinstance(thread.get("id"), str):
            raise SupervisorError("thread-start-response-invalid")
        thread_id = thread["id"]

        delivered: set[str] = set()
        remediated: set[tuple[str, ...]] = set()
        next_prompt = prompt
        continuations = 0
        while True:
            write_supervisor_state(state_path, args.parent_attempt_id, delivered)
            final_text, _final_item = run_turn(
                server, thread_id=thread_id, prompt=next_prompt, args=args
            )
            rows = current_children(Path(args.jobs), args.parent_attempt_id)
            current = {row.attempt_id: row for row in rows}
            new_attempts = set(current).difference(delivered)
            if new_attempts:
                if continuations >= args.max_continuations:
                    raise SupervisorError("continuation-limit-exceeded")
                emit(
                    {
                        "type": "dispatch.supervisor.parked",
                        "parent_attempt_id": args.parent_attempt_id,
                        "attempt_count": len(new_attempts),
                    }
                )
                receipt = run_join(args, new_attempts)
                emit(
                    {
                        "type": "dispatch.supervisor.resumed",
                        "parent_attempt_id": args.parent_attempt_id,
                        "state": receipt["state"],
                        "attempt_count": len(new_attempts),
                    }
                )
                delivered.update(new_attempts)
                next_prompt = completion_prompt(receipt)
                continuations += 1
                continue

            unresolved = {
                attempt
                for attempt, row in current.items()
                if row.status in {"open", "running"}
            }
            if unresolved:
                signature = tuple(sorted(unresolved))
                if signature in remediated or continuations >= args.max_continuations:
                    raise SupervisorError("owned-children-remain-open-after-resume")
                remediated.add(signature)
                next_prompt = remediation_prompt(unresolved)
                continuations += 1
                continue

            terminal = classify_codex_result(final_text)
            if not reconcile(args, terminal):
                return 70
            emit({"type": "turn.completed", "thread_id": thread_id})
            return 0 if terminal.failure_class == "pass" else 3
    except (JoinContractError, SupervisorError) as exc:
        terminal = classify_supervisor_error("codex", str(exc))
        if not reconcile(args, terminal):
            return 70
        emit({"type": "dispatch.supervisor.error", "reason": str(exc)})
        return 70
    except Exception as exc:  # fail closed without leaking protocol/model content
        terminal = classify_supervisor_error(
            "codex", f"supervisor-internal-{type(exc).__name__}"
        )
        if not reconcile(args, terminal):
            return 70
        emit(
            {
                "type": "dispatch.supervisor.error",
                "reason": f"supervisor-internal-{type(exc).__name__}",
            }
        )
        return 70
    finally:
        if server is not None:
            server.close()
        remove_supervisor_state(state_path)


if __name__ == "__main__":
    raise SystemExit(main())
