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

> 📐 **Blueprint context (agent-note PRD §54.10, 2026-07-30):** before deciding Pass 2 matches or Pass 3 creation, read the target repo's blueprint summary block — the `<!-- BLUEPRINT-SUMMARY:BEGIN -->` … `<!-- BLUEPRINT-SUMMARY:END -->` markers at the top of `<artifact-root>/spec/prd.md`, when present — and use it as matching and creation context: the blueprint states which work streams and tasks the project expects, so it grounds both "which existing task does this note belong to" and "what new task is worth creating". A missing block changes nothing; never fall back to token matching as a substitute for reading it.

### Resolve `card_id` (→ Layer 1) in three passes

#### Pass 1 — deterministic frontmatter

- When an autopilot-code or autopilot-lab `pipeline_state.yaml` specifies `task_card`, use that **task card** stem.
- When artifact frontmatter specifies `project: <name>`, resolve it to a **task card** under that project by matching `kind: task` and `project` in `<target>/cards/`. Under v44, a project card itself is never a `card_id` target. If no task matches, continue to ambient routing instead of linking directly to the project.

#### Pass 2 — fuzzy keyword matching

- Fuzzy-match artifact keywords against the `title` and body headings of **`kind: task`** files under `<target>/cards/**.md`.
- **Task only (PRD v44 invariant; reaffirmed and write-layer-enforced by agent-note PRD §54, v125).** A `card_id` always targets a task card; direct matching to `kind: project` is forbidden because a project is a derived label from the task's `project` field, not an attachment target. When no task matches, do not force the artifact onto a project — the app write layer now rejects project-card note routing with 422 on every path. The v43 project-fallback behavior is retired.
- Confidence: at **≥0.7**, set `card_id` and record high `routing_confidence`; at **0.4–0.7**, set `card_id` and record medium confidence; below **0.4**, continue to Pass 3. Always record `routing_reason` and `matched_signals` for correction on the board note screen.
- **Single-card link (agent-note PRD §54, v125 — supersedes the v32 multiple-card rule):** emit exactly one `card_id` (the highest-confidence task match) and do not emit `secondary_card_ids`. The app write layer rejects new note secondary links (422) and the `l2.note_cards` relation is dormant (zero rows in production as of 2026-07-30). Record lower-confidence candidates in `routing_reason`/`matched_signals`, not as extra links.

#### Pass 3 — ambient

- When nothing matches and no owning project is identifiable, use `card_id: null`, `routing_status: confirmed`, and low `routing_confidence`; users may organize the ambient note later.
- **Gated task creation (agent-note PRD §54.4 ③, v125 — supersedes the earlier "card creation remains a separate user action" rule):** when the owning project is clear but no existing task fits, create a **task card** and route to it instead of leaving the note ambient or forcing it onto the project. All gates must hold: ⓐ the note content matches no existing task under the owning project — a semantic judgment on content (use the blueprint context above), never token matching; ⓑ bundle first — route N related notes to one new task, never one card per note; ⓒ retrospective records may be created directly with `process: done`; ⓓ the new task must carry the owning project's `project_id`; ⓔ never create a project card; ⓕ list every created card in the run report so the user can audit it — silent card growth is forbidden.

### Resolve `backbone_ids`, `task_ids`, and `paper_id` (→ Layer 2)

- Match architecture and technique keywords in the artifact body, such as SR-CorrNet, TF-Restormer, attention, separation, and enhancement, to slugs under `<target>/_layer2/backbones/` and `tasks/`.
- When no entry matches and the artifact signals an emerging reusable asset, such as reuse, lightweight variants, a new backbone, architecture, or baseline, create and log the appropriate backbone, task, or paper catalog entry using its README schema.
- For paper artifacts from autopilot-draft or research paper IDs, resolve a `papers/` slug and emerge one when absent.

### Infer `intent` and `work_status`

- Recommended `intent` values are `원천기술` for horizontally reusable assets, `상용화` for a product or API, `논문` for external publication, `수탁` for external delivery, and `운영` for lab operations or administration. Infer the default from artifact type and keywords.
- Recommended `work_status` values are `설계` for blueprints, `탐색` for ideas and exploration, `검증` for experiments, `진행중` for active work, `통합` for integration or library work, `출시` for release or submission, `완료` for finished work, and `null` when unknown.
- **Schema tolerance:** `intent` and `work_status` are `z.string()` in `NoteSchema`, not enums. Prefer the canonical values for consistent UI pickers and badges, but never silently drop a new vocabulary value.
