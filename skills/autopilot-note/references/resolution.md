## Source Resolution (new and changed detection in Stage A)

Use `last_run_ts` from `<artifact-root>/notes/.last_run.yaml`:

1. **`pipeline_state.yaml`:** every autopilot artifact has `last_updated`; compare it with `last_run_ts`.
2. **mtime fallback:** treat a `<artifact-root>/**/pipeline_summary.md` whose mtime is newer than `last_run_ts` as changed.
3. **Git log:** run `git log --since=<scope> --name-only --pretty=oneline` to collect changed commits and file lists.
4. **Notion source, Phase 3:** use `~/.agent_reports/notion_mirror/<date>/` (legacy `~/.claude_reports/notion_mirror/<date>/`). Skip it through Phase 2 and enable it only with `--source notion`.

Persist `last_run_ts` in `<artifact-root>/notes/.last_run.yaml`. It is this skill's session state and one layer of idempotency.

## Target Resolution — matching both layers (core of Stage C)

For each artifact, decide which L1 card and which L2 catalogs it should attach to.

> ⚠️ **Unattended cron stages proposals and never auto-confirms (2026-06-10, PRD §13.C.1).** Routing from this skill is a proposal, not a final decision. For every unattended cron run, set `routing_status: inbox` regardless of confidence. Emit confidence through `routing_confidence` only for sorting and highlighting in `/triage` and home; it is not a switch that promotes records to `confirmed`. Only user confirmation in worklog-board `/triage` may approve or revise note routing. Automatic confirmation emptied the morning review queue and broke the daily agent-proposal → human-correction loop (observed state: confirmed 476, inbox 4). The only exception is a direct `/autopilot-note` invocation where the user explicitly requests immediate confirmation through `--confirm-high` or equivalent language; then confidence ≥0.7 may be confirmed.

### Resolve `card_id` (→ Layer 1) in three passes

#### Pass 1 — deterministic frontmatter

- When an autopilot-code or autopilot-lab `pipeline_state.yaml` specifies `task_card`, use that **task card** stem.
- When artifact frontmatter specifies `project: <name>`, resolve it to a **task card** under that project by matching `kind: task` and `project` in `<target>/cards/`. Under v44, a project card itself is never a `card_id` target. If no task matches, propose a new task instead of linking directly to the project.

#### Pass 2 — fuzzy keyword matching

- Fuzzy-match artifact keywords against the `title` and body headings of **`kind: task`** files under `<target>/cards/**.md`.
- **Task only (PRD v44 invariant).** Preserve the user's verbatim requirement: _"무조건 연결되는 task가 있어야 한다. 없으면 생성 제안. 노션이면 그냥 동명의 task 카드라도."_ A `card_id` always targets a task card; direct matching to `kind: project` is forbidden because a project is a derived label from the task's `project` field, not an attachment target. When no task matches, do not force the artifact onto a project. Continue to ambient routing, then routing proposal #4 for a new task. When Notion or another source has no natural task unit, proposing a same-title task is acceptable. `secondary_card_ids` follows the same task-only rule. The v43 project-fallback behavior is retired.
- Confidence: at **≥0.7**, set `card_id` and record high `routing_confidence`; at **0.4–0.7**, set `card_id` and record medium confidence; below **0.4**, continue to Pass 3. Unattended cron still uses `routing_status: inbox`. Always record `routing_reason` and `matched_signals` for morning correction.
- **Multiple-card proposals (worklog-board PRD v32):** propose one primary card and zero or more secondary cards. The highest-confidence match remains `card_id`. Put other meaningful task matches in `secondary_card_ids: [<id>, …]`; DB ingestion stores them in the `l2.note_cards` M:N relation and the `/triage` editor lets the user add or remove them. Reports, home widgets, and digests continue to use the single primary card.

#### Pass 3 — ambient

- When nothing matches, use `card_id: null`, `routing_status: inbox`, and low `routing_confidence`; the user may promote it later.
- When there is no matching card but the artifact represents a new task or project unit, separately create a **new L1 card triage proposal**. Under PRD v41, default to a **task card** using `type: new-card` and a payload with `source_note_ids: [<note id>, …]`. One approval creates the card and links the source notes. Propose a project only when several task proposals share the same nonexistent project context. Keep the former `proposal_type: new_l1_card` project format as backward-compatible half of a project-plus-task set.
- **Proposals only; never create automatically. Prefer grouping and existing-task matching (PRD v45).** Preserve the user's verbatim correction: _"노션 아닌 경우 새 카드는 애초에 제안만 하라니까? 혹은 하나의 카드에 묶어서 넣을 수 있으면 하나로."_ No-match artifacts appear only as proposals in the review-board segment. Neither the skill nor cron creates `l1_cards` directly. Apply these rules:
  1. **Group first:** when several artifacts share a project and semantic content, create one proposal with multiple `source_note_ids`, not one proposal per artifact. Use semantic grouping rather than fixed string rules.
  2. **Prefer existing tasks:** before proposing a new task, evaluate semantically matching tasks within the project. For a strong match, propose `type: link-note` with `target_card_id` and multiple `source_note_ids`; this proposes links without creating a card. Use `new-card` only when no task matches.
  3. **Zero creation invariant:** create only `_triage/<id>.md`, with `id` derived from a stable hash of grouped note IDs. Do not create `l1_cards` or change `l2_notes.card_id`, including in bulk rerouting. See worklog-board PRD §4.3 v45.
  4. **Align with the IA model (PRD §19 v56/v57):** ownership priority is an existing _active_ project, then unlinked one-off work with `project_id=NULL`, then a new project as an exception. Exclude archived projects with `status: closed`; never route into retired catch-all buckets. When no active project fits and the task is one-off, omit `project_ref` and `project` from the `new-card` proposal so approval creates an unlinked task. Keep new-project proposals rare: only when there is no existing match and the group has at least two folders and three notes.
  5. **Use descriptive proposed task titles.** Preserve the user's verbatim concern: _"제목만 봐서 뭔지 알 길이 없어."_ Summarize the core work in a natural title. Do not use folder slugs, source-directory basenames, note IDs, dates, or other opaque labels. Example: `triage-tabs` ❌ → `검토함 4-탭 재편 구현` ✅.

### Resolve `backbone_ids`, `task_ids`, and `paper_id` (→ Layer 2)

- Match architecture and technique keywords in the artifact body, such as SR-CorrNet, TF-Restormer, attention, separation, and enhancement, to slugs under `<target>/_layer2/backbones/` and `tasks/`.
- When no entry matches and the artifact signals an emerging reusable asset, such as reuse, lightweight variants, a new backbone, architecture, or baseline, create and log the appropriate backbone, task, or paper catalog entry using its README schema.
- For paper artifacts from autopilot-draft or research paper IDs, resolve a `papers/` slug and emerge one when absent.

### Infer `intent` and `work_status`

- Recommended `intent` values are `원천기술` for horizontally reusable assets, `상용화` for a product or API, `논문` for external publication, `수탁` for external delivery, and `운영` for lab operations or administration. Infer the default from artifact type and keywords.
- Recommended `work_status` values are `설계` for blueprints, `탐색` for ideas and exploration, `검증` for experiments, `진행중` for active work, `통합` for integration or library work, `출시` for release or submission, `완료` for finished work, and `null` when unknown.
- **Schema tolerance:** `intent` and `work_status` are `z.string()` in `NoteSchema`, not enums. Prefer the canonical values for consistent UI pickers and badges, but never silently drop a new vocabulary value.
