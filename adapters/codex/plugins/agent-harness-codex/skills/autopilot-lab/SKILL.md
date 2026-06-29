---
name: autopilot-lab
description: "Use when the user requests autopilot-lab: 빠른 실험 prototype. 학습 세팅과 ckpt 평가·분석 앞뒤를 돕는다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# autopilot-lab

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-lab.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info autopilot-lab`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/autopilot-lab.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info autopilot-lab`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `autopilot-lab`
- Supported modes: `setup, eval`
- Argument shape: `<task description> [--mode setup|eval|auto] [--parent <slug>] [--ref <similar-model-path>] [--qa quick|light|standard|thorough|adversarial] [--report] [--from spec|scaffold|run|eval|summary]`
- Portable meaning: 빠른 실험 prototype. 학습 세팅과 ckpt 평가·분석 앞뒤를 돕는다.

## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability autopilot-lab [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
