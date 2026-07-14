## Scope

### Input sources (six active branches plus one Phase 3 branch)

| # | Source | Location | Attachment signals (frontmatter/body) |
|---|---|---|---|
| 1 | autopilot-research | `<artifact-root>/research/{topic}/pipeline_summary.md` plus chapters and `cards/` | Topic name and paper IDs in cards |
| 2 | autopilot-draft | `<artifact-root>/documents/{date}_{name}/pipeline_summary.md` plus draft | Name, frontmatter `topic`, or paper ID |
| 3 | autopilot-code | `<artifact-root>/plans/<date>_<slug>/pipeline_summary.md` plus dev logs | Plan and checklist keywords |
| 4 | autopilot-lab | `experiments/<id>/STORY.md` plus `experiments/_RUNLOG.md` | Experiment ID, parent link, and `similar_models` references |
| 5 | analyze-project | `<artifact-root>/analysis_project/{code,paper,doc}/{matching}/` | Matching label |
| 6 | git log | `git log --since=<scope> --name-only --pretty=oneline` | Commit message and changed file path |
| 7 | Phase 3: Notion | Notion API export under `~/.agent_reports/notion_mirror/<date>/` (legacy `~/.claude_reports/notion_mirror/<date>/`) | Database page ID and properties |

Sources 1–6 are active through Phase 2. Enable source 7 only in Phase 3 or with an explicit `--source notion` flag.

### Output locations

| Location | Layer | Operation |
|---|---|---|
| `<target>/_layer2/notes/<id>.md` | **L2** | Primary output: one artifact becomes one note row with routing frontmatter and a readable body |
| `<target>/_layer2/{backbones,tasks,papers}/<slug>.md` | **L2** | Catalog entry referenced by a note; emerge and log it when absent, following the directory README schema |
| `<target>/cards/**.md` | **L1** | Read-only matching targets for note `card_id`; never modify body or frontmatter |
| `<target>/_triage/{date}_<seq>.md` | **L1 proposal** | Proposed project or task card read by the worklog-board `/triage` UI |
| `<target>/digests/YYYY-MM-DD.md` | — | Daily digest; prepend the new entry and preserve history |
| `<artifact-root>/notes/{date}/` | — | This skill's routing log: T1 result table, T2 source scan, and T3 reviewer evidence |

> 🗄️ **Required DB ingestion:** worklog-board now reads L2 from the libSQL database at `.cache/worklog.db`; Markdown under `_layer2/*.md` is the source and mirror. After writing notes or catalog Markdown, finish Stage D by running **`npm run migrate:fs-to-db`** from the worklog-board directory. The idempotent upsert is safe to rerun. Verify with `npx tsx scripts/verify-migration.ts`, which checks count parity and extras round trips. For another NAS location supplied through `--target`, confirm that worklog-board `LAYER2_DIR` points to that `_layer2` directory before migration.
>
> 📝 **Write rich note bodies for direct reading.** Users should not need to inspect the source-file tree. Include `# Title`, a one- or two-line summary, `## 결과` with required metrics for experiments or benchmarks, `## 핵심 결정·해결` for root causes and design decisions, `## 변경 코드` for major files and scale, `## 남은 자리` with 🔴/🟡 markers, and `**원본**: <source path or Notion URL>`. Use `_layer2/notes/note-20260528-onnxse.md` as the quality reference. Cross-link related notes and backbones with `[[slug]]`. Treat backbone/technology catalog bodies as wiki anchors covering definition, genealogy, handled work, major note links, and tasks that use them; populate them on emergence and update them as notes accumulate.

### Not for

- Changing Layer 1 card frontmatter or bodies; that belongs to the worklog-board UI or the user. This skill is read-only and proposes new cards only.
- Modifying source artifacts under `<artifact-root>/{research,documents,plans}/`; treat them as read-only.
- Building worklog-board code, including Layer 2 UI or API work; use `autopilot-code`.
- Writing reports; use `autopilot-draft`. This skill only extracts report candidates and turns them into notes.
- Large-scale restructuring of Layer 2 backbone, task, or paper catalogs; leave that to the user or `autopilot-code`. This skill may only emerge necessary entries.

