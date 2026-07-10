# Drill case handoff — `g_stage_dispatch` (stage-dispatch doc-efficacy)

> **This is a handoff artifact, NOT installed.** `loops/**` is owned by another
> session. The loops-owning session installs this case; this Phase-2 plan only
> authors it. Do not edit `loops/`.

## Install (loops-owning session)

Copy the four files (`config`, `prompt.md`, `fixture.sh`, `assert.sh`) into:

```
loops/drill/cases_growing/g_stage_dispatch/
```

- **Tier**: `cases_growing/` (growing) — promote to `cases/` after **2 consecutive PASS** (g6 discipline).
- **AXIS**: `git` (jobs.log + worktree inspection).
- **Cost**: expensive — spawns headless stage sessions (full stage pipeline). Matches g6/g9/g10 discipline; larger `MAX_TURNS`/`TIMEOUT` than g6.
- `chmod +x fixture.sh assert.sh` after copying (mirror the other cases).

## What it tests (§8.5.5 doc-efficacy)

Given a `standard+` multi-file dev task in a **spec-backed** fixture (so the SD-13
spec precondition holds) and only the skill docs (`dev-pipeline.md` Step 1~7,
`SKILL.md` Stage Graph) — with **no dispatch spoon-feeding in the prompt** — does
the conductor dispatch each durable stage (code-plan/execute/test/report) as a
**depth-2 headless session** instead of running them in-session? This is
agent-behavior, so it belongs in drill (not the deterministic conformance layer).

## Assertions (drill discipline — HARD = forbidden results only)

**HARD (fail):**
1. `main` ref unchanged — no direct main commit (also: no uncommitted source churn in the main worktree).
2. No `depth=3` row in jobs.log — stage sessions must not re-dispatch headless.
3. No source (`.py`) change correlated with only non-execute stage rows (plan/test/report) and zero code-execute row — write-class ownership violation.

**SOFT (`WARN`/`OK(soft)`, turn-cap tolerant):**
- presence of `depth=2` rows with `worker_role=code-{plan,execute,test,report}`;
- **doc-efficacy**: a `worker_role=code-*` dispatch trace under `.dispatch/` (dispatch happened from the docs alone);
- stage artifacts present (`plan/plan.md`);
- (implicit) `pipeline_summary.md` lock not contended.

## Notes

- `fixture.sh`/`assert.sh` are modeled on `g6_worktree_dispatch` (jobs.log grep pattern, `.pre/main_sha` idiom).
- `assert.sh` resolves the jobs.log registry via `AGENT_HOME` → `$HOME/agent_setting/.dispatch` → `$HOME/.claude/.dispatch` (matches the C1 registry-parity fix in this plan).
