# Procedure

The full cycle is **setup** → user training → **eval**. With `--mode auto`, infer the branch from the request. Each mode is an independent invocation and persists state in `pipeline_state.yaml`.

> **Stage-dispatch contract for standard+:** dispatch durable setup, eval, and report stages as separate dispatch-depth-2 headless sessions under OPERATIONS §5.10. In-session teams run inside their stage session. Use file-only handoff: read inputs from artifacts and never rely on earlier conversational context. The dispatch-depth-1 conductor passes paths and collects only verdicts and status. **Do not dispatch the actual experiment run:** it is long, asynchronous, and human-gated by the pending `_RUNLOG.md` row. Keep using the existing `lab-runner.yaml` profile for that segment. Direct, quick, and one-off run guidance remain inline. Stage sessions never redispatch; dispatch depth 3+ is forbidden.

#### Setup stage-worker mapping

| Stage | In-session team | Input artifacts | Output artifacts | Write class |
|---|---|---|---|---|
| S1 spec | 연구팀, plan-review | Recent `_RUNLOG.md` rows and research artifacts | `experiments/{date}_{slug}/experiment_spec.md` | Dispatched dispatch depth 2 |
| S2 scaffold | 개발팀, new-lib | `experiment_spec.md` plus reference or parent config | `train.py`, `eval.py`, `config.yaml`, and `metrics.jsonl` logger | Dispatched dispatch depth 2 |
| S3 run | User or cluster submit | `config.yaml` | Pending `_RUNLOG.md` row and `run.json` with running status | **Not dispatched**; long, asynchronous, human-gated |

See `eval-procedure.md` for E2, E3-2, and E3-3.

## Setup mode

### S1 — One-screen specification

**S1-0. Secure a worktree and experiment branch.** Never begin from main. Reuse `<repo>-wt/<slug>` when it exists; otherwise run `git worktree add <repo>-wt/<slug> -b exp/<slug> <base>`, omitting `-b` for an existing branch. Perform every edit, scaffold, config change, and commit inside that worktree. Main only coordinates.

**S1-1. Auto-read Step 0 context.** Report one concise line, such as the previous experiment, validation metric, convention readiness, and recommended similar model. With `--parent`, include one line for parent result and config.

**S1-2. Draft from the user's requested change.** Combine the auto-loaded context with the one-line experiment request.

**S1-3. Confirm in one screen.** Localize prose to the user's communication language while preserving this schema:

```text
=== Experiment Spec (setup) ===
Project:        <name>
Experiment:     <date>_<slug>
mode:           setup
Reference:      model/TF_Restormer from similar_models.md
                or parent: <slug> with checkpoint continuation
Motivation:     <derived from the previous or parent result>
This attempt:   <one line from the request>

Dataset:        <reference or parent data plus fine-tuning additions>
Metric:         <PSNR, SSIM, SI-SDR, ...>
Ablation grid:  <inferred or explicit>

Experiment ready:  ✓ or ❌
Conventions ready: ✓
Research plan-review: on or off

Proceed? (continue / revise / stop)
```

**S1-4. Invoke research plan-review only at standard+.** Use `Agent(subagent_type="연구팀")` with `Mode: plan-review` and provide the latest five RUNLOG rows, the draft `experiment_spec.md`, and any research directory. Ask it to check:

- whether a completed or pending row already represents the same ablation;
- whether motivation follows from the previous or parent result;
- whether the grid changes one variable at a time; and
- whether expected metrics are plausible against the prior baseline.

Have it add `<!-- review: ... -->` comments to `experiment_spec.md` and return the file plus a one-line summary. Skip this review at quick and light.

**S1-5. Save** `experiments/{date}_{slug}/experiment_spec.md` in 7–12 lines. Include `parent:` when applicable.

### S2 — Scaffold with development/new-lib

**S2-1. Choose the base.**

