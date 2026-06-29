#!/usr/bin/env python3
"""Generate the Codex-native plugin projection for the portable harness."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ADAPTER = ROOT / "adapters" / "codex"
PLUGIN_NAME = "agent-harness-codex"
PLUGIN_ROOT = ADAPTER / "plugins" / PLUGIN_NAME
MARKETPLACE = ADAPTER / ".agents" / "plugins" / "marketplace.json"
SKILLS = ADAPTER / "skills"
VALIDATOR = Path.home() / ".codex" / "skills" / ".system" / "plugin-creator" / "scripts" / "validate_plugin.py"


def plugin_json() -> dict:
    return {
        "name": PLUGIN_NAME,
        "version": "0.1.0",
        "description": "Codex-native plugin projection for the portable agent harness.",
        "author": {
            "name": "agent_setting",
        },
        "skills": "./skills/",
        "interface": {
            "displayName": "Agent Harness Codex",
            "shortDescription": "Portable agent harness capabilities for Codex.",
            "longDescription": (
                "Adapter-owned Codex plugin projection generated from portable "
                "agent_setting capability contracts. Legacy runtime files are reference only."
            ),
            "developerName": "agent_setting",
            "category": "Developer Tools",
            "capabilities": ["Interactive", "Write"],
            "defaultPrompt": [
                "Use the portable agent harness in Codex.",
            ],
        },
    }


def marketplace_json() -> dict:
    return {
        "name": "agent-harness",
        "interface": {
            "displayName": "Agent Harness",
        },
        "plugins": [
            {
                "name": PLUGIN_NAME,
                "source": {
                    "source": "local",
                    "path": f"./plugins/{PLUGIN_NAME}",
                },
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "ON_INSTALL",
                },
                "category": "Developer Tools",
            }
        ],
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def sync() -> None:
    if not SKILLS.exists():
        raise SystemExit("Codex native skills are missing; run adapters/codex/bin/sync-native-skills.py first")

    write_json(PLUGIN_ROOT / ".codex-plugin" / "plugin.json", plugin_json())

    plugin_skills = PLUGIN_ROOT / "skills"
    if plugin_skills.exists() or plugin_skills.is_symlink():
        shutil.rmtree(plugin_skills)
    shutil.copytree(SKILLS, plugin_skills)

    write_json(MARKETPLACE, marketplace_json())


def check_file(path: Path, expected: str, stale: list[str]) -> None:
    if not path.exists() or path.read_text(encoding="utf-8") != expected:
        stale.append(str(path.relative_to(ROOT)))


def check() -> int:
    stale: list[str] = []
    check_file(
        PLUGIN_ROOT / ".codex-plugin" / "plugin.json",
        json.dumps(plugin_json(), indent=2) + "\n",
        stale,
    )
    check_file(MARKETPLACE, json.dumps(marketplace_json(), indent=2) + "\n", stale)

    for skill in sorted(SKILLS.glob("*/SKILL.md")):
        rel = skill.relative_to(SKILLS)
        plugin_skill = PLUGIN_ROOT / "skills" / rel
        if not plugin_skill.exists() or plugin_skill.read_text(encoding="utf-8") != skill.read_text(encoding="utf-8"):
            stale.append(str(plugin_skill.relative_to(ROOT)))

    expected = {PLUGIN_ROOT / "skills" / skill.relative_to(SKILLS) for skill in SKILLS.glob("*/SKILL.md")}
    plugin_skill_files = sorted((PLUGIN_ROOT / "skills").glob("*/SKILL.md")) if (PLUGIN_ROOT / "skills").exists() else []
    for path in plugin_skill_files:
        if path not in expected:
            stale.append(str(path.relative_to(ROOT)))

    if VALIDATOR.exists():
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(PLUGIN_ROOT)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if result.returncode != 0:
            print(result.stdout, file=sys.stderr)
            stale.append(str(PLUGIN_ROOT.relative_to(ROOT)))

    if stale:
        print("Codex native plugin projection is stale:", file=sys.stderr)
        for item in stale:
            print(f"  {item}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify generated projection")
    args = parser.parse_args()

    if args.check:
        return check()
    sync()
    print(f"generated Codex native plugin projection at {PLUGIN_ROOT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
