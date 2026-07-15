---
name: autopilot-code
description: "Use when needed: Code-work entrypoint that detects spec context and closes the plan→execute→test→report loop."
metadata:
  portable_source: capabilities/autopilot-code.md
  adapter: opencode
---

# autopilot-code

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-code.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-code`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-code.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-code`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-code`
- Supported modes: `dev, debug, audit`
- Argument shape: `--mode dev|debug <task/plan/error description> [--from <step>] [--intensity direct|quick|standard|strong|thorough|adversarial] [--user-refine]`
- Portable meaning: Code-work entrypoint that detects spec context and closes the plan→execute→test→report loop.

## Portable Contract

- Invocation semantics: General code-work entrypoint for libraries, research code, and applications, whether new or existing; it detects the cwd automatically. It supports `dev` (features/new work) and `debug` (diagnosis/fixes). When `spec/` exists, read it and branch by spec mode: app adds design critique, migration safety, and push/deploy handling; library checks public API consistency; CLI checks command and option consistency; research checks reproducibility, configs, and metrics. Non-code decisions such as PRDs, stack selection, skeletons, and ship setup belong to autopilot-spec. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-code [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
