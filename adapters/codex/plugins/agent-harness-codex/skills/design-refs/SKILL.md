---
name: design-refs
description: "Use when the user requests design-refs: 외부·사용자 reference 시각 자료를 수집하고 brief를 만든다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# design-refs

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/design-refs.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info design-refs`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/design-refs.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info design-refs`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the missing tool contract before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `design-refs`
- Supported modes: `none`
- Argument shape: `<design task> [--design <path>] [--refs <image paths>] [--no-web]`
- Portable meaning: 외부·사용자 reference 시각 자료를 수집하고 brief를 만든다.

## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability design-refs [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use `skills/design-refs/SKILL.md` or
`adapters/claude/skills/design-refs/SKILL.md` as Codex-native source. Those
files are Claude compatibility/reference surfaces.
