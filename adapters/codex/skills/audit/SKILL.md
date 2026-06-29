---
name: audit
description: "Use when the user requests audit: 산출물·파이프 사후 점검. drift·일관성·누락을 읽기 중심으로 진단한다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# audit

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/audit.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info audit`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/audit.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info audit`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `audit`
- Supported modes: `none`
- Argument shape: `<artifact_path> [--scope auto|facts|style|structure|cross-ref|coverage|all] [--read-only] [--report-only] [--no-fact-check]`
- Portable meaning: 산출물·파이프 사후 점검. drift·일관성·누락을 읽기 중심으로 진단한다.

## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability audit [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or Claude adapter Skill files as
Codex-native source. Those files are compatibility/reference surfaces only.
