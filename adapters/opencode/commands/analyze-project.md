---
description: "Run the portable analyze-project capability through the OpenCode adapter. Meaning: 사전 분석. 코드·논문·문서 primary 자료를 구조화해 다운스트림 입력으로 만든다."
---

Use the OpenCode adapter realization of portable capability `analyze-project`.
This is adapter-owned output generated from `capabilities/analyze-project.md`, not a Claude command copy.

1. Read `capabilities/analyze-project.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info analyze-project` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability analyze-project [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `[--mode code|paper|doc] [<scope/target/input-folder>] [--skip-qa]`.

Do not use Claude adapter command files or Claude slash-command files as
OpenCode-native command source.
