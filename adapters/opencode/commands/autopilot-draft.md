---
description: "Run the portable autopilot-draft capability through the OpenCode adapter. Meaning: 문서 초안 파이프. 전략·초안·검증·편집을 거쳐 적용용 문서 artifact를 만든다."
---

Use the OpenCode adapter realization of portable capability `autopilot-draft`.
This is adapter-owned output generated from `capabilities/autopilot-draft.md`, not a runtime-specific command copy.

1. Read `capabilities/autopilot-draft.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-draft` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract`, run any
   `tool_contract_check`, and obey `runtime_surface` / `fallback` before
   claiming full support. For `unsupported`, stop or use the reported
   `fallback`.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-draft [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<task description> [--mode paper|presentation|doc] [--intensity direct|quick|standard|strong|thorough|adversarial] [--user-refine] [--no-clarify] [--from analyze|strategy|strategy-refine|draft|draft-refine|finalize]`.

Portable contract excerpt:

- Invocation semantics: Document draft pipeline — analyze → strategy → strategy-refine → draft → draft-refine → finalize. NOTE: in `paper` mode 'draft' means a **paste-ready cheatsheet draft** — a set of LaTeX paste-ready cards (a mutation/edit plan the user pastes into the canonical main.tex via autopilot-apply), NOT blank-page body writing. 'draft' = the *cheatsheet draft*, regardless of whether the paper is new or already complete. 3 modes by output form: `paper` (LaTeX academic output, always produced as a paste-ready cheatsheet draft that autopilot-apply pastes into main.tex — new-body cheatsheet entries for an initial submission/thesis/book chapter, edit/mutation cheatsheet entries for camera-ready/major-revision of an existing body) / `presentation` (slide-by-slide markdown for PPT) / `doc` (prose for Word/HWP/markdown — reports·proposals·rebuttal responses·peer reviews·tech blogs·memos). Mode is form-first; purpose/genre is conveyed via natural-language task description (no subtype enum). All inputs implicitly discovered from `<artifact-root>/{analysis_project,research}/*` — pre-process external materials via `/analyze-project --mode {paper|doc}` first (cwd 자동 발견). Format specs auto-loaded from `analysis_project/doc/{matching}/formats/` — no explicit `--format-ref` flag. Mode-specific conventions live in `## Mode-Specific Conventions` (§Common + §paper / §presentation / §doc). `presentation` produces markdown only (PPTX export NOT supported — use PowerPoint directly). Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


User arguments from OpenCode: `$ARGUMENTS`

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
