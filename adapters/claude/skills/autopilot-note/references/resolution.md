## Source Resolution (new and changed detection in Stage A)

Use `last_run_ts` from `<artifact-root>/notes/.last_run.yaml`:

1. **`pipeline_state.yaml`:** every autopilot artifact has `last_updated`; compare it with `last_run_ts`.
2. **mtime fallback:** treat a `<artifact-root>/**/pipeline_summary.md` whose mtime is newer than `last_run_ts` as changed.
3. **Git log:** run `git log --since=<scope> --name-only --pretty=oneline` to collect changed commits and file lists.
4. **Notion source, Phase 3:** use `~/.agent_reports/notion_mirror/<date>/` (legacy `~/.claude_reports/notion_mirror/<date>/`). Skip it through Phase 2 and enable it only with `--source notion`.

Persist `last_run_ts` in `<artifact-root>/notes/.last_run.yaml`. It is this skill's session state and one layer of idempotency.

## Target Resolution — matching both layers (core of Stage C)

For each artifact, decide which L1 card and which L2 catalogs it should attach to.

> ✅ **Routing policy (2026-07-28):** The agent confirms every routing result and records `routing_status: confirmed`. Keep `routing_confidence` only as an ordering and emphasis signal so low-confidence items can be corrected on the board note screen. The 2026-06-10 automatic-confirmation prohibition is historical and was withdrawn when the review surface was retired on 2026-07-28.

### Resolve `card_id` (→ Layer 1) in three passes

#### Pass 1 — deterministic frontmatter

- When an autopilot-code or autopilot-lab `pipeline_state.yaml` specifies `task_card`, use that **task card** stem.
- When artifact frontmatter specifies `project: <name>`, resolve it to a **task card** under that project by matching `kind: task` and `project` in `<target>/cards/`. Under v44, a project card itself is never a `card_id` target. If no task matches, continue to ambient routing instead of linking directly to the project.

#### Pass 2 — fuzzy keyword matching

- Fuzzy-match artifact keywords against the `title` and body headings of **`kind: task`** files under `<target>/cards/**.md`.
- **Task only (PRD v44 invariant).** A `card_id` always targets a task card; direct matching to `kind: project` is forbidden because a project is a derived label from the task's `project` field, not an attachment target. When no task matches, do not force the artifact onto a project. `secondary_card_ids` follows the same task-only rule. The v43 project-fallback behavior is retired.
- Confidence: at **≥0.7**, set `card_id` and record high `routing_confidence`; at **0.4–0.7**, set `card_id` and record medium confidence; below **0.4**, continue to Pass 3. Always record `routing_reason` and `matched_signals` for correction on the board note screen.
- **Multiple-card links (worklog-board PRD v32):** select one primary card and zero or more secondary cards. The highest-confidence match remains `card_id`. Put other meaningful task matches in `secondary_card_ids: [<id>, …]`; DB ingestion stores them in the `l2.note_cards` M:N relation. Reports, home widgets, and digests continue to use the single primary card.

#### Pass 3 — ambient

- When nothing matches, use `card_id: null`, `routing_status: confirmed`, and low `routing_confidence`; users may organize the ambient note later.
- Do not create a Layer 1 card automatically. Leave unmatched artifacts as ambient notes with `card_id: null`; card creation remains a separate user action.

### Resolve `backbone_ids`, `task_ids`, and `paper_id` (→ Layer 2)

- Match architecture and technique keywords in the artifact body, such as SR-CorrNet, TF-Restormer, attention, separation, and enhancement, to slugs under `<target>/_layer2/backbones/` and `tasks/`.
- When no entry matches and the artifact signals an emerging reusable asset, such as reuse, lightweight variants, a new backbone, architecture, or baseline, create and log the appropriate backbone, task, or paper catalog entry using its README schema.
- For paper artifacts from autopilot-draft or research paper IDs, resolve a `papers/` slug and emerge one when absent.

### Infer `intent` and `work_status`

- Recommended `intent` values are `원천기술` for horizontally reusable assets, `상용화` for a product or API, `논문` for external publication, `수탁` for external delivery, and `운영` for lab operations or administration. Infer the default from artifact type and keywords.
- Recommended `work_status` values are `설계` for blueprints, `탐색` for ideas and exploration, `검증` for experiments, `진행중` for active work, `통합` for integration or library work, `출시` for release or submission, `완료` for finished work, and `null` when unknown.
- **Schema tolerance:** `intent` and `work_status` are `z.string()` in `NoteSchema`, not enums. Prefer the canonical values for consistent UI pickers and badges, but never silently drop a new vocabulary value.
