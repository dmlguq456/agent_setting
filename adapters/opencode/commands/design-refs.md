---
description: "Run the portable design-refs capability through the OpenCode adapter. Meaning: 외부·사용자 reference 시각 자료를 수집하고 brief를 만든다."
---

Use the OpenCode adapter realization of portable capability `design-refs`.
This is adapter-owned output generated from `capabilities/design-refs.md`, not a runtime-specific command copy.

1. Read `capabilities/design-refs.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info design-refs` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability design-refs [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<design task> [--design <path>] [--refs <image paths>] [--no-web]`.

User arguments from OpenCode: `$ARGUMENTS`

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
