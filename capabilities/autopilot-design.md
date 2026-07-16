# Capability: autopilot-design

This is the portable capability contract for `autopilot-design`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract
<!-- GENERATED: harness-manifest.json -->

| Field | Value |
|---|---|
| Identifier | `autopilot-design` |
| Group | `entry` |
| Supported modes | `none` |
| Portable meaning | Visual-design pipeline coordinating references→tokens→components→review→handoff. |
| Argument shape | `<design task or app path> [--scope ui\|webapp\|slide\|icon\|diagram\|mixed] [--artifact standalone\|project] [--from <phase>] [--intensity direct\|quick\|standard\|strong\|thorough\|adversarial]` |
| Execution topology | `staged`; registry `capabilities/topologies.json` |
| Entry load phase | `post-approval`; owner contract `capabilities/autopilot-design.md` |

## Invocation Semantics

Unified design pipeline — orchestrates design-init → design-refs → design-tokens → design-components → design-review → design-handoff. For visual artifacts across UI/UX, slides, diagrams, icons, logos. Can be invoked standalone or auto-delegated from autopilot-spec Phase 2. Distinct from autopilot-draft (text-only documents) — autopilot-design handles visual deliverables. A runtime design harness must render every output for visual self-verification (preview/screenshot/console/eval_js/view_image where supported), run a separate-context verifier gate for console/layout breakage, apply shared design rules and reusable scaffold assets, and support PDF/PPTX/single-HTML bundle export where available. Outputs can be a self-contained single-file HTML preview viewable without any project stack.

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
| Claude Code | `adapters/claude/skills/autopilot-design/SKILL.md` and `skills/autopilot-design/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-design/SKILL.md`, while `skills/autopilot-design/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-design`. Use `adapters/codex/skills/autopilot-design/SKILL.md` as the native Codex Skill projection; do not consume `skills/autopilot-design/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info autopilot-design`. Use `adapters/opencode/skills/autopilot-design/SKILL.md` and `adapters/opencode/commands/autopilot-design.md` as native OpenCode projections; do not consume `skills/autopilot-design/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/autopilot-design/SKILL.md` and `adapters/claude/skills/autopilot-design/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-design/SKILL.md`, while `skills/autopilot-design/SKILL.md` remains the compatibility reference kept for parity/drift checks.
