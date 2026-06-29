---
name: code-execute
description: "Use when the user requests code-execute: plan 단계별 구현 실행. 개발 role에 작업을 위임하고 execution log를 남긴다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# code-execute

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/code-execute.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info code-execute`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/code-execute.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info code-execute`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `code-execute`
- Supported modes: `none`
- Argument shape: `<plan name or path>`
- Portable meaning: plan 단계별 구현 실행. 개발 role에 작업을 위임하고 execution log를 남긴다.

## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability code-execute [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
