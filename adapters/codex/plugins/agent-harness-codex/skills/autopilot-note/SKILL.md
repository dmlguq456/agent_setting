---
name: autopilot-note
description: "Use when needed: Route and note artifacts, producing digests and triage proposals."
---

# autopilot-note

This is a Codex-native Skill projection generated from the portable capability
contract. It is adapter-owned output, not a legacy compatibility Skill copy.

## Source

- Portable source: `capabilities/autopilot-note.md`
- Runtime check: `adapters/codex/bin/preflight.sh capability-info autopilot-note`
- Bootstrap: `adapters/codex/AGENTS.md`

## Use

1. Read `capabilities/autopilot-note.md` for the runtime-neutral contract.
2. Run `adapters/codex/bin/preflight.sh capability-info autopilot-note`.
3. Obey the reported status:
   - `instruction-only`: use this Skill as Codex guidance plus explicit preflight guards.
   - `tool-contract`: report the named `tool_contract`, run any `tool_contract_check`, and obey `runtime_surface` / `fallback` before claiming full support.
   - `unsupported`: stop or use the reported `fallback`.

## Shape

- Identifier: `autopilot-note`
- Supported modes: `none`
- Argument shape: `[--scope today|yesterday|since <date>|all] [--target <notes-root>] [--dry-run] [--intensity direct|quick|standard|strong|thorough|adversarial] [--digest-only] [--triage-only] [--source <list>]`
- Portable meaning: Route and note artifacts, producing digests and triage proposals.

## Portable Contract

- Invocation semantics: Autopilot-family periodic and on-demand artifact-routing pipeline using a two-layer model. Scan `<artifact-root>/{research,documents,plans,analysis_project}/`, `experiments/`, and `git log` for changes since the previous run. Convert each item into a **Layer 2 artifact note** at `<agent-notes-root>/_layer2/notes/<id>.md` and link it to the user's **Layer 1** cards under `<agent-notes-root>/cards/`. Five-way routing creates an L2 row automatically; proposes linking `card_id` to an existing L1 card as `routing_status: inbox` with confidence/reason (unattended cron never confirms; the user confirms in `/triage`); links `backbone_ids`/`task_ids` to the L2 catalog, creating entries when necessary; proposes a new L1 card during triage; or parks an ambient `card_id: null` note as the fallback. Append daily digests to `<agent-notes-root>/digests/YYYY-MM-DD.md`. Processing is idempotent. Routine cron uses `quick` intensity and its derived rigor; use `standard+` for weekly bulk consolidation, Notion migration, or pre-handoff cleanup. Source 6 is the gated Phase 3 Notion mirror. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.



## Projected Portable Details

## Artifact Ownership

Use the shared artifact root rule: prefer `.agent_reports/`; use legacy `.claude_reports/` only when it already exists and `.agent_reports/` does not. Capability-specific output placement follows `core/CONVENTIONS.md` section 5 until this spec is expanded with a stricter per-capability artifact map.

The capability has two output surfaces: `<artifact-root>/notes/<date>/` for the
run log/reviewer artifacts, and `<agent-notes-root>/` for the cross-project board
state. The latter is mutable continuity state, not harness source. Adapter
defaults for resolving `<agent-notes-root>` belong in adapter-native files.

## Role Requirements

Use portable role names from `roles/README.md` and `core/CONVENTIONS.md`. Concrete model names, subagent frontmatter, and runtime-specific tool lists belong in adapter files.

Pipeline intensity follows `core/CONVENTIONS.md §1`: `direct` has no plan stage or durable plan artifact; `quick` is a depth-1 one-shot worker with its inline micro-plan plus plan-check-lite; `standard+` uses the capability's durable work-cycle plan when applicable. `plan-check` is required for every non-`direct` graph, but independent QA is not repeated after every stage by default. Verification rigor for plan-check, selected independent reviews, and final verify is derived from intensity; it does not name a model or introduce a separate stage graph.

## Guard Requirements

Adapters must preserve the portable invariants relevant to this capability:

- resolve artifact root through `utilities/artifact-root.sh` or equivalent logic;
- enforce git/worktree safety before edits;
- enforce artifact ordering before new durable artifacts;
- enforce spec-read gating when this capability changes spec-backed code or specs;
- use DB memory paths, not runtime-native memory files.

## Routing Boundary

`autopilot-note` registers and routes finished artifacts. Under
`WORKFLOW §0.2` it is always a secondary, final step and never substitutes for
the execution capability that produces the results it routes.


## Required Guards

- Before edits: `adapters/codex/bin/preflight.sh write <file> [session-id]`
- Before capability routing/spec-changing work: `adapters/codex/bin/preflight.sh route autopilot-note [cwd] [session-id]`
- Before spec-changing work: `adapters/codex/bin/preflight.sh capability autopilot-note [cwd] [session-id]`
- After actually reading a spec PRD: `adapters/codex/bin/preflight.sh read <prd.md> [session-id]`
- For workflow state: `adapters/codex/bin/preflight.sh status [cwd] [session-id]`, `adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]`, and `adapters/codex/bin/preflight.sh mode [cwd] [session-id]`

Do not use legacy compatibility Skill files or non-native adapter Skill files
as Codex-native source. Those files are compatibility/reference surfaces only.
