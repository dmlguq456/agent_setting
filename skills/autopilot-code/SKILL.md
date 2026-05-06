---
name: autopilot-code
description: "Unified code pipeline — dev/audit/debug modes. Orchestrates init-plan → refine-plan → execute-plan → run-test → final-report with mode-specific behavior."
argument-hint: "--mode dev|audit|debug <task/plan/error description> [--from <step>] [--qa light|standard|thorough|adversarial] [--user-refine]"
---

## Language Rule
- When explaining something to the user, write in Korean.

## Argument Parsing

### --mode (REQUIRED)
- `--mode dev` — development pipeline (default if omitted)
- `--mode audit` — audit pipeline for post-dev review
- `--mode debug` — debug pipeline for runtime error diagnosis and fix
- If omitted: treat as `--mode dev` and warn: "모드가 지정되지 않았습니다. dev 모드로 기본 설정합니다."
- If invalid value: report error and stop.

### --from <step> (mode-specific)
- dev: plan|refine|execute|test|report (5 points)
- audit: plan|execute|test|report (4 points, no refine)
- debug: not supported — always starts from diagnosis
- If --from is used with debug mode: warn "debug 모드에서는 --from이 지원되지 않습니다. 진단부터 시작합니다." and ignore.

### --qa <level>
- `--qa light` → sonnet, single reviewer
- `--qa standard` → opus, single reviewer (default)
- `--qa thorough` → opus, parallel reviewers
- `--qa adversarial` → opus, parallel reviewers + Codex adversarial-review.
- Mode-specific validation:
  - dev: accepts light|standard|thorough|adversarial (4 levels)
  - audit: accepts light|standard|thorough|adversarial (4 levels)
  - debug: accepts light|standard|thorough only. If adversarial passed → downgrade to thorough + warn.
- If the value is not one of the accepted levels for the mode, treat as `standard` and warn the user: "유효하지 않은 QA level '{value}'. standard로 기본 설정합니다."
- If omitted, each skill auto-detects level based on scope.
- **Propagation**: Pass `--qa <level>` to init-plan and refine-plan as a flag. For execute-plan, run-test, and final-report, write `qa_level: <level>` into the English plan's frontmatter at Step 1 or Step 3 initialization.
- **Mid-pipeline switching**: When starting from Step 2+ AND `--qa` is explicitly passed, update `qa_level` in the existing plan's YAML frontmatter before invoking the sub-skill. Explicit CLI flag always overrides frontmatter. If `--qa` is NOT passed on resume, preserve the existing frontmatter value (or default to `standard` if absent).

### --user-refine (boolean flag)
When present, the orchestrator **pauses** at refine points so the user can add their own `<!-- memo: ... -->` comments on top of 연구팀's memos before refine-plan runs.

- Applies to: **dev mode only** (Step 2 plan refine, and the failure-loop refine after test failure).
- Audit mode: no refine step → flag ignored with one-line warning.
- Debug mode: 연구팀 review skipped → flag ignored with one-line warning.

**Pause behavior** (dev mode):
1. After 연구팀 writes memos at Step 2 (or after failure memos are written in the test-failure retry loop), do NOT invoke refine-plan.
2. Update plan frontmatter: `user_refine: true`, `paused_at_stage: refine`.
3. Print to user (Korean) the memo file path and the resume command:
   ```
   연구팀 메모가 {ko_plan_path}에 기록되었습니다.
   직접 메모를 추가한 뒤 다음 명령으로 재개하세요:
       /autopilot-code --mode dev --from refine <plan-name>
   ```
4. Exit. Do NOT write pipeline_summary.md (pipeline is paused, not terminated).

**Resume behavior**: When invoked with `--from refine`, the orchestrator skips Step 1 and goes directly to Step 2's refine-plan invocation, then continues normally.

**Persistence**: `user_refine: <true|false>` lives in the English plan's YAML frontmatter (same place as `qa_level`). On `--from` resume, if `--user-refine` is not re-specified, preserve the frontmatter value.

When `--from` is used together with `--user-refine` (dev only), `--from refine` is the natural resume point after a user-refine pause.

The remaining text (after removing flags) is the task description, plan name, or error description (depending on mode).

**When starting from Step 2+** (dev/audit modes), the argument must be a plan name (not a task description). Use the Plan Resolution section below to locate the plan folder.

## Decision Defaults (no autonomy gating)

The pipeline runs with sane defaults and only pauses on genuinely ambiguous or destructive situations. There is no autonomy-level dial.

