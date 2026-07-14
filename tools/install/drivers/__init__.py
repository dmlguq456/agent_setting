"""Per-runtime channel drivers from the PRD's channel-driver component.

Each driver invokes the canonical ``tools/generate.py --check`` and runtime
preflight. Drivers do not reimplement projection generation; this package only
selects the appropriate driver.
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
