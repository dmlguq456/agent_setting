---
name: autopilot-spec
description: "Use when needed: Create or update requirements/blueprints while keeping `prd.md` as the only spec-change path."
metadata:
  portable_source: capabilities/autopilot-spec.md
  adapter: opencode
---

# autopilot-spec

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-spec.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-spec`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-spec.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-spec`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-spec`
- Supported modes: `app, library, api, cli, research, update`
- Argument shape: `<task description> [--mode auto|app|library|api|cli|research|update (comma-separated for multiple)] [--intensity direct|quick|standard|strong|thorough|adversarial] [--user-refine]`
- Portable meaning: Create or update requirements/blueprints while keeping `prd.md` as the only spec-change path.

## Portable Contract

- Invocation semantics: General entrypoint for creating and updating requirements and blueprints: new intent, cleanup/public-release preparation for existing code, and iteration of an existing spec through `prd.md`. It supports app, library, API, CLI, and research modes; multiple modes; auto detection; and update mode. Update mode edits the existing `prd.md`, the canonical path for every spec change, and automatically snapshots the previous version. PRDs contain common sections plus independent per-mode sections. Automatically cite autopilot-research and analyze-project outputs. This is the blueprint counterpart to analyze-project's new-intent analysis. Actual code work belongs to autopilot-code, which detects `spec/` context automatically. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-spec [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