| Decision Point | Default Behavior |
|---|---|
| Test failure (after run-test internal hotfix loop) | Auto-retry once (mode dev; mode audit auto-stops with no retry). |
| Pipeline-level catastrophic failure (plan status = failed) | Stop and report; no retry. |
| Final retry failure | Auto-stop, write pipeline_summary(failed), report. |
| Research team adds many memos | Auto-refine (or pause if `--user-refine` is set). |
| init-plan: existing plan with status `active` | **Always ask** — no safe default; user must choose resume vs. create new. |
| init-plan: existing plan with status `done` / `failed` | Auto-create a new plan (note the previous one for reference). |
| init-plan: existing plan with status `partial` | Auto-create a new plan covering the failed steps (read `failed_steps` from frontmatter). |
| audit: existing audit plan conflict | Auto-decide by status — `active` → resume; `done`/`partial`/`failed` → create new. |
| audit: test failure | Auto-rollback audit changes + stop (dev changes already committed). |
| debug: confirm diagnosis before fix | Auto-proceed unless root cause is ambiguous. |
| debug: ambiguous root cause (multiple possible) | **Always ask** — list candidates, ask which to investigate first. |
| debug: fix verification failed | Auto-rollback + report. |
| debug: environment issue (not code bug) | Auto-report env-fix steps; do not modify code. |

**Logging**: When the pipeline pauses (active-plan ambiguity, ambiguous root cause, or `--user-refine`), record the event for the Decision Points table in `pipeline_summary.md`. Auto-decisions are not individually logged.

## Plan Resolution (canonical — keep in sync with execute-plan, run-test, final-report, refine-plan)
Resolve `$ARG` to a plan file path:
1. If it ends with `.md` → use as-is
2. If it's a directory path → append `/plan/plan.md`
3. Otherwise, fuzzy search: `ls -d .claude_reports/plans/*$ARG* 2>/dev/null`
   - **1 match** → use `{match}/plan/plan.md`
   - **Multiple matches** → prefer folder without `_audit`/`_fix_` suffix; if still multiple, ask user
   - **No match** → report error

### Audit-specific Post-Resolution
(This is ONLY executed when mode=audit)
After resolving the dev plan path: read `status` from dev plan frontmatter — if `failed`, stop. Read `$DEV_SAFETY_COMMIT` from `plan/checklist.md` header (`Safety commit:` line); fallback: `git log --oneline -1`.

## Existing Audit Plan Detection (mode=audit only)
Before creating a new audit plan, check if an audit plan already exists:
- Search for `{dev_plan_folder_name}_audit` in `.claude_reports/plans/`
- If found AND `--from plan` (default):
  - Read its frontmatter `status`:
    - `active`: An incomplete audit exists. Auto-decide — resume existing audit plan.
    - `done`/`partial`/`failed`: Auto-decide — note for reference and create a new audit plan.
- If found AND `--from` is execute/test/report: use the existing audit plan.

## Pipeline: Mode dev
You (the main Claude) orchestrate by invoking each skill directly via the Skill tool. All tasks go through the full pipeline. The **연구팀** (research-team) agent is invoked only for Step 2 (plan review as user proxy) and Step 6 (meta-report).

### Step 1: init-plan
Invoke Skill: `init-plan` with the task description as args.
Wait for completion before proceeding.

### Step 2: refine-plan (연구팀 as user proxy)
1. Resolve plan paths from init-plan output: `en_plan_path`, `ko_plan_path`, `log_dir`.
2. Invoke **연구팀** (research-team) agent: "Review this plan as user proxy. Korean plan: {ko_plan_path}. English plan: {en_plan_path}. Review log: {log_dir}/plan_reviews/research_review.md."
3. If memos added:
   - **`--user-refine` pause**: if the flag is set (CLI or plan frontmatter), update plan frontmatter (`user_refine: true`, `paused_at_stage: refine`), print the resume command, and exit. Do NOT invoke refine-plan.
   - Otherwise: invoke Skill `refine-plan` with the Korean plan path.
4. If no memos: skip to Step 3.

### Step 3: execute-plan
Invoke Skill: `execute-plan` with the plan name/path as args.
Wait for completion before proceeding.

#### Status Check (between Step 3 and Step 4)
After execute-plan completes, read the English plan's frontmatter `status` field:
- `done` → proceed to Step 4.
- `partial` → proceed to Step 4 (test what succeeded).
- `failed` → execute-plan already rolled back source code. **STOP the pipeline.** Write pipeline_summary.md (status: failed) FIRST, then report failure to the user with the checklist summary. Do NOT proceed to run-test or final-report.

### Step 4: run-test
Invoke Skill: `run-test` with the plan name/path as args.
Wait for completion before proceeding.

## Retry Budget (Total)
- run-test internal hotfix loop: max 2 attempts per test run
- Mode dev retry loop: max 1 pipeline-level retry
- Total theoretical maximum: 2 (first run-test) + 2 (second run-test after retry) = 4 hotfix attempts
- At each run-test invocation, the hotfix counter resets.

#### Test Failure → Retry Loop (max 1 pipeline-level retry)
If run-test reports failure (after its internal hotfix loop of 2 attempts), auto-retry once:

