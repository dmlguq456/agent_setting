#!/usr/bin/env python3
"""Generate Codex-native Skill projections from portable capabilities."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CAPABILITIES = ROOT / "capabilities"
OUT = ROOT / "adapters" / "codex" / "skills"


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


def markdown_section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == marker:
            start = index + 1
            break
    if start is None:
        return ""
    body: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    return compact("\n".join(body))


def markdown_section_raw(text: str, heading: str) -> str:
    marker = f"## {heading}"
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == marker:
            start = index
            break
    if start is None:
        return ""
    body: list[str] = []
    for line in lines[start:]:
        if body and line.startswith("## "):
            break
        body.append(line)
    return "\n".join(body).strip()


def portable_sections(source: str) -> str:
    sections: list[str] = []
    for heading in (
        "Artifact Ownership",
        "Role Requirements",
        "Guard Requirements",
        "Portable Procedure",
        "Routing Boundary",
        "Mode-Specific Semantics",
    ):
        section = markdown_section_raw(source, heading)
        if section:
            sections.append(section)
    if not sections:
        return ""
    return "\n\n## Projected Portable Details\n\n" + "\n\n".join(sections) + "\n"


def render(capability_file: Path) -> tuple[str, str]:
    slug = capability_file.stem
    source = capability_file.read_text(encoding="utf-8")
    rows = contract_rows(source)
    identifier = rows.get("Identifier", f"`{slug}`").strip("`")
    modes = rows.get("Supported modes", "none").strip("`")
    argument_shape = rows.get("Argument shape", "").strip("`")
    meaning = compact(rows.get("Portable meaning", identifier))
    invocation_semantics = markdown_section(source, "Invocation Semantics")
    portable_contract = ""
    if invocation_semantics:
        portable_contract = f"""
## Portable Contract

- Invocation semantics: {invocation_semantics}
"""
    projected_details = portable_sections(source)
    meaning_sentence = meaning if meaning.endswith((".", "!", "?")) else f"{meaning}."
    description = compact(f"Use for {identifier}: {meaning_sentence}")

    body = f"""---
name: {identifier}
description: "{description}"
---

# {identifier}

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/{identifier}.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info {identifier}`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/{identifier}.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info {identifier}`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `{identifier}`
- Supported modes: `{modes}`
- Argument shape: `{argument_shape}`
- Portable meaning: {meaning}
{portable_contract}
{projected_details}

## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before capability routing/spec-changing work: `adapters/codex/bin/preflight.sh route {identifier} [cwd] [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability {identifier} [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh status [cwd] [session-id]`, `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]`, and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
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
        print("Codex native skill projections are stale:", file=sys.stderr)
        for item in stale:
            print(f"  {item}", file=sys.stderr)
        return 1

    if not args.check:
        print(f"generated {len(expected)} Codex native skill projections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
