---
description: "Run the portable autopilot-ship capability through the OpenCode adapter. Meaning: 앱 배포·출시 준비. build/deploy setup과 ship checklist를 만든다."
---

Use the OpenCode adapter realization of portable capability `autopilot-ship`.
This is adapter-owned output generated from `capabilities/autopilot-ship.md`, not a Claude command copy.

1. Read `capabilities/autopilot-ship.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-ship` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-ship [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<task description (선택)> [--qa quick|light|standard|thorough]`.

Do not use `adapters/claude/commands/` or Claude slash-command files as
OpenCode-native command source.
