## Eval mode: post-training evaluation and analysis

Evaluate a completed checkpoint from the latest setup experiment or from `--parent <slug>` for reevaluation or new data.

> **Stage dispatch:** use the contract in `setup-procedure.md`. At standard+, dispatch durable E2 execution, E3-2 plotting, and E3-3 comparison as depth-2 headless sessions with file-only handoff. Each team reads only artifact paths such as `metrics.jsonl`, `REPORT.md`, and research inputs, never earlier conversational context.

#### Eval stage-worker mapping

| Stage | In-session team | Input artifacts | Output artifacts | Write class |
|---|---|---|---|---|
| E2 execution | 테스트팀, functional | `eval.py` and checkpoint | Metric values in `run.json best` plus `metrics.jsonl` | Dispatched depth 2 |
| E3-2 plot | 자료팀, figure-gen | `metrics.jsonl` | `figures/*.{png,pdf}` | Dispatched depth 2 |
| E3-3 compare | 연구팀, research-survey | `REPORT.md`, `research/`, and `analysis_project/paper/` | Comparison section in `REPORT.md` | Dispatched depth 2 |

Do not let stages write the same file concurrently without the OPERATIONS §5.8 `.pipeline-lock`. `_RUNLOG.md` is an append-only timeline exception: S3-2 appends the experiment row, and E3-4 updates only that row rather than appending another.

### E1 — One-screen eval specification

**E1-1. Resolve the target.** Use `--from`, the latest pending `_RUNLOG` row, or `--parent` to select the experiment and checkpoint. Infer evaluation data and metrics from the existing test set or new-data request.

**E1-2. Confirm in one screen**, localized to the user's communication language:

```text
=== Eval Spec ===
Experiment:     <date>_<slug> or parent: <slug>
Checkpoint:     experiments/<slug>/runs/run-001/ckpt/best.pt
Mode:           eval
Evaluation data:<existing test set or new data>
Metrics:        <PSNR, SSIM, SI-SDR, ...>
Comparison:     <sibling, parent, or paper baseline>

Proceed? (continue / revise / stop)
```

**E1-3. Create `run.json` only for direct eval-only entry.** If `experiments/<id>/run.json` does not exist, create it here; never recreate or overwrite the file born in setup S3-2. For `eval --parent`, write `status: "running"`, `skill_mode: "eval"` from `pipeline_state.mode`, parent slug, current ISO 8601 `started_at`, parent config path or null `config_ref`, and the evaluated parent checkpoint path. Omit `best`. E3-4 updates it to done with `best` and `ended_at`.

### E2 — Execution guidance

Run the scaffolded `eval.py` against the checkpoint and data:

```bash
cd experiments/<slug>
python eval.py --config config.yaml --ckpt runs/run-001/ckpt/best.pt [--data <new_data>]
```

The user runs heavy evaluation. For an explicit lightweight request such as `가볍게 평가 돌려줘`, the test team may execute a small test set. Invoke `Agent(subagent_type="테스트팀")` in functional eval mode with `eval.py` and the checkpoint. It returns final metrics summarized into `run.json best` and the per-step stream path `experiments/<slug>/metrics.jsonl`.

### E3 — Analysis, report, and completion

**E3-1. Draft the result** when the user asks to organize results or the main agent observes eval completion. Use a localized one-screen preview with experiment, attempted change, best/final/delta metrics, sibling ablation table, parent delta, two or three observations, inline figure paths, and one next candidate. Ask whether to save, revise, or stop.

**E3-2. Optional plotting on user request.** For `결과 plot 그려줘` or `ablation 표 정리`, invoke `Agent(subagent_type="자료팀", mode="figure-gen")` with `metrics.jsonl`, the project's figure conventions from memory or existing plots, and output paths under `figures/`.

Embed every generated figure in `REPORT.md` with `![<caption>](figures/<plot>.png)`. Do not merely list the path. Embed it in `STORY.md` too when it directly supports the narrative. Markdown already renders images, so do not create HTML for figures alone. Reserve E3-5 HTML for audio or media playback that Markdown previews cannot handle.

**E3-3. Optional paper comparison at standard+ on user request.** For `결과를 기존 paper 와 비교해줘`, invoke `Agent(subagent_type="연구팀", mode="research-survey")` with `REPORT.md`, `<artifact-root>/research/`, and `analysis_project/paper/`. Compare metrics with published baselines, locate the changed surface in prior work, and explain whether observations support or challenge paper claims. Add a comparison table and a concise audience-language summary under `## 기존 paper 와의 비교` in `REPORT.md`.

**E3-5. Optional formal report** for `--report`, `보고서 써줘`, `공유용`, or high-stakes publication:

- **General prose report:** hand off to `autopilot-draft --mode doc` with `summary.md`, `STORY.md`, `figures/`, and run metrics. Draft owns prose generation and produces `documents/{date}_{slug}/`; eval only requests the handoff.
- **Playback HTML for audio/media experiments:** have the material team generate separated audio, spectrogram segments, and embedded `<audio>`/`<img>` in `experiments/{date}_{slug}/report/report.html`. Markdown previews block `<audio>`, so audio domains default to HTML. Split long audio into pages of bounded segments. When necessary, serve locally through `python -m http.server --bind 0.0.0.0 <port>` and provide the URL.

`REPORT.md` remains the default self-contained deliverable. Prose-pipeline output and playback HTML are optional layers; when both exist, let prose link relatively to the HTML comparison.

**E3-4. Save and finalize:**

- `REPORT.md` is the self-contained final report. Put Executive Summary first, followed by background, hypothesis, method, results, interpretation, conclusion, next steps, and reproduction. Embed figures. Define every condition, structure, acronym, and metric so a reader without the conversation understands it. Consolidate summary, STORY, metrics, and figures here.
- `summary.md` is only a one-line index for RUNLOG and parent auto-loading, with a verdict and a pointer to `REPORT.md`; it is not the user deliverable.
- `STORY.md` accumulates motivation, previous or parent context, this attempt, result, and next candidate.
- Update the existing experiment row in `<artifact-root>/experiments/_RUNLOG.md` from pending to done with result and next step. Do not append a second row. Mark the attempt with `(← <parent_slug>)` when applicable. Append only when an eval-only entry has no existing row. Use failed status for interruption or failure.
- Update the existing `run.json` to `status: "done"`, current `ended_at`, and `best: {name,value,step}` using the same metric as the report and RUNLOG. On failure, write `status: "failed"` and `ended_at` but omit `best`.
- Emit `run.json best` and parent delta for worklog consumption. Lab emits only; worklog receives and creates cards. Do not recompute the result or push proactively.
