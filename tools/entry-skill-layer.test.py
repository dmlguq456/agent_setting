#!/usr/bin/env python3
"""Deterministic entry-router layer gate, including owner-link resolution."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIMIT, TOTAL_LIMIT = 4096, 53248
manifest = json.loads((ROOT / "harness-manifest.json").read_text())
entries = sorted(name for name, spec in manifest["capabilities"].items()
                 if spec["invocation"]["class"] == "entry-router")
assert len(entries) == 13, f"expected exactly 13 entry routers, got {len(entries)}"
owner_row = re.compile(
    r"^\| Entry load phase \| `post-approval`; owner contract `capabilities/([^`]+)\.md` \|$",
    re.MULTILINE,
)
declared_owners = {}
for capability in (ROOT / "capabilities").glob("*.md"):
    matches = owner_row.findall(capability.read_text(encoding="utf-8"))
    assert len(matches) <= 1, f"{capability.relative_to(ROOT)} has duplicate owner rows"
    if matches:
        declared_owners[capability.stem] = matches[0]
assert sorted(declared_owners) == entries, "capability owner rows must match exactly the 13 entry routers"
assert all(name == target for name, target in declared_owners.items()), "capability owner row target mismatch"
for document, phrases in {
    "core/DESIGN_PRINCIPLES.md": ("compact pre-approval router", "assigned stage worker"),
    "capabilities/README.md": ("compact pre-approval router", "Assigned stage workers"),
}.items():
    text = " ".join((ROOT / document).read_text(encoding="utf-8").split())
    assert all(phrase in text for phrase in phrases), f"{document} lost entry-layer contract"


def anchor(value: str) -> str:
    value = re.sub(r"`([^`]*)`", r"\1", value).lower()
    value = re.sub(r"[^a-z0-9 _-]", "", value)
    return re.sub(r"[ _]", "-", value).strip("-")


def owner_targets(text: str) -> list[tuple[str, bool]]:
    markdown = [(target, True) for target in re.findall(r"\]\(([^)]+)\)", text)]
    literals = [(target, False) for target in re.findall(r"`((?:\.\.?/)?[^`\s#]+\.md(?:#[^`\s]+)?)`", text)]
    return markdown + literals


def resolve_owner(owner: Path) -> None:
    text = owner.read_text(encoding="utf-8")
    assert "](<agent-home>/" not in text, f"{owner.relative_to(ROOT)} has a non-CommonMark owner link"
    for target, required in owner_targets(text):
        if "*" in target or target.startswith(("http:", "https:", "mailto:")):
            continue
        path_text, separator, fragment = target.partition("#")
        if path_text.startswith("<agent-home>/"):
            target_path = ROOT / path_text[len("<agent-home>/"):]
        else:
            target_path = owner if not path_text else (owner.parent / path_text).resolve()
        if not required and not target_path.exists():
            # Inline-code filenames may describe future artifacts; only resolve
            # them when they name a concrete adjacent Skill reference.
            continue
        assert target_path.is_file(), f"{owner.relative_to(ROOT)} unresolved target {target}"
        if separator:
            anchors = {anchor(line[1:].strip()) for line in target_path.read_text(encoding="utf-8").splitlines()
                       if line.startswith("#")}
            assert fragment in anchors, f"{owner.relative_to(ROOT)} unresolved anchor {target}"


OWNER_TREES = (
    "skills",
    "adapters/claude/skills",
    "adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills",
)
for tree in OWNER_TREES + ("adapters/codex/skills", "adapters/opencode/skills"):
    sizes = []
    for name in entries:
        skill = ROOT / tree / name / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        size = len(skill.read_bytes())
        sizes.append(size)
        assert size <= LIMIT, f"{skill.relative_to(ROOT)} exceeds {LIMIT} bytes"
        assert "Use when " in text and "Not for " in text, f"{skill} lost manifest routing metadata"
        if tree in OWNER_TREES:
            owner = skill.parent / "references" / "owner-execution.md"
            assert owner.is_file(), f"{owner} missing"
            resolve_owner(owner)
            assert "Post-approval owner contract" in text and "Do not load references" in text
            assert "owner-execution.md" not in text.split("## Post-approval owner contract", 1)[0]
            assert text.count("## Reference Index") == 1, f"{skill} needs exactly one Reference Index"
            assert "| File | Load when | Obligation |" in text, f"{skill} lost the reference-map contract"
            owner_edges = re.findall(r"\]\((references/owner-execution\.md)\)", text)
            assert owner_edges == ["references/owner-execution.md"], f"{skill} must expose one owner edge"
            assert not (skill.parent / "README.md").exists(), f"{skill.parent} retains redundant README.md"
            directories = {path.name for path in skill.parent.iterdir() if path.is_dir()}
            assert directories == {"references"}, f"{skill.parent} must use only references/: {directories}"
            nested = [path for path in (skill.parent / "references").rglob("*") if path.is_dir()]
            assert not nested, f"{skill.parent} has nested reference directories: {nested}"
        else:
            assert "Before approval" in text and f"capabilities/{name}.md" in text
            assert "## Projected Portable Details" not in text and "## Portable Contract" not in text
    assert sum(sizes) <= TOTAL_LIMIT, f"{tree} aggregate exceeds {TOTAL_LIMIT} bytes"
    print(f"PASS {tree}: entries={len(entries)} total={sum(sizes)} max={max(sizes)}")
for tree in OWNER_TREES:
    for name in entries:
        resolve_owner(ROOT / tree / name / "references" / "owner-execution.md")
for tree in OWNER_TREES:
    resolve_owner(ROOT / tree / "draft-strategy" / "references" / "delegate-prompt.md")
print(f"PASS owner-links: trees={len(OWNER_TREES)} entries={len(entries)}")
