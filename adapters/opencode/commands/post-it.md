---
description: "Run the portable post-it capability through the OpenCode adapter. Meaning: 프로젝트·cross-project 기록과 handoff를 working memory로 남긴다."
---

Use the OpenCode adapter realization of portable capability `post-it`.
This is adapter-owned output generated from `capabilities/post-it.md`, not a Claude command copy.

1. Read `capabilities/post-it.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info post-it` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability post-it [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `[show]|add <category> <text>|resolve <hint>|decide <text>|handoff [--no-confirm]|sweep [--no-confirm]|promote [<hint>] [--scope project|user [<aspect>]]`.

Do not use Claude adapter command files or Claude slash-command files as
OpenCode-native command source.
