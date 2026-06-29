---
description: "Run the portable code-plan capability through the OpenCode adapter. Meaning: 코드 분석 후 상세 구현 plan 작성. planning role과 QA loop를 사용한다."
---

Use the OpenCode adapter realization of portable capability `code-plan`.
This is adapter-owned output generated from `capabilities/code-plan.md`, not a Claude command copy.

1. Read `capabilities/code-plan.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info code-plan` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability code-plan [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<task description> [--qa quick|light|standard|thorough|adversarial]`.

Do not use `adapters/claude/commands/` or Claude slash-command files as
OpenCode-native command source.
