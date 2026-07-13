---
description: "Run the portable code-refine capability through the OpenCode adapter. Meaning: 사용자 메모·plan-check 피드백·검증 실패 메모를 반영해 기존 plan을 정정한다."
---

Use the OpenCode adapter realization of portable capability `code-refine`.
This is adapter-owned output generated from `capabilities/code-refine.md`, not a runtime-specific command copy.

1. Read `capabilities/code-refine.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info code-refine` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract`, run any
   `tool_contract_check`, and obey `runtime_surface` / `fallback` before
   claiming full support. For `unsupported`, stop or use the reported
   `fallback`.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability code-refine [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<plan name or path> [--intensity direct|quick|standard|strong|thorough|adversarial]`.

Portable contract excerpt:

- Invocation semantics: Reflect user memos/comments in a plan and update it (do NOT implement) Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


User arguments from OpenCode: `$ARGUMENTS`

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
