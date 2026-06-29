#!/usr/bin/env python3
"""Generate OpenCode-native Agent projections from portable role profiles."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ROLES = ROOT / "roles" / "README.md"
OUT = ROOT / "adapters" / "opencode" / "agents"


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).replace('"', "'")


def strip_code(text: str) -> str:
    text = text.strip()
    if text.startswith("`") and text.endswith("`"):
        return text[1:-1]
    return text


def role_rows(text: str) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 4 or cells[0] == "Role profile":
            continue
        rows.append((strip_code(cells[0]), strip_code(cells[1]), compact(cells[2])))
    return rows


def render(profile: str, portable_role: str, responsibility: str) -> str:
    description = compact(
        f"OpenCode-native agent for portable role profile {profile}. "
        f"Use when delegating work whose primary responsibility is: {responsibility}"
    )
    return f"""---
description: "{description}"
---

You are the OpenCode-native realization of the portable `{profile}` role
profile. This is adapter-owned output generated from `roles/README.md`, not a Claude Agent copy.

## Source

- Portable source: `roles/README.md`
- Mode inventory: `roles/MODES.md`
- Runtime role mapper: `adapters/opencode/bin/preflight.sh role <portable-role>`
- Runtime mode mapper: `adapters/opencode/bin/preflight.sh mode-info <family/mode>`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Role Contract

- Role profile: `{profile}`
- Portable model role: `{portable_role}`
- Primary responsibility: {responsibility}

## Use

1. Read `roles/README.md` and the task-relevant entry in `roles/MODES.md`.
2. Use `adapters/opencode/bin/preflight.sh role <portable-role>` for concrete
   model/variant availability before assuming a model tier.
3. Use `adapters/opencode/bin/preflight.sh mode-info <family/mode>` before
   applying a mode persona.
4. Run normal harness guards through `adapters/opencode/bin/preflight.sh`.

Do not use `adapters/claude/agents/*.md` as OpenCode-native source. Claude
Agent files are compatibility/reference surfaces.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify generated projections")
    args = parser.parse_args()

    rows = role_rows(ROLES.read_text(encoding="utf-8"))
    expected = {OUT / profile / f"{profile}.md": render(profile, role, responsibility) for profile, role, responsibility in rows}

    stale: list[str] = []
    for path, body in expected.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != body:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")

    existing = sorted(OUT.glob("*/*.md")) if OUT.exists() else []
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
        print("OpenCode native agent projections are stale:", file=sys.stderr)
        for item in stale:
            print(f"  {item}", file=sys.stderr)
        return 1

    if not args.check:
        print(f"generated {len(expected)} OpenCode native agent projections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
