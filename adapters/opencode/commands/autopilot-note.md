---
description: "Run the portable autopilot-note capability through the OpenCode adapter. Meaning: Route and note artifacts, producing digests."
---

Use the OpenCode adapter realization of portable capability `autopilot-note`.
This is adapter-owned output generated from `capabilities/autopilot-note.md`, not a runtime-specific command copy.

1. Read `capabilities/autopilot-note.md` for the runtime-neutral contract.
2. Run `adapters/opencode/bin/preflight.sh capability-info autopilot-note` and
   obey `instruction-only`, `tool-contract`, or `unsupported` status. For
   `tool-contract`, report the named `tool_contract`, run any
   `tool_contract_check`, and obey `runtime_surface` / `fallback` before
   claiming full support. For `unsupported`, stop or use the reported
   `fallback`.
3. Before edits, run `adapters/opencode/bin/preflight.sh write <file> [session-id]`.
4. Before spec-changing work, run
   `adapters/opencode/bin/preflight.sh capability autopilot-note [cwd] [session-id]`.
5. If the command receives arguments, map them to the portable argument shape:
   `[--scope today|yesterday|since <date>|all] [--from <artifact-path>] [--target <notes-root>] [--dry-run] [--intensity direct|quick|standard|strong|thorough|adversarial] [--digest-only] [--source <list>]`.

Portable contract excerpt:

- Invocation semantics: Autopilot-family periodic and on-demand artifact-routing pipeline using a two-layer model. Scan `<artifact-root>/{research,documents,plans,analysis_project}/`, `experiments/`, and `git log` for changes since the previous run. Convert each item into a **Layer 2 artifact note** at `<agent-notes-root>/_layer2/notes/<id>.md` and link it to the user's **Layer 1** cards under `<agent-notes-root>/cards/`. Four-way routing creates an L2 row automatically; links `card_id` to an existing L1 card with `routing_status: confirmed`, confidence, and reason; links `backbone_ids`/`task_ids` to the L2 catalog, creating entries when necessary; or parks an unmatched ambient `card_id: null` note with `routing_status: confirmed`. `routing_confidence` is an ordering and emphasis signal. Append daily digests to `<agent-notes-root>/digests/YYYY-MM-DD.md`. Processing is idempotent. Routine cron uses `quick` intensity and its derived rigor; use `standard+` for weekly bulk consolidation, Notion migration, or pre-handoff cleanup. Source 6 is the gated Phase 3 Notion mirror. When a source artifact carries a `report_manifest.json`, the note preserves its bundle metadata as a `report_bundle` block — classification, shared title, `primary_representation_id`, and each representation's `id`, `format`, `roles`, resolved path, and hash — instead of flattening the outputs into an unlabeled pair. `source` remains the single-path idempotency key. Publication is part of this capability contract: Stages A–F culminate in the deterministic Stage G `publish cycle`. Skipped or failed publication is surfaced without invalidating Markdown already written; mechanics live in the process contract. Adapters may expose this capability through native commands, skill files, prompt instructions, or explicit wrappers. The adapter must report unsupported runtime mechanics instead of silently treating another runtime's native file format as portable.


User arguments from OpenCode: `$ARGUMENTS`

Do not use non-OpenCode command files or runtime-specific slash-command files
as OpenCode-native command source.
