---
description: "Run the portable analyze-user capability through the OpenCode adapter. Meaning: cross-project 사용자 성향 프로필 작성·갱신. 코드·작성·분석 패턴을 추출한다."
---

Use the OpenCode adapter realization of portable capability `analyze-user`.
This is adapter-owned output generated from `capabilities/analyze-user.md`, not a Claude command copy.

1. Read `capabilities/analyze-user.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info analyze-user` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability analyze-user [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<aspect> [--source <path>] [--mode init|update] [--from discover|analyze|verify|qa|output|summary] [--user-refine]`.

Do not use `adapters/claude/commands/` or Claude slash-command files as
OpenCode-native command source.
