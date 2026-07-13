---
description: "Run the portable code-plan capability through the OpenCode adapter. Meaning: 코드 분석 후 상세 구현 plan을 작성하고 선택된 intensity에서 파생된 rigor에 맞는 plan-check gate를 수행한다."
---

Use the OpenCode adapter realization of portable capability `code-plan`.
This is adapter-owned output generated from `capabilities/code-plan.md`, not a runtime-specific command copy.

1. Read `capabilities/code-plan.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info code-plan` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract`, run any
   `tool_contract_check`, and obey `runtime_surface` / `fallback` before
   claiming full support. For `unsupported`, stop or use the reported
   `fallback`.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability code-plan [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<task description> [--intensity direct|quick|standard|strong|thorough|adversarial]`.

Portable contract excerpt:

- Invocation semantics: Create a detailed implementation plan based on actual codebase Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


User arguments from OpenCode: `$ARGUMENTS`

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
