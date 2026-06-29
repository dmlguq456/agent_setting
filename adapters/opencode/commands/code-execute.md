---
description: "Run the portable code-execute capability through the OpenCode adapter. Meaning: plan 단계별 구현 실행. 개발 role에 작업을 위임하고 execution log를 남긴다."
---

Use the OpenCode adapter realization of portable capability `code-execute`.
This is adapter-owned output generated from `capabilities/code-execute.md`, not a Claude command copy.

1. Read `capabilities/code-execute.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info code-execute` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability code-execute [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<plan name or path>`.

Do not use `adapters/claude/commands/` or Claude slash-command files as
OpenCode-native command source.
