---
description: "Run the portable autopilot-draft capability through the OpenCode adapter. Meaning: 문서 초안 파이프. 전략·초안·검증·편집을 거쳐 적용용 문서 artifact를 만든다."
---

Use the OpenCode adapter realization of portable capability `autopilot-draft`.
This is adapter-owned output generated from `capabilities/autopilot-draft.md`, not a Claude command copy.

1. Read `capabilities/autopilot-draft.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-draft` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-draft [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<task description> [--mode paper|presentation|doc] [--qa quick|light|standard|thorough|adversarial] [--user-refine] [--no-clarify] [--from analyze|strategy|strategy-refine|draft|draft-refine|finalize]`.

Do not use Claude adapter command files or Claude slash-command files as
OpenCode-native command source.
