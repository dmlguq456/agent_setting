#!/usr/bin/env python3
"""Fail-closed guard: concrete model IDs must live only in adapters/*/config/models.conf.

Each adapter declares its concrete model names and default efforts in a single
config source of truth (core/ADAPTATION.md §3, roles/README Adapter Requirements).
Every other adapter/core/roles/tools surface must derive from that config. A
concrete model ID appearing outside the config (and generated regions) is a
violation. Display-only model-family palettes and test fixtures are exempt.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Surfaces that are scanned for stray concrete model IDs.
SCAN_DIRS = ["adapters", "core", "roles"]

# The single sources of truth (allowed to contain concrete model IDs).
CONFIG_SUFFIX = "config/models.conf"

# Whole-file exemptions (generated projections, display palettes, tests, fixtures).
EXEMPT_SUBSTRINGS = (
    "/config/models.conf",              # the SoT itself
    "/agents/memory-scout",             # kernel helper, hand-authored per adapter (ONLY agents exemption)
    "/node_modules/",                   # vendored third-party code, not a harness surface
    "/roles/units/",                    # unit catalog owned by check-unit-config.py
    "/statusline.sh",                   # model-family -> color palette (display only)
    "/tools/fleet/",                    # Fleet render/demo palettes and fixtures (display only)
    "/loops/drill/",                    # drill fixtures pin explicit models on purpose
    ".test.",                           # test fixtures
    "/tests/",
    "check-model-config.py",            # this guard's own doc/patterns
    "check-adaptation-boundary.sh",     # boundary guard references models in comments/tests
)

# Concrete model-ID patterns (unambiguous identifiers + alias-as-model-value).
PATTERNS = [
    re.compile(r"gpt-5\.\d"),                                   # codex: gpt-5.6-sol, gpt-5.4-mini, ...
    re.compile(r"claude-(?:opus|sonnet|haiku|fable)-\d"),       # claude versioned full ids
    re.compile(r"opencode-go/[a-z0-9]"),                        # opencode-go provider model-id
    re.compile(r"\bglm-\d"),                                    # opencode glm-5.2
    re.compile(r"\bdeepseek-v\d"),                              # opencode deepseek-v4-*
    # Claude short alias used as a concrete model VALUE (frontmatter / :- default / assignment).
    re.compile(r"model:\s*(?:opus|sonnet|haiku|fable)\b"),
    re.compile(r":-\s*(?:opus|sonnet|haiku|fable)\b"),
    re.compile(r"=\s*[\"']?(?:opus|sonnet|haiku|fable)[\"']?\s*(?:;|$)"),
]

GEN_OPEN = re.compile(r"<!--\s*GENERATED")
GEN_CLOSE = re.compile(r"<!--\s*END GENERATED")


def is_exempt(path: Path) -> bool:
    p = str(path).replace(str(ROOT), "")
    return any(s in p for s in EXEMPT_SUBSTRINGS)


def scan_file(path: Path) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    in_generated = False
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return hits
    for i, line in enumerate(text.splitlines(), 1):
        if GEN_OPEN.search(line):
            in_generated = True
        if GEN_CLOSE.search(line):
            in_generated = False
            continue
        if in_generated:
            continue
        for pat in PATTERNS:
            if pat.search(line):
                hits.append((i, line.strip()[:120]))
                break
    return hits


def main() -> int:
    violations: list[str] = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or is_exempt(path):
                continue
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".db", ".lock"}:
                continue
            for lineno, snippet in scan_file(path):
                violations.append(f"{path.relative_to(ROOT)}:{lineno}: {snippet}")

    if violations:
        print("check-model-config: concrete model IDs found outside config/models.conf:", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        print(f"\n{len(violations)} violation(s). Move the model ID into the adapter's "
              f"config/models.conf and derive the surface from it.", file=sys.stderr)
        return 1
    print("check-model-config: OK — no concrete model IDs outside config/models.conf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
