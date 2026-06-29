---
name: draft-strategy
description: "Use when the user requests draft-strategy: 문서 전략 초안 작성. 자료 기반으로 writing plan을 만든다. Read the portable capability spec and run the OpenCode preflight wrapper before claiming support."
metadata:
  portable_source: capabilities/draft-strategy.md
  adapter: opencode
---

# draft-strategy

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/draft-strategy.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info draft-strategy`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/draft-strategy.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info draft-strategy`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the missing tool contract before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `draft-strategy`
- Supported modes: `rebuttal, paper, review, report, proposal, presentation`
- Argument shape: `<mode> --inputs <comma-separated-paths> --output <artifact-dir> [--qa quick|light|standard|thorough|adversarial] <task description>`
- Portable meaning: 문서 전략 초안 작성. 자료 기반으로 writing plan을 만든다.

## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability draft-strategy [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use `skills/draft-strategy/SKILL.md` or
`adapters/claude/skills/draft-strategy/SKILL.md` as OpenCode-native source. Those
files are Claude compatibility/reference surfaces.
