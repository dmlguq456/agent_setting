## Two-layer model (worklog-board PRD §2 — operating premise of this skill)

worklog-board uses a _two-layer_ model (PRD v18, 2026-06-09):

| | **Layer 1** (`<target>/cards/`) | **Layer 2** (`<target>/_layer2/`) |
|---|---|---|
| Owner | **User** — creates items directly on the board | **Agent (this skill)** — organizes source artifacts |
| Unit | `kind: task` and `kind: project` cards | `backbones/`, `tasks/`, and `papers/` catalogs plus `notes/` artifact-note rows |
| This skill | _Read-only_ matching; proposes new items only through `_triage/` | _Writes_ note rows and emerging catalog entries |

**The link is the `_layer2/notes/<id>.md` row.** One note connects both layers through `card_id` (→ L1 card), `backbone_ids` and `task_ids` (→ L2 axes), and `paper_id` (→ papers). These note rows are the primary output of this skill.

> ⚠️ **Different from the pre-v18 model:** the former skill appended artifacts to the _Layer 1 card body_ under `## 진행` or `## 쓰인 자리`. Since v18, it records artifacts as _Layer 2 note rows_. Do not modify card bodies.

## Note-row schema (`_layer2/notes/<id>.md`)

Follow the frontmatter specification in `<target>/_layer2/notes/README.md`:

```yaml
---
id: note-YYYYMMDD-xxxxxx        # Generated: date + six-character source-path hash (idempotency key)
card_id: research_some-task     # → Layer 1 card-file stem; null means ambient/no matching card
backbone_ids: [sr-corrnet]      # → _layer2/backbones/<slug>.md (M:N)
task_ids: [sep]                 # → _layer2/tasks/<slug>.md (M:N)
paper_id: tf-restormer-icml2026 # → _layer2/papers/<slug>.md (optional)
intent: 원천기술                # 원천기술 | 상용화 | 논문 | 수탁
work_status: 검증               # 탐색 | 검증 | 통합 | 출시 | null (divergence stage)
routing_status: inbox           # inbox | confirmed | manual; unattended cron always stages an inbox proposal. Only user confirmation promotes it.
routing_confidence: 0.82        # 0–1 routing confidence; never auto-confirms, only sorts/highlights /triage and home
routing_reason: "TF window ablation → matches ICML TF-Restormer task keywords"
matched_signals: [project:TF-Restormer, path:plans/2026-..._exp-043, kw:ablation]
run_id: run-20260610-0500       # Nightly batch that created this note
run_at: 2026-06-10T05:00:00.000Z
created_at: 2026-06-09T00:00:00.000Z
source: <artifact-root>/plans/2026-06-08_x/   # Original artifact path (idempotency-check key)
---

A readable note derived from the artifact. Summarize results, decisions, hypotheses, and metrics, and include [[links]].
```

## Position in the autopilot family

`autopilot-note` handles accumulation and routing by creating Layer 2 records. Other `autopilot-*` members create source artifacts:

- `autopilot-research`, `autopilot-code`, `autopilot-draft`, `autopilot-lab`, and `analyze-project` create artifacts under `<artifact-root>/{research,plans,documents,experiments,analysis_project}/` or `experiments/`.
- `autopilot-note` reads those artifacts, turns them into Layer 2 notes, and links them to Layer 1 cards. It never changes the source artifacts.

The worklog-board app (`~/worklog-board/`) is the UI that displays notes and cards. This skill creates Layer 2 notes; a user cron job or manual invocation triggers it. Keep these responsibilities separate.

`autopilot-refine` corrects the Markdown artifacts themselves under `<artifact-root>/{research,documents}/`. `autopilot-note` reads those artifacts as sources and creates separate Layer 2 notes. Their targets and operations are fundamentally different.
