#!/usr/bin/env python3
"""Namespace-safe lifecycle selection and foreground child supervision."""

from __future__ import annotations

from dataclasses import dataclass
import math
import os
from pathlib import Path
import signal
import subprocess
import time
from typing import Mapping

from dispatch_contract import process_identity_is_live, process_start_ticks

DETACHED = "detached"
FOREGROUND_SCOPED = "foreground-scoped"
LIFECYCLES = (DETACHED, FOREGROUND_SCOPED)

FOREGROUND_TIMEOUT_DEFAULT = 3600.0  # 1h: what a non-positive/non-finite request clamps to
FOREGROUND_TIMEOUT_MAX = 86400.0  # 24h hard ceiling: no finite request may be effectively infinite


def bounded_foreground_timeout(timeout: float) -> float:
    """Clamp a foreground wait to a finite window — it may never be indefinite.

    A foreground-scoped parent blocks on its child for the whole wait, so an
    unbounded wait is a hang hazard, not a valid choice: a wedged child would pin
    the parent forever with no visibility. Two ways in are closed here:
      * ``<= 0`` (the historical "disable timeout" sentinel) and any non-finite
        request — ``inf``/``nan``, both accepted by ``argparse type=float`` — clamp
        to the safe default;
      * any finite request above the hard ceiling clamps down to it, so even an
        absurd value like ``1e18`` cannot be effectively infinite.
    (A no-progress watchdog that tells slow-but-progressing apart from wedged is
    the planned follow-up; until it lands, a finite window is the floor of safety.)
    """

    if not math.isfinite(timeout) or timeout <= 0:
        return FOREGROUND_TIMEOUT_DEFAULT
    return min(timeout, FOREGROUND_TIMEOUT_MAX)


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


def _bounded_group_stop(proc: subprocess.Popen, grace: float = 5.0) -> int:
    _terminate_group(proc, signal.SIGTERM)
    try:
        return proc.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        _terminate_group(proc, signal.SIGKILL)
        return proc.wait()


def wait_foreground(
    proc: subprocess.Popen,
    timeout: float,
    *,
    parent_pid: int | None = None,
    parent_pid_start: str | None = None,
    poll_interval: float = 0.2,
) -> ForegroundResult:
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
        bounded_timeout = bounded_foreground_timeout(timeout)
        if parent_pid is not None and parent_pid_start:
            deadline = time.monotonic() + bounded_timeout
            while True:
                exit_code = proc.poll()
                if exit_code is not None:
                    break
                if not process_identity_is_live(parent_pid, parent_pid_start):
                    exit_code = _bounded_group_stop(proc)
                    return ForegroundResult(exit_code, "parent-terminated")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    exit_code = _bounded_group_stop(proc)
                    return ForegroundResult(exit_code, "timeout")
                time.sleep(min(max(poll_interval, 0.01), remaining))
        else:
            try:
                exit_code = proc.wait(timeout=bounded_timeout)
            except subprocess.TimeoutExpired:
                exit_code = _bounded_group_stop(proc)
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
