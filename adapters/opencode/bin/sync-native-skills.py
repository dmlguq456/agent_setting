#!/usr/bin/env python3
"""Generate OpenCode-native Skill projections from portable capabilities."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CAPABILITIES = ROOT / "capabilities"
OUT = ROOT / "adapters" / "opencode" / "skills"


def contract_rows(text: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 2:
            rows[cells[0]] = "|".join(cells[1:]).strip()
    return rows


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).replace('"', "'")


def render(capability_file: Path) -> tuple[str, str]:
    slug = capability_file.stem
    source = capability_file.read_text(encoding="utf-8")
    rows = contract_rows(source)
    identifier = rows.get("Identifier", f"`{slug}`").strip("`")
    modes = rows.get("Supported modes", "none").strip("`")
    argument_shape = rows.get("Argument shape", "").strip("`")
    meaning = compact(rows.get("Portable meaning", identifier))
    meaning_sentence = meaning if meaning.endswith((".", "!", "?")) else f"{meaning}."
    description = compact(
        f"Use when the user requests {identifier}: {meaning_sentence} "
        "Read the portable capability spec and run the OpenCode preflight wrapper before claiming support."
    )

    body = f"""---
name: {identifier}
description: "{description}"
metadata:
  portable_source: capabilities/{identifier}.md
  adapter: opencode
---

# {identifier}

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/{identifier}.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info {identifier}`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/{identifier}.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info {identifier}`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `{identifier}`
- Supported modes: `{modes}`
- Argument shape: `{argument_shape}`
- Portable meaning: {meaning}

## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability {identifier} [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
"""
    return identifier, body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify generated projections")
    args = parser.parse_args()

    capability_files = sorted(p for p in CAPABILITIES.glob("*.md") if p.name != "README.md")
    expected: dict[Path, str] = {}
    for capability_file in capability_files:
        identifier, body = render(capability_file)
        expected[OUT / identifier / "SKILL.md"] = body

    stale: list[str] = []
    for path, body in expected.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != body:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")

    existing = sorted(OUT.glob("*/SKILL.md")) if OUT.exists() else []
    extras = [path for path in existing if path not in expected]
    if args.check:
        stale.extend(str(path.relative_to(ROOT)) for path in extras)
    else:
        for path in extras:
            path.unlink()
            try:
                path.parent.rmdir()
            except OSError:
                pass

    if stale:
        print("OpenCode native skill projections are stale:", file=sys.stderr)
        for item in stale:
            print(f"  {item}", file=sys.stderr)
        return 1

    if not args.check:
        print(f"generated {len(expected)} OpenCode native skill projections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