1. **Collect failure context**: Note the test failure verdict from run-test's return. Failure details are in `test_logs/test_report.md` and `test_reviews/` — these will be consumed by refine-plan's agent, not by the orchestrator.

2. **Rollback source code only** (preserve plan/log files):
   - Read Safety commit hash from `plan/checklist.md` header: `Safety commit: {hash}`
   - Run: `git checkout <safety-commit> -- <changed paths>` (NOT `.claude_reports/`)
   - Verify with `git status`

3. **Write failure memos into Korean plan**: Append `<!-- memo: [테스트 실패] run-test 실패. 상세: test_logs/test_report.md, test_reviews/. 대안 필요. -->` at relevant steps in `plan/plan_ko.md`.

4. **Reset checklist**: Reset all step marks in `plan/checklist.md` to `[ ]`.

5. **Loop back to Step 2**:
   - **`--user-refine` pause**: if the flag is set, update plan frontmatter (`user_refine: true`, `paused_at_stage: refine`), print the resume command (`/autopilot-code --mode dev --from refine <plan>`), and exit. The user can review the failure memos plus add their own before re-resuming.
   - Otherwise: invoke Skill `refine-plan` with the plan path (QA review loop runs as usual, max 3 rounds).

6. **Re-execute**: Invoke Skill: `execute-plan` with the same plan path.

7. **Re-test**: If plan status is not `failed`, invoke Skill: `run-test`.
   - **Pass** → continue to Step 5 (final-report).
   - **Fail again** → rollback, **STOP**. Write pipeline_summary.md (status: failed, note both attempts) FIRST, then report to user. Do NOT proceed to final-report.

### Step 5: final-report
Invoke Skill: `final-report` with the plan name/path as args.

### Step 6: Pipeline Summary Report
Write `pipeline_summary.md` per the **Pipeline Summary Template (mode=dev)** (see below).
Then report to the user: pipeline_summary.md path + 2-3 line verdict.

## Pipeline: Mode audit

### Step 1: Generate audit task + init-plan
Invoke Skill: `init-plan` with an audit task description that includes:
- Source: `Audit changes from: {dev_en_plan_path}` and `Git diff: {dev-safety-commit}..HEAD`
- Review scope (5 areas): Bugs, Consistency, Safety, Missed spots, Suboptimal patterns. Scope: ONLY files changed in the dev cycle.

Plan folder: `.claude_reports/plans/{YYYY-MM-DD}_{original-task-name}_audit/`. Wait for completion.

### Step 1.5: Quick review (optional)

**Trigger:** run if EITHER: (1) audit plan has >10 steps, OR (2) git diff touches `model.py`, `modules/module.py`, or `modules/network.py`.

**When triggered:** Invoke 연구팀 with the audit plan path for one lightweight review pass (memo insertion only — no refine-plan loop). Include: `Review log file: {log_dir}/plan_reviews/research_review.md`. Wait for completion.

**Otherwise:** skip and proceed to Step 2.

### Step 2: execute-plan
Invoke Skill: `execute-plan` with the audit plan path.
- Status check: same rules as Mode dev, Step 3.

### Step 3: run-test
Invoke Skill: `run-test` with the audit plan path.
- **NO retry loop** (max 0 retries). If tests fail after the internal hotfix loop (2 attempts), auto-rollback and stop:
  - Rollback audit changes only: determine changed paths from checklist or git diff. The audit plan's safety commit is stored in its own `plan/checklist.md` header, written by execute-plan during audit execution. Run `git checkout <audit-safety-commit> -- <changed paths>`
  - This restores to post-dev state (dev changes are already committed).
  - Write pipeline_summary.md (status: failed) FIRST, then report to user, and stop.

### Step 4: final-report
Invoke Skill: `final-report` with the audit plan path.

### Step 5: Pipeline Summary Report
Write `pipeline_summary.md` per the **Pipeline Summary Template (mode=audit)** (see below).
Then report to the user: pipeline_summary.md path + 2-3 line verdict.

## Pipeline: Mode debug

### Step 1: Diagnose — trace root cause
Do NOT delegate this step. You (the main Claude) perform the diagnosis directly.

1. **Parse the error & check runtime context**: Extract error type, message, traceback, affected file/line. Run `git log --oneline -10` and `git diff HEAD~3`; check config/checkpoint files if relevant.
2. **Read the relevant code**: Follow the call stack or error location. Read the source files.
3. **Identify root cause**: Determine whether the issue is in:
   - Code logic (bug introduced by recent changes)
   - Environment (missing files, wrong config state, missing dependencies)
   - Data (corrupted checkpoint, wrong format, missing keys)
   - Interaction (code is correct individually but breaks when combined)
