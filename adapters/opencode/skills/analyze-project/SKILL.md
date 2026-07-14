---
name: analyze-project
description: "Use for analyze-project: Creates or refreshes persistent analysis from primary code, paper, or document materials when analysis is absent, stale, or explicitly requested; not for read-only context recovery."
metadata:
  portable_source: capabilities/analyze-project.md
  adapter: opencode
---

# analyze-project

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/analyze-project.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info analyze-project`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/analyze-project.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info analyze-project`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `analyze-project`
- Supported modes: `code, paper, doc`
- Argument shape: `[--mode code|paper|doc] [<scope/target/input-folder>] [--skip-qa]`
- Portable meaning: Creates or refreshes persistent analysis from primary code, paper, or document materials when analysis is absent, stale, or explicitly requested; not for read-only context recovery.

## Portable Contract

- Invocation semantics: Pre-work analysis capability — analyzes the project's primary materials and writes structured artifacts to `<artifact-root>/analysis_project/`. Invoke it only when no usable project analysis exists, existing analysis is demonstrably stale for the requested downstream work, or the user explicitly requests a persistent analysis document or refresh. A request to understand the current project, recover prior context, resume work, or report status is read-only orientation and is not an `analyze-project` trigger by itself. When analysis already exists, read it before deciding that reanalysis is needed. Three modes are available: code (codebase), paper (academic PDFs), and doc (miscellaneous document materials such as reviewer comments, format templates, samples, and internal notes). Mode auto-detects between code and doc when omitted; paper requires explicit `--mode paper`. Output is the persistent input source for downstream `autopilot-{draft,code,research}` capabilities. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability analyze-project [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
