---
description: "Run the portable audit capability through the OpenCode adapter. Meaning: 산출물·파이프 사후 점검. drift·일관성·누락을 읽기 중심으로 진단한다."
---

Use the OpenCode adapter realization of portable capability `audit`.
This is adapter-owned output generated from `capabilities/audit.md`, not a Claude command copy.

1. Read `capabilities/audit.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info audit` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability audit [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<artifact_path> [--scope auto|facts|style|structure|cross-ref|coverage|all] [--read-only] [--report-only] [--no-fact-check]`.

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
