---
name: design-review
description: "Use when the user requests design-review: 디자인 결과물을 품질·토큰 계약·breakage 관점으로 점검한다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# design-review

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/design-review.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info design-review`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/design-review.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info design-review`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the missing tool contract before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `design-review`
- Supported modes: `none`
- Argument shape: `<design path or app path>`
- Portable meaning: 디자인 결과물을 품질·토큰 계약·breakage 관점으로 점검한다.

## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability design-review [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use `skills/design-review/SKILL.md` or
`adapters/claude/skills/design-review/SKILL.md` as Codex-native source. Those
files are Claude compatibility/reference surfaces.
