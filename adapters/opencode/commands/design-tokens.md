---
description: "Run the portable design-tokens capability through the OpenCode adapter. Meaning: 색·타이포·간격 등 디자인 토큰을 정의한다."
---

Use the OpenCode adapter realization of portable capability `design-tokens`.
This is adapter-owned output generated from `capabilities/design-tokens.md`, not a runtime-specific command copy.

1. Read `capabilities/design-tokens.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info design-tokens` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability design-tokens [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<design path or app path>`.

User arguments from OpenCode: `$ARGUMENTS`

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