## Verification rigor tiers (derived from intensity; default light-tier)

Verification rigor is derived deterministically from `--intensity`, not selected through a separate `--qa` axis. [`CONVENTIONS.md §1.1`](../../../core/CONVENTIONS.md#11-verification-rigor-tiers) is the single source for tiers and mapping. Apply them here as follows:

| Rigor tier | Behavior |
|---|---|
| **quick** | Classify routing, produce the Stage C dry summary, and apply automatically. Use for bulk backfills or one-time lightweight work. No reviewer rounds or polish. |
| **light** (default) | Add one fast reviewer on linking precision and one batched editorial polish pass in Stage D.5. Use for daily cron. |
| **standard** | Add one deep reviewer, two fast reviewers for linking precision, note narrative, and catalog/triage quality, plus one fast source-to-note fact checker. One round. Use for weekly cleanup. |
| **thorough** | Use two deep reviewers, two fast reviewers, and one fast fact checker for two rounds. Use for monthly cleanup or Notion-migration verification. |
| **adversarial** | Add one external adversary (`codex-review-team` in the Claude adapter) to thorough. Use for high-stakes work such as initial Phase 3 Notion migration verification. |

Fact and source checks follow the rigor budget derived from intensity. This entry point exposes no fact-check opt-out flag.

Reviewer axes:

- _Linking precision_ (deep reviewer): confirm that note `card_id`, `backbone_ids`, and `task_ids` point to the right L1 cards and L2 catalogs.
- _Note narrative_ (fast reviewer): confirm that the body accurately and readably summarizes the source's results, decisions, and metrics and remains valid Markdown.
- _Emergence and triage quality_ (fast reviewer): confirm that new catalog entries and L1 card proposals have complete frontmatter and adequate evidence.

## Examples

```text
# Daily cron: most common path
/autopilot-note --scope today --intensity quick

# Weekly accumulation and digest narrative
/autopilot-note --scope since 2026-05-26 --intensity standard

# First run: note every available historical source at default light-tier
/autopilot-note --scope all

# Dry run: inspect note IDs, card IDs, and catalog routing before applying
/autopilot-note --scope yesterday --dry-run

# Regenerate only the digest
/autopilot-note --scope today --digest-only

# Summarize only new L1 card proposals
/autopilot-note --triage-only

# Phase 3 Notion migration
/autopilot-note --scope since 2026-01-01 --source notion --intensity adversarial

# Note only autopilot-lab experiment artifacts
/autopilot-note --source experiment --scope yesterday

# Override the target with another NAS location
/autopilot-note --target ~/nas_alt/notes/
```

## When not to use

- To modify L1 card frontmatter or bodies: use the worklog-board UI or direct user editing.
- To modify source artifacts: use `autopilot-refine`.
- To change worklog-board code, including the Layer 2 UI/API and `/hubs` stack: use `autopilot-code`.
- To attach one artifact to one card manually: set the artifact frontmatter `project`; deterministic first-pass routing will honor it.
- To write a report: use `autopilot-draft`. This skill only records candidate material and markers.
- To reorganize the L2 catalog substantially, such as restructuring backbone families: use the user-directed or `autopilot-code` path.

## Post-run checklist

After success, recommend that the user:

1. Confirm new L1 card proposals in the worklog-board `/triage` view when `M > 0`.
2. Attach ambient or inbox notes in `/hubs` when `A > 0`.
3. Review the digest in TodayDigest on the worklog-board home page.
4. Enrich emerged backbone and task metadata weekly.
5. Inspect `.last_run.yaml` for cron consistency and prolonged inactivity.
