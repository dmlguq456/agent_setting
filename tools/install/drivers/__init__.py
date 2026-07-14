"""drivers — 런타임별 channel driver (PRD "channel drivers" component diagram).

각 driver 는 canonical ``tools/generate.py --check``와 runtime preflight를 호출한다.
projection 생성 규칙을 driver에서 재구현하지 않으며 이 패키지는 driver 선택만 맡는다.
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
