## Pipeline Summary Template (all modes)

**Write `{log_dir}/pipeline_summary.md` as the FIRST action on reaching any terminal state** (success, partial, failed, stop) — before reporting to the user, on all paths.

This is a process log and artifact index — NOT a change analysis (that's code-report's job).

Populate the Decision Points table from in-memory decision records. If none: `| - | No gated decisions triggered | - | - |`.

```markdown
# {mode_title}: {task_or_error_name}

- **Date**: {YYYY-MM-DD}
- **Status**: done / partial / failed{debug: " / unresolved"}
{mode_specific_fields}
- **User-Refine**: {true | false}

## Process Log
| Step | Skill/Action | Result | Notes |
|---|---|---|---|
{mode_specific_rows}

## Artifacts
{mode_specific_artifacts}

## Decision Points
| Step | Decision | User Response | Action Taken |
|---|---|---|---|
```

### Mode-specific fields

| Field | dev | debug |
|---|---|---|
| Title prefix | "Pipeline Summary" | "Debug Pipeline Summary" |
| Extra header fields | `Plan: {en_plan_path}` | `Error: {msg}` + `Root Cause: {diagnosis}` + `Fix Plan: {path}` + `Attempts: {N}` |
| Process Log rows | Steps 1-5 + 4R (retry: refine→execute→test) | Steps 1-6 (Step 1=Diagnosis, no row for Step 3) |
| Artifacts | plan/ (T1), dev_logs/ (T2), test_logs/ (T2), _internal/{plan_reviews,dev_reviews,test_reviews}/ (T3), final_report | same minus research artifacts |

## Safety Rules

### Common (all modes)
- If execution fails catastrophically (plan status = `failed`), stop and report to user immediately.
- Always verify — testing 은 모든 path 에서 실행.
- QA/verification responsibility follows the selected stage graph: stage-local gates stay small, independent QA runs only when selected, and final verification stays concrete.

### Mode dev
(No additional mode-specific rules beyond common.)

### Mode debug
- **Minimal scope**: Fix the bug only. Do not refactor, improve, or clean up surrounding code.
- **Preserve existing behavior**: The fix should not change behavior for cases that were already working.
- If the root cause is ambiguous (multiple possible causes), list them and ask the user which to investigate first — this is the only debug-mode pause point.
- If the root cause is an environment issue (not a code bug), auto-report env fix steps; do not modify code.
