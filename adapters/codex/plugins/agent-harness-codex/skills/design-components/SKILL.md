---
name: design-components
description: "Use when the user requests design-components: UI component/mockup 구현과 preview artifact를 만든다. Read the portable capability spec and run the Codex preflight wrapper before claiming support."
---

# design-components

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/design-components.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info design-components`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/design-components.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info design-components`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `design-components`
- Supported modes: `none`
- Argument shape: `<design path or app path>`
- Portable meaning: UI component/mockup 구현과 preview artifact를 만든다.

## Portable Contract

- Invocation semantics: Component / visual asset creation — invokes 디자인팀 maker mode. Produces shadcn/Tailwind components (ui), composed full-screen pages (webapp), slide visual guides (slide), SVG icons (icon), or mermaid/direct-SVG/excalidraw diagrams (diagram). Every output is rendered and visually self-verified (render → Read → fix loop), and can be emitted as a self-contained single-file HTML preview artifact (--artifact standalone). Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability design-components [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]` and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
