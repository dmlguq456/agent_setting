---
description: "Run the portable autopilot-apply capability through the OpenCode adapter. Meaning: cheatsheet 초안을 실제 source artifact에 적용하고 검증한다."
---

Use the OpenCode adapter realization of portable capability `autopilot-apply`.
This is adapter-owned output generated from `capabilities/autopilot-apply.md`, not a runtime-specific command copy.

1. Read `capabilities/autopilot-apply.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-apply` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-apply [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `\"<cheatsheet hint / task>\" [--target latex] [--source <path-to-real-source>] [--isolation branch|worktree] [--from preflight|apply|verify|handback]`.

User arguments from OpenCode: `$ARGUMENTS`

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
