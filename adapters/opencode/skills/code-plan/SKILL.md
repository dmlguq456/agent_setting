---
name: code-plan
description: "Use when the user requests code-plan: 코드 분석 후 상세 구현 plan 작성. planning role과 QA loop를 사용한다. Read the portable capability spec and run the OpenCode preflight wrapper before claiming support."
metadata:
  portable_source: capabilities/code-plan.md
  adapter: opencode
---

# code-plan

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/code-plan.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info code-plan`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/code-plan.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info code-plan`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the missing tool contract before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `code-plan`
- Supported modes: `none`
- Argument shape: `<task description> [--qa quick|light|standard|thorough|adversarial]`
- Portable meaning: 코드 분석 후 상세 구현 plan 작성. planning role과 QA loop를 사용한다.

## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability code-plan [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use `skills/code-plan/SKILL.md` or
`adapters/claude/skills/code-plan/SKILL.md` as OpenCode-native source. Those
files are Claude compatibility/reference surfaces.
