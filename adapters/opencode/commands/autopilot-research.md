---
description: "Run the portable autopilot-research capability through the OpenCode adapter. Meaning: 공통 사전조사. 논문·기술·시장 survey 후 downstream capability로 분기한다."
---

Use the OpenCode adapter realization of portable capability `autopilot-research`.
This is adapter-owned output generated from `capabilities/autopilot-research.md`, not a runtime-specific command copy.

1. Read `capabilities/autopilot-research.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-research` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract`, run any
   `tool_contract_check`, and obey `runtime_surface` / `fallback` before
   claiming full support. For `unsupported`, stop or use the reported
   `fallback`.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-research [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<query> [--mode academic|technology|market] [--depth shallow|medium|deep] [--intensity direct|quick|standard|strong|thorough|adversarial] [--qa quick|light|standard|thorough|adversarial] [--no-clarify] [--no-figures] [--from search|analyze|report]`.

Portable contract excerpt:

- Invocation semantics: Research survey pipeline — _세 family 의 공통 사전_ entry. academic (논문 survey·trend·필드 정리) / technology (라이브러리·프로젝트·스택·코드 baseline 비교) / market (시장·경쟁·reference 앱·UX 패턴) 3 mode. 다운스트림 매핑: academic → autopilot-draft (paper/presentation) + autopilot-code (academic baseline 코드) | technology → autopilot-code (라이브러리·연구 baseline 위) + autopilot-spec (스택·reference 패턴) | market → autopilot-draft (proposal/report) + autopilot-spec (reference 앱 UX). Field intelligence only — 실제 문서·코드·앱 생성은 다운스트림 skill 이 담당. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


User arguments from OpenCode: `$ARGUMENTS`

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
