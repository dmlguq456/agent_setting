---
name: code-report
description: "Use when the user requests code-report: 코드 작업 사이클 결과를 사용자-facing 보고서로 조립한다. Read the portable capability spec and run the OpenCode preflight wrapper before claiming support."
metadata:
  portable_source: capabilities/code-report.md
  adapter: opencode
---

# code-report

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/code-report.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info code-report`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/code-report.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info code-report`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `code-report`
- Supported modes: `none`
- Argument shape: `<plan name or path>`
- Portable meaning: 코드 작업 사이클 결과를 사용자-facing 보고서로 조립한다.

## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability code-report [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
