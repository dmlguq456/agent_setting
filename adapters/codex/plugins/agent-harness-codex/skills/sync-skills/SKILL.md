---
name: sync-skills
description: "Use when the user requests sync-skills: 정의 변경을 읽어 README/manifest/cross-doc invariant drift를 점검·동기화한다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# sync-skills

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/sync-skills.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info sync-skills`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/sync-skills.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info sync-skills`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `sync-skills`
- Supported modes: `none`
- Argument shape: `[--check] [--force] [--auto-fix [--dry-run]]`
- Portable meaning: 정의 변경을 읽어 README/manifest/cross-doc invariant drift를 점검·동기화한다.

## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability sync-skills [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or Claude adapter Skill files as
Codex-native source. Those files are compatibility/reference surfaces only.
