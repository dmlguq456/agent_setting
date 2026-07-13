# Capability: code-plan

This is the portable capability contract for `code-plan`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `code-plan` |
| Group | `sub` |
| Supported modes | `none` |
| Portable meaning | 코드 분석 후 상세 구현 plan을 작성하고 선택된 intensity에서 파생된 rigor에 맞는 plan-check gate를 수행한다. |
| Argument shape | `<task description> [--intensity direct|quick|standard|strong|thorough|adversarial]` |

## Invocation Semantics

Create a detailed implementation plan based on actual codebase

Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.

## Assurance Contract

This sub-capability follows `core/CONVENTIONS.md §1`: plan-check and review rigor is derived from intensity rather than independently selected. `code-plan` is used for durable `standard+` code work cycles; `direct` skips it and `quick` is handled by a depth-1 one-shot worker with its inline micro-plan plus `plan-check-lite`. Independent plan review is selected by intensity/risk and is not repeated after every sub-stage by default.


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
| Claude Code | `adapters/claude/skills/code-plan/SKILL.md` and `skills/code-plan/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/code-plan/SKILL.md`, while `skills/code-plan/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info code-plan`. Use `adapters/codex/skills/code-plan/SKILL.md` and `adapters/codex/plugins/agent-harness-codex/skills/code-plan/SKILL.md` as native Codex Skill/plugin projections; do not consume `skills/code-plan/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info code-plan`. Use `adapters/opencode/skills/code-plan/SKILL.md` and `adapters/opencode/commands/code-plan.md` as native OpenCode projections; do not consume `skills/code-plan/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/code-plan/SKILL.md` and `adapters/claude/skills/code-plan/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/code-plan/SKILL.md`, while `skills/code-plan/SKILL.md` remains the compatibility reference kept for parity/drift checks.
