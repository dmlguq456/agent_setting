---
description: "Run the portable design-review capability through the OpenCode adapter. Meaning: 디자인 결과물을 품질·토큰 계약·breakage 관점으로 점검한다."
---

Use the OpenCode adapter realization of portable capability `design-review`.
This is adapter-owned output generated from `capabilities/design-review.md`, not a Claude command copy.

1. Read `capabilities/design-review.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info design-review` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability design-review [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<design path or app path>`.

Do not use Claude adapter command files or Claude slash-command files as
OpenCode-native command source.
