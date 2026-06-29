---
name: autopilot-spec
description: "Use when the user requests autopilot-spec: 요구사항·청사진 작성·갱신. `prd.md`를 spec 변경의 단일 경로로 유지한다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# autopilot-spec

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/autopilot-spec.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info autopilot-spec`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/autopilot-spec.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info autopilot-spec`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `autopilot-spec`
- Supported modes: `app, library, api, cli, research, update`
- Argument shape: `<task description> [--mode auto|app|library|api|cli|research|update (콤마로 다중)] [--qa quick|light|standard|thorough] [--user-refine]`
- Portable meaning: 요구사항·청사진 작성·갱신. `prd.md`를 spec 변경의 단일 경로로 유지한다.

## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability autopilot-spec [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
