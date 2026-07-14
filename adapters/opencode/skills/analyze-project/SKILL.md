---
name: analyze-project
description: "Use for analyze-project: Upfront analysis that structures primary code, paper, and document materials for downstream work."
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
- Portable meaning: Upfront analysis that structures primary code, paper, and document materials for downstream work.

## Portable Contract

- Invocation semantics: Pre-work analysis skill — analyzes the project's primary materials and writes structured artifacts to <artifact-root>/analysis_project/. Three modes — code (codebase), paper (academic PDFs), doc (miscellaneous doc materials like reviewer comments, format templates, samples, internal notes). Mode auto-detects between code and doc when omitted; paper requires explicit --mode paper. Output is the persistent input source for downstream autopilot-{draft,code,research} skills. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability analyze-project [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
