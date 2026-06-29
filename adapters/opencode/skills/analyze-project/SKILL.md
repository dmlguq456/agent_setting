---
name: analyze-project
description: "Use when the user requests analyze-project: 사전 분석. 코드·논문·문서 primary 자료를 구조화해 다운스트림 입력으로 만든다. Read the portable capability spec and run the OpenCode preflight wrapper before claiming support."
metadata:
  portable_source: capabilities/analyze-project.md
  adapter: opencode
---

# analyze-project

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/analyze-project.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info analyze-project`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/analyze-project.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info analyze-project`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `analyze-project`
- Supported modes: `code, paper, doc`
- Argument shape: `[--mode code|paper|doc] [<scope/target/input-folder>] [--skip-qa]`
- Portable meaning: 사전 분석. 코드·논문·문서 primary 자료를 구조화해 다운스트림 입력으로 만든다.

## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability analyze-project [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
