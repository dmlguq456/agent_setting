# Capability: analyze-user

This is the portable capability contract for `analyze-user`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `analyze-user` |
| Group | `pre` |
| Supported modes | `init, update` |
| Portable meaning | Create or update a cross-project user-preference profile from coding, writing, and analysis patterns. |
| Argument shape | `<aspect> [--source <path>] [--mode init|update] [--from discover|analyze|verify|qa|output|summary] [--user-refine]` |

## Invocation Semantics

Scan and analyze the user's cross-project artifacts (papers, presentations,
reports, code, and memory) in stages, then accumulate general working
preferences in DB `type=profile` records (`mem profile <stem>`). This uses the
same ceremony level as autopilot entrypoints because every sub-agent treats the
resulting profile as a default, so even small errors propagate. The six phases
are source discovery, per-aspect analysis, cross-aspect consistency checks,
multiple QA gates, artifact creation, and pipeline summary. QA is always
adversarial and is not user-adjustable.

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
| Claude Code | `adapters/claude/skills/analyze-user/SKILL.md` and `skills/analyze-user/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/analyze-user/SKILL.md`, while `skills/analyze-user/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info analyze-user`. Use `adapters/codex/skills/analyze-user/SKILL.md` and `adapters/codex/plugins/agent-harness-codex/skills/analyze-user/SKILL.md` as native Codex Skill/plugin projections; do not consume `skills/analyze-user/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info analyze-user`. Use `adapters/opencode/skills/analyze-user/SKILL.md` and `adapters/opencode/commands/analyze-user.md` as native OpenCode projections; do not consume `skills/analyze-user/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/analyze-user/SKILL.md` and `adapters/claude/skills/analyze-user/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/analyze-user/SKILL.md`, while `skills/analyze-user/SKILL.md` remains the compatibility reference kept for parity/drift checks.
