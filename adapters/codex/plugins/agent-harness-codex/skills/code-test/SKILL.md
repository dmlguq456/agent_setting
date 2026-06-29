---
name: code-test
description: "Use when the user requests code-test: 구현 결과를 단계별로 검증하고 evidence를 기록한다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# code-test

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/code-test.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info code-test`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/code-test.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info code-test`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the missing tool contract before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `code-test`
- Supported modes: `none`
- Argument shape: `<plan name, path, or test scope>`
- Portable meaning: 구현 결과를 단계별로 검증하고 evidence를 기록한다.

## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability code-test [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use `skills/code-test/SKILL.md` or
`adapters/claude/skills/code-test/SKILL.md` as Codex-native source. Those
files are Claude compatibility/reference surfaces.
