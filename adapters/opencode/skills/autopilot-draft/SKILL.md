---
name: autopilot-draft
description: "Use for autopilot-draft: Document-drafting pipeline that produces an applicable artifact through strategy, drafting, verification, and editing."
metadata:
  portable_source: capabilities/autopilot-draft.md
  adapter: opencode
---

# autopilot-draft

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-draft.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-draft`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-draft.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-draft`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-draft`
- Supported modes: `paper, presentation, doc`
- Argument shape: `<task description> [--mode paper|presentation|doc] [--intensity direct|quick|standard|strong|thorough|adversarial] [--user-refine] [--no-clarify] [--from analyze|strategy|strategy-refine|draft|draft-refine|finalize]`
- Portable meaning: Document-drafting pipeline that produces an applicable artifact through strategy, drafting, verification, and editing.

## Portable Contract

- Invocation semantics: Document draft pipeline: analyze → strategy → strategy-refine → draft → draft-refine → finalize. In `paper` mode, “draft” means a **paste-ready cheatsheet draft**: LaTeX-ready cards describing mutations that the user applies to canonical `main.tex` through autopilot-apply, not blank-page body writing. This meaning is unchanged for new and existing papers. Output-form modes are `paper` (LaTeX academic cheatsheet), `presentation` (slide-by-slide PPT markdown), and `doc` (Word/HWP/Markdown prose such as reports, proposals, rebuttals, reviews, blogs, and memos). The mode is form-first; the natural language task describes purpose/genre without a subtype enum. Discover inputs from `<artifact-root>/{analysis_project,research}/*`; preprocess external materials with `/analyze-project --mode {paper|doc}`. Load matching format specs from `analysis_project/doc/{matching}/formats/` without a `--format-ref` flag. Mode conventions live under `## Mode-Specific Conventions` (common plus paper, presentation, or doc). Presentation mode produces Markdown only; PPTX export is unsupported, so use PowerPoint directly. When a draft contains generated spectrograms, finalization requires the report figure evidence contract in `core/CONVENTIONS.md §4.1`: a semantic manifest, the fail-closed verifier result, claim-to-range evidence, and at least one recorded representative PNG review. A file/count/link-only check cannot satisfy this gate. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-draft [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
