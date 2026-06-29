---
name: autopilot-refine
description: "Use when the user requests autopilot-refine: 기존 문서·연구 산출물의 정정·갱신. 버전 snapshot과 변경 이력을 보존한다. Read the portable capability spec and run the OpenCode preflight wrapper before claiming support."
metadata:
  portable_source: capabilities/autopilot-refine.md
  adapter: opencode
---

# autopilot-refine

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/autopilot-refine.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-refine`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-refine.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-refine`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `autopilot-refine`
- Supported modes: `none`
- Argument shape: `\"<prompt>\" [--qa quick|light|standard|thorough|adversarial] [--review-only|--memo <file>] [--confirm] [--no-fact-check] [--no-style-audit]`
- Portable meaning: 기존 문서·연구 산출물의 정정·갱신. 버전 snapshot과 변경 이력을 보존한다.

## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-refine [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
