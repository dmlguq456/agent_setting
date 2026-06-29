---
name: design-init
description: "Use when the user requests design-init: 디자인 환경과 state를 bootstrap한다. Read the portable capability spec and run the OpenCode preflight wrapper before claiming support."
metadata:
  portable_source: capabilities/design-init.md
  adapter: opencode
---

# design-init

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/design-init.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info design-init`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/design-init.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info design-init`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `design-init`
- Supported modes: `none`
- Argument shape: `<design task description> [--scope ui|slide|icon|diagram|mixed]`
- Portable meaning: 디자인 환경과 state를 bootstrap한다.

## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability design-init [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
