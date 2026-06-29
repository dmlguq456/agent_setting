---
name: autopilot-apply
description: "Use when the user requests autopilot-apply: cheatsheet 초안을 실제 source artifact에 적용하고 검증한다. Read the portable capability spec and run the OpenCode preflight wrapper before claiming support."
metadata:
  portable_source: capabilities/autopilot-apply.md
  adapter: opencode
---

# autopilot-apply

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/autopilot-apply.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-apply`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-apply.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-apply`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the missing tool contract before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `autopilot-apply`
- Supported modes: `none`
- Argument shape: `\"<cheatsheet hint / task>\" [--target latex] [--source <path-to-real-source>] [--isolation branch|worktree] [--from preflight|apply|verify|handback]`
- Portable meaning: cheatsheet 초안을 실제 source artifact에 적용하고 검증한다.

## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-apply [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use `skills/autopilot-apply/SKILL.md` or
`adapters/claude/skills/autopilot-apply/SKILL.md` as OpenCode-native source. Those
files are Claude compatibility/reference surfaces.
