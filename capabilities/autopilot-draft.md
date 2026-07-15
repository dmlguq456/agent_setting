# Capability: autopilot-draft

This is the portable capability contract for `autopilot-draft`. It defines runtime-neutral meaning and adapter obligations. It is not a Claude Skill file.

## Contract
<!-- GENERATED: harness-manifest.json -->

| Field | Value |
|---|---|
| Identifier | `autopilot-draft` |
| Group | `entry` |
| Supported modes | `paper, presentation, doc` |
| Portable meaning | Document-drafting pipeline that produces an applicable artifact through strategy, drafting, verification, and editing. |
| Argument shape | `<task description> [--mode paper\|presentation\|doc] [--intensity direct\|quick\|standard\|strong\|thorough\|adversarial] [--user-refine] [--no-clarify] [--from analyze\|strategy\|strategy-refine\|draft\|draft-refine\|finalize]` |
| Execution topology | `staged`; registry `capabilities/topologies.json` |

## Invocation Semantics

Document draft pipeline: analyze → strategy → strategy-refine → draft →
draft-refine → finalize. In `paper` mode, “draft” means a **paste-ready
cheatsheet draft**: LaTeX-ready cards describing mutations that the user applies
to canonical `main.tex` through autopilot-apply, not blank-page body writing.
This meaning is unchanged for new and existing papers. Output-form modes are
`paper` (LaTeX academic cheatsheet), `presentation` (slide-by-slide PPT
markdown), and `doc` (Word/HWP/Markdown prose such as reports, proposals,
rebuttals, reviews, blogs, and memos). The mode is form-first; the natural
language task describes purpose/genre without a subtype enum. Discover inputs
from `<artifact-root>/{analysis_project,research}/*`; preprocess external
materials with `/analyze-project --mode {paper|doc}`. Load matching format specs
from `analysis_project/doc/{matching}/formats/` without a `--format-ref` flag.
Mode conventions live under `## Mode-Specific Conventions` (common plus paper,
presentation, or doc). Presentation mode produces Markdown only; PPTX export is
unsupported, so use PowerPoint directly.

When a draft contains generated spectrograms, finalization requires the report
figure evidence contract in `core/CONVENTIONS.md §4.1`: a semantic manifest,
the fail-closed verifier result, claim-to-range evidence, and at least one
recorded representative PNG review. A file/count/link-only check cannot satisfy
this gate.

Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.

## Artifact Ownership

Use the shared artifact root rule: prefer `.agent_reports/`; use legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not. Capability-specific output placement follows `core/CONVENTIONS.md` section 5 until this spec is expanded with a stricter per-capability artifact map.

## Role Requirements

Use portable role names from `roles/README.md` and `core/CONVENTIONS.md`. Concrete model names, subagent frontmatter, and runtime-specific tool lists belong in adapter files.

Pipeline intensity follows `core/CONVENTIONS.md §1`: `direct` has no plan stage or durable plan artifact; `quick` is a depth-1 one-shot worker with its inline micro-plan plus plan-check-lite; `standard+` uses the capability's durable work-cycle plan when applicable. `plan-check` is required for every non-`direct` graph, but independent QA is not repeated after every stage by default. Verification rigor for plan-check, selected independent reviews, and final verify is derived from intensity; it does not name a model or introduce a separate stage graph.

## Guard Requirements

When a draft consumes lab media, it consumes the shared
`report_manifest.json` and preserves its Markdown/HTML link and summary-stat
bindings. It does not create a second media manifest.

Adapters must preserve the portable invariants relevant to this capability:

- resolve artifact root through `utilities/artifact-root.sh` or equivalent logic;
- enforce git/worktree safety before edits;
- enforce artifact ordering before new durable artifacts;
- enforce spec-read gating when this capability changes spec-backed code or specs;
- use DB memory paths, not runtime-native memory files.

## Adapter Realization

| Adapter | Realization |
|---|---|
| Claude Code | `adapters/claude/skills/autopilot-draft/SKILL.md` and `skills/autopilot-draft/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-draft/SKILL.md`, while `skills/autopilot-draft/SKILL.md` remains the compatibility reference kept for parity/drift checks. |
| Codex | Read this spec and run `adapters/codex/bin/preflight.sh capability-info autopilot-draft`. Use `adapters/codex/skills/autopilot-draft/SKILL.md` as the native Codex Skill projection; do not consume `skills/autopilot-draft/SKILL.md` or Claude command files as native Codex configuration. |
| OpenCode | Read this spec and run `adapters/opencode/bin/preflight.sh capability-info autopilot-draft`. Use `adapters/opencode/skills/autopilot-draft/SKILL.md` and `adapters/opencode/commands/autopilot-draft.md` as native OpenCode projections; do not consume `skills/autopilot-draft/SKILL.md` or Claude command files as native OpenCode configuration. |

## Compatibility Reference

`skills/autopilot-draft/SKILL.md` and `adapters/claude/skills/autopilot-draft/SKILL.md` are byte-identical (enforced by `check-adaptation-boundary.sh`'s `diff -qr`); the only difference is the runtime discovery path — Claude Code discovers `adapters/claude/skills/autopilot-draft/SKILL.md`, while `skills/autopilot-draft/SKILL.md` remains the compatibility reference kept for parity/drift checks.
