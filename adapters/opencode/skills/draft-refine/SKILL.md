---
name: draft-refine
description: "Use when the user requests draft-refine: 초안 정련·다듬기. memo/review feedback을 문서 전략이나 draft에 반영한다. Read the portable capability spec and run the OpenCode preflight wrapper before claiming support."
metadata:
  portable_source: capabilities/draft-refine.md
  adapter: opencode
---

# draft-refine

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/draft-refine.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info draft-refine`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/draft-refine.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info draft-refine`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the missing tool contract before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `draft-refine`
- Supported modes: `none`
- Argument shape: `<strategy or draft name or path> [--qa quick|light|standard|thorough|adversarial]`
- Portable meaning: 초안 정련·다듬기. memo/review feedback을 문서 전략이나 draft에 반영한다.

## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability draft-refine [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use `skills/draft-refine/SKILL.md` or
`adapters/claude/skills/draft-refine/SKILL.md` as OpenCode-native source. Those
files are Claude compatibility/reference surfaces.
