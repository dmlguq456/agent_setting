---
description: "Run the portable draft-strategy capability through the OpenCode adapter. Meaning: 문서 전략 초안 작성. 자료 기반으로 writing plan을 만든다."
---

Use the OpenCode adapter realization of portable capability `draft-strategy`.
This is adapter-owned output generated from `capabilities/draft-strategy.md`, not a runtime-specific command copy.

1. Read `capabilities/draft-strategy.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info draft-strategy` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract`, run any
   `tool_contract_check`, and obey `runtime_surface` / `fallback` before
   claiming full support. For `unsupported`, stop or use the reported
   `fallback`.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability draft-strategy [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<mode> --inputs <comma-separated-paths> --output <artifact-dir> [--intensity direct|quick|standard|strong|thorough|adversarial] <task description>`.

Portable contract excerpt:

- Invocation semantics: Create an initial document strategy. Internal mode enum 6종 (rebuttal / paper / review / report / proposal / presentation) — autopilot-draft 의 form-first 3-mode (paper / presentation / doc) 에서 doc intent (자연어 키워드 → rebuttal-response / review / report / proposal / generic) 가 본 sub-skill 의 직접 mode 라벨로 변환되어 전달됨. 직접 호출 시는 사용자가 첫 인자로 6-mode 중 하나를 명시. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


User arguments from OpenCode: `$ARGUMENTS`

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
