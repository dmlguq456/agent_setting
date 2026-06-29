---
description: "Run the portable draft-refine capability through the OpenCode adapter. Meaning: 초안 정련·다듬기. memo/review feedback을 문서 전략이나 draft에 반영한다."
---

Use the OpenCode adapter realization of portable capability `draft-refine`.
This is adapter-owned output generated from `capabilities/draft-refine.md`, not a Claude command copy.

1. Read `capabilities/draft-refine.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info draft-refine` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability draft-refine [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<strategy or draft name or path> [--qa quick|light|standard|thorough|adversarial]`.

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
