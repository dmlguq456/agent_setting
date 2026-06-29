# Capability: autopilot-spec

This is the portable capability contract for `autopilot-spec`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `autopilot-spec` |
| Group | `entry` |
| Supported modes | `app, library, api, cli, research, update` |
| Portable meaning | 요구사항·청사진 작성·갱신. `prd.md`를 spec 변경의 단일 경로로 유지한다. |
| Argument shape | `<task description> [--mode auto|app|library|api|cli|research|update (콤마로 다중)] [--qa quick|light|standard|thorough] [--user-refine]` |

## Invocation Semantics

_요구사항·청사진 작성·갱신_ 의 일반화 entry — 신규 의도, 기존 코드 정돈·공개 준비, 그리고 기존 spec 의 update·iteration (prd.md 갱신) 자리 모두. mode 5종 (app / library / api / cli / research) + 다중 + auto + update mode (기존 prd.md 갱신 — 모든 spec 변경의 canonical 경로, 버전 snapshot 자동). PRD 구조 = 공통 + mode 별 독립 섹션. autopilot-research / analyze-project 결과 자동 인용. analyze-project 의 _신규 의도 → 청사진_ 대칭 자리. 실제 코드 작업은 autopilot-code 가 담당 (spec/ 컨텍스트 자동 감지).

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
| Claude Code | `adapters/claude/skills/autopilot-spec` currently projects compatibility source `skills/autopilot-spec/SKILL.md`. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-spec`. Do not consume `skills/autopilot-spec/SKILL.md` as native Codex configuration. |

## Compatibility Reference

The historical Claude Skill source remains at `skills/autopilot-spec/SKILL.md` while this capability is being split into portable and adapter-native layers.
