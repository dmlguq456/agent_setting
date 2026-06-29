---
description: "Run the portable autopilot-note capability through the OpenCode adapter. Meaning: 산출물 라우팅/노트화. digest와 triage 제안을 만든다."
---

Use the OpenCode adapter realization of portable capability `autopilot-note`.
This is adapter-owned output generated from `capabilities/autopilot-note.md`, not a Claude command copy.

1. Read `capabilities/autopilot-note.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-note` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-note [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `[--scope today|yesterday|since <date>|all] [--target <notes-root>] [--dry-run] [--qa quick|light|standard|thorough|adversarial] [--digest-only] [--triage-only] [--source <list>] [--no-fact-check]`.

Do not use Claude adapter command files or Claude slash-command files as
OpenCode-native command source.
