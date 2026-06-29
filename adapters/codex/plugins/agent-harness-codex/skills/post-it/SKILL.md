---
name: post-it
description: "Use when the user requests post-it: 프로젝트·cross-project 기록과 handoff를 working memory로 남긴다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# post-it

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/post-it.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info post-it`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/post-it.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info post-it`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `post-it`
- Supported modes: `none`
- Argument shape: `[show]|add <category> <text>|resolve <hint>|decide <text>|handoff [--no-confirm]|sweep [--no-confirm]|promote [<hint>] [--scope project|user [<aspect>]]`
- Portable meaning: 프로젝트·cross-project 기록과 handoff를 working memory로 남긴다.

## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability post-it [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
