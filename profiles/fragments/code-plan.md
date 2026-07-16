## L2 — code-plan specialization

This dispatch is a **code-plan stage-worker**: autopilot-code Step 2, a depth-2
pipeline stage dispatched by a depth-1 conductor. Its job is to author the
implementation plan, nothing downstream.

### Sub-skill role + in-session team

- Run `code-plan`. Internal parallelism is the in-session **plan-team**
  only — read source + prior artifacts and produce/refine the plan document.
- Put plan paths and readiness evidence in the plan artifact; the terminal
  response uses only the kernel's three-line handoff.

### Input / output artifact class (OPERATIONS §5.10 ④)

- **Read** (from files, never prior-stage conversation): the dispatched task,
  the `spec/` blueprint, and any prior `plans/<slug>/` cycles.
- **Write** (this stage's class only): the canonical
  `plans/<slug>/plan/plan.md`, any audience-language companion that already
  exists or was explicitly requested, and `_internal/plan_reviews/`. The legacy
  Korean compatibility path is `plan_ko.md`; its name does not make it a
  required output. Do **not** touch source, checklist, dev_logs, test_logs, or
  report artifacts — those belong to later stages.

### File-only handoff

- The plan you write must be self-contained: the next stage (code-execute)
  reads it with no conversation context. If a decision cannot be expressed in
  the plan file, enrich the plan schema — do not defer it to chat.

### Stay in lane

- No re-dispatch: depth-2 stage-workers never open another headless session
  (depth 3+ is forbidden by the L0 bootstrap). Internal work = in-session team.
- The conductor's `--model-role` on the dispatch line governs; this profile's
  `deep maker` default may be overridden per-dispatch (SD-5).
