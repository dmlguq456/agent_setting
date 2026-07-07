---
name: analyze-user
description: "Use for analyze-user: cross-project 사용자 성향 프로필 작성·갱신. 코드·작성·분석 패턴을 추출한다."
metadata:
  portable_source: capabilities/analyze-user.md
  adapter: opencode
---

# analyze-user

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/analyze-user.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info analyze-user`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/analyze-user.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info analyze-user`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `analyze-user`
- Supported modes: `init, update`
- Argument shape: `<aspect> [--source <path>] [--mode init|update] [--from discover|analyze|verify|qa|output|summary] [--user-refine]`
- Portable meaning: cross-project 사용자 성향 프로필 작성·갱신. 코드·작성·분석 패턴을 추출한다.

## Portable Contract

- Invocation semantics: 사용자의 cross-project 산출물 (paper / presentation / report / code / memory) 을 다단계로 스캔·분석해 DB `type=profile` 레코드 (`mem profile <stem>`) 의 _범용 작업 성향_ 을 누적·갱신. autopilot-* 와 동급 ceremony — 사용자 프로필은 _한 번 만들어지면 모든 sub-agent 가 default 로 따르는 자료_ 라 작은 오류도 propagating. 따라서 source discovery → aspect 별 분석 → cross-aspect 일관성 검증 → 다중 QA gate (adversarial 고정) → 산출 → pipeline summary 6 phase. QA level 은 _항상 adversarial_ — 사용자 협상 불가. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability analyze-user [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
