---
name: analyze-user
description: "Use when the user requests analyze-user: cross-project 사용자 성향 프로필 작성·갱신. 코드·작성·분석 패턴을 추출한다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# analyze-user

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/analyze-user.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info analyze-user`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/analyze-user.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info analyze-user`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `analyze-user`
- Supported modes: `init, update`
- Argument shape: `<aspect> [--source <path>] [--mode init|update] [--from discover|analyze|verify|qa|output|summary] [--user-refine]`
- Portable meaning: cross-project 사용자 성향 프로필 작성·갱신. 코드·작성·분석 패턴을 추출한다.

## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability analyze-user [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
