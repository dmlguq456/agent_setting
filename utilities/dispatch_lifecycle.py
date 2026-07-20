#!/usr/bin/env python3
"""Namespace-safe lifecycle selection and foreground child supervision."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import signal
import subprocess
from typing import Mapping

DETACHED = "detached"
FOREGROUND_SCOPED = "foreground-scoped"
LIFECYCLES = (DETACHED, FOREGROUND_SCOPED)


def pid_namespace_scoped(
    status_path: Path = Path("/proc/self/status"),
    init_comm_path: Path = Path("/proc/1/comm"),
) -> bool:
    """Detect a transient nested PID namespace conservatively.

    A nested ``NSpid`` vector is authoritative. When proc is remounted inside
    the namespace, a non-init PID 1 is the fallback signal. An unreadable proc
    fails safe because a detached child cannot then be proven durable.
    """

    try:
        for line in status_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("NSpid:"):
                if len(line.split()) > 2:
                    return True
                break
    except OSError:
        pass
    try:
        return init_comm_path.read_text(encoding="utf-8").strip() not in {
            "systemd",
            "init",
        }
    except OSError:
        return True


def select_launch_lifecycle(
    environ: Mapping[str, str] | None = None,
    *,
    namespace_scoped: bool | None = None,
) -> str:
    """Choose the lifecycle for an actual dispatch-chain launcher scope."""

    env = os.environ if environ is None else environ
    if env.get("AGENT_DISPATCH_ALLOW_NAMESPACED_SPAWN") == "1":
        return DETACHED
    scoped = pid_namespace_scoped() if namespace_scoped is None else namespace_scoped
    return FOREGROUND_SCOPED if scoped else DETACHED


@dataclass(frozen=True)
class ForegroundResult:
    exit_code: int
    failure: str


def _terminate_group(proc: subprocess.Popen, signum: int) -> None:
    try:
        os.killpg(proc.pid, signum)
    except ProcessLookupError:
        pass


def wait_foreground(proc: subprocess.Popen, timeout: float) -> ForegroundResult:
    """Wait in scope, forwarding termination and returning a typed outcome."""

    received: list[int] = []
    previous: dict[int, object] = {}

    def forward(signum: int, _frame: object) -> None:
        received.append(signum)
        _terminate_group(proc, signum)

    for signum in (signal.SIGINT, signal.SIGTERM):
        previous[signum] = signal.getsignal(signum)
        signal.signal(signum, forward)
    try:
        try:
            exit_code = proc.wait(timeout=None if timeout <= 0 else timeout)
        except subprocess.TimeoutExpired:
            _terminate_group(proc, signal.SIGTERM)
            try:
                exit_code = proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _terminate_group(proc, signal.SIGKILL)
                exit_code = proc.wait()
            return ForegroundResult(exit_code, "timeout")
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)

    if received:
        return ForegroundResult(exit_code, f"signal-{received[-1]}")
    if exit_code < 0:
        return ForegroundResult(exit_code, f"signal-{-exit_code}")
    if exit_code:
        return ForegroundResult(exit_code, f"exit-{exit_code}")
    return ForegroundResult(exit_code, "")
