---
description: "Run the portable code-report capability through the OpenCode adapter. Meaning: 코드 작업 사이클 결과를 사용자-facing 보고서로 조립한다."
---

Use the OpenCode adapter realization of portable capability `code-report`.
This is adapter-owned output generated from `capabilities/code-report.md`, not a runtime-specific command copy.

1. Read `capabilities/code-report.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info code-report` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability code-report [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<plan name or path>`.

User arguments from OpenCode: `$ARGUMENTS`

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
