---
name: code-refine
description: "Use when the user requests code-refine: 사용자 메모·plan-check 피드백·검증 실패 메모를 반영해 기존 plan을 정정한다. Read the portable capability spec and run the OpenCode preflight wrapper before claiming support."
metadata:
  portable_source: capabilities/code-refine.md
  adapter: opencode
---

# code-refine

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/code-refine.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info code-refine`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/code-refine.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info code-refine`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `code-refine`
- Supported modes: `none`
- Argument shape: `<plan name or path> [--qa quick|light|standard|thorough|adversarial]`
- Portable meaning: 사용자 메모·plan-check 피드백·검증 실패 메모를 반영해 기존 plan을 정정한다.

## Portable Contract

- Invocation semantics: Reflect user memos/comments in a plan and update it (do NOT implement) Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability code-refine [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
