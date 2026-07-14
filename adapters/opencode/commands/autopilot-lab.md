---
description: "Run the portable autopilot-lab capability through the OpenCode adapter. Meaning: Rapid experiment prototyping around training setup and checkpoint evaluation/analysis."
---

Use the OpenCode adapter realization of portable capability `autopilot-lab`.
This is adapter-owned output generated from `capabilities/autopilot-lab.md`, not a runtime-specific command copy.

1. Read `capabilities/autopilot-lab.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-lab` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract`, run any
   `tool_contract_check`, and obey `runtime_surface` / `fallback` before
   claiming full support. For `unsupported`, stop or use the reported
   `fallback`.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-lab [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `<task description> [--mode setup|eval|auto] [--parent <slug>] [--ref <similar-model-path>] [--intensity direct|quick|standard|strong|thorough|adversarial] [--report] [--from spec|scaffold|run|eval|summary]`.

Portable contract excerpt:

- Invocation semantics: Rapid experiment prototype entrypoint. The user runs heavy training; the lab supports the work before and after it. `setup` prepares an experiment from spec to scaffold and run commands. `eval` analyzes a trained checkpoint through metrics, ablations, paper comparisons, plots, and optional formal reports (prose routes to autopilot-draft; audio/media uses playback HTML). Extension cases use `--parent <slug>` rather than new modes: fine-tuning creates a setup config branch, and reevaluation uses eval. Enforce per-experiment folders, a STORY narrative, and an append-only `_RUNLOG` timeline with pending/completed state and parent links to prevent overwrites and ad hoc loss. Automatically read `experiment_conventions.md` and `similar_models.md` from analyze-project, giving the user's existing layer, prefix, and config patterns priority. Graduate refinement or library work to autopilot-code. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


User arguments from OpenCode: `$ARGUMENTS`

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
