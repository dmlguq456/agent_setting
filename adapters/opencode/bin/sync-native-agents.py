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


EXTRA_AGENTS = {
    "memory-scout": {
        "description": "Read-only memory scout for recall-first deep memory reconnaissance.",
        "instructions": """You are the OpenCode-native memory-scout custom agent.
This is adapter-owned output generated from `core/MEMORY.md` §7.4, not a non-OpenCode Agent copy.

## Contract

1. Read-only only. Do not edit files or write memory.
2. Never run memory mutation commands such as mem add, mem note, mem consume, mem restore, mem delete, mem reinforce, mem merge, mem prune, mem graduate, or mem reattribute.
3. Use `<agent-home>/tools/memory/recall.sh` first in the current cwd with narrow synonym and Korean/English variants.
4. Read one selected hit with `python3 <agent-home>/tools/memory/mem.py show <id>`, or a small ranked set with `<agent-home>/tools/memory/recall.sh "<query>" --full --limit 3`. These reads do not consume pending handoffs.
5. If misses matter, expand to `--all`, then `--sessions`. Never bypass the CLI with direct SQLite or `dump.jsonl` reads.
6. Cross-check one live file/code fact when the memory result implies an actionable convention.

Output at most 15 lines:
- verdict: 있음 / 없음 / 애매
- hits: up to 3 short quotes or paraphrases with record id / session pointer
- apply: one line telling the main agent what to do now
- check: one live-code or file cross-check line, or not checked with reason
""",
    }
}


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).replace('"', "'")


def strip_code(text: str) -> str:
    text = text.strip()
    if text.startswith("`") and text.endswith("`"):
        return text[1:-1]
    return text


def clean_role_note(text: str) -> str:
    return re.sub(r"`([^`]*)`", r"\1", text.strip())


def mapper_role(profile: str, role_note: str) -> str:
    note = clean_role_note(role_note).lower()
    if "external adversary" in note:
        return "external adversary"
    if "fast implementer" in note:
        return "fast implementer"
    if "fast reviewer" in note:
        return "fast reviewer"
    if "fast fact" in note:
        return "fast fact checker"
    if "fast tool worker" in note:
        return "fast tool worker"
    if "deep reviewer" in note:
        return "deep reviewer"
    if "deep editor" in note:
        return "deep editor"
    if "deep maker" in note:
        return "deep maker"
    profile_defaults = {
        "qa-team": "fast reviewer",
        "research-team": "deep reviewer",
        "editorial-team": "deep editor",
    }
    return profile_defaults.get(profile, "fast reviewer")


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
    role_note = clean_role_note(portable_role)
    mapped_role = mapper_role(profile, role_note)
    read_only = profile in {"qa-team", "external-adversary"}
    tool_lines = ["  task: false"]
    permission_lines = ["  task: deny"]
    if read_only:
        tool_lines.extend(["  edit: false", "  write: false"])
        permission_lines.append("  edit: deny")
    description = compact(
        f"OpenCode-native agent for portable role profile {profile}. "
        f"Use when delegating work whose primary responsibility is: {responsibility}"
    )
    return f"""---
description: "{description}"
mode: subagent
tools:
{chr(10).join(tool_lines)}
permission:
{chr(10).join(permission_lines)}
---

You are the OpenCode-native realization of the portable `{profile}` role
profile. This is adapter-owned output generated from `roles/README.md`, not a non-OpenCode Agent copy.

## Source

- Portable source: `roles/README.md`
- Mode inventory: `roles/MODES.md`
- Runtime role mapper: `adapters/opencode/bin/preflight.sh role {mapped_role}`
- Runtime mode mapper: `adapters/opencode/bin/preflight.sh mode-info <family/mode>`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Role Contract

- Role profile: `{profile}`
- Portable model role note: `{role_note}`
- OpenCode role-map input: `{mapped_role}`
- Primary responsibility: {responsibility}

## Use

1. Read `roles/README.md` and the task-relevant entry in `roles/MODES.md`.
2. Use `adapters/opencode/bin/preflight.sh role {mapped_role}` for concrete
   model/variant availability before assuming a model tier.
3. Use `adapters/opencode/bin/preflight.sh mode-info <family/mode>` before
   applying a mode persona.
4. Run normal harness guards through `adapters/opencode/bin/preflight.sh`.

Do not use non-OpenCode Agent files as OpenCode-native source. Runtime-specific
Agent files are compatibility/reference surfaces only.
"""


def render_extra_agent(name: str, spec: dict[str, str]) -> str:
    tool_lines = ["  task: false", "  edit: false", "  write: false"]
    permission_lines = ["  task: deny", "  edit: deny"]
    description = compact(spec["description"])
    return f"""---
description: "{description}"
mode: subagent
tools:
{chr(10).join(tool_lines)}
permission:
{chr(10).join(permission_lines)}
---

{spec["instructions"]}"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify generated projections")
    args = parser.parse_args()

    rows = role_rows(ROLES.read_text(encoding="utf-8"))
    expected = {OUT / profile / f"{profile}.md": render(profile, role, responsibility) for profile, role, responsibility in rows}
    for name, spec in EXTRA_AGENTS.items():
        expected[OUT / name / f"{name}.md"] = render_extra_agent(name, spec)

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
