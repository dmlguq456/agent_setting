---
description: "Run the portable analyze-project capability through the OpenCode adapter. Meaning: Upfront analysis that structures primary code, paper, and document materials for downstream work."
---

Use the OpenCode adapter realization of portable capability `analyze-project`.
This is adapter-owned output generated from `capabilities/analyze-project.md`, not a runtime-specific command copy.

1. Read `capabilities/analyze-project.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info analyze-project` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract`, run any
   `tool_contract_check`, and obey `runtime_surface` / `fallback` before
   claiming full support. For `unsupported`, stop or use the reported
   `fallback`.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability analyze-project [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `[--mode code|paper|doc] [<scope/target/input-folder>] [--skip-qa]`.

Portable contract excerpt:

- Invocation semantics: Pre-work analysis skill — analyzes the project's primary materials and writes structured artifacts to <artifact-root>/analysis_project/. Three modes — code (codebase), paper (academic PDFs), doc (miscellaneous doc materials like reviewer comments, format templates, samples, internal notes). Mode auto-detects between code and doc when omitted; paper requires explicit --mode paper. Output is the persistent input source for downstream autopilot-{draft,code,research} skills. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


User arguments from OpenCode: `$ARGUMENTS`

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
