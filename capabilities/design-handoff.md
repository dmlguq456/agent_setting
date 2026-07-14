# Capability: design-handoff

This is the portable capability contract for `design-handoff`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract
<!-- GENERATED: harness-manifest.json -->

| Field | Value |
|---|---|
| Identifier | `design-handoff` |
| Group | `sub` |
| Supported modes | `none` |
| Portable meaning | 디자인 결과를 개발 handoff용 자산·스펙으로 정리한다. |
| Argument shape | `<design path or app path>` |

## Invocation Semantics

Final handoff — consolidates design artifacts into a single handoff.md that frontend devs (or autopilot-spec build phase) can use directly. Lists components, token paths, import paths, reproduction guide.

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
| Claude Code | `adapters/claude/skills/design-handoff/SKILL.md` and `skills/design-handoff/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/design-handoff/SKILL.md`, while `skills/design-handoff/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info design-handoff`. Use `adapters/codex/skills/design-handoff/SKILL.md` as the native Codex Skill projection; do not consume `skills/design-handoff/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info design-handoff`. Use `adapters/opencode/skills/design-handoff/SKILL.md` and `adapters/opencode/commands/design-handoff.md` as native OpenCode projections; do not consume `skills/design-handoff/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/design-handoff/SKILL.md` and `adapters/claude/skills/design-handoff/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/design-handoff/SKILL.md`, while `skills/design-handoff/SKILL.md` remains the compatibility reference kept for parity/drift checks.
