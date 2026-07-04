# Capability: design-init

This is the portable capability contract for `design-init`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `design-init` |
| Group | `sub` |
| Supported modes | `none` |
| Portable meaning | 디자인 환경과 state를 bootstrap한다. |
| Argument shape | `<design task description> [--scope ui|slide|icon|diagram|mixed]` |

## Invocation Semantics

Design environment check and bootstrap — self-provisions the runtime design harness that powers visual self-verification, plus optional Figma MCP, shadcn/ui, Tailwind tokens, SVG rasterizer, and image-generation integration where supported. Adapter-native files own concrete MCP registration commands and runtime paths. Per spec §0.5 it installs what is missing rather than stopping. Creates design_state.yaml.

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
| Claude Code | `adapters/claude/skills/design-init/SKILL.md` and `skills/design-init/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/design-init/SKILL.md`, while `skills/design-init/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info design-init`. Use `adapters/codex/skills/design-init/SKILL.md` and `adapters/codex/plugins/agent-harness-codex/skills/design-init/SKILL.md` as native Codex Skill/plugin projections; do not consume `skills/design-init/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info design-init`. Use `adapters/opencode/skills/design-init/SKILL.md` and `adapters/opencode/commands/design-init.md` as native OpenCode projections; do not consume `skills/design-init/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/design-init/SKILL.md` and `adapters/claude/skills/design-init/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/design-init/SKILL.md`, while `skills/design-init/SKILL.md` remains the compatibility reference kept for parity/drift checks.
