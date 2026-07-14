# Capability: autopilot-lab

This is the portable capability contract for `autopilot-lab`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract

| Field | Value |
|---|---|
| Identifier | `autopilot-lab` |
| Group | `entry` |
| Supported modes | `setup, eval` |
| Portable meaning | Rapid experiment prototyping around training setup and checkpoint evaluation/analysis. |
| Argument shape | `<task description> [--mode setup|eval|auto] [--parent <slug>] [--ref <similar-model-path>] [--intensity direct|quick|standard|strong|thorough|adversarial] [--report] [--from spec|scaffold|run|eval|summary]` |

## Invocation Semantics

Rapid experiment prototype entrypoint. The user runs heavy training; the lab
supports the work before and after it. `setup` prepares an experiment from spec
to scaffold and run commands. `eval` analyzes a trained checkpoint through
metrics, ablations, paper comparisons, plots, and optional formal reports
(prose routes to autopilot-draft; audio/media uses playback HTML). Extension
cases use `--parent <slug>` rather than new modes: fine-tuning creates a setup
config branch, and reevaluation uses eval. Enforce per-experiment folders, a
STORY narrative, and an append-only `_RUNLOG` timeline with pending/completed
state and parent links to prevent overwrites and ad hoc loss. Automatically read
`experiment_conventions.md` and `similar_models.md` from analyze-project, giving
the user's existing layer, prefix, and config patterns priority. Graduate
refinement or library work to autopilot-code.

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
| Claude Code | `adapters/claude/skills/autopilot-lab/SKILL.md` and `skills/autopilot-lab/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-lab/SKILL.md`, while `skills/autopilot-lab/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-lab`. Use `adapters/codex/skills/autopilot-lab/SKILL.md` and `adapters/codex/plugins/agent-harness-codex/skills/autopilot-lab/SKILL.md` as native Codex Skill/plugin projections; do not consume `skills/autopilot-lab/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info autopilot-lab`. Use `adapters/opencode/skills/autopilot-lab/SKILL.md` and `adapters/opencode/commands/autopilot-lab.md` as native OpenCode projections; do not consume `skills/autopilot-lab/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/autopilot-lab/SKILL.md` and `adapters/claude/skills/autopilot-lab/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-lab/SKILL.md`, while `skills/autopilot-lab/SKILL.md` remains the compatibility reference kept for parity/drift checks.
