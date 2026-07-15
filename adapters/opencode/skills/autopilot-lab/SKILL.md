---
name: autopilot-lab
description: "Use when needed: Rapid experiment prototyping around training setup and checkpoint evaluation/analysis."
metadata:
  portable_source: capabilities/autopilot-lab.md
  adapter: opencode
---

# autopilot-lab

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-lab.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-lab`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-lab.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-lab`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-lab`
- Supported modes: `setup, eval`
- Argument shape: `<task description> [--mode setup|eval|auto] [--parent <slug>] [--ref <similar-model-path>] [--intensity direct|quick|standard|strong|thorough|adversarial] [--report] [--from spec|scaffold|run|eval|summary]`
- Portable meaning: Rapid experiment prototyping around training setup and checkpoint evaluation/analysis.

## Portable Contract

- Invocation semantics: Rapid experiment prototype entrypoint. The user runs heavy training; the lab supports the work before and after it. `setup` prepares an experiment from spec to scaffold and run commands. `eval` analyzes a trained checkpoint through metrics, ablations, paper comparisons, plots, and optional formal reports (prose routes to autopilot-draft; audio/media uses playback HTML). Extension cases use `--parent <slug>` rather than new modes: fine-tuning creates a setup config branch, and reevaluation uses eval. Enforce per-experiment folders, a STORY narrative, and an append-only `_RUNLOG` timeline with pending/completed state and parent links to prevent overwrites and ad hoc loss. Automatically read `experiment_conventions.md` and `similar_models.md` from analyze-project, giving the user's existing layer, prefix, and config patterns priority. Graduate refinement or library work to autopilot-code. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-lab [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
