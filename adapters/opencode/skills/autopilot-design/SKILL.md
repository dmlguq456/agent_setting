---
name: autopilot-design
description: "Use when the user requests autopilot-design: 시각 산출물 디자인 파이프. refs→tokens→components→review→handoff를 조율한다. Read the portable capability spec and run the OpenCode preflight wrapper before claiming support."
metadata:
  portable_source: capabilities/autopilot-design.md
  adapter: opencode
---

# autopilot-design

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-design.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-design`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-design.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-design`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-design`
- Supported modes: `none`
- Argument shape: `<design task or app path> [--scope ui|webapp|slide|icon|diagram|mixed] [--artifact standalone|project] [--from <phase>] [--intensity direct|quick|standard|strong|thorough|adversarial] [--qa quick|standard|thorough]`
- Portable meaning: 시각 산출물 디자인 파이프. refs→tokens→components→review→handoff를 조율한다.

## Portable Contract

- Invocation semantics: Unified design pipeline — orchestrates design-init → design-refs → design-tokens → design-components → design-review → design-handoff. For visual artifacts across UI/UX, slides, diagrams, icons, logos. Can be invoked standalone or auto-delegated from autopilot-spec Phase 2. Distinct from autopilot-draft (text-only documents) — autopilot-design handles visual deliverables. A runtime design harness must render every output for visual self-verification (preview/screenshot/console/eval_js/view_image where supported), run a separate-context verifier gate for console/layout breakage, apply shared design rules and reusable scaffold assets, and support PDF/PPTX/single-HTML bundle export where available. Outputs can be a self-contained single-file HTML preview viewable without any project stack. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-design [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
