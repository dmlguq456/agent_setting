---
name: code-test
description: "Use for code-test: 구현 결과를 단계별로 검증하고 evidence를 기록한다."
metadata:
  portable_source: capabilities/code-test.md
  adapter: opencode
---

# code-test

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/code-test.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info code-test`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/code-test.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info code-test`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `code-test`
- Supported modes: `none`
- Argument shape: `<plan name, path, or test scope> [--qa quick|light|standard|thorough|adversarial]`
- Portable meaning: 구현 결과를 단계별로 검증하고 evidence를 기록한다.

## Portable Contract

- Invocation semantics: Run graduated verification after `code-execute` or on demand to verify code correctness. `--qa` scales final verification and test-adequacy review; it does not force a separate parallel QA loop by itself. The capability resolves a plan path, changed-file list, or test scope, runs the applicable test levels, stops on the first failing level, and records durable evidence before reporting a verdict. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability code-test [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
