---
name: autopilot-research
description: "Use when the user requests autopilot-research: 공통 사전조사. 논문·기술·시장 survey 후 downstream capability로 분기한다. Read the portable capability spec and run the OpenCode preflight wrapper before claiming support."
metadata:
  portable_source: capabilities/autopilot-research.md
  adapter: opencode
---

# autopilot-research

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/autopilot-research.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-research`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-research.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-research`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `autopilot-research`
- Supported modes: `academic, technology, market`
- Argument shape: `<query> [--mode academic|technology|market] [--depth shallow|medium|deep] [--qa quick|light|standard|thorough|adversarial] [--no-clarify] [--no-figures] [--from search|analyze|report]`
- Portable meaning: 공통 사전조사. 논문·기술·시장 survey 후 downstream capability로 분기한다.

## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-research [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or Claude adapter Skill files as
OpenCode-native source. Those files are compatibility/reference surfaces only.
