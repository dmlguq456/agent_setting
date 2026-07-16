#!/usr/bin/env python3
"""Generate the Skill invocation registry from the canonical manifest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "skill-conformance" / "invocation-policy.tsv"
sys.path.insert(0, str(ROOT / "tools"))

import harness_manifest


def render(manifest: dict) -> str:
    lines = [
        "# GENERATED — edit harness-manifest.json, then run tools/generate.py.",
        "# Columns: skill<TAB>class<TAB>caller/intent",
        "# Classes: user-only | parent-invoked | entry-router | model-support",
    ]
    for identifier, spec in manifest["capabilities"].items():
        invocation = spec["invocation"]
        intent = f"{invocation['use_when']} {invocation['not_for']}"
        lines.append(f"{identifier}\t{invocation['class']}\t{intent}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify generated projection")
    args = parser.parse_args()

    expected = render(harness_manifest.load())
    if args.check:
        if not OUT.is_file() or OUT.read_text(encoding="utf-8") != expected:
            print(f"Skill invocation policy is stale: {OUT.relative_to(ROOT)}", file=sys.stderr)
            return 1
        return 0

    OUT.write_text(expected, encoding="utf-8")
    print("generated Skill invocation policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
