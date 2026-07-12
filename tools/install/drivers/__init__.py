"""drivers — 런타임별 channel driver (PRD "channel drivers" component diagram).

각 driver 는 기존 adapter 실현(adapters/<runtime>/bin/sync-native-*.py, preflight.sh)을
**호출**한다 — 재구현 금지(PRD §공통 "Module 구조"). 이 패키지는 driver 선택만 맡는다.
"""
from . import claude as _claude
from . import codex as _codex
from . import opencode as _opencode

RUNTIMES = ("claude", "codex", "opencode")

_DRIVERS = {
    "claude": _claude,
    "codex": _codex,
    "opencode": _opencode,
}


def get_driver(runtime):
    try:
        return _DRIVERS[runtime]
    except KeyError:
        raise ValueError(f"unknown runtime: {runtime!r} (expected one of {RUNTIMES})")
