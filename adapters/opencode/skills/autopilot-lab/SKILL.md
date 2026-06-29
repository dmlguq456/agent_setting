---
name: autopilot-lab
description: "Use when the user requests autopilot-lab: 빠른 실험 prototype. 학습 세팅과 ckpt 평가·분석 앞뒤를 돕는다. Read the portable capability spec and run the OpenCode preflight wrapper before claiming support."
metadata:
  portable_source: capabilities/autopilot-lab.md
  adapter: opencode
---

# autopilot-lab

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/autopilot-lab.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-lab`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-lab.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-lab`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the missing tool contract before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `autopilot-lab`
- Supported modes: `setup, eval`
- Argument shape: `<task description> [--mode setup|eval|auto] [--parent <slug>] [--ref <similar-model-path>] [--qa quick|light|standard|thorough|adversarial] [--report] [--from spec|scaffold|run|eval|summary]`
- Portable meaning: 빠른 실험 prototype. 학습 세팅과 ckpt 평가·분석 앞뒤를 돕는다.

## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-lab [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use `skills/autopilot-lab/SKILL.md` or
`adapters/claude/skills/autopilot-lab/SKILL.md` as OpenCode-native source. Those
files are Claude compatibility/reference surfaces.
