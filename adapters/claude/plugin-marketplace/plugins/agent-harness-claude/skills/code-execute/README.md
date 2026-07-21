# code-execute

> This README summarizes the portable capability for users and maintainers. The model-neutral contract lives under `<agent-home>/capabilities/`; `SKILL.md` in this directory provides shared guidance for runtime-specific projections.

## Overview

Executes an implementation plan with progress tracking. It implements individual steps as the `dev/*` unit, relies on the conductor-dispatched `impl-review` sibling node (unit `qa/code-review`) for phase review, and establishes a Git safety checkpoint.

## Invocation

```
/code-execute <plan name or path>
```

## Plan Resolution

> The single authority for resolving `$ARG` to a plan path is [autopilot-code/references/arguments-and-decisions.md#plan-resolution](../autopilot-code/references/arguments-and-decisions.md).

## Commit Message Rules

- Safety checkpoint: `chore: Safety checkpoint before {plan-name} execution`
- Success: `{type}: {description}\n\n{key changes}` — type: feat/fix/refactor/chore

## Git Safety Checkpoint

1. Run `git fetch && git pull`. On a merge conflict, abort, warn the user, and stop.
2. Run `git status`. If uncommitted changes exist, inspect the diff and create a meaningful rollback-point commit.
3. Run `git rev-parse HEAD`, save it as `$SAFETY_COMMIT`, and record it in the checklist header.

## Initialization

- Read the plan file.
- **Log directory = the grandparent of `plan/plan.md`** (for example, `<artifact-root>/plans/2026-03-18_refactor/`).
- **Inspect the existing log directory**:
  - If `{log_dir}/plan/checklist.md` contains `[x]`, `[FAIL]`, or `[SKIP-DEP]`, **resume**: update the safety commit, skip completed steps, and start at the first `[ ]`.
  - Otherwise, start a new run.
- Run `mkdir -p {log_dir}/dev_logs {log_dir}/_internal/dev_reviews`.
- Write `{log_dir}/plan/checklist.md`.

## Rules

- Read the checklist before every step.
- **Implement one step at a time as the `dev/*` unit**, with specific files and changes plus the `dev_logs` path.
- Launch independent steps in parallel.
- Mark each completed step `[x]` or `[FAIL]`.
- Do not stop until every actionable step has been processed.

## QA Scaling

The plan frontmatter's `qa_level` overrides automatic phase-level detection.

| Level | Condition | Action |
|---|---|---|
| Quick | `--intensity quick`, propagated from autopilot-code | 1 fast reviewer, one pass; only record 🔴 issues under Decision Points in `pipeline_summary.md` |
| Light | ≤3 units, mechanical, one variant | 1 fast reviewer |
| Standard | 4–10 units, logic change, one module | 1 deep reviewer |
| Thorough | >10 units, cross-module or architectural | 2–3 parallel reviews: A correctness (deep) / B consistency (fast) / C safety (deep) |
| Adversarial | Cross-variant, shared modules, >20 files, and external adversary available | Thorough + 1 external adversary |

## Change Log and Phase Review

Each step writes `dev_logs/step_*.md`, including old/new content and a required `Decision:` entry.

**At phase completion**:

1. Evaluate the QA level and record the review request in the stage artifact; the conductor dispatches the `impl-review` node (unit `qa/code-review`).
2. Inspect the review files:
   - 🟡: log and continue.
   - 🔴 minor: fix once in the execute boundary, then re-verify. If still 🔴, promote to major.
   - 🔴 major: **auto-rollback and continue** without asking the user.
3. Rollback procedure:
   1. Roll back using the `old_string` from the step log.
   2. If that fails, restore `$SAFETY_COMMIT` with `git checkout .` (reverting all uncommitted work, including earlier phases), mark every step `[FAIL]`, and proceed to the final report.
   3. If rollback succeeds, mark the phase steps `[FAIL]` and continue to the next phase. Mark dependent steps `[SKIP-DEP]`.

- With ≤3 steps, omit phase grouping and review once after all steps finish.
- **Total failure**: **auto-rollback to the safety commit** without asking the user.

## Safety Rules

- Before changing a signature, search every call site, update every caller, and inspect implicit contracts.
- If cascading errors exceed plan scope, mark the step `[FAIL]`, roll it back from the step log, and continue.
- Do not change code outside plan scope, except where a required signature change necessarily affects callers.

## Final Report

After all phases have been processed:

- List only `[FAIL]` and `[SKIP-DEP]` steps with their reasons.
- If every step is `[x]`, report success only.
- End by recommending `code-test <plan path>`.

## Plan Status Update

- All `[x]` → `status: done`
- Some `[x]` plus some `[FAIL]`/`[SKIP-DEP]` → `status: partial` and add `failed_steps`
- All `[FAIL]`/`[SKIP-DEP]` → `status: failed`

---
*Portable capability contract: `<agent-home>/capabilities/code-execute.md`; shared skill guidance: `<agent-home>/skills/code-execute/SKILL.md`.*
