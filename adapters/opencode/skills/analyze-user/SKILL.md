---
name: analyze-user
description: "Use for analyze-user: Create or update a cross-project user-preference profile from coding, writing, and analysis patterns."
metadata:
  portable_source: capabilities/analyze-user.md
  adapter: opencode
---

# analyze-user

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/analyze-user.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info analyze-user`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/analyze-user.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info analyze-user`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `analyze-user`
- Supported modes: `init, update`
- Argument shape: `<aspect> [--source <path>] [--mode init|update] [--from discover|analyze|verify|qa|output|summary] [--user-refine]`
- Portable meaning: Create or update a cross-project user-preference profile from coding, writing, and analysis patterns.

## Portable Contract

- Invocation semantics: Scan and analyze the user's cross-project artifacts (papers, presentations, reports, code, and memory) in stages, then accumulate general working preferences in DB `type=profile` records (`mem profile <stem>`). This uses the same ceremony level as autopilot entrypoints because every sub-agent treats the resulting profile as a default, so even small errors propagate. The six phases are source discovery, per-aspect analysis, cross-aspect consistency checks, multiple QA gates, artifact creation, and pipeline summary. QA is always adversarial and is not user-adjustable. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability analyze-user [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
