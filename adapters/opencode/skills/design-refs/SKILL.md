---
name: design-refs
description: "Use when the user requests design-refs: 외부·사용자 reference 시각 자료를 수집하고 brief를 만든다. Read the portable capability spec and run the OpenCode preflight wrapper before claiming support."
metadata:
  portable_source: capabilities/design-refs.md
  adapter: opencode
---

# design-refs

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/design-refs.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info design-refs`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/design-refs.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info design-refs`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `design-refs`
- Supported modes: `none`
- Argument shape: `<design task> [--design <path>] [--refs <image paths>] [--no-web]`
- Portable meaning: 외부·사용자 reference 시각 자료를 수집하고 brief를 만든다.

## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability design-refs [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or Claude adapter Skill files as
OpenCode-native source. Those files are compatibility/reference surfaces only.
