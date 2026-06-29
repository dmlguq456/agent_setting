---
description: "Run the portable autopilot-design capability through the OpenCode adapter. Meaning: 시각 산출물 디자인 파이프. refs→tokens→components→review→handoff를 조율한다."
---

Use the OpenCode adapter realization of portable capability `autopilot-design`.
This is adapter-owned output generated from `capabilities/autopilot-design.md`, not a runtime-specific command copy.

1. Read `capabilities/autopilot-design.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-design` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-design [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<design task or app path> [--scope ui|webapp|slide|icon|diagram|mixed] [--artifact standalone|project] [--from <phase>] [--qa quick|standard|thorough]`.

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
