# Capability: post-it

This is the portable capability contract for `post-it`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract
<!-- GENERATED: harness-manifest.json -->

| Field | Value |
|---|---|
| Identifier | `post-it` |
| Group | `ops` |
| Supported modes | `none` |
| Portable meaning | Store project/cross-project notes and handoffs in working memory. |
| Argument shape | `[show] \| add <category> <text> \| resolve <hint> \| decide <text> \| handoff [--no-confirm] \| sweep [--no-confirm] \| promote [<hint>] [--scope project\|user [<aspect>]]` |

## Invocation Semantics

Manually-controlled working-memory layer, two scopes. `--scope project` (default): `mem note`/`mem add` (working tier, per-cwd) — thread/decision/convention/reference records in DB. `--scope user <aspect>`: `mem add` (durable, global, profile-adjacent) — splices a note into the `## 사용자 수동 메모` block of the profile record (`source user-profile:<stem>`), shared with analyze-user. All entries are designed to graduate (into artifacts/profiles) or expire — `sweep` flags stale working records; `promote` graduates user notes into the profile record. DB working tier is injected at session start by `mem inject` (not a file read).

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
| Claude Code | `adapters/claude/skills/post-it/SKILL.md` and `skills/post-it/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/post-it/SKILL.md`, while `skills/post-it/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info post-it`. Use `adapters/codex/skills/post-it/SKILL.md` as the native Codex Skill projection; do not consume `skills/post-it/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info post-it`. Use `adapters/opencode/skills/post-it/SKILL.md` and `adapters/opencode/commands/post-it.md` as native OpenCode projections; do not consume `skills/post-it/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/post-it/SKILL.md` and `adapters/claude/skills/post-it/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/post-it/SKILL.md`, while `skills/post-it/SKILL.md` remains the compatibility reference kept for parity/drift checks.
