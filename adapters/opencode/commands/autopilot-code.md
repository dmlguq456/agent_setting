---
description: "Run the portable autopilot-code capability through the OpenCode adapter. Meaning: 코드 작업 entry. spec 컨텍스트를 감지하고 plan→execute→test→report 흐름을 닫는다."
---

Use the OpenCode adapter realization of portable capability `autopilot-code`.
This is adapter-owned output generated from `capabilities/autopilot-code.md`, not a runtime-specific command copy.

1. Read `capabilities/autopilot-code.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-code` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract`, run any
   `tool_contract_check`, and obey `runtime_surface` / `fallback` before
   claiming full support. For `unsupported`, stop or use the reported
   `fallback`.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-code [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `--mode dev|debug <task/plan/error description> [--from <step>] [--intensity direct|quick|standard|strong|thorough|adversarial] [--user-refine]`.

Portable contract excerpt:

- Invocation semantics: _코드 작업 일반_ entry — 라이브러리·연구 코드·앱 모두 커버. 신규·기존 코드 무관 (cwd 자동 감지). dev (기능 추가·신규) / debug (진단·수정) 두 mode. spec/ 컨텍스트 발견 시 spec 자동 Read + spec mode 별 분기: app mode → 디자인팀 critic + DB migration 안전 + push 자동 deploy. library mode → 공개 API 일관성 점검. cli mode → 명령·옵션 일관성. research mode → 재현성·configs·metric 검증. 코드 외 결정 (PRD·스택·skeleton·ship setup) 은 autopilot-spec 영역. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


User arguments from OpenCode: `$ARGUMENTS`

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
