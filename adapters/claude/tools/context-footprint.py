#!/usr/bin/env python3
"""Report early-context footprint for the portable agent harness.

This is a deterministic audit helper, not a failing CI gate by default. It counts
bootstrap files, active skill metadata surfaces, duplicate Codex skill exposure,
representative hook outputs, and the largest Skill bodies.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

CODEX_BUDGET = 8000
CLAUDE_BUDGET = 10000


def chars(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return 0


def skill_meta(base: Path, prefix: str = "") -> tuple[int, int, set[str]]:
    total = 0
    count = 0
    names: set[str] = set()
    for skill in sorted(base.glob("*/SKILL.md")):
        text = skill.read_text(encoding="utf-8", errors="ignore")
        name_match = re.search(r"^name:\s*(.+)$", text, re.M)
        desc_match = re.search(r"^description:\s*(.+)$", text, re.M)
        if not name_match or not desc_match:
            continue
        name = name_match.group(1).strip().strip('"')
        desc = desc_match.group(1).strip().strip('"')
        names.add(name)
        count += 1
        total += len(prefix + name) + len(desc) + len(str(skill))
    return total, count, names


def skill_body_sizes(paths: Iterable[Path]) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    for base in paths:
        for skill in sorted(base.glob("*/SKILL.md")):
            rows.append((chars(skill), str(skill)))
    return sorted(rows, reverse=True)


def run_capture(args: list[str], cwd: Path, env: dict[str, str] | None = None, timeout: int = 10) -> tuple[int, str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    try:
        proc = subprocess.run(
            args,
            cwd=cwd,
            env=merged,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return 69, str(exc)


def plugin_installed(root: Path, codex_home: Path | None, timeout: int) -> bool | None:
    if codex_home is None:
        return None
    rc, out = run_capture(["codex", "plugin", "list", "--json"], root, {"CODEX_HOME": str(codex_home)}, timeout)
    if rc != 0:
        return None
    return "agent-harness-codex" in out


def harness_native_skill_links(root: Path, codex_home: Path | None) -> set[str]:
    if codex_home is None:
        return set()
    skills_home = codex_home / "skills"
    projected = (root / "codex_setting" / "codex-skills").resolve()
    names: set[str] = set()
    if not skills_home.exists():
        return names
    for item in skills_home.iterdir():
        if not item.is_symlink():
            continue
        try:
            target = item.resolve()
        except OSError:
            continue
        try:
            target.relative_to(projected)
        except ValueError:
            continue
        if (target / "SKILL.md").exists():
            names.add(item.name)
    return names


def hook_samples(root: Path, timeout: int) -> list[tuple[str, int, int]]:
    env = {"AGENT_HOME": str(root)}
    samples: list[tuple[str, int, int]] = []
    commands = [
        ("codex-mode", [str(root / "adapters/codex/bin/preflight.sh"), "mode", str(root), "footprint-sample"]),
        ("codex-recall-neutral", [str(root / "adapters/codex/bin/preflight.sh"), "recall", "오늘 작업", str(root)]),
        ("codex-recall-signal", [str(root / "adapters/codex/bin/preflight.sh"), "recall", "지난번 작업", str(root)]),
        ("codex-briefing-default", [str(root / "adapters/codex/bin/preflight.sh"), "briefing", str(root)]),
    ]
    with tempfile.TemporaryDirectory(prefix="context-footprint-mem-") as tmp:
        sample_env = dict(env)
        sample_env["MEM_STORE"] = tmp
        for label, cmd in commands:
            rc, out = run_capture(cmd, root, sample_env, timeout)
            samples.append((label, rc, len(out)))
    return samples


def main() -> int:
    parser = argparse.ArgumentParser(description="Report agent harness context footprint")
    parser.add_argument("--root", default=".", help="harness repository root")
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--skip-runtime", action="store_true", help="do not inspect CODEX_HOME/plugin state")
    parser.add_argument("--skip-hooks", action="store_true", help="do not run hook/preflight samples")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--strict", action="store_true", help="exit 1 when warnings are present")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    codex_home = None if args.skip_runtime else Path(args.codex_home).expanduser().resolve()
    warnings: list[str] = []

    print("context_footprint_report=1")
    print(f"root={root}")

    bootstraps = [
        root / "adapters/codex/AGENTS.md",
        root / "adapters/claude/CLAUDE.md",
        root / "adapters/opencode/AGENTS.md",
    ]
    print("\n[bootstrap]")
    for path in bootstraps:
        print(f"chars={chars(path)} path={path.relative_to(root)}")

    print("\n[skill-metadata]")
    codex_local, codex_local_count, codex_local_names = skill_meta(root / "adapters/codex/skills")
    codex_plugin, codex_plugin_count, codex_plugin_names = skill_meta(
        root / "adapters/codex/plugins/agent-harness-codex/skills", "agent-harness-codex:"
    )
    opencode, opencode_count, _ = skill_meta(root / "adapters/opencode/skills")
    claude, claude_count, _ = skill_meta(root / "adapters/claude/skills")
    print(f"surface=codex-local items={codex_local_count} chars={codex_local}")
    print(f"surface=codex-plugin items={codex_plugin_count} chars={codex_plugin}")
    print(f"surface=opencode items={opencode_count} chars={opencode}")
    print(f"surface=claude items={claude_count} chars={claude}")

    plugin_state = plugin_installed(root, codex_home, args.timeout) if codex_home else None
    native_links = harness_native_skill_links(root, codex_home)
    if codex_home:
        active = 0
        active_labels: list[str] = []
        if native_links:
            active += codex_local
            active_labels.append("native")
        if plugin_state is True:
            active += codex_plugin
            active_labels.append("plugin")
        if not active_labels:
            active_labels.append("none-or-unknown")
        overlap = sorted(native_links & codex_plugin_names) if plugin_state is True else []
        print(f"codex_home={codex_home}")
        print(f"codex_active_surfaces={'+'.join(active_labels)} chars={active} duplicate_names={len(overlap)}")
        if active > CODEX_BUDGET:
            warnings.append(f"codex active skill metadata {active} > {CODEX_BUDGET}")
        if overlap:
            warnings.append(f"codex duplicate skill names active={len(overlap)}")
    else:
        print("codex_active_surfaces=skipped")

    if claude > CLAUDE_BUDGET:
        warnings.append(f"claude skill metadata {claude} > {CLAUDE_BUDGET}")

    print("\n[hook-samples]")
    if args.skip_hooks:
        print("skipped=1")
    else:
        for label, rc, size in hook_samples(root, args.timeout):
            print(f"sample={label} exit={rc} chars={size}")
            if label == "codex-briefing-default" and size > 0:
                warnings.append("briefing default emitted context outside explicit briefing desk")

    print("\n[largest-skill-bodies]")
    for size, path in skill_body_sizes([
        root / "adapters/claude/skills",
        root / "adapters/codex/skills",
        root / "adapters/opencode/skills",
    ])[:10]:
        try:
            rel = Path(path).relative_to(root)
        except ValueError:
            rel = Path(path)
        print(f"chars={size} path={rel}")

    print("\n[warnings]")
    if warnings:
        for warning in warnings:
            print(f"warning={warning}")
    else:
        print("none")
    print("status=ok" if not warnings else f"status=warn warnings={len(warnings)}")
    return 1 if args.strict and warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
