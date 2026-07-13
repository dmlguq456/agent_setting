---
name: autopilot-draft
description: "Use for autopilot-draft: 문서 초안 파이프. 전략·초안·검증·편집을 거쳐 적용용 문서 artifact를 만든다."
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
- Portable meaning: 문서 초안 파이프. 전략·초안·검증·편집을 거쳐 적용용 문서 artifact를 만든다.

## Portable Contract

- Invocation semantics: Document draft pipeline — analyze → strategy → strategy-refine → draft → draft-refine → finalize. NOTE: in `paper` mode 'draft' means a **paste-ready cheatsheet draft** — a set of LaTeX paste-ready cards (a mutation/edit plan the user pastes into the canonical main.tex via autopilot-apply), NOT blank-page body writing. 'draft' = the *cheatsheet draft*, regardless of whether the paper is new or already complete. 3 modes by output form: `paper` (LaTeX academic output, always produced as a paste-ready cheatsheet draft that autopilot-apply pastes into main.tex — new-body cheatsheet entries for an initial submission/thesis/book chapter, edit/mutation cheatsheet entries for camera-ready/major-revision of an existing body) / `presentation` (slide-by-slide markdown for PPT) / `doc` (prose for Word/HWP/markdown — reports·proposals·rebuttal responses·peer reviews·tech blogs·memos). Mode is form-first; purpose/genre is conveyed via natural-language task description (no subtype enum). All inputs implicitly discovered from `<artifact-root>/{analysis_project,research}/*` — pre-process external materials via `/analyze-project --mode {paper|doc}` first (cwd 자동 발견). Format specs auto-loaded from `analysis_project/doc/{matching}/formats/` — no explicit `--format-ref` flag. Mode-specific conventions live in `## Mode-Specific Conventions` (§Common + §paper / §presentation / §doc). `presentation` produces markdown only (PPTX export NOT supported — use PowerPoint directly). Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.



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
