---
name: autopilot-spec
description: "Use for autopilot-spec: 요구사항·청사진 작성·갱신. `prd.md`를 spec 변경의 단일 경로로 유지한다."
metadata:
  portable_source: capabilities/autopilot-spec.md
  adapter: opencode
---

# autopilot-spec

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-spec.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-spec`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-spec.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-spec`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-spec`
- Supported modes: `app, library, api, cli, research, update`
- Argument shape: `<task description> [--mode auto|app|library|api|cli|research|update (콤마로 다중)] [--intensity direct|quick|standard|strong|thorough|adversarial] [--qa quick|light|standard|thorough] [--user-refine]`
- Portable meaning: 요구사항·청사진 작성·갱신. `prd.md`를 spec 변경의 단일 경로로 유지한다.

## Portable Contract

- Invocation semantics: _요구사항·청사진 작성·갱신_ 의 일반화 entry — 신규 의도, 기존 코드 정돈·공개 준비, 그리고 기존 spec 의 update·iteration (prd.md 갱신) 자리 모두. mode 5종 (app / library / api / cli / research) + 다중 + auto + update mode (기존 prd.md 갱신 — 모든 spec 변경의 canonical 경로, 버전 snapshot 자동). PRD 구조 = 공통 + mode 별 독립 섹션. autopilot-research / analyze-project 결과 자동 인용. analyze-project 의 _신규 의도 → 청사진_ 대칭 자리. 실제 코드 작업은 autopilot-code 가 담당 (spec/ 컨텍스트 자동 감지). Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-spec [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
