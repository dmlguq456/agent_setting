# Capability: design-review

This is the portable capability contract for `design-review`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract
<!-- GENERATED: harness-manifest.json -->

| Field | Value |
|---|---|
| Identifier | `design-review` |
| Group | `sub` |
| Supported modes | `none` |
| Portable meaning | Review design output for quality, token-contract compliance, and breakage. |
| Argument shape | `<design path or app path>` |

## Invocation Semantics

Visual review with two gates. First, a verifier in a separate context uses the
adapter visual harness to screen for console errors, layout collapse, and intent
mismatch; it must pass before critique. Second, a critic evaluates hierarchy,
alignment, accessibility, responsiveness, UX flow, and tone. Both gates render
through the adapter-provided visual harness and inspect the image. Read only;
never auto-fix.

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
| Claude Code | `adapters/claude/skills/design-review/SKILL.md` and `skills/design-review/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/design-review/SKILL.md`, while `skills/design-review/SKILL.md` remains the compatibility reference kept for parity/drift checks. `tools/design-mcp/` provides the visual harness. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info design-review`. Use `adapters/codex/skills/design-review/SKILL.md` as the native Codex Skill projection; do not consume `skills/design-review/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info design-review`. Use `adapters/opencode/skills/design-review/SKILL.md` and `adapters/opencode/commands/design-review.md` as native OpenCode projections; do not consume `skills/design-review/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/design-review/SKILL.md` and `adapters/claude/skills/design-review/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/design-review/SKILL.md`, while `skills/design-review/SKILL.md` remains the compatibility reference kept for parity/drift checks.
