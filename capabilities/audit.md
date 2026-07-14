# Capability: audit

This is the portable capability contract for `audit`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `audit` |
| Group | `ops` |
| Supported modes | `none` |
| Portable meaning | Read-oriented post-run inspection for artifact drift, inconsistency, and omissions. |
| Argument shape | `<artifact_path> [--scope auto|facts|style|structure|cross-ref|coverage|all] [--read-only] [--report-only] [--no-fact-check]` |

## Invocation Semantics

Read-only multi-aspect audit/lint for
`<artifact-root>/{plans,research,documents}/*` artifacts. A single global entry
auto-detects artifact type from the path prefix (`plans`=code,
`research`=field survey, `documents`=document deliverable). Per-type aspects:
documents use facts/style/structure/cross-reference/coverage; research uses card
integrity/tier consistency/coverage/cross-card checks; plans use test results,
lint, code review, TODOs, and unimplemented work. `--scope auto` selects from
artifact characteristics by default; an explicit user scope overrides it.
Report only—never modify the artifact. This complements autopilot-refine:
refine edits, while audit inspects.

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
| Claude Code | `adapters/claude/skills/audit/SKILL.md` and `skills/audit/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/audit/SKILL.md`, while `skills/audit/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info audit`. Use `adapters/codex/skills/audit/SKILL.md` and `adapters/codex/plugins/agent-harness-codex/skills/audit/SKILL.md` as native Codex Skill/plugin projections; do not consume `skills/audit/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info audit`. Use `adapters/opencode/skills/audit/SKILL.md` and `adapters/opencode/commands/audit.md` as native OpenCode projections; do not consume `skills/audit/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/audit/SKILL.md` and `adapters/claude/skills/audit/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/audit/SKILL.md`, while `skills/audit/SKILL.md` remains the compatibility reference kept for parity/drift checks.
