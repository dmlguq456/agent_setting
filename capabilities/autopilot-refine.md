# Capability: autopilot-refine

This is the portable capability contract for `autopilot-refine`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract
<!-- GENERATED: harness-manifest.json -->

| Field | Value |
|---|---|
| Identifier | `autopilot-refine` |
| Group | `entry` |
| Supported modes | `none` |
| Portable meaning | 기존 문서·연구 산출물의 정정·갱신. 버전 snapshot과 변경 이력을 보존한다. |
| Argument shape | `"<prompt>" [--intensity direct\|quick\|standard\|strong\|thorough\|adversarial] [--review-only \| --memo <file>] [--confirm] [--no-fact-check] [--no-style-audit]` |

## Invocation Semantics

Autopilot family — post-creation iteration pipeline for research and doc artifacts (NOT code). Prompt-driven: target artifact identified via prompt fuzzy match against `<artifact-root>/{research,documents}/*`, then auto-discovers the artifact's file structure, plans edits, shows a diff preview in chat, and on user confirm applies edits with versioning + integrated history logging in `pipeline_summary.md` (single source of truth — no separate CHANGELOG). Default intensity is `quick` (1-pass review, fastest path); escalate intensity to `standard|strong|thorough|adversarial` for multi-round review, fact-check, or external adversary work. Optional `--memo <file>` falls back to file-memo style for deferred reviews.

Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.

## Artifact Ownership

Use the shared artifact root rule: prefer `.agent_reports/`; use legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not. Capability-specific output placement follows `core/CONVENTIONS.md` section 5 until this spec is expanded with a stricter per-capability artifact map.

## Role Requirements

Use portable role names from `roles/README.md` and `core/CONVENTIONS.md`. Concrete model names, subagent frontmatter, and runtime-specific tool lists belong in adapter files.

Pipeline intensity follows `core/CONVENTIONS.md §1`: `direct` has no plan stage or durable plan artifact; `quick` is a depth-1 one-shot worker with its inline micro-plan plus plan-check-lite; `standard+` uses the capability's durable work-cycle plan when applicable. `plan-check` is required for every non-`direct` graph, but independent QA is not repeated after every stage by default. Verification rigor for plan-check, selected independent reviews, and final verify is derived from intensity; it does not name a model or introduce a separate stage graph.

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
| Claude Code | `adapters/claude/skills/autopilot-refine/SKILL.md` and `skills/autopilot-refine/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-refine/SKILL.md`, while `skills/autopilot-refine/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-refine`. Use `adapters/codex/skills/autopilot-refine/SKILL.md` as the native Codex Skill projection; do not consume `skills/autopilot-refine/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info autopilot-refine`. Use `adapters/opencode/skills/autopilot-refine/SKILL.md` and `adapters/opencode/commands/autopilot-refine.md` as native OpenCode projections; do not consume `skills/autopilot-refine/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/autopilot-refine/SKILL.md` and `adapters/claude/skills/autopilot-refine/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-refine/SKILL.md`, while `skills/autopilot-refine/SKILL.md` remains the compatibility reference kept for parity/drift checks.
