---
description: "Run the portable autopilot-code capability through the OpenCode adapter. Meaning: 코드 작업 entry. spec 컨텍스트를 감지하고 plan→execute→test→report 흐름을 닫는다."
---

Use the OpenCode adapter realization of portable capability `autopilot-code`.
This is adapter-owned output generated from `capabilities/autopilot-code.md`, not a Claude command copy.

1. Read `capabilities/autopilot-code.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-code` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-code [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `--mode dev|debug <task/plan/error description> [--from <step>] [--qa quick|light|standard|thorough|adversarial] [--user-refine]`.

Do not use Claude adapter command files or Claude slash-command files as
OpenCode-native command source.