4. **Report diagnosis to user** in Korean:
   ```
   ## 진단 결과
   - **에러**: {error type and message}
   - **위치**: {file:line}
   - **근본 원인**: {root cause explanation}
   - **영향 범위**: {what else might be affected}
   - **수정 방향**: {proposed fix approach}
   ```
5. **Diagnosis confirmation**:
   - If the root cause is **unambiguous** (single clearly-identified cause): auto-proceed to fix plan.
   - If the root cause is **ambiguous** (multiple plausible causes): list the candidates and ask the user which to investigate first before creating the fix plan. This is the only debug-mode pause point.

### Step 2: Create fix plan
Invoke Skill: `init-plan` with a fix task description:
```
Fix: {root cause summary}

Error: {error message}
Location: {file:line}
Root cause: {diagnosis from Step 1}
Proposed fix: {fix approach}

Scope: Minimal — fix the root cause only. Do not refactor or improve surrounding code.
```

The plan folder will be: `.claude_reports/plans/{YYYY-MM-DD}_fix_{short-error-name}/`

### Step 3: Review fix plan (QA only, skip research-team)
- Skip 연구팀 review — debugging fixes should be fast.
- QA review still runs via init-plan's built-in Post-Plan Review Loop.
- If QA has 🔴 issues, let the review loop resolve them (max 3 rounds as usual).

### Step 4: Execute fix
Invoke Skill: `execute-plan` with the fix plan path.
- Status check: if `failed`, report to user and stop.

### Step 5: Verify fix
Invoke Skill: `run-test` with the fix plan path.

**Additional verification**: After run-test passes, reproduce the original error scenario:
- If the user provided a specific command that triggered the error, re-run it.
- If the error was during training, run a short training session (1-2 epochs).
- If the error was during inference, run an inference test.
- Report whether the original error is resolved.

If tests fail or the original error persists, auto-rollback and then proceed to reporting.

On rollback path:
1. **Rollback**: Determine changed paths from checklist or git diff. Read the Safety commit hash from the fix plan's `plan/checklist.md` header line: `Safety commit: {hash}`. Run `git checkout <safety-commit> -- <changed paths>`
2. **Write pipeline_summary.md (status: unresolved)** BEFORE reporting to the user. See Step 6 for the format.
3. **Report to user** with:
   - Original diagnosis
   - What was attempted
   - Why it didn't work
   - Suggested manual investigation steps

### Step 6: Report
Invoke Skill: `final-report` with the fix plan path.

**pipeline_summary.md must be written BEFORE reporting to the user, regardless of success/failure path.** This is the first action upon reaching any terminal state (fixed, partial, unresolved, or stop). On failure path (Step 5 rollback), pipeline_summary.md is written as part of that failure path — do NOT skip it.

Write `pipeline_summary.md` per the **Pipeline Summary Template (mode=debug)** (see below).
Report to user: summary + verdict.

## Pipeline Summary Template (all modes)

**Write `{log_dir}/pipeline_summary.md` as the FIRST action on reaching any terminal state** (success, partial, failed, stop) — before reporting to the user, on all paths.

This is a process log and artifact index — NOT a change analysis (that's final-report's job).

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

| Field | dev | audit | debug |
|---|---|---|---|
| Title prefix | "Pipeline Summary" | "Audit Pipeline Summary" | "Debug Pipeline Summary" |
| Extra header fields | `Plan: {en_plan_path}` | `Dev Plan: {path}` + `Audit Plan: {path}` + `Dev Safety Commit: {hash}` | `Error: {msg}` + `Root Cause: {diagnosis}` + `Fix Plan: {path}` + `Attempts: {N}` |
| Process Log rows | Steps 1-5 + 4R (retry: refine→execute→test) | Steps 1, 1.5, 2-4 | Steps 1-6 (Step 1=Diagnosis, no row for Step 3) |
| Artifacts | plan/, dev_logs/, dev_reviews/, test_logs/, test_reviews/, final_report | same + audit-specific prefixes | same minus research artifacts |

## Safety Rules

### Common (all modes)
- If execution fails catastrophically (plan status = `failed`), stop and report to user immediately.
- Do NOT skip testing — always verify.
- Do NOT intervene in individual skill execution — let each skill handle its own QA loops.

### Mode dev
(No additional mode-specific rules beyond common.)

### Mode audit
- Audit failures do NOT roll back dev cycle changes — dev changes are already committed. Rollback scope is audit changes only.

### Mode debug
- **Minimal scope**: Fix the bug only. Do not refactor, improve, or clean up surrounding code.
- **Preserve existing behavior**: The fix should not change behavior for cases that were already working.
- If the root cause is ambiguous (multiple possible causes), list them and ask the user which to investigate first — this is the only debug-mode pause point.
- If the root cause is an environment issue (not a code bug), auto-report env fix steps; do not modify code.
