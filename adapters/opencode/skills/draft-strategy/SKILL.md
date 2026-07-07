---
name: draft-strategy
description: "Use for draft-strategy: 문서 전략 초안 작성. 자료 기반으로 writing plan을 만든다."
metadata:
  portable_source: capabilities/draft-strategy.md
  adapter: opencode
---

# draft-strategy

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/draft-strategy.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info draft-strategy`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/draft-strategy.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info draft-strategy`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `draft-strategy`
- Supported modes: `rebuttal, paper, review, report, proposal, presentation`
- Argument shape: `<mode> --inputs <comma-separated-paths> --output <artifact-dir> [--qa quick|light|standard|thorough|adversarial] <task description>`
- Portable meaning: 문서 전략 초안 작성. 자료 기반으로 writing plan을 만든다.

## Portable Contract

- Invocation semantics: Create an initial document strategy. Internal mode enum 6종 (rebuttal / paper / review / report / proposal / presentation) — autopilot-draft 의 form-first 3-mode (paper / presentation / doc) 에서 doc intent (자연어 키워드 → rebuttal-response / review / report / proposal / generic) 가 본 sub-skill 의 직접 mode 라벨로 변환되어 전달됨. 직접 호출 시는 사용자가 첫 인자로 6-mode 중 하나를 명시. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability draft-strategy [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
