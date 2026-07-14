## Output data contract for machine-readable experiment dashboards

> Preserve lab behavior and standardize only its output format. `metrics.jsonl`, `run.json`, and `report/` are the machine-readable surfaces consumed directly from disk by the experiment dashboard in worklog §25. **Disk is the source of truth.** The contract source is `e0-lab-contract-scope.md §3` and worklog PRD §25.4; `claude_setting` is only a cross-reference. Human-facing mirrors such as `_RUNLOG`, `REPORT.md`, `summary.md`, and `STORY.md` remain in place. These surfaces supplement rather than replace them.

### `metrics.jsonl` — append-only per-step stream

Store it at `experiments/<id>/metrics.jsonl`, with one record per line. The scaffolded JSONL logger in train/eval scripts is the only writer and appends once per step.

```jsonl
{"step": 1200, "split": "val",   "name": "loss", "value": 0.342, "ts": "2026-06-23T14:02:11Z"}
{"step": 1200, "split": "train", "name": "loss", "value": 0.318, "ts": "2026-06-23T14:02:11Z"}
{"step": 1200, "split": "val",   "name": "psnr", "value": 28.41, "ts": "2026-06-23T14:02:11Z"}
```

| Field | Type | Meaning |
|---|---|---|
| `step` | int | X axis; the UI may toggle to `ts` wall time |
| `split` | str | Curve group: `train`, `val`, or `test` |
| `name` | str | Metric series such as `loss`, `psnr`, or `si_sdr` |
| `value` | float | Scalar value |
| `ts` | ISO 8601 str | Wall clock for time toggles and tail-follow |
| `kind` | optional str | `scalar` by default, with `image` and `hist` reserved; E0 supports only scalar |

Rules: append only, one record per line, and **the file is the source of truth**. Do not ingest this high-volume stream into the DB. worklog filters through `?name=&split=`.

**Path boundary:** the root `experiments/<id>/metrics.jsonl` is the one per-step chart stream. Put a one-off per-run evaluation blob at `runs/run-001/eval_result.json`. Never create `metrics.json` or `metrics.jsonl` under `runs/`; the consumer streams the single root file and would break on distributed same-name files.

### `run.json` — machine-readable run manifest

Store `experiments/<id>/run.json` as the consolidation of existing run facts such as slug, parent, mode, checkpoint, and best result. It introduces no new calculation. `_RUNLOG.md` is its human-readable mirror.

```json
{ "id": "2026-06-23_lr_sweep", "parent": null, "skill_mode": "setup", "status": "done",
  "config_ref": "experiments/2026-06-23_lr_sweep/config.yaml",
  "ckpt_path": "experiments/2026-06-23_lr_sweep/runs/run-001/ckpt/best.pt",
  "started_at": "2026-06-23T09:00:00Z", "ended_at": "2026-06-23T14:30:00Z",
  "best": { "name": "psnr", "value": 28.7, "step": 18000 } }
```

| Field | Meaning and lab source |
|---|---|
| `id` | `<date>_<slug>`, the experiment-directory name |
| `parent` | `--parent` slug or null; the lineage-edge source of truth |
| `skill_mode` | `setup` or `eval` from `pipeline_state.mode`; never hardcode it |
| `status` | `running`, `done`, or `failed`, mirrored by `_RUNLOG` status |
| `config_ref`, `ckpt_path` | Config and best-checkpoint pointers |
| `started_at`, `ended_at` | Birth and completion timestamps in ISO 8601 |
| `best` | `{name,value,step}` from evaluation; source for completion dispatch and summary cards |

Lifecycle: create with `status: "running"` during setup S3-2 or direct eval-only E1-3, then update to `done` with `best` and `ended_at` in E3-4. For `running` and `failed`, omit the `best` key entirely. A running run also omits `ended_at`; a failed run records `ended_at` but still omits `best`.

### Parent-lineage source of truth

Use `run.json.parent` as the machine-readable edge for comparison and lineage graphs. `pipeline_state.parent`, `_RUNLOG (← parent)`, and `STORY.md` mirror the same value. Graph consumers read only `run.json`.

### Completion dispatch from lab to worklog

At evaluation completion, emit the `run.json best` result plus its delta from the parent for the worklog approval queue and board to consume. Lab only emits; it does not push proactively. Worklog E3 performs receipt and card creation under PRD §25.7. Reuse the already computed `run.json best` without new analysis.

### `report/` — iframe-rendered report artifacts

`experiments/<id>/report/` is the HTML directory rendered by the dashboard in a sandboxed iframe. One directory supports two producers:

- Lab continues to generate its existing audio/media playback page at `report/report.html`, including separated audio, spectrograms, `<audio>`, and `<img>` embeds.
- `autopilot-draft` or design produces rich prose HTML. Lab does not generate prose HTML itself.

The statement that draft/design owns `report/` applies only to prose reports; it does not prohibit lab's audio HTML. These may coexist with `REPORT.md`: lab Markdown, lab audio/media HTML, and draft/design prose HTML.
