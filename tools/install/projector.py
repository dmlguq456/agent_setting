"""projector.py — symlink projection plan (INSTALL_LAYOUT.md 레시피의 기계화).

SoT 는 언제나 `capabilities/`·`roles/`·core (PRD §0.5 원칙 3). 이 모듈은 그 SoT 로부터
런타임 home 아래 심어야 할 링크·복사·위임 항목 목록을 계산만 한다 — 실제 `os.symlink()`
적용은 이 모듈의 범위 밖, drivers/<runtime>.py 가 채운다 (Phase 3).

각 runtime 별 projection 표는 INSTALL_LAYOUT.md 의 `ln -sfn` 나열을 그대로 데이터로
옮긴 것 — 새 항목은 INSTALL_LAYOUT.md 먼저 갱신 후 이 표에 반영한다 (single source).
"""

from pathlib import Path

import paths


# ---------------------------------------------------------------------------
# Claude Code projection (INSTALL_LAYOUT.md "Claude Code Projection")
# ---------------------------------------------------------------------------

_CLAUDE_SYMLINK_NAMES = [
    "CLAUDE.md", "README.md", "core", "commands", "skills", "agents",
    "agent-modes", "hooks", "utilities", "tools", "scaffolds", "loops",
    "manifest.json", "statusline.sh", "track-toggle.sh",
]

_CLAUDE_COPY_ONCE_NAMES = ["settings.json", "keybindings.json"]

_CLAUDE_TABLE = (
    [
        {"action": "symlink", "source": f"claude_setting/{name}", "dest_name": name}
        for name in _CLAUDE_SYMLINK_NAMES
    ]
    + [
        {"action": "copy_once", "source": f"claude_setting/{name}", "dest_name": name}
        for name in _CLAUDE_COPY_ONCE_NAMES
    ]
    + [
        # Windows 전용 분기 — install-windows.sh 는 재구현하지 않고 위임만 기록.
        {"action": "delegate", "cmd": ["bash", "adapters/claude/bin/install-windows.sh"]},
    ]
)


# ---------------------------------------------------------------------------
# Codex projection (INSTALL_LAYOUT.md "Codex Projection")
# ---------------------------------------------------------------------------

# (dest name under runtime_home, source relpath) — "" source 는 AGENT_HOME 자체
# (agent-harness 포인터 심링크, repo 루트를 통째로 가리킴).
_CODEX_FIXED_SYMLINKS = [
    ("agent-harness", ""),
    ("AGENTS.md", "codex_setting/AGENTS.md"),
    ("agent-harness-readme.md", "codex_setting/README.md"),
    ("agent-core", "codex_setting/core"),
    ("agent-capabilities", "codex_setting/capabilities"),
    ("agent-roles", "codex_setting/roles"),
    ("agent-bin", "codex_setting/bin"),
    ("agent-tools", "codex_setting/tools"),
    ("agent-utilities", "codex_setting/utilities"),
    ("agent-scaffolds", "codex_setting/scaffolds"),
    ("agent-skills", "codex_setting/codex-skills"),
    ("agent-modes", "codex_setting/codex-modes"),
    ("agent-agents", "codex_setting/codex-agents"),
    ("agent-plugin-marketplace", "codex_setting/codex-plugin-marketplace"),
    ("agent-hooks", "codex_setting/codex-hooks"),
    ("agent-config", "codex_setting/codex-config"),
    ("hooks.json", "codex_setting/codex-hooks/hooks.json"),
]

_CODEX_TABLE = (
    [
        {"action": "symlink", "source": source, "dest_name": dest_name}
        for dest_name, source in _CODEX_FIXED_SYMLINKS
    ]
    + [
        {
            "action": "symlink_glob",
            "source_dir": "codex_setting/codex-skills",
            "dest_subdir": "skills",
            "pattern": "*",
        },
        {
            "action": "symlink_glob",
            "source_dir": "codex_setting/codex-agents",
            "dest_subdir": "agents",
            "pattern": "*.toml",
            # scope=="project" 일 때는 runtime_home 대신 프로젝트 로컬
            # .codex/agents/ 로 뒤집힌다 (INSTALL_LAYOUT.md line 141-142) — plan() 에서 처리.
            "project_scope_override": True,
        },
    ]
)


# ---------------------------------------------------------------------------
# OpenCode projection (INSTALL_LAYOUT.md "OpenCode Projection")
# 로컬 1.17.13 singular 배선 사용 (`agent/`, `command/`, `skills.paths`) — INST-OPEN-4 는
# OPEN 유지, plural `.opencode/skills|commands|agents|plugins/` 로 바꾸지 않는다.
# ---------------------------------------------------------------------------

