# Capability: autopilot-code

This is the portable capability contract for `autopilot-code`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `autopilot-code` |
| Group | `entry` |
| Supported modes | `dev, debug, audit` |
| Portable meaning | 코드 작업 entry. spec 컨텍스트를 감지하고 plan→execute→test→report 흐름을 닫는다. |
| Argument shape | `--mode dev|debug <task/plan/error description> [--from <step>] [--qa quick|light|standard|thorough|adversarial] [--user-refine]` |

## Invocation Semantics

_코드 작업 일반_ entry — 라이브러리·연구 코드·앱 모두 커버. 신규·기존 코드 무관 (cwd 자동 감지). dev (기능 추가·신규) / debug (진단·수정) 두 mode. spec/ 컨텍스트 발견 시 spec 자동 Read + spec mode 별 분기: app mode → 디자인팀 critic + DB migration 안전 + push 자동 deploy. library mode → 공개 API 일관성 점검. cli mode → 명령·옵션 일관성. research mode → 재현성·configs·metric 검증. 코드 외 결정 (PRD·스택·skeleton·ship setup) 은 autopilot-spec 영역.

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
| Claude Code | `adapters/claude/skills/autopilot-code` currently projects compatibility source `skills/autopilot-code/SKILL.md`. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-code`. Do not consume `skills/autopilot-code/SKILL.md` as native Codex configuration. |

## Compatibility Reference

The historical Claude Skill source remains at `skills/autopilot-code/SKILL.md` while this capability is being split into portable and adapter-native layers.
