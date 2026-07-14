---
name: autopilot-research
description: "Use for autopilot-research: Shared upfront research that surveys academic, technology, or market sources before downstream routing."
metadata:
  portable_source: capabilities/autopilot-research.md
  adapter: opencode
---

# autopilot-research

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-research.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-research`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-research.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-research`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-research`
- Supported modes: `academic, technology, market`
- Argument shape: `<query> [--mode academic|technology|market] [--depth shallow|medium|deep] [--intensity direct|quick|standard|strong|thorough|adversarial] [--no-clarify] [--no-figures] [--from search|analyze|report]`
- Portable meaning: Shared upfront research that surveys academic, technology, or market sources before downstream routing.

## Portable Contract

- Invocation semantics: Shared research-survey entrypoint with three modes: academic (papers, trends, and field mapping), technology (libraries, projects, stacks, and code baselines), and market (market/competitor/reference-app/UX patterns). Downstream routing: academic → autopilot-draft for papers/presentations and autopilot-code for academic baselines; technology → autopilot-code for library or research implementation and autopilot-spec for stack/reference decisions; market → autopilot-draft for proposals/reports and autopilot-spec for reference-app UX. This capability produces field intelligence only; downstream skills create actual documents, code, or applications. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-research [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
