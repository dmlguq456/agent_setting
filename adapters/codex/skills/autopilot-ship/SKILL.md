---
name: autopilot-ship
description: "Use when the user requests autopilot-ship: 앱 배포·출시 준비. build/deploy setup과 ship checklist를 만든다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# autopilot-ship

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a Claude Skill copy.

## Source

- Portable source: `capabilities/autopilot-ship.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info autopilot-ship`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/autopilot-ship.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info autopilot-ship`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract` and run any `tool_contract_check` before claiming full support.
   - `unsupported`: stop or use the documented fallback.

## Shape

- Identifier: `autopilot-ship`
- Supported modes: `none`
- Argument shape: `<task description (선택)> [--qa quick|light|standard|thorough]`
- Portable meaning: 앱 배포·출시 준비. build/deploy setup과 ship checklist를 만든다.

## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability autopilot-ship [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or Claude adapter Skill files as
Codex-native source. Those files are compatibility/reference surfaces only.
