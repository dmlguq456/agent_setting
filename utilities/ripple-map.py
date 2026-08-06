#!/usr/bin/env python3
"""Map symbols or literal signatures to deterministic file/line references."""

from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path
import re

SKIP_DIRS = {
    ".git", ".agent_reports", ".claude_reports", ".venv", "__pycache__",
    "node_modules", "dist", "build", "vendor", ".tox", ".mypy_cache",
}
MAX_FILE_BYTES = 4 * 1024 * 1024


def targets(root: Path, includes: list[str], excludes: list[str]):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        if includes and not any(fnmatch.fnmatch(rel, pattern) for pattern in includes):
            continue
        if any(fnmatch.fnmatch(rel, pattern) for pattern in excludes):
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        yield path, rel


def pattern(value: str) -> re.Pattern[str]:
    escaped = re.escape(value)
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        return re.compile(rf"(?<![A-Za-z0-9_]){escaped}(?![A-Za-z0-9_])")
    return re.compile(escaped)


def scan(root: Path, symbols: list[str], includes: list[str], excludes: list[str]) -> dict:
    compiled = [(symbol, pattern(symbol)) for symbol in symbols]
    matches = []
    files: set[str] = set()
    for path, rel in targets(root, includes, excludes):
        try:
            raw = path.read_bytes()
            if b"\x00" in raw:
                continue
            lines = raw.decode("utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(lines, 1):
            for symbol, regex in compiled:
                for hit in regex.finditer(line):
                    files.add(rel)
                    matches.append({
                        "symbol": symbol,
                        "file": rel,
                        "line": number,
                        "column": hit.start() + 1,
                        "text": line.strip()[:300],
                    })
    matches.sort(key=lambda row: (row["file"], row["line"], row["column"], row["symbol"]))
    return {
        "schema_version": 1,
        "root": str(root),
        "symbols": symbols,
        "target_files": sorted(files),
        "matches": matches,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".")
    p.add_argument("--symbol", action="append", default=[])
    p.add_argument("--symbols-file")
    p.add_argument("--include", action="append", default=[])
    p.add_argument("--exclude", action="append", default=[])
    p.add_argument("--format", choices=("text", "json"), default="text")
    args = p.parse_args()
    symbols = list(args.symbol)
    if args.symbols_file:
        symbols.extend(
            line.strip() for line in Path(args.symbols_file).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    symbols = list(dict.fromkeys(symbols))
    if not symbols:
        p.error("at least one --symbol or --symbols-file entry is required")
    receipt = scan(Path(args.root).resolve(), symbols, args.include, args.exclude)
    if args.format == "json":
        print(json.dumps(receipt, sort_keys=True, indent=2))
    else:
        print("target_files:")
        for file in receipt["target_files"]:
            print(f"- {file}")
        print("references:")
        for row in receipt["matches"]:
            print(f"- {row['file']}:{row['line']}:{row['column']} [{row['symbol']}] {row['text']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
