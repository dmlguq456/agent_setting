#!/usr/bin/env python3
"""Generate the manifest-owned frontmatter of Claude-native Skills.

Claude Skill procedure bodies remain adapter-owned. Only the frontmatter block
through the second `---` delimiter is generated from `harness-manifest.json`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOTS = (
    ROOT / "adapters" / "claude" / "skills",
    ROOT / "skills",
)
sys.path.insert(0, str(ROOT / "tools"))

import harness_manifest


def quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def generated_frontmatter(identifier: str, spec: dict) -> str:
    invocation = spec["invocation"]
    description = f"{invocation['use_when']} {invocation['not_for']}"
    modes = json.dumps(spec["modes"], ensure_ascii=False)
    return f"""---
# GENERATED METADATA — edit harness-manifest.json, then run tools/generate.py.
name: {identifier}
description: {quoted(description)}
argument-hint: {quoted(spec["argument_shape"])}
metadata:
  group: {spec["group"]}
  fam: {spec["family"]}
  invocation_class: {invocation["class"]}
  modes: {modes}
  blurb: {quoted(spec["summary"])}
  use_when: {quoted(invocation["use_when"])}
  not_for: {quoted(invocation["not_for"])}
---"""


def project_body(path: Path, identifier: str, spec: dict) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise harness_manifest.ManifestError(f"Claude Skill lacks frontmatter: {path}")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise harness_manifest.ManifestError(f"Claude Skill frontmatter is unterminated: {path}")
    return generated_frontmatter(identifier, spec) + parts[2]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify generated frontmatter")
    args = parser.parse_args()

    manifest = harness_manifest.load()
    expected: dict[Path, str] = {}
    for output_root in OUTPUT_ROOTS:
        for identifier, spec in manifest["capabilities"].items():
            path = output_root / identifier / "SKILL.md"
            if not path.is_file():
                raise harness_manifest.ManifestError(f"Claude Skill missing: {path}")
            expected[path] = project_body(path, identifier, spec)

    existing = set()
    for output_root in OUTPUT_ROOTS:
        existing.update(output_root.glob("*/SKILL.md"))
    extras = sorted(existing - set(expected))
    stale = [
        path for path, body in expected.items()
        if path.read_text(encoding="utf-8") != body
    ] + extras
    if args.check:
        if stale:
            print("Claude native Skill metadata is stale:", file=sys.stderr)
            for path in stale:
                print(f"  {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        return 0

    for path, body in expected.items():
        path.write_text(body, encoding="utf-8")
    for path in extras:
        path.unlink()
    print(
        f"generated metadata for {len(manifest['capabilities'])} Claude native Skills "
        "and compatibility references"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
