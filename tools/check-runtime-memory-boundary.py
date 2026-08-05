#!/usr/bin/env python3
"""D-4 static guard: no new writer targets `_runtime/`, `NOTES.md`, `memo.md`,
or `.claude/agent-memory/` inside an artifact root (generate.py battery member).

`.runtime/` is the only bucket name for artifact-root-scoped runtime state
(core/CONVENTIONS.md \u00a76.5-anchors); legacy `_runtime/` is read-only, and file
memory is retired -- the memory database is the sole source of truth.

F8 (2026-08-05 remediation): the first cut only matched a write primitive and
a forbidden path literal on the *same line*, and exempted whole files. Both
were real gaps -- `target = root / "_runtime/state"` followed by
`target.mkdir(parents=True)` on the next line passed clean, and a newly added
forbidden writer in an already-allowlisted file passed clean too. Python files
are now checked with `ast`: every write-sink call's path argument is resolved
either directly (the argument's own source text) or through a simple
same-file def-use of a bare variable name (the variable was assigned a value
whose source text carries the forbidden token). Shell files get the shell
equivalent: a variable assigned a forbidden-token string is tracked, and a
sink line referencing `$var`/`${var}` for a flagged variable counts even
without the literal string PING on that same line. The allowlist is a set of
exact (file, sink line text) signatures, not a whole-file exemption -- a new
forbidden writer anywhere else in an allowlisted file still fails.
"""
from __future__ import annotations

import ast
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

# (relative path, exact stripped sink-line text) -- a real, audited exception
# for one specific call site, not a way to silence the whole file. Empty
# today: no currently scanned file has a legitimate forbidden-path writer: the
# XDG-scoped call sites that used to blanket-allowlist this file (mem.py,
# material-route-guard.py, the fleet memory collectors) all join an
# `agent-memory` *path segment* under an XDG state root, never the literal
# `.claude/agent-memory/` artifact-root token this guard forbids, so they were
# never real exceptions -- an accurate, per-line check needs none of them.
ALLOWLIST: dict[str, frozenset[str]] = {}

FORBIDDEN_TOKEN_RE = re.compile(
    r'(?<![\w.])_runtime/'      # `_runtime` used as a path segment
    r'|\bNOTES\.md\b'
    r'|\bmemo\.md\b'
    r'|\.claude/agent-memory(?:/|\b)'
)

PY_SINK_METHODS = {"mkdir", "write_text", "write_bytes", "touch"}
PY_SHUTIL_FUNCS = {"copy", "copy2", "copyfile", "copytree", "move"}
PY_OS_FUNCS = {"mkdir", "makedirs", "open"}
PY_BARE_SINK_FUNCS = {"write_once", "atomic_write"}

SH_SINK_RE = re.compile(
    r'\bmkdir\s+-p\b'
    r'|\binstall\s+-d\b'
    r'|\btee\b'
    r'|\bcp\b'
    r'|\bmv\b'
    r'|>>?(?!=)'  # redirection, not a shell `>=`/here-doc comparison operator
)
SH_ASSIGNMENT_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)=(.*)$')
SH_VAR_REF_RE = re.compile(r'\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?')

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


def _allowed(rel: str, line_text: str) -> bool:
    return line_text.strip() in ALLOWLIST.get(rel, frozenset())


def _py_call_sink_args(call: ast.Call) -> list[ast.AST]:
    """Return the argument expression(s) that a sink call writes a *path* to,
    or [] if `call` is not a recognized write sink."""
    func = call.func
    if isinstance(func, ast.Attribute):
        if func.attr in PY_SINK_METHODS:
            return [func.value]
        if func.attr in PY_SHUTIL_FUNCS and isinstance(func.value, ast.Name) and func.value.id == "shutil":
            return list(call.args[:2])
        if func.attr in PY_OS_FUNCS and isinstance(func.value, ast.Name) and func.value.id == "os":
            return call.args[:1]
    elif isinstance(func, ast.Name):
        if func.id == "open" and call.args:
            mode = None
            if len(call.args) > 1 and isinstance(call.args[1], ast.Constant) and isinstance(call.args[1].value, str):
                mode = call.args[1].value
            for kw in call.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    mode = kw.value.value
            if mode is None or any(flag in mode for flag in ("w", "a", "x")):
                return call.args[:1]
        if func.id in PY_BARE_SINK_FUNCS and call.args:
            return call.args[:1]
    return []