- With `--parent`, copy the parent config into a new `_ftNN_` branch, preserve the parent config and model, set `init_ckpt` to the parent checkpoint, and add the new dataset. This is a config branch, not a model-code rewrite.
- For a new reference, copy the `--ref` model or the recommendation from `similar_models.md`, then vary it.
- Obtain one-line user confirmation.

**S2-2. Invoke `Agent(subagent_type="개발팀", mode="new-lib")`.** Provide the reference or parent checkpoint/config, experiment directory, and spec. Enforce four rules:

1. Make the smallest change by copying and varying the reference or parent; do not introduce a new layer by default.
2. Prefer layers listed in `experiment_conventions.md`.
3. Express minor changes in `config.yaml`; do not modify `model.py`.
4. Name fine-tuning variants beside the base with `_ft01_`-style prefixes.

Required outputs:

- `experiments/{date}_{slug}/train.py`, copied from the reference with only the variation points changed
- `experiments/{date}_{slug}/eval.py`, copied from the reference
- `experiments/{date}_{slug}/config.yaml`, copied from the reference or parent with the current ablation marked
- A `metrics.jsonl` logger in train/eval that appends `{step,split,name,value,ts}` to the root experiment stream once per step. Follow the data contract exactly; never create `metrics.json(l)` under `runs/`, and use `eval_result.json` for one-off per-run blobs.
- For parent fine-tuning, a new `_ftNN_` config with parent checkpoint and new data, without overwriting the parent config or model
- Or a `_ft01_` file under the base-model directory when project convention requires it

Do not introduce new layers, modify in-use layers in the parent/reference model directory, or perform library refactoring; those belong to autopilot-code. Return the created-file list and a concise variation summary.

**S2-3. Confirm in one screen:** list scaffold files, logger inclusion, optional variant path, parent checkpoint when applicable, and the one-line changed surface. Offer continue to run, revise scaffold, or stop.

### S3 — Run guidance and pending RUNLOG

**S3-1. Provide the command:**

```bash
cd experiments/{date}_{slug}
python train.py --config config.yaml
```

The user may submit it to a cluster instead. Do not auto-run training because GPU, queue, and cluster environments vary. The user returns through eval mode afterward.

**S3-2. Append one pending row before the run** to `<artifact-root>/experiments/_RUNLOG.md`, leaving the result as `—`. This makes in-flight work and duplicate setup visible during long queues and mirrors `pipeline_state.run: in_progress`.

At the same point, create `experiments/{date}_{slug}/run.json` with `status: "running"`, `skill_mode: "setup"` from `pipeline_state.mode`, `parent`, current ISO 8601 `started_at`, scaffold config path in `config_ref`, and the expected best-checkpoint path in `ckpt_path`. Omit `best` and `ended_at` while running. E3-4 updates them on completion.

```markdown
| 2026-05-26 | lr_sweep | TF_Restormer base, lr 1e-3→3e-4 | ⏳ 대기 | — |
```

**S3-3. Mandatory hash-bound smoke before full-run entry.** Run one epoch or the minimum batch through `tools/smoke-attestation.py attest`, binding the exact config, source, input/checkpoint signature, working directory, and command. Validate data loading, forward/backward, loss, and optimizer step, not convergence. A detached full run must verify that attestation immediately before launch and reject missing, failed, or stale hashes. If a one-batch probe is impossible, the capability registry must name the bounded substitute; there is no free-form skip.

**S3-4. Escalate convergence failures on user request.** For prompts such as `loss 가 안 떨어져`, `NaN`, or `수렴 이상`, invoke `Agent(subagent_type="품질관리팀", mode="ml-debug")`. Provide the experiment directory, symptom, available logs, and `experiment_spec.md`. Check data shape/range/NaN/balance, model initialization/freezing/gradient flow, loss scale/sign/stability, optimizer learning rate/weight decay/warmup, and batch/device/mixed precision. Return the one or two most likely causes plus commands that distinguish them.

After training, continue with `/autopilot-lab "결과 평가"` in eval mode.
