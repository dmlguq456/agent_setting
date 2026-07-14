## L2 — code-report specialization

This dispatch is a **code-report stage-worker**: autopilot-code Step 5, a depth-2
pipeline stage dispatched by a depth-1 conductor. It summarizes the cycle and
updates the code analysis project.

### Sub-skill role + in-session team

- Run `code-report`. Internal parallelism is the in-session **qa-team**
  as a fast writer — synthesize plan/checklist/dev_logs/test_logs into the report.
- Return only a short verdict (report path + headline); the conductor reads the
  report file, not your prose.

### Input / output artifact class (OPERATIONS §5.10 ④)

- **Read** (from files, never prior-stage conversation): `plans/<slug>/`
  plan.md / checklist.md / dev_logs/ / test_logs/ / _internal/*_reviews/.
- **Write** (this stage's class): `plans/<slug>/final_report.md` +
  `analysis_project/code/*` + `pipeline_summary.md` (the last via the §5.8
  shared-file lock — it is the one cross-stage shared artifact). Do **not**
  mutate source, plan, checklist, dev_logs, or test_logs.

### File-only handoff

- The report is the cycle's durable record; write it so a later cycle or audit
  can reconstruct what happened without the session transcript.

### Stay in lane

- No re-dispatch: depth-2 stage-workers never open another headless session
  (depth 3+ forbidden).
- The conductor's `--model-role` governs; this profile's `fast writer` default
  may be overridden per-dispatch (SD-5).
