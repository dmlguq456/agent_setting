# autopilot-note

Accumulation and routing entrypoint. Read artifacts from other capabilities, convert each trackable artifact into a Layer 2 note row, and propose links to user-owned Layer 1 cards. This file defines routing, invocation forms, and constraints; load a reference only when its detailed data model or procedure is needed.

> **Output convention**: Store run logs, digest staging, and reviewer logs under `<artifact-root>/notes/{date}/` using the CONVENTIONS §5 (`<agent-home>/core/CONVENTIONS.md#5-skill-output-convention--t1t2t3`) 3-tier layout. Durable Layer 2 notes live at `<target>/_layer2/notes/<id>.md`; user-owned Layer 1 cards live at `<target>/cards/**.md`. These stores are separate from the run artifact.

## Invocation

Route here when the user asks to collect recent artifacts, update the note layer, regenerate a digest, inspect triage, or summarize changes since a date. Scheduled callers may invoke the same idempotent interface; scheduler configuration is outside this skill.

- Manual or scheduled default: `--scope today`
- Multi-day catch-up: `--scope since <date> --intensity standard`
- Initial historical import: `--scope all`
- Resolve `<target>` from explicit `--target` first, then the configured `<agent-notes-root>`. If neither exists, report the missing configuration instead of guessing a personal path.

Use a deterministic note ID derived from date plus source-path hash. Reprocessing the same source updates or skips the same note rather than creating a duplicate.

## Invocation Forms

| Form | Behavior |
|---|---|
| `autopilot-note` | Run Stages A-F with `--scope today` |
| `--scope yesterday` | Process changes from the previous local midnight interval |
| `--scope since 2026-05-20` | Process changes since the explicit date |
| `--scope all` | Scan all supported sources for an initial historical import |
| `--dry-run` | Run Stages A-C, write nothing, and show the routing plan |
| `--digest-only` | Run Stage E against existing notes |
| `--triage-only` | Run only the Stage D proposal path for new Layer 1 cards or task links |
| `--source plans,experiment` | Restrict scanning to the listed source families |
| `--target <notes-root>` | Override the configured notes root and derive `cards/`, `_layer2/`, `_triage/`, and `digests/` beneath it |
| `--feedback` | Process pending `_feedback/` items through the lightweight bidirectional feedback flow rather than Stages A-F |

## Routing Rules

| # | Destination | Trigger | Action | Ownership |
|---|---|---|---|---|
| 1 | Layer 2 note row | Every trackable artifact | Create or update `_layer2/notes/<id>.md` with frontmatter and a readable summary | Automatic |
| 2 | Existing Layer 1 card link | Primary or secondary match | Set proposed `card_id`, `routing_status: inbox`, `routing_confidence`, and `routing_reason` | Automatic proposal |
| 3 | Layer 2 catalogs | Architecture, task, paper, or emergence evidence | Set `backbone_ids`, `task_ids`, or `paper_id`; create a lightweight catalog entry when needed | Automatic |
| 4 | New Layer 1 card or existing-task proposal | No task match but a coherent new work unit exists, or an existing task matches strongly | Write a grouped `_triage/<id>.md` `new-card` or `link-note` proposal with `source_note_ids` | User-confirmed triage; never automatic card creation |
| 5 | Ambient inbox note | No confident destination | Keep `card_id: null` and `routing_status: inbox` | Automatic |

Layer 2 writes and links are proposals while they remain `routing_status: inbox`. The worklog board's triage flow owns confirmation and any creation of Layer 1 cards.

## Language Rule

Follow an explicit artifact or audience language when provided. Otherwise, write note bodies, digests, triage proposals, and chat reports in the conversation language according to `<agent-home>/roles/response-policy.md`. Keep frontmatter IDs, slugs, and filenames lowercase English with hyphens, such as `note-20260609-a1b2c3`, `sr-corrnet`, `sep`, or `tf-restormer-icml2026`.

## Constraints

- **Layer 1 is user-owned**: never modify `cards/**.md`. Read cards for matching and write only `_triage/` proposals.
- **One artifact, one Layer 2 note**: summarize the artifact for reading; do not dump the full source.
- **Keep catalog emergence lightweight**: create small backbone, task, or paper entries when justified; route large restructuring elsewhere.
- **Remain idempotent**: enforce source-to-ID stability through the note ID, frontmatter `source`, and `.last_run.yaml` checks.
- **Keep source artifacts read-only**: never modify `<artifact-root>/{research,documents,plans,analysis_project}/` or `experiments/`.
- **Require triage for new Layer 1 cards**: the user or worklog-board UI performs confirmed creation.
- **Keep ambient notes temporary**: retain unmatched notes in the inbox for later user promotion.
- **Do not perform structural source edits**: route artifact changes through `autopilot-refine` or the owning capability.

## Reference Index

| File | When to load (mandatory) | Content |
|---|---|---|
| `data-model.md` | When reading or writing model contracts | Two-layer model, note-row schema, and position in the autopilot family |
| `scope-qa-usage.md` | When resolving sources, outputs, rigor, boundaries, or post-run checks | Six input families, output locations, intensity-derived rigor, examples, when-not-to-use guidance, and checklist |
| `feedback-mode.md` | When processing `--feedback` | Feedback inputs, proposal/UI-code routing, risk branches, completion state, and boundaries |
| `resolution.md` | When running Stage A or C matching | Source-change detection and target resolution for cards, backbones, tasks, papers, intent, and work status |
| `process.md` | When running Stages A-F (required) | Scan, analyze, match, verify, apply, `editorial/polish` unit polish, digest, and report |
