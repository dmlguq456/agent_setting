#!/usr/bin/env python3
"""D-4 static guard: no new writer targets `_runtime/`, `NOTES.md`, `memo.md`,
or `.claude/agent-memory/` inside an artifact root (generate.py battery member).

`.runtime/` is the only bucket name for artifact-root-scoped runtime state
(core/CONVENTIONS.md §6.5-anchors); legacy `_runtime/` is read-only, and file
memory is retired -- the memory database is the sole source of truth. This
scans for a write PRIMITIVE (`mkdir`/`os.makedirs`/`open(..., "w")`/
`write_text`/`write_once`/`atomic_write`/shell `>`, `>>`, `mkdir -p`) whose
same-line path literal names one of those. A bare substring grep over the
whole tree over-fires on three unrelated shapes (2026-08-05 plan.md §2.5):
(a) XDG state event logs that are not artifact-root writes, (b) test
fixtures that plant the very string this check looks for, (c) unrelated
identifiers like `parent_runtime` or `product.runtimes` -- so this checker
requires a write primitive AND a path-shaped literal on the same line, not
just the substring anywhere.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("utilities", "tools", "hooks", "skills", "adapters")
SOURCE_SUFFIXES = (".py", ".sh")
TEST_SUFFIXES = (".test.py", ".test.sh")
# adapters/**/skills, adapters/claude/plugin-marketplace/**: generated projections
# (tools/sync-entry-skill-layer.py owns them) -- scanning the generator's own
# source is enough; scanning its output would just double-report the same line.
GENERATED_ADAPTER_PREFIXES = (
    "adapters/claude/skills/",
    "adapters/codex/skills/",
    "adapters/opencode/skills/",
    "adapters/claude/plugin-marketplace/",
)

# Each entry: (relative path, reason). Every allowlist member is a real,
# audited exception, not a way to silence the checker.
ALLOWLIST = {
    # XDG-scoped memory event log, not an artifact-root write (core/CORE.md §2).
    "tools/memory/mem.py",
    # XDG-scoped route-marker bookkeeping, not an artifact-root write.
    "hooks/material-route-guard.py",
    "tools/fleet/collectors/memory.py",
    "adapters/claude/tools/fleet/collectors/memory.py",
    # Fixture text that intentionally plants the guarded strings to test a
    # portable guard's own detection, not a real write site.
    "hooks/portable-guards.test.sh",
}

FORBIDDEN_TOKEN_RE = re.compile(
    r'(?<![\w.])_runtime/'      # `_runtime` used as a path segment
    r'|\bNOTES\.md\b'
    r'|\bmemo\.md\b'
    r'|\.claude/agent-memory(?:/|\b)'
)
PY_WRITE_PRIMITIVE_RE = re.compile(
    r'\b(?:os\.)?(?:mkdir|makedirs)\s*\('
    r'|\.write_text\s*\('
    r'|\bwrite_once\s*\('
    r'|\batomic_write\s*\('
    r'|\bopen\s*\([^)]*["\']a?w'
)
SH_WRITE_PRIMITIVE_RE = re.compile(
    r'\bmkdir\s+-p\b'
    r'|>>?(?!=)'  # redirection, not a shell `>=`/here-doc comparison operator
)
FENCE_RE = re.compile(r'^\s*```(bash|sh|python)?\s*$')


def _code_block_lines(text: str) -> list[tuple[int, str]]:
    """skills/**: only fenced bash/python code blocks are in scope (advisory-4)
    -- markdown prose mentioning these paths as documentation is not a write."""
    lines = []
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            lines.append((lineno, line))
    return lines


def _violations_in_file(path: Path, rel: str) -> list[str]:
    if rel in ALLOWLIST:
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    is_markdown = rel.startswith("skills/") and path.suffix == ".md"
    if is_markdown:
        lines = _code_block_lines(text)
        primitive_re = re.compile(f"{PY_WRITE_PRIMITIVE_RE.pattern}|{SH_WRITE_PRIMITIVE_RE.pattern}")
    elif path.suffix == ".py":
        lines = list(enumerate(text.splitlines(), start=1))
        primitive_re = PY_WRITE_PRIMITIVE_RE
    elif path.suffix == ".sh":
        lines = list(enumerate(text.splitlines(), start=1))
        primitive_re = SH_WRITE_PRIMITIVE_RE
    else:
        return []
    found = []
    for lineno, line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if FORBIDDEN_TOKEN_RE.search(line) and primitive_re.search(line):
            found.append(f"  {rel}:{lineno}: {stripped}")
    return found


def find_violations(root: Path = ROOT) -> list[str]:
    violations: list[str] = []
    for scan_dir in SCAN_DIRS:
        base = root / scan_dir
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            rel = str(path.relative_to(root))
            if any(rel.startswith(prefix) for prefix in GENERATED_ADAPTER_PREFIXES):
                continue
            if rel.endswith(TEST_SUFFIXES):
                continue
            if path.suffix not in SOURCE_SUFFIXES and not (scan_dir == "skills" and path.suffix == ".md"):
                continue
            violations.extend(_violations_in_file(path, rel))
    return violations


def main() -> int:
    # --check and write mode behave identically: this tool only verifies.
    violations = find_violations()
    if violations:
        print("runtime/memory boundary violations (D-4: no new writer may target", file=sys.stderr)
        print("_runtime/, NOTES.md, memo.md, or .claude/agent-memory/):", file=sys.stderr)
        for row in violations:
            print(row, file=sys.stderr)
        return 1
    print("runtime/memory boundary clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
