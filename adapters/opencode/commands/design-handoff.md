---
description: "Run the portable design-handoff capability through the OpenCode adapter. Meaning: 디자인 결과를 개발 handoff용 자산·스펙으로 정리한다."
---

Use the OpenCode adapter realization of portable capability `design-handoff`.
This is adapter-owned output generated from `capabilities/design-handoff.md`, not a Claude command copy.

1. Read `capabilities/design-handoff.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info design-handoff` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability design-handoff [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<design path or app path>`.

Do not use `adapters/claude/commands/` or Claude slash-command files as
OpenCode-native command source.
