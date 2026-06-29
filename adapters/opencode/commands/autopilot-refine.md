---
description: "Run the portable autopilot-refine capability through the OpenCode adapter. Meaning: 기존 문서·연구 산출물의 정정·갱신. 버전 snapshot과 변경 이력을 보존한다."
---

Use the OpenCode adapter realization of portable capability `autopilot-refine`.
This is adapter-owned output generated from `capabilities/autopilot-refine.md`, not a Claude command copy.

1. Read `capabilities/autopilot-refine.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-refine` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-refine [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `\"<prompt>\" [--qa quick|light|standard|thorough|adversarial] [--review-only|--memo <file>] [--confirm] [--no-fact-check] [--no-style-audit]`.

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
