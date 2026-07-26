#!/usr/bin/env python3
"""Read authoritative current-hash Codex hook trust through App Server."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any


class HookTrustError(RuntimeError):
    pass


def event_label(value: str) -> str:
    chars: list[str] = []
    for index, char in enumerate(value):
        if char.isupper() and index:
            chars.append("_")
        chars.append(char.lower())
    return "".join(chars)


def expected_handlers(path: Path) -> Counter[str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HookTrustError("hooks-file-unreadable") from exc
    hooks = value.get("hooks") if isinstance(value, dict) else None
    if not isinstance(hooks, dict):
        raise HookTrustError("hooks-file-shape-invalid")
    expected: Counter[str] = Counter()
    for event, groups in hooks.items():
        if not isinstance(event, str) or not isinstance(groups, list):
            raise HookTrustError("hooks-file-event-invalid")
        for group in groups:
            handlers = group.get("hooks") if isinstance(group, dict) else None
            if not isinstance(handlers, list):
                raise HookTrustError("hooks-file-group-invalid")
            for handler in handlers:
                if (
                    isinstance(handler, dict)
                    and handler.get("type") == "command"
                    and isinstance(handler.get("command"), str)
                    and handler["command"].strip()
                ):
                    expected[event_label(event)] += 1
    if not expected:
        raise HookTrustError("hooks-file-empty")
    return expected


class AppServer:
    def __init__(self, command: list[str], cwd: Path):
        try:
            self.process = subprocess.Popen(
                command,
                cwd=cwd,
                env=os.environ.copy(),
                text=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=1,
            )
        except OSError as exc:
            raise HookTrustError("app-server-launch-failed") from exc
        self.next_id = 1

    def send(self, value: dict[str, Any]) -> None:
        if self.process.stdin is None:
            raise HookTrustError("app-server-stdin-closed")
        self.process.stdin.write(json.dumps(value, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        self.send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params,
            }
        )
        if self.process.stdout is None:
            raise HookTrustError("app-server-stdout-closed")
        while True:
            line = self.process.stdout.readline()
            if not line:
                raise HookTrustError("app-server-eof")
            try:
                value = json.loads(line)
            except ValueError as exc:
                raise HookTrustError("app-server-json-invalid") from exc
            if not isinstance(value, dict) or value.get("id") != request_id:
                continue
            if "error" in value or not isinstance(value.get("result"), dict):
                raise HookTrustError(f"app-server-request-failed-{method}")
            return value["result"]

    def notify(self, method: str) -> None:
        self.send({"jsonrpc": "2.0", "method": method})

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)


def same_source(raw: object, expected: Path) -> bool:
    if not isinstance(raw, str) or not raw:
        return False
    candidate = Path(raw).expanduser()
    try:
        return candidate.samefile(expected)
    except OSError:
        return candidate.absolute() == expected.absolute()


def inspect_trust(
    *,
    hooks_file: Path,
    cwd: Path,
    command: list[str],
) -> tuple[bool, str, list[str]]:
    expected = expected_handlers(hooks_file)
    server = AppServer(command, cwd)
    try:
        server.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "agent-harness-hook-trust-check",
                    "title": "Agent Harness Hook Trust Check",
                    "version": "1",
                },
                "capabilities": None,
            },
        )
        server.notify("initialized")
        result = server.request("hooks/list", {"cwds": [str(cwd)]})
    finally:
        server.close()

    data = result.get("data")
    if not isinstance(data, list):
        raise HookTrustError("hooks-list-shape-invalid")
    scoped: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict) or item.get("cwd") != str(cwd):
            continue
        hooks = item.get("hooks")
        if not isinstance(hooks, list):
            raise HookTrustError("hooks-list-entry-invalid")
        scoped.extend(
            hook
            for hook in hooks
            if isinstance(hook, dict)
            and same_source(hook.get("sourcePath"), hooks_file)
        )
    observed = Counter(
        event_label(str(hook.get("eventName")))
        for hook in scoped
        if isinstance(hook.get("eventName"), str)
    )
    if observed != expected:
        affected = sorted(set(expected).union(observed))
        return False, "definition-set-mismatch", affected
    untrusted = sorted(
        {
            event_label(str(hook["eventName"]))
            for hook in scoped
            if hook.get("enabled") is not True
            or hook.get("trustStatus") not in {"trusted", "managed"}
        }
    )
    if untrusted:
        return False, "current-hash-not-trusted", untrusted
    return True, "current-hash-trusted", sorted(expected)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--hooks-file", required=True, type=Path)
    value.add_argument("--cwd", required=True, type=Path)
    value.add_argument(
        "--app-server-command",
        default=os.environ.get(
            "CODEX_HOOK_TRUST_APP_SERVER_COMMAND",
            "codex app-server --listen stdio://",
        ),
    )
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    hooks_file = args.hooks_file.expanduser().absolute()
    cwd = args.cwd.expanduser().resolve()
    try:
        trusted, reason, events = inspect_trust(
            hooks_file=hooks_file,
            cwd=cwd,
            command=shlex.split(args.app_server_command),
        )
    except HookTrustError as exc:
        print(f"status=unavailable reason={exc}")
        return 69
    print(
        f"status={'trusted' if trusted else 'review-needed'} "
        f"reason={reason} events={','.join(events) or '-'}"
    )
    return 0 if trusted else 3


if __name__ == "__main__":
    raise SystemExit(main())
