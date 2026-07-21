#!/usr/bin/env python3
"""Generate OpenCode-native Agent projections for kernel agents.

Team agents are retired: former team behavior lives in the portable unit catalog
(`roles/units/**`) and runs as dispatched depth-2 nodes, never as native agents.
Only kernel helpers (`kernel.agents` in `harness-manifest.json`) project here.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "adapters" / "opencode" / "agents"
sys.path.insert(0, str(ROOT / "tools"))

import harness_manifest


KERNEL_AGENTS = {
    "memory-scout": {
        "description": "Read-only memory scout for agent-initiated deep memory reconnaissance.",
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
- verdict: found / not-found / ambiguous
- hits: up to 3 short quotes or paraphrases with record id / session pointer
- apply: one line telling the main agent what to do now
- check: one live-code or file cross-check line, or not checked with reason
""",
    }
}

# Backward-compatible alias for callers that patched/consumed the old constant name.
EXTRA_AGENTS = KERNEL_AGENTS


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).replace('"', "'")


def render_kernel_agent(name: str, spec: dict[str, str]) -> str:
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

    manifest = harness_manifest.load()
    expected: dict[Path, str] = {}
    for name in manifest["kernel"]["agents"]:
        spec = KERNEL_AGENTS.get(name)
        if spec is None:
            print(f"unknown kernel agent (no OpenCode projection defined): {name}", file=sys.stderr)
            return 1
        expected[OUT / name / f"{name}.md"] = render_kernel_agent(name, spec)

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