def _source_segments(source: str):
    """`ast.get_source_segment` re-splits the whole file on every call (a slow
    path in the CPython 3.8 stdlib -- quadratic in file size across the many
    calls this checker makes); split once per file and return a lookup
    function instead, same algorithm, amortized cost."""
    lines = ast._splitlines_no_ff(source)

    def segment(node) -> str:
        lineno = getattr(node, "lineno", None)
        end_lineno = getattr(node, "end_lineno", None)
        col_offset = getattr(node, "col_offset", None)
        end_col_offset = getattr(node, "end_col_offset", None)
        if None in (lineno, end_lineno, col_offset, end_col_offset):
            return ""
        lineno -= 1
        end_lineno -= 1
        if end_lineno == lineno:
            return lines[lineno].encode()[col_offset:end_col_offset].decode()
        first = lines[lineno].encode()[col_offset:].decode()
        last = lines[end_lineno].encode()[:end_col_offset].decode()
        middle = lines[lineno + 1:end_lineno]
        return "".join([first, *middle, last])

    return segment


def _py_flagged_names(tree: ast.AST, segment) -> set[str]:
    """Simple same-file def-use: a bare name is flagged when some assignment
    anywhere in the file gives it a value whose own source text carries a
    forbidden token. Not scope- or order-aware -- a static safety net errs
    toward over-flagging, never under-flagging."""
    flagged = set()
    for node in ast.walk(tree):
        targets = []
        value = None
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AugAssign):
            targets, value = [node.target], node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        if not FORBIDDEN_TOKEN_RE.search(segment(value)):
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                flagged.add(target.id)
    return flagged


def _py_violations(path: Path, rel: str, text: str) -> list[str]:
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return []
    segment = _source_segments(text)
    flagged_names = _py_flagged_names(tree, segment)
    text_lines = text.splitlines()
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for arg in _py_call_sink_args(node):
            direct = bool(FORBIDDEN_TOKEN_RE.search(segment(arg)))
            via_name = isinstance(arg, ast.Name) and arg.id in flagged_names
            if not (direct or via_name):
                continue
            lineno = node.lineno
            line_text = text_lines[lineno - 1].strip()
            if _allowed(rel, line_text):
                continue
            found.append(f"  {rel}:{lineno}: {line_text}")
    return found


def _sh_violations(rel: str, text: str) -> list[str]:
    lines = text.splitlines()
    flagged_vars = set()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        match = SH_ASSIGNMENT_RE.match(stripped)
        if match and FORBIDDEN_TOKEN_RE.search(match.group(2)):
            flagged_vars.add(match.group(1))
    found = []
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#") or not SH_SINK_RE.search(line):
            continue
        direct = bool(FORBIDDEN_TOKEN_RE.search(line))
        via_var = any(name in flagged_vars for name in SH_VAR_REF_RE.findall(line))
        if not (direct or via_var):
            continue
        if _allowed(rel, stripped):
            continue
        found.append(f"  {rel}:{lineno}: {stripped}")
    return found


def _md_fenced_violations(rel: str, text: str) -> list[str]:
    lines = _code_block_lines(text)
    found = []
    for lineno, line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        has_py_shape = "(" in line and any(
            token in line for token in ("mkdir", "write_text", "write_bytes", "touch", "write_once", "atomic_write", "open(")
        )
        has_sh_shape = bool(SH_SINK_RE.search(line))
        if not (has_py_shape or has_sh_shape):
            continue
        if not FORBIDDEN_TOKEN_RE.search(line):
            continue
        if _allowed(rel, stripped):
            continue
        found.append(f"  {rel}:{lineno}: {stripped}")
    return found


def _violations_in_file(path: Path, rel: str) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if rel.startswith("skills/") and path.suffix == ".md":
        return _md_fenced_violations(rel, text)
    if path.suffix == ".py":
        return _py_violations(path, rel, text)
    if path.suffix == ".sh":
        return _sh_violations(rel, text)
    return []


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
