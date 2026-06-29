---
name: code-report
description: "Use when the user requests code-report: 코드 작업 사이클 결과를 사용자-facing 보고서로 조립한다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# code-report

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/code-report.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info code-report`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/code-report.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info code-report`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `code-report`
- Supported modes: `none`
- Argument shape: `<plan name or path>`
- Portable meaning: 코드 작업 사이클 결과를 사용자-facing 보고서로 조립한다.

## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability code-report [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or Claude adapter Skill files as
Codex-native source. Those files are compatibility/reference surfaces only.
