#!/usr/bin/env python3
"""Launch an opt-in Codex App Server, single-ingress gateway, and remote client."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import signal
import stat
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GATEWAY = ROOT / "utilities" / "codex-managed-gateway.py"


class EntryError(RuntimeError):
    """The isolated managed-entry boundary is unsafe or unavailable."""


def canonical(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def safe_directory(path: Path, label: str) -> Path:
    if not path.is_absolute() or path.is_symlink():
        raise EntryError(f"{label}-path-unsafe")
    try:
        info = path.stat()
    except OSError as exc:
        raise EntryError(f"{label}-unavailable") from exc
    if not stat.S_ISDIR(info.st_mode):
        raise EntryError(f"{label}-not-directory")
    return path.resolve()


def safe_private_directory(path: Path, label: str) -> Path:
    resolved = safe_directory(path, label)
    info = resolved.stat()
    if info.st_uid != os.geteuid() or info.st_mode & 0o077:
        raise EntryError(f"{label}-permissions-unsafe")
    return resolved


def wait_socket(path: Path, process: subprocess.Popen[Any], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise EntryError(f"process-exited-before-socket:{process.returncode}")
        try:
            if stat.S_ISSOCK(path.lstat().st_mode):
                return
        except FileNotFoundError:
            pass
        time.sleep(0.02)
    raise EntryError(f"socket-start-timeout:{path.name}")


def terminate(process: subprocess.Popen[Any] | None) -> None:
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        process.wait(timeout=5)


def cleanup_socket(path: Path) -> None:
    """Remove only an exact leftover socket inside the explicit state dir."""

    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISSOCK(info.st_mode):
        path.unlink()


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--codex", default="codex")
    value.add_argument("--codex-home", required=True, type=Path)
    value.add_argument("--state-dir", required=True, type=Path)
    value.add_argument("--workspace", required=True, type=Path)
    value.add_argument(
        "--client-command",
        help=(
            "proof-only command; token {remote} is replaced by the gateway URI. "
            "Default launches the real Codex remote TUI"
        ),
    )
    value.add_argument(
        "--gateway-fault",
        choices=("none", "before-send", "after-send"),
        default="none",
    )
    value.add_argument("client_args", nargs=argparse.REMAINDER)
    return value


def execute(args: argparse.Namespace) -> int:
    codex_home = safe_private_directory(args.codex_home, "codex-home")
    state_dir = safe_private_directory(args.state_dir, "state-dir")
    workspace = safe_directory(args.workspace, "workspace")
    auth = codex_home / "auth.json"
    if not auth.is_file() or auth.is_symlink():
        raise EntryError("codex-home-auth-missing")
    upstream = state_dir / "app-server.sock"
    front = state_dir / "managed-tui.sock"
    control = state_dir / "managed-control.sock"
    ledger = state_dir / "managed-deliveries.json"
    trace = state_dir / "managed-gateway.trace.jsonl"
    for path in (upstream, front, control):
        if path.exists() or path.is_symlink():
            raise EntryError(f"managed-socket-already-exists:{path.name}")
    environment = dict(os.environ)
    environment.update(
        {
            "CODEX_HOME": str(codex_home),
            "CODEX_SQLITE_HOME": str(codex_home),
            "AGENT_HOME": str(ROOT),
            "AGENT_CODEX_MANAGED_GATEWAY": "1",
            "AGENT_CODEX_MANAGED_PARENT_RUNTIME": "codex",
            "AGENT_CODEX_MANAGED_CONTROL_SOCKET": str(control),
        }
    )
    app_server: subprocess.Popen[Any] | None = None
    gateway: subprocess.Popen[Any] | None = None
    try:
        app_server = subprocess.Popen(
            [
                args.codex,
                "app-server",
                "--listen",
                f"unix://{upstream}",
            ],
            cwd=workspace,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=None,
            start_new_session=True,
        )
        wait_socket(upstream, app_server, 20)
        gateway_command = [
            sys.executable,
            str(GATEWAY),
            "--listen",
            str(front),
            "--upstream",
            str(upstream),
            "--control",
            str(control),
            "--ledger",
            str(ledger),
            "--trace",
            str(trace),
        ]
        if args.gateway_fault != "none":
            gateway_command += ["--fault", args.gateway_fault]
        gateway = subprocess.Popen(
            gateway_command,
            cwd=workspace,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=None,
            start_new_session=True,
        )
        wait_socket(front, gateway, 20)
        wait_socket(control, gateway, 20)
        remote = f"unix://{front}"
        if args.client_command:
            client = [
                token.replace("{remote}", remote)
                for token in shlex.split(args.client_command)
            ]
        else:
            trailing = list(args.client_args)
            if trailing[:1] == ["--"]:
                trailing = trailing[1:]
            client = [args.codex, "--remote", remote, *trailing]
        result = subprocess.run(
            client,
            cwd=workspace,
            env=environment,
            check=False,
        )
        return result.returncode
    finally:
        terminate(gateway)
        terminate(app_server)
        for path in (front, control, upstream):
            cleanup_socket(path)


def main() -> int:
    args = parser().parse_args()
    try:
        return execute(args)
    except (EntryError, OSError) as exc:
        print(
            canonical({"status": "error", "reason": str(exc)}),
            file=sys.stderr,
        )
        return 65


if __name__ == "__main__":
    raise SystemExit(main())
