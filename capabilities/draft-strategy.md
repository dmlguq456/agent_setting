# Capability: draft-strategy

This is the portable capability contract for `draft-strategy`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `draft-strategy` |
| Group | `sub` |
| Supported modes | `rebuttal, paper, review, report, proposal, presentation` |
| Portable meaning | 문서 전략 초안 작성. 자료 기반으로 writing plan을 만든다. |
| Argument shape | `<mode> --inputs <comma-separated-paths> --output <artifact-dir> [--intensity direct|quick|standard|strong|thorough|adversarial] <task description>` |

## Invocation Semantics

Create an initial document strategy. Internal mode enum 6종 (rebuttal / paper / review / report / proposal / presentation) — autopilot-draft 의 form-first 3-mode (paper / presentation / doc) 에서 doc intent (자연어 키워드 → rebuttal-response / review / report / proposal / generic) 가 본 sub-skill 의 직접 mode 라벨로 변환되어 전달됨. 직접 호출 시는 사용자가 첫 인자로 6-mode 중 하나를 명시.

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
| Claude Code | `adapters/claude/skills/draft-strategy/SKILL.md` and `skills/draft-strategy/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/draft-strategy/SKILL.md`, while `skills/draft-strategy/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info draft-strategy`. Use `adapters/codex/skills/draft-strategy/SKILL.md` and `adapters/codex/plugins/agent-harness-codex/skills/draft-strategy/SKILL.md` as native Codex Skill/plugin projections; do not consume `skills/draft-strategy/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info draft-strategy`. Use `adapters/opencode/skills/draft-strategy/SKILL.md` and `adapters/opencode/commands/draft-strategy.md` as native OpenCode projections; do not consume `skills/draft-strategy/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/draft-strategy/SKILL.md` and `adapters/claude/skills/draft-strategy/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/draft-strategy/SKILL.md`, while `skills/draft-strategy/SKILL.md` remains the compatibility reference kept for parity/drift checks.
