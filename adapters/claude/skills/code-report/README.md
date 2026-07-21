# code-report

> This README summarizes the portable capability for users and maintainers. The model-neutral contract lives under `<agent-home>/capabilities/`; `SKILL.md` in this directory provides shared guidance for runtime-specific projections.

## Overview

Generate a detailed change report from the plan and execution logs. Focus on material changes, underlying reasoning, and reusable insights.

## Invocation

```text
/code-report <plan name or path>
```

## Plan resolution

The single authority for resolving `$ARG` to a plan is [autopilot-code plan resolution](../autopilot-code/references/arguments-and-decisions.md#plan-resolution).

## Model and QA policy

Use one fast writer. The report synthesizes artifacts already checked by plan, code, and test review stages. Do not add another report-review loop or external adversary. `qa_level` is prompt context only and does not change the writer role.

## Report Assembly — `editorial/report` unit

Inputs: the canonical plan, `plan/checklist.md`, `dev_logs/`, `test_logs/`, `_internal/{plan_reviews,dev_reviews,test_reviews}/`, and any existing required language companion.

Procedure:

1. Read the goal, baseline, and change plan.
2. Identify successful, failed, and skipped checklist steps.
3. Read every `dev_logs/step_*.md`; extract each old → new change and recorded decision.
4. Read `_internal/dev_reviews/phase_*.md` and the corresponding plan/test review directories; extract findings and resolutions.
5. Update documentation only for successful steps. Follow the existing mapping to `analysis_project/code/` and Interface Reference tables. Verify class and function line numbers against the post-edit source.
6. Confirm documentation changes exist with `git diff --stat`; redo the documentation step if the intended diff is empty.
7. Read `pipeline_summary.md` and extract actual Decision Points.
8. Synthesize causes, effects, and the larger design context instead of listing events mechanically.

## Report structure

Localize headings to the report language while preserving this information architecture:

```markdown
# Change Report: {task name}
- Date / Plan / Status: ✅ / ⚠️ / ❌

## 1. Overview — what changed and why
## 2. Material Changes — grouped by logical category
   ### 2.N {category} — {file or module}
   - Change / reason / principle / affected surface
## 3. Design Insights — reusable takeaways
## 4. QA Summary — findings, resolutions, unresolved items
## 4.5 Autonomous Decisions — narrative summary of Decision Points
## 5. Failed or Skipped Steps — reasons, or a clean-success statement
## 6. Follow-up Notes — watch-outs and next work
```

## Quality guidelines

- Extract insight; emphasize *why* and what future work should remember.
- State concrete effects such as callers, tensor shapes, and configuration keys.
- Connect changes to the project's design.
- Write in the user's communication language unless the user or report audience requests another language. Preserve identifiers, paths, and precise technical terms.
- Scale length to the change: roughly one to three pages.

## Post-report reconciliation

After the `editorial/report` unit returns:

1. Read `final_report.md` once.
2. Compare it with concrete orchestration evidence from the current run:
   - Step counts, review rounds, test results, commit hash, and file counts.
   - Line numbers, which frequently drift.
   - Follow-up state, especially stale `pending` labels.
   - Deviations reported by execution or review stages.
3. Brief the user in their communication language with final status and commit, three to five deliverables, any discrepancy, and the clearest next step.
4. Do not run additional report QA. Reconciliation is a lightweight evidence check, not a new review stage.

Persistent memory may inform the agent's judgment, but it is not a fixed report schema or an authority that overrides current repository and run evidence.

---

*Portable capability contract: `<agent-home>/capabilities/code-report.md`; shared skill guidance: `<agent-home>/skills/code-report/SKILL.md`.*
