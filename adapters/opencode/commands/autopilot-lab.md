---
description: "Run the portable autopilot-lab capability through the OpenCode adapter. Meaning: 빠른 실험 prototype. 학습 세팅과 ckpt 평가·분석 앞뒤를 돕는다."
---

Use the OpenCode adapter realization of portable capability `autopilot-lab`.
This is adapter-owned output generated from `capabilities/autopilot-lab.md`, not a Claude command copy.

1. Read `capabilities/autopilot-lab.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-lab` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract` and run any
   `tool_contract_check` before claiming full support.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-lab [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<task description> [--mode setup|eval|auto] [--parent <slug>] [--ref <similar-model-path>] [--qa quick|light|standard|thorough|adversarial] [--report] [--from spec|scaffold|run|eval|summary]`.

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
