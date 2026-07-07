---
name: design-handoff
description: "Use for design-handoff: 디자인 결과를 개발 handoff용 자산·스펙으로 정리한다."
metadata:
  portable_source: capabilities/design-handoff.md
  adapter: opencode
---

# design-handoff

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/design-handoff.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info design-handoff`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/design-handoff.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info design-handoff`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `design-handoff`
- Supported modes: `none`
- Argument shape: `<design path or app path>`
- Portable meaning: 디자인 결과를 개발 handoff용 자산·스펙으로 정리한다.

## Portable Contract

- Invocation semantics: Final handoff — consolidates design artifacts into a single handoff.md that frontend devs (or autopilot-spec build phase) can use directly. Lists components, token paths, import paths, reproduction guide. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability design-handoff [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
