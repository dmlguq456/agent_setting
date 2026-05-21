---
name: run-test
description: Run functional tests after execute-plan or on demand to verify code correctness
argument-hint: "<plan name, path, or test scope>"
---

## Plan Resolution (canonical — keep in sync with execute-plan, run-test, final-report, refine-plan, autopilot-code)
Resolve `$ARG` to a plan file path:
1. If it ends with `.md` → use as-is
2. If it's a directory path → append `/plan/plan.md`
3. Otherwise, fuzzy search: `ls -d .claude_reports/plans/*$ARG* 2>/dev/null`
   - **1 match** → use `{match}/plan/plan.md`
   - **Multiple matches** → prefer folder without `_audit`/`_fix_` suffix; if still multiple, ask user
   - **No match** → fallback: treat argument as a file/directory path for direct testing

Example: `/run-test inference-refactor` → `.claude_reports/plans/2026-03-18_inference-refactor/plan/plan.md`

## Language Rule
- Think and reason in English internally.
- Write all user-facing output in Korean.

## Delegate to 테스트팀
Invoke the **test-team** (테스트팀) agent as a subagent with the following prompt:

- If $ARG points to a plan file:
  ```
  Run graduated tests for plan: {$ARG}
  Read the plan's verification sections and the log directory's plan/checklist.md to identify targets.
  Execute Level 1 → 2 → 3 → 4 → 5 in order, stopping on first failure.
  ```

- If $ARG is a file/directory path:
  ```
  Run graduated tests on: {$ARG}
  Execute Level 1 → 2 → 3 → 4 → 5 in order, stopping on first failure.
  Skip levels that don't apply (e.g., Level 4 if no plan file).
  ```

- If $ARG is empty:
  ```
  Run graduated tests on recently changed files.
  Use git diff --name-only HEAD~1 to find targets.
  Execute Level 1 → 2 → 3 → 4 → 5 in order, stopping on first failure.
  Skip levels that don't apply (e.g., Level 4 if no plan file).
  ```

### Test Log Requirement (CRITICAL)
**Always** include this in the 테스트팀 prompt. Every test must record: exact command, full stdout/stderr (last 50 lines if long), and PASS/FAIL verdict with error message.

```
Write a detailed test log to: {log_dir}/test_logs/test_report.md

Format:
## Level N: [Level Name]
### Test N.1: [description]
**Command:** [exact command]
**Output:** [stdout/stderr]
**Verdict:** PASS / FAIL — [reason]
```

## QA Requirements (Mandatory Thorough, Adversarial if Codex available)
**run-test always uses at minimum Thorough mode (2 parallel QA agents).** The `qa_level` flag does NOT apply to run-test — testing rigor is non-negotiable.

**Adversarial auto-escalation**: Before launching QA, run `codex --version 2>/dev/null`. If Codex is available and authenticated, automatically escalate to Adversarial mode (add Codex agent to the parallel batch). If Codex is unavailable, proceed with Thorough.

**Always launch 2 QA agents in parallel** (Agent A with `model: 'sonnet'` for the coverage checklist; Agent B with default opus for accuracy diagnosis):
- Agent A (sonnet): "Focus on **coverage**: Were ALL changed files tested? Are any untested code paths or edge cases? Did tests use real data where available? Are behavioral changes compared before/after?"
- Agent B (opus): "Focus on **accuracy**: Are failures correctly diagnosed (not misdiagnosed as pre-existing)? Were correct engine_modes used? Do commands match changed code paths? Are negative tests present?"
- Each writes to: `_internal/test_reviews/test_review_coverage.md`, `_internal/test_reviews/test_review_accuracy.md`.

**Adversarial (when Codex available):**
- Agent C (Codex): 1× codex-review-team (`adversarial-review --wait --scope auto`). Writes to `_internal/test_reviews/test_review_codex.md`.
- Launched in the same parallel batch as Agent A and B.

All issues from ANY agent (including Codex) must be addressed before proceeding.

## Post-Test: QA Review
After the 테스트팀 agent returns:
1. **Read the test log** (skill-level read — permitted per DESIGN_PRINCIPLES 3.3) (`{log_dir}/test_logs/test_report.md`).
2. **Invoke 2× 품질관리팀 in parallel** (Agent A with `model: 'sonnet'`, Agent B with default opus):

   - **Agent A prompt (coverage)**:
   ```
   Review this test report in code review mode.
   Test log: {log_dir}/test_logs/test_report.md
   Changed source files: [list from plan or git diff]
   Review focus (COVERAGE): untested files/paths, real vs. random data, missing before/after comparisons.
   Write review to: {log_dir}/_internal/test_reviews/test_review_coverage.md
   Return the file path and a one-line verdict.
   ```

   - **Agent B prompt (accuracy)**:
   ```
   Review this test report in code review mode.
   Test log: {log_dir}/test_logs/test_report.md
   Changed source files: [list from plan or git diff]
   Review focus (ACCURACY): correct failure diagnosis, correct engine_modes, commands match changed paths, negative tests present.
   Write review to: {log_dir}/_internal/test_reviews/test_review_accuracy.md
   Return the file path and a one-line verdict.
   ```

3. **Read both QA reviews** (skill-level read — permitted per DESIGN_PRINCIPLES 3.3). If either finds issues: re-invoke 테스트팀 for those items, appending to test_report.md. If both pass: proceed to result reporting.

## Commit Message Convention
- Safety checkpoint: `chore: Safety checkpoint before {plan-name} execution`
- Success commit: `{type}: {plan goal summary}\n\n{bullet list of key changes from checklist}`
- Type prefix: `feat` (new functionality), `fix` (bug fix), `refactor` (code restructuring), `chore` (maintenance) — determined from the plan's goal

## Report Results
1. Relay the test results to the user (concise summary table).
2. If all levels passed and QA approved:
   - Check `git status` for uncommitted changes. If changes exist: **auto-commit** with a success commit message following the Commit Message Convention above (no user gating — per the family-wide "no autonomy gating" policy).
   - Report success and stop.
3. If any level failed, enter the **Hotfix Loop** (max 2 attempts):

### Hotfix Loop
> Note: This loop is self-contained within a single run-test invocation. If the calling pipeline retries, this loop resets.

1. **Attempt 1** (always automatic — low risk): Invoke a 개발팀 (dev-team) subagent in auto mode with the failing level, exact error, files involved, and instruction: "Auto mode. Hotfix: fix the following test failure. Read the error, read the file, fix it directly. Write a step log to the plan's log directory if available, otherwise skip logging."
2. Re-invoke 테스트팀 from the failed level onward (same logging requirements).
3. If tests pass AND QA approves: auto-commit and report success.
4. **Attempt 2** (always automatic — repeated failure but bounded retry budget): repeat with new error context.
5. If still failing after 2 attempts: report failure with original error, what was attempted, and suggested next steps.

> Record each commit / hotfix outcome per the Decision Point Logging Rule. run-test keeps decisions in memory; they propagate up to the pipeline skill's pipeline_summary.md.

## Log Directory Resolution
- If $ARG points to a plan file: log directory is the task root (grandparent of `plan/plan.md`).
  Example: `.claude_reports/plans/2026-03-18_refactor/plan/plan.md` → `.claude_reports/plans/2026-03-18_refactor/`
- If no plan file: use `.claude_reports/tests/` with a date-stamped subdirectory.

## Task
Test: $ARG
