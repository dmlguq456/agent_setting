---
name: code-test
description: "Use when the user requests code-test: 구현 결과를 단계별로 검증하고 evidence를 기록한다. Read the portable capability spec and run the OpenCode preflight wrapper before claiming support."
metadata:
  portable_source: capabilities/code-test.md
  adapter: opencode
---

# code-test

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/code-test.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info code-test`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/code-test.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info code-test`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the missing tool contract before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `code-test`
- Supported modes: `none`
- Argument shape: `<plan name, path, or test scope>`
- Portable meaning: 구현 결과를 단계별로 검증하고 evidence를 기록한다.

## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability code-test [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use `skills/code-test/SKILL.md` or
`adapters/claude/skills/code-test/SKILL.md` as OpenCode-native source. Those
files are Claude compatibility/reference surfaces.
