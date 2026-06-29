---
description: "Run the portable draft-strategy capability through the OpenCode adapter. Meaning: 문서 전략 초안 작성. 자료 기반으로 writing plan을 만든다."
---

Use the OpenCode adapter realization of portable capability `draft-strategy`.
This is adapter-owned output generated from `capabilities/draft-strategy.md`, not a Claude command copy.

1. Read `capabilities/draft-strategy.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info draft-strategy` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability draft-strategy [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<mode> --inputs <comma-separated-paths> --output <artifact-dir> [--qa quick|light|standard|thorough|adversarial] <task description>`.

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
