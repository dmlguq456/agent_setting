---
description: "Run the portable autopilot-research capability through the OpenCode adapter. Meaning: 공통 사전조사. 논문·기술·시장 survey 후 downstream capability로 분기한다."
---

Use the OpenCode adapter realization of portable capability `autopilot-research`.
This is adapter-owned output generated from `capabilities/autopilot-research.md`, not a Claude command copy.

1. Read `capabilities/autopilot-research.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-research` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-research [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<query> [--mode academic|technology|market] [--depth shallow|medium|deep] [--qa quick|light|standard|thorough|adversarial] [--no-clarify] [--no-figures] [--from search|analyze|report]`.

Do not use Claude adapter command files or Claude slash-command files as
OpenCode-native command source.
