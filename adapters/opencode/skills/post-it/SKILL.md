---
name: post-it
description: "Use when the user requests post-it: 프로젝트·cross-project 기록과 handoff를 working memory로 남긴다. Read the portable capability spec and run the OpenCode preflight wrapper before claiming support."
metadata:
  portable_source: capabilities/post-it.md
  adapter: opencode
---

# post-it

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/post-it.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info post-it`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/post-it.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info post-it`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the missing tool contract before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `post-it`
- Supported modes: `none`
- Argument shape: `[show]|add <category> <text>|resolve <hint>|decide <text>|handoff [--no-confirm]|sweep [--no-confirm]|promote [<hint>] [--scope project|user [<aspect>]]`
- Portable meaning: 프로젝트·cross-project 기록과 handoff를 working memory로 남긴다.

## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability post-it [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use `skills/post-it/SKILL.md` or
`adapters/claude/skills/post-it/SKILL.md` as OpenCode-native source. Those
files are Claude compatibility/reference surfaces.
