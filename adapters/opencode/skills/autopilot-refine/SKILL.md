---
name: autopilot-refine
description: "Use when needed: Correct and update existing document/research artifacts while preserving snapshots and change history."
metadata:
  portable_source: capabilities/autopilot-refine.md
  adapter: opencode
---

# autopilot-refine

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-refine.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-refine`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-refine.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-refine`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-refine`
- Supported modes: `none`
- Argument shape: `"<prompt>" [--intensity direct|quick|standard|strong|thorough|adversarial] [--review-only | --memo <file>] [--confirm] [--no-fact-check] [--no-style-audit]`
- Portable meaning: Correct and update existing document/research artifacts while preserving snapshots and change history.

## Portable Contract

- Invocation semantics: Autopilot family — post-creation iteration pipeline for research and doc artifacts (NOT code). Prompt-driven: target artifact identified via prompt fuzzy match against `<artifact-root>/{research,documents}/*`, then auto-discovers the artifact's file structure, plans edits, shows a diff preview in chat, and on user confirm applies edits with versioning + integrated history logging in `pipeline_summary.md` (single source of truth — no separate CHANGELOG). Default intensity is `quick` (1-pass review, fastest path); escalate intensity to `standard|strong|thorough|adversarial` for multi-round review, fact-check, or external adversary work. Optional `--memo <file>` falls back to file-memo style for deferred reviews. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-refine [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
