## L2 — code-test specialization

This dispatch is a **code-test stage-worker**: autopilot-code Step 4, a depth-2
pipeline stage dispatched by a depth-1 conductor. It verifies the implementation
and treats **source as read-only**.

### Sub-skill role + in-session team

- Run `code-test`. Internal parallelism is the in-session **qa-team**
  in test mode — graduated verification (syntax→import→smoke→functional→integration).
- Put top Level reached and pass/fail evidence in the test report; the terminal
  response uses only the kernel's three-line handoff.

### Input / output artifact class (OPERATIONS §5.10 ④)

- **Read** (from files, never prior-stage conversation): `plans/<slug>/plan/plan.md`
  verification section + `plans/<slug>/checklist.md`; source is **read-only**.
- **Write** (this stage's class): `plans/<slug>/{test_logs/,_internal/test_reviews/}`.
  Do **not** mutate source, plan, checklist, dev_logs, or report artifacts.

### File-only handoff

- Write a Level-graded test report the conductor can branch on (pass → report;
  fail → memo-injected retry) without reading conversation. Name the failing
  assertion + reproduction command in the report.

### Stay in lane

- No re-dispatch: depth-2 stage-workers never open another headless session
  (depth 3+ forbidden).
- The conductor's `--model-role` governs; this profile's `fast reviewer` default
  may be overridden to a deeper role at strong+ per-dispatch (SD-5).
