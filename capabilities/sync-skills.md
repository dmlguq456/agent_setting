# Capability: sync-skills

This is the portable capability contract for `sync-skills`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `sync-skills` |
| Group | `ops` |
| Supported modes | `none` |
| Portable meaning | 정의 변경을 읽어 README/manifest/cross-doc invariant drift를 점검·동기화한다. |
| Argument shape | `[--check] [--force] [--auto-fix [--dry-run]]` |

## Invocation Semantics

Skills + Agents 정의 변경을 감지해 <agent-home>/README.md (GitHub) 의 대시보드 (워크플로우 map + cheat-sheet + 통합 가이드라인) 를 동기화한다. drift 체크 전용 모드도 지원.

Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.

## Artifact Ownership

Use the shared artifact root rule: prefer `.agent_reports/`; use legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not. Capability-specific output placement follows `core/CONVENTIONS.md` section 5 until this spec is expanded with a stricter per-capability artifact map.

## Role Requirements

Use portable role names from `roles/README.md` and `core/CONVENTIONS.md`. Concrete model names, subagent frontmatter, and runtime-specific tool lists belong in adapter files.

## Guard Requirements

Adapters must preserve the portable invariants relevant to this capability:

- resolve artifact root through `utilities/artifact-root.sh` or equivalent logic;
- enforce git/worktree safety before edits;
- enforce artifact ordering before new durable artifacts;
- enforce spec-read gating when this capability changes spec-backed code or specs;
- use DB memory paths, not runtime-native memory files.

## Adapter Realization

| Adapter | Realization |
|---|---|
| Claude Code | `adapters/claude/skills/sync-skills` currently projects compatibility source `skills/sync-skills/SKILL.md`. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info sync-skills`. Do not consume `skills/sync-skills/SKILL.md` as native Codex configuration. |

## Compatibility Reference

The historical Claude Skill source remains at `skills/sync-skills/SKILL.md` while this capability is being split into portable and adapter-native layers.
