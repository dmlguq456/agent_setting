---
description: "Run the portable autopilot-spec capability through the OpenCode adapter. Meaning: 요구사항·청사진 작성·갱신. `prd.md`를 spec 변경의 단일 경로로 유지한다."
---

Use the OpenCode adapter realization of portable capability `autopilot-spec`.
This is adapter-owned output generated from `capabilities/autopilot-spec.md`, not a Claude command copy.

1. Read `capabilities/autopilot-spec.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-spec` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-spec [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<task description> [--mode auto|app|library|api|cli|research|update (콤마로 다중)] [--qa quick|light|standard|thorough] [--user-refine]`.

Do not use `adapters/claude/commands/` or Claude slash-command files as
OpenCode-native command source.
