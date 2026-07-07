# Capability: code-refine

This is the portable capability contract for `code-refine`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `code-refine` |
| Group | `sub` |
| Supported modes | `none` |
| Portable meaning | 사용자 메모·plan-check 피드백·검증 실패 메모를 반영해 기존 plan을 정정한다. |
| Argument shape | `<plan name or path> [--qa quick|light|standard|thorough|adversarial]` |

## Invocation Semantics

Reflect user memos/comments in a plan and update it (do NOT implement)

Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.

## Assurance Contract

This sub-capability follows `core/CONVENTIONS.md §1`: `--qa` is an assurance override, not a stage graph selector. `code-refine` is optional correction of an existing durable plan after user memo, plan-check feedback, or verification failure. It is not an automatic stage in `direct` or `quick`; `quick` records residual plan concerns instead of opening a repeated review/fix loop.


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
| Claude Code | `adapters/claude/skills/code-refine/SKILL.md` and `skills/code-refine/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/code-refine/SKILL.md`, while `skills/code-refine/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info code-refine`. Use `adapters/codex/skills/code-refine/SKILL.md` and `adapters/codex/plugins/agent-harness-codex/skills/code-refine/SKILL.md` as native Codex Skill/plugin projections; do not consume `skills/code-refine/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info code-refine`. Use `adapters/opencode/skills/code-refine/SKILL.md` and `adapters/opencode/commands/code-refine.md` as native OpenCode projections; do not consume `skills/code-refine/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/code-refine/SKILL.md` and `adapters/claude/skills/code-refine/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/code-refine/SKILL.md`, while `skills/code-refine/SKILL.md` remains the compatibility reference kept for parity/drift checks.
