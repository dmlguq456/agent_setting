# Capability: autopilot-apply

This is the portable capability contract for `autopilot-apply`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `autopilot-apply` |
| Group | `entry` |
| Supported modes | `none` |
| Portable meaning | cheatsheet 초안을 실제 source artifact에 적용하고 검증한다. |
| Argument shape | `\"<cheatsheet hint / task>\" [--target latex] [--source <path-to-real-source>] [--isolation branch|worktree] [--from preflight|apply|verify|handback]` |

## Invocation Semantics

Autopilot family — the document-side _apply + verify_ arm. Takes a draft-produced cheatsheet (a mutation/edit plan) and applies it to a real working source file _outside_ `<artifact-root>/` (e.g. the user's `main.tex`), under git, with a build/compile verify gate. This is the missing counterpart to autopilot-draft: draft _produces_ the cheatsheet (plan), autopilot-apply _executes_ it on the canonical source and _verifies_ it compiles — mirroring code-execute + code-test on the code side. Default target `latex` (latexmk compile gate + latexdiff rendered-diff review). Never touches the canonical source directly: applies on a git branch (or worktree), each mutation = one commit, hands back via `git merge`. Cheatsheet auto-discovered from `<artifact-root>/documents/*/draft/`. NOT for `<artifact-root>/` markdown artifacts (use autopilot-refine) or codebases (use autopilot-code).

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
| Claude Code | `adapters/claude/skills/autopilot-apply/SKILL.md` and `skills/autopilot-apply/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-apply/SKILL.md`, while `skills/autopilot-apply/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-apply`. Use `adapters/codex/skills/autopilot-apply/SKILL.md` and `adapters/codex/plugins/agent-harness-codex/skills/autopilot-apply/SKILL.md` as native Codex Skill/plugin projections; do not consume `skills/autopilot-apply/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info autopilot-apply`. Use `adapters/opencode/skills/autopilot-apply/SKILL.md` and `adapters/opencode/commands/autopilot-apply.md` as native OpenCode projections; do not consume `skills/autopilot-apply/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/autopilot-apply/SKILL.md` and `adapters/claude/skills/autopilot-apply/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-apply/SKILL.md`, while `skills/autopilot-apply/SKILL.md` remains the compatibility reference kept for parity/drift checks.
