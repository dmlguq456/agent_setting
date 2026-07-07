---
name: autopilot-research
description: "Use for autopilot-research: 공통 사전조사. 논문·기술·시장 survey 후 downstream capability로 분기한다."
metadata:
  portable_source: capabilities/autopilot-research.md
  adapter: opencode
---

# autopilot-research

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-research.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-research`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-research.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-research`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-research`
- Supported modes: `academic, technology, market`
- Argument shape: `<query> [--mode academic|technology|market] [--depth shallow|medium|deep] [--intensity direct|quick|standard|strong|thorough|adversarial] [--qa quick|light|standard|thorough|adversarial] [--no-clarify] [--no-figures] [--from search|analyze|report]`
- Portable meaning: 공통 사전조사. 논문·기술·시장 survey 후 downstream capability로 분기한다.

## Portable Contract

- Invocation semantics: Research survey pipeline — _세 family 의 공통 사전_ entry. academic (논문 survey·trend·필드 정리) / technology (라이브러리·프로젝트·스택·코드 baseline 비교) / market (시장·경쟁·reference 앱·UX 패턴) 3 mode. 다운스트림 매핑: academic → autopilot-draft (paper/presentation) + autopilot-code (academic baseline 코드) | technology → autopilot-code (라이브러리·연구 baseline 위) + autopilot-spec (스택·reference 패턴) | market → autopilot-draft (proposal/report) + autopilot-spec (reference 앱 UX). Field intelligence only — 실제 문서·코드·앱 생성은 다운스트림 skill 이 담당. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-research [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
