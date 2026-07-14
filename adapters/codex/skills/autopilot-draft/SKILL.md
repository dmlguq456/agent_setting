---
name: autopilot-draft
description: "Use for autopilot-draft: Document-drafting pipeline that produces an applicable artifact through strategy, drafting, verification, and editing."
---

# autopilot-draft

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-draft.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info autopilot-draft`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/autopilot-draft.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info autopilot-draft`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-draft`
- Supported modes: `paper, presentation, doc`
- Argument shape: `<task description> [--mode paper|presentation|doc] [--intensity direct|quick|standard|strong|thorough|adversarial] [--user-refine] [--no-clarify] [--from analyze|strategy|strategy-refine|draft|draft-refine|finalize]`
- Portable meaning: Document-drafting pipeline that produces an applicable artifact through strategy, drafting, verification, and editing.

## Portable Contract

- Invocation semantics: Document draft pipeline: analyze → strategy → strategy-refine → draft → draft-refine → finalize. In `paper` mode, “draft” means a **paste-ready cheatsheet draft**: LaTeX-ready cards describing mutations that the user applies to canonical `main.tex` through autopilot-apply, not blank-page body writing. This meaning is unchanged for new and existing papers. Output-form modes are `paper` (LaTeX academic cheatsheet), `presentation` (slide-by-slide PPT markdown), and `doc` (Word/HWP/Markdown prose such as reports, proposals, rebuttals, reviews, blogs, and memos). The mode is form-first; the natural language task describes purpose/genre without a subtype enum. Discover inputs from `<artifact-root>/{analysis_project,research}/*`; preprocess external materials with `/analyze-project --mode {paper|doc}`. Load matching format specs from `analysis_project/doc/{matching}/formats/` without a `--format-ref` flag. Mode conventions live under `## Mode-Specific Conventions` (common plus paper, presentation, or doc). Presentation mode produces Markdown only; PPTX export is unsupported, so use PowerPoint directly. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.



## Projected Portable Details

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


## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before capability routing/spec-changing work: `adapters/codex/bin/preflight.sh route autopilot-draft [cwd] [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability autopilot-draft [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh status [cwd] [session-id]`, `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]`, and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
