---
name: autopilot-apply
description: "Use when the user requests autopilot-apply: cheatsheet 초안을 실제 source artifact에 적용하고 검증한다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# autopilot-apply

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/autopilot-apply.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info autopilot-apply`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/autopilot-apply.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info autopilot-apply`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `autopilot-apply`
- Supported modes: `none`
- Argument shape: `\"<cheatsheet hint / task>\" [--target latex] [--source <path-to-real-source>] [--isolation branch|worktree] [--from preflight|apply|verify|handback]`
- Portable meaning: cheatsheet 초안을 실제 source artifact에 적용하고 검증한다.

## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability autopilot-apply [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or Claude adapter Skill files as
Codex-native source. Those files are compatibility/reference surfaces only.
