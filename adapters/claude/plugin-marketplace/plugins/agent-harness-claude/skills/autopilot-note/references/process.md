## Process

### Stage A — Source scan

1. Read `last_run_ts` from `<artifact-root>/notes/.last_run.yaml`. If absent, use the start of `--scope`.
2. Apply the time filter to all six source branches (`mtime > last_run_ts`). With `--source`, scan only the specified source.
3. Return `[(source_type, path, mtime, summary_excerpt)]`.

### Stage B — Analyze source bodies

For each source:

1. Read `pipeline_summary.md` first; it is short T1 context.
2. Extract keywords from the title, topic, project, paper ID, commit message, and experiment ID.
3. Extract note material: results, decisions, hypotheses, metrics, and next steps.
4. Extract L1 attachment hints from frontmatter `project` or pipeline-state `task_card`.
5. Extract L2 attachment hints from architecture and task keywords plus reusable-asset emergence signals.
6. Return `[(source, keywords, note_material, l1_hints, l2_hints)]`.

### Stage C — Target matching

Apply Target Resolution to each source and return:

```
[(source, note_id, card_id, backbone_ids, task_ids, paper_id, intent, work_status,
  routing_status, routing_confidence, routing_reason, matched_signals[],
  run_id, run_at, emerge_catalog[], propose_l1_card?)]
```

`run_id` and `run_at` identify one execution batch. Set them once when Stage A begins and apply the same values to every note in that run: `run-{YYYYMMDD}-{HHMM}`.

### Stage C.5 — Verification (light+)

Invoke reviewers according to the rigor tier derived from intensity; there is no separate `--qa` axis. Keep this aligned with `CONVENTIONS.md §1.1`. Review:

- _Linking precision_: incorrect `card_id`, `backbone_ids`, or `task_ids` attachments
- _Catalog emergence and L1 proposals_: overly broad or overly conservative decisions
- _Note narrative_: whether the note captures the source's essential content (standard+)
- _Fact check_: whether venue, year, and metrics agree with the source (standard+)

When a reviewer raises an issue, record it in `_internal/reviews/round_{N}.md` and surface it in the report. On a blocking issue, halt automatic application and fall back to dry-run output.

### Stage D — Apply

1. **Create L2 notes (#1, #2, #3, #5):**
   - Create `<target>/_layer2/notes/<id>.md`. Derive `id` as `note-{YYYYMMDD}-{six-character source-path hash}` for idempotency.
   - Write frontmatter for `card_id`, **`secondary_card_ids`** (multiple secondary card proposals, v32), `backbone_ids`, `task_ids`, `paper_id`, `intent`, `work_status`, `routing_status`, **`routing_confidence`, `routing_reason`, `matched_signals`, `run_id`, and `run_at`**, plus `created_at` and `source`. Unattended cron always uses `routing_status: inbox`.
   - Write a readable summary of the source: results, decisions, metrics, next steps, and `[[links]]`. Follow the selected audience language rather than imposing a fixed locale.
2. **Emerge L2 catalog entries (#3):**
   - When a referenced backbone, task, or paper slug is absent under `<target>/_layer2/{backbones,tasks,papers}/`, create the entry from that directory's README frontmatter specification and log the emergence.
3. **Propose L1 cards (#4):**
   - Create `<target>/_triage/{date}_<seq>.md` with proposed `kind: project` or `task` frontmatter, a candidate slug, a body outline, confirm/reject markers, and the supporting source link. The worklog-board `/triage` UI watches this directory.
4. **Check idempotency:** when the note `id` or frontmatter `source` marker already exists, update or skip it. The same source must resolve to the same note, never a duplicate.
5. **Preserve L1 cards:** treat `<target>/cards/**.md` as read-only. Propose new cards only through `_triage/`.
6. **Maintain manifests on every run (PRD v33):** scan the backbone catalog and:
   - For a backbone with an **empty body and at least three accumulated notes**, draft its definition and uses from those notes and set `manifest_status: draft`. This fills an empty slot without overwriting user content and naturally covers backbones that emerged earlier.
   - For a backbone whose body already has content, especially `manifest_status: confirmed`, do not edit directly. Stage a review proposal when new derivations or changed uses should be recorded.
   - **Genealogy and derivation chains always require user confirmation.** Present them only as candidates in a draft and never state them as established fact.

### Stage D.5 — Editorial polish (light+, once per batch)

Notes are user-facing artifacts. Send all note bodies created or updated in the run, plus the Stage E digest, to `Agent(편집팀)` in polish mode as one batch:

- Scope: wording in the selected audience language, including literal-translation artifacts, awkward prose, excessive expansion, and consistency of concise note style
- Preserve all frontmatter, `[[links]]`, slugs, numbers, metrics, code identifiers, headings, tables, and structure
- Invoke once for the batch, never once per note. Skip when the run creates no notes.
- Skip in quick mode. Keep responsibilities separate: reviewers in C.5 check consistency and accuracy; the editorial team checks readability.

### Stage E — Generate the digest as a run-based review group

The digest is a review group for each nightly run, not merely a count summary. Put the `run_id` header and review-needed inbox items first so the home page and `/triage` provide an effective morning entry point.

1. Prepend an entry to `<target>/digests/YYYY-MM-DD.md`:

```markdown
## YYYY-MM-DD <weekday> (autopilot-note <scope> · run-<YYYYMMDD-HHMM>)

- This run: created <N> · **review needed (inbox) <I>** · catalog entries emerged <E> · new card proposals <M>
- Notes: <N> (L1 link proposals <P> / ambient <A>)
- Catalog emergence: backbone <B> / task <T> / paper <Pa>
- New L1 card proposals (triage): <M>

### ⚠ Review needed (low confidence or ambient — correct in /triage)
- ◯ <one-line note> — _conf <0.xx>_ · <routing_reason>
- ...

### Top notes
- ◯ <backbone/task> · ▭ <linked card> — <one-line note>
- ...

### Triage paths (new L1 card proposals)
- <triage path 1>
```

2. Preserve prior entries and place the new entry at the top.
3. The TodayDigest component on the worklog-board home page reads the latest entry.

### Stage F — Report

Write `<artifact-root>/notes/{date}/pipeline_summary.md` using the three-tier layout:

- **T1:** routing result table (artifact → note ID → card ID/catalog), digest link, and `.last_run.yaml` update time
- **T2:** raw scan log by source
- **T3:** light+ reviewer log

Update `.last_run.yaml`.

Keep the final user-facing report within eight lines and use the user's communication language unless another audience contract applies. Its content should cover:

```
✓ autopilot-note complete — <scope> · run-<YYYYMMDD-HHMM>
• Notes: <N> (all proposals; routing_status: inbox)
• Review needed (low confidence or ambient): <I>
• Catalog emergence: backbone <B> / task <T>
• New L1 card proposals (triage): <M>
• Digest: <target>/digests/<date>.md
• Internal log: <artifact-root>/notes/<date>/

Next: review this run's <N> items on worklog-board home or `/triage`, then approve, revise, or discard them to promote confirmed routing. Unattended runs never auto-confirm. If M > 0, also confirm the <M> new L1 card proposals.
```
