# Capability: code-report

This is the portable capability contract for `code-report`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract
<!-- GENERATED: harness-manifest.json -->

| Field | Value |
|---|---|
| Identifier | `code-report` |
| Group | `sub` |
| Supported modes | `none` |
| Portable meaning | 코드 작업 사이클 결과를 사용자-facing 보고서로 조립한다. |
| Argument shape | `<plan name or path>` |

## Invocation Semantics

Generate a detailed change report from plan + dev logs — focuses on key changes, principles, and insights for future reference

Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.

## Artifact Ownership

Use the shared artifact root rule: prefer `.agent_reports/`; use legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not.

In a `standard+` `autopilot-code` stage cycle, `code-report` owns
`final_report.md`, `analysis_project/code/`, and `pipeline_summary.md` (using the
shared lock where required). It consumes plan, checklist, development, and test
evidence but must not rewrite source or another stage's evidence class. This is
the report half of the stage ownership contract in `core/OPERATIONS.md` §5.10.

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
| Claude Code | `adapters/claude/skills/code-report/SKILL.md` and `skills/code-report/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/code-report/SKILL.md`, while `skills/code-report/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info code-report`. Use `adapters/codex/skills/code-report/SKILL.md` as the native Codex Skill projection; do not consume `skills/code-report/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info code-report`. Use `adapters/opencode/skills/code-report/SKILL.md` and `adapters/opencode/commands/code-report.md` as native OpenCode projections; do not consume `skills/code-report/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/code-report/SKILL.md` and `adapters/claude/skills/code-report/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/code-report/SKILL.md`, while `skills/code-report/SKILL.md` remains the compatibility reference kept for parity/drift checks.
