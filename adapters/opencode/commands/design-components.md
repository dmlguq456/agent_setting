---
description: "Run the portable design-components capability through the OpenCode adapter. Meaning: UI component/mockup 구현과 preview artifact를 만든다."
---

Use the OpenCode adapter realization of portable capability `design-components`.
This is adapter-owned output generated from `capabilities/design-components.md`, not a Claude command copy.

1. Read `capabilities/design-components.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info design-components` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability design-components [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<design path or app path>`.

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
