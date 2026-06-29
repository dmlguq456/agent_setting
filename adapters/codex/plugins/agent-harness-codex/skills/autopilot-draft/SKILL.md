---
name: autopilot-draft
description: "Use when the user requests autopilot-draft: 문서 초안 파이프. 전략·초안·검증·편집을 거쳐 적용용 문서 artifact를 만든다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# autopilot-draft

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-draft.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info autopilot-draft`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/autopilot-draft.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info autopilot-draft`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `autopilot-draft`
- Supported modes: `paper, presentation, doc`
- Argument shape: `<task description> [--mode paper|presentation|doc] [--qa quick|light|standard|thorough|adversarial] [--user-refine] [--no-clarify] [--from analyze|strategy|strategy-refine|draft|draft-refine|finalize]`
- Portable meaning: 문서 초안 파이프. 전략·초안·검증·편집을 거쳐 적용용 문서 artifact를 만든다.

## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability autopilot-draft [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
