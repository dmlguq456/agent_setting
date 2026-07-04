# Capability: design-components

This is the portable capability contract for `design-components`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `design-components` |
| Group | `sub` |
| Supported modes | `none` |
| Portable meaning | UI component/mockup 구현과 preview artifact를 만든다. |
| Argument shape | `<design path or app path>` |

## Invocation Semantics

Component / visual asset creation — invokes 디자인팀 maker mode. Produces shadcn/Tailwind components (ui), composed full-screen pages (webapp), slide visual guides (slide), SVG icons (icon), or mermaid/direct-SVG/excalidraw diagrams (diagram). Every output is rendered and visually self-verified (render → Read → fix loop), and can be emitted as a self-contained single-file HTML preview artifact (--artifact standalone).

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
| Claude Code | `adapters/claude/skills/design-components/SKILL.md` and `skills/design-components/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/design-components/SKILL.md`, while `skills/design-components/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info design-components`. Use `adapters/codex/skills/design-components/SKILL.md` and `adapters/codex/plugins/agent-harness-codex/skills/design-components/SKILL.md` as native Codex Skill/plugin projections; do not consume `skills/design-components/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info design-components`. Use `adapters/opencode/skills/design-components/SKILL.md` and `adapters/opencode/commands/design-components.md` as native OpenCode projections; do not consume `skills/design-components/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/design-components/SKILL.md` and `adapters/claude/skills/design-components/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/design-components/SKILL.md`, while `skills/design-components/SKILL.md` remains the compatibility reference kept for parity/drift checks.
