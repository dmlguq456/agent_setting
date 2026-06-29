---
description: "Run the portable code-refine capability through the OpenCode adapter. Meaning: 사용자 메모·QA 피드백을 반영해 기존 plan을 정정한다."
---

Use the OpenCode adapter realization of portable capability `code-refine`.
This is adapter-owned output generated from `capabilities/code-refine.md`, not a Claude command copy.

1. Read `capabilities/code-refine.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info code-refine` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability code-refine [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<plan name or path> [--qa quick|light|standard|thorough|adversarial]`.

Do not use `adapters/claude/commands/` or Claude slash-command files as
OpenCode-native command source.