_OPENCODE_FIXED_SYMLINKS = [
    ("agent-harness", ""),
    ("agent-agents.md", "opencode_setting/AGENTS.md"),
    ("agent-harness-readme.md", "opencode_setting/README.md"),
    ("agent-core", "opencode_setting/core"),
    ("agent-capabilities", "opencode_setting/capabilities"),
    ("agent-roles", "opencode_setting/roles"),
    ("agent-bin", "opencode_setting/bin"),
    ("agent-tools", "opencode_setting/tools"),
    ("agent-utilities", "opencode_setting/utilities"),
    ("agent-skills", "opencode_setting/opencode-skills"),
    ("agent-agents", "opencode_setting/opencode-agents"),
    ("agent-commands", "opencode_setting/opencode-commands"),
    ("plugins/agent-harness-guards.js", "opencode_setting/opencode-plugins/agent-harness-guards.js"),
]

_OPENCODE_TABLE = (
    [
        {"action": "symlink", "source": source, "dest_name": dest_name}
        for dest_name, source in _OPENCODE_FIXED_SYMLINKS
    ]
    + [
        {
            "action": "symlink_glob",
            "source_dir": "opencode_setting/opencode-agents",
            "dest_subdir": "agent",
            "pattern": "*/*.md",
        },
        {
            "action": "symlink_glob",
            "source_dir": "opencode_setting/opencode-commands",
            "dest_subdir": "command",
            "pattern": "*.md",
        },
        {
            "action": "merge",
            "note": (
                "opencode.json instructions[]/skills.paths 비파괴 merge — "
                "실제 merge 로직은 drivers/opencode.py (Phase 3), projector 는 intent 만 emit."
            ),
        },
    ]
)


_TABLES = {
    "claude": _CLAUDE_TABLE,
    "codex": _CODEX_TABLE,
    "opencode": _OPENCODE_TABLE,
}


def _resolve_source_path(relpath):
    """relpath 를 절대경로로. 빈 문자열은 agent_home() 자체(포인터 심링크 소스)."""
    if relpath == "":
        return paths.agent_home()
    return paths.resolve_source(relpath)


def _dest_dir_for(runtime, scope, dest_subdir):
    """symlink_glob 항목의 dest_dir 계산. codex agents glob + scope=project 특례 처리."""
    if runtime == "codex" and dest_subdir == "agents" and scope == "project":
        # INSTALL_LAYOUT.md: project-scoped install 은 codex agents glob 만
        # 프로젝트 로컬 `.codex/agents/` 로 뒤집힌다 (runtime_home 자체는 바뀌지 않음).
        return Path.cwd() / ".codex" / "agents"
    return paths.runtime_home(runtime, scope) / dest_subdir


def _expand(table, runtime, scope):
    """table 의 추상 항목들을 concrete plan 항목으로 펼친다."""
    runtime_home = paths.runtime_home(runtime, scope)
    entries = []

    for item in table:
        action = item["action"]

        if action in ("symlink", "copy_once"):
            source_relpath = item["source"]
            source_path = _resolve_source_path(source_relpath)
            dest_path = runtime_home / item["dest_name"]
            source_present = source_path.exists()
            if source_present:
                entries.append(
                    {
                        "action": action,
                        "source": str(source_path),
                        "dest": str(dest_path),
                        "source_present": True,
                    }
                )
            else:
                entries.append(
                    {
                        "action": "skip",
                        "reason": f"source absent: {source_path}",
                        "dest": str(dest_path),
                    }
                )

        elif action == "delegate":
            entries.append({"action": "delegate", "cmd": item["cmd"], "source_present": True})

        elif action == "merge":
            entries.append({"action": "merge", "note": item["note"], "source_present": True})

        elif action == "symlink_glob":
            source_dir_relpath = item["source_dir"]
            source_dir = paths.resolve_source(source_dir_relpath)
            dest_dir = _dest_dir_for(runtime, scope, item["dest_subdir"])
            if not source_dir.exists():
                # source_dir 자체가 없으면 아무 것도 만들지 않는다 (에러 아님).
                continue
            for match in sorted(source_dir.glob(item["pattern"])):
                dest_path = dest_dir / match.name
                source_present = match.exists()
                if source_present:
                    entries.append(
                        {
                            "action": "symlink",
                            "source": str(match),
                            "dest": str(dest_path),
                            "source_present": True,
                        }
                    )
                else:
                    entries.append(
                        {
                            "action": "skip",
                            "reason": f"source absent: {match}",
                            "dest": str(dest_path),
                        }
                    )

        else:
            raise ValueError(f"알 수 없는 projection action: {action!r}")

    return entries


def plan(runtimes, scope="global"):
    """runtime 별 resolved projection 계획을 돌려준다.

    반환 shape: {runtime: [entry, ...]} — entry 는 action 별로
    {"action": "symlink"|"copy_once", "source": str, "dest": str, "source_present": True}
    {"action": "delegate", "cmd": [...], "source_present": True}
    {"action": "merge", "note": str, "source_present": True}
    {"action": "skip", "reason": str, "dest": str}
    """
    return {rt: _expand(_TABLES.get(rt, []), rt, scope) for rt in runtimes}
