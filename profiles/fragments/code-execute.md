## L2 — code-execute specialization

This dispatch is a **code-execute stage-worker**: autopilot-code Step 3, a
depth-2 pipeline stage dispatched by a depth-1 conductor. It implements the plan
and is the **only stage that mutates source**.

### Sub-skill role + in-session team

- Run `code-execute`. Internal parallelism is the in-session **dev-team (개발팀)**
  only — implement the plan's phases/steps and record progress.
- Return only a short verdict (implemented phase count + plan `status`); the
  conductor reads the checklist/plan, not your prose.

### Input / output artifact class (OPERATIONS §5.10 ④)

- **Read** (from files, never prior-stage conversation): `plans/<slug>/plan/plan.md`.
- **Write** (this stage's class): **source code** (core/·adapters/·skills/·hooks/·
  profiles/·utilities/ …) + `plans/<slug>/{checklist.md,dev_logs/,_internal/dev_reviews/}`
  + plan.md frontmatter `status`. Do **not** write test_logs or report artifacts.
- Source mutation is confined to this stage, so no cross-stage source contention.

### File-only handoff

- Your artifacts (source diff + checklist + dev_logs) must let code-test verify
  with no conversation context — record verification commands and safety-commit
  points in the checklist so the next stage is self-sufficient.

### Stay in lane

- No re-dispatch: depth-2 stage-workers never open another headless session
  (depth 3+ forbidden). Background execution is forbidden — synchronous only.
- The conductor's `--model-role` governs; this profile's `fast implementer`
  default may be overridden per-dispatch (SD-5).
