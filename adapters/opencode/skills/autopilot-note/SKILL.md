---
name: autopilot-note
description: "Use for autopilot-note: Route and note artifacts, producing digests and triage proposals."
metadata:
  portable_source: capabilities/autopilot-note.md
  adapter: opencode
---

# autopilot-note

This is an OpenCode-native Skill projection generated from the portable
capability contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-note.md`
- Runtime check: `adapters/opencode/bin/preflight.sh capability-info autopilot-note`
- Bootstrap: `adapters/opencode/AGENTS.md`

## Use

1. Read `capabilities/autopilot-note.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-note`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as OpenCode guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-note`
- Supported modes: `none`
- Argument shape: `[--scope today|yesterday|since <date>|all] [--target <notes-root>] [--dry-run] [--intensity direct|quick|standard|strong|thorough|adversarial] [--digest-only] [--triage-only] [--source <list>]`
- Portable meaning: Route and note artifacts, producing digests and triage proposals.

## Portable Contract

- Invocation semantics: Autopilot-family periodic and on-demand artifact-routing pipeline using a two-layer model. Scan `<artifact-root>/{research,documents,plans,analysis_project}/`, `experiments/`, and `git log` for changes since the previous run. Convert each item into a **Layer 2 artifact note** at `<agent-notes-root>/_layer2/notes/<id>.md` and link it to the user's **Layer 1** cards under `<agent-notes-root>/cards/`. Five-way routing creates an L2 row automatically; proposes linking `card_id` to an existing L1 card as `routing_status: inbox` with confidence/reason (unattended cron never confirms; the user confirms in `/triage`); links `backbone_ids`/`task_ids` to the L2 catalog, creating entries when necessary; proposes a new L1 card during triage; or parks an ambient `card_id: null` note as the fallback. Append daily digests to `<agent-notes-root>/digests/YYYY-MM-DD.md`. Processing is idempotent. Routine cron uses `quick` intensity and its derived rigor; use `standard+` for weekly bulk consolidation, Notion migration, or pre-handoff cleanup. Source 6 is the gated Phase 3 Notion mirror. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


## Required Guards

- Before edits: `adapters/opencode/bin/preflight.sh write <file> [session-id]`
- Before spec-changing work: `adapters/opencode/bin/preflight.sh capability autopilot-note [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as OpenCode-native source. Those files are compatibility/reference surfaces only.
