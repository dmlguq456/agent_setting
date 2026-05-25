---
name: code-execute
description: Execute an implementation plan with progress tracking
argument-hint: "<plan name or path>"
---

## Plan Resolution (canonical — keep in sync with code-execute, code-test, code-report, code-refine, autopilot-code)
Resolve `$ARG` to a plan file path:
1. If it ends with `.md` → use as-is
2. If it's a directory path → append `/plan/plan.md`
3. Otherwise, fuzzy search: `ls -d .claude_reports/plans/*$ARG* 2>/dev/null`
   - **1 match** → use `{match}/plan/plan.md`
   - **Multiple matches** → prefer folder without `_audit`/`_fix_` suffix; if still multiple, ask user
   - **No match** → report error

## Language Rule
- Think and reason in English internally. Write all user-facing output in Korean.

## Commit Message Convention
- Safety checkpoint: `chore: Safety checkpoint before {plan-name} execution`
- Success commit: `{type}: {description}\n\n{bullet list of key changes}` — type: `feat`/`fix`/`refactor`/`chore`

## Git Safety Checkpoint
Before any code changes, ensure the working tree is clean and up-to-date:
1. Run `git fetch && git pull` to sync with the remote.
   - If pull fails due to merge conflicts: abort the pull (`git merge --abort`), warn the user, and stop. Do NOT proceed with execution.
2. Run `git status` to check for uncommitted changes.
3. If there are uncommitted changes:
   - Run `git add -A && git commit` with a commit message that accurately describes the current uncommitted changes (analyze the diff to write a meaningful message).
   - This commit serves as a restore point if rollback fails later.
4. Record the current commit hash: `git rev-parse HEAD` → save as `$SAFETY_COMMIT`.
   - `$SAFETY_COMMIT` is persisted into the checklist header during Initialization.

## Initialization
- Read the plan file at $ARG.
- The log directory is the task root folder (two levels up from `plan/plan.md`).
  - Example: `.claude_reports/plans/2026-03-18_refactor_engine/plan/plan.md` → log dir is `.claude_reports/plans/2026-03-18_refactor_engine/`
- **Check for existing log directory** at `{log_dir}`:
  - If `{log_dir}/plan/checklist.md` already exists with `[x]`/`[FAIL]`/`[SKIP-DEP]` marks: this is a **resume**. Read the checklist, update the `Safety commit:` line with the current `$SAFETY_COMMIT`, and skip all completed steps. Continue from the first `[ ]` step.
  - Otherwise: this is a **fresh execution**. Proceed to create the log directory and checklist.
- **Create the log directory** and the checklist:
  1. `mkdir -p {log_dir}/dev_logs {log_dir}/_internal/dev_reviews`
  2. Write `{log_dir}/plan/checklist.md` — checklist derived directly from the English plan with the following header and body:
  ```
  Safety commit: {$SAFETY_COMMIT}

  Phase A: [description]
    [ ] Step 1: [file] — [what to change]
    [ ] Step 2: [file] — [what to change]
  Phase B: [description]
    [ ] Step 3: [file] — [what to change]
  ```
- Subagents will create their own step log files inside this directory (they have the Write tool).
- Use this checklist file as the sole tracking document for orchestration.
  - Mark `[x]` or `[FAIL]` as steps complete or fail.
  - Do NOT modify the plan files (neither English nor Korean) during execution.

## Rules
- Read the English checklist file before each step to decide what to do next.
- Implement all steps in the plan, in order of dependencies.
- **Delegate implementation to the dev-team (개발팀) agent as a subagent.**
  - Include "auto mode" in the prompt, and specify files/changes concretely.
  - Include the dev_logs directory path so the subagent can write its own step log file (e.g., `dev_logs/step_01_model_py.md`).
  - Launch multiple dev-team (개발팀) subagents in parallel for independent steps.
- After completing each step:
  - Mark `[x]` in the English checklist file
  - Syntax/import verification is handled by the code reviewer during phase review
- Do NOT stop until all processable steps are done (marked `[x]` or `[FAIL]`).

## QA Scaling
`qa_level` in plan frontmatter overrides auto-detect for ALL phases. Otherwise, detect per phase.

| Level | Auto-detect condition | Action |
|---|---|---|
| **Quick** | (manual via `--qa quick` only — inherited from autopilot-code) | 1× 품질관리팀 (`model: "sonnet"`), single pass; major 🔴 issues are logged but the pipeline does NOT branch to rollback retry — issues propagate to `pipeline_summary.md` Decision Points instead |
| **Light** | ≤3 units, mechanical, single-variant | 1× 품질관리팀 (`model: "sonnet"`) |
| **Standard** | 4–10 units, logic changes, single module | 1× 품질관리팀 (default opus) |
| **Thorough** | >10 units, cross-module/variant, architectural | 2–3× 품질관리팀 in parallel: A=correctness (opus), B=consistency (sonnet), C=safety (opus, >20 files) |
| **Adversarial** | Cross-variant (SE+SS+CSS), shared modules (utils/, network.py), or >20 files with architectural impact — **AND Codex available** | Thorough-level 품질관리팀 + 1× codex-review-team (`adversarial-review`) in parallel |

Thorough mode — A: bugs/logic/signature mismatches (opus); B: naming/conventions/dead code (sonnet); C: tensor shapes/None edge cases (opus). Each writes to `_internal/dev_reviews/phase_{NN}_{focus}.md`. All 🔴 from ANY agent must be addressed.

Adversarial mode — runs all Thorough agents PLUS an additional `codex-review-team` agent in the same parallel batch. The Codex agent runs `adversarial-review --wait --scope auto` and writes to `_internal/dev_reviews/phase_{NN}_codex.md`. All 🔴 from ANY agent (including Codex) must be addressed.

**Codex availability check**: Before selecting Adversarial, run `codex --version` (suppress stderr). If the command fails or Codex is not authenticated, fall back to Thorough silently. This check is skipped if `--qa adversarial` is explicitly specified (fail loudly instead).

## Change Log & Phase Review
- Each 개발팀 subagent writes its own step log file in `{log_dir}/dev_logs/`.
  - See Initialization section for log directory convention.
  - The log contains exact old/new per Edit with a `Decision:` field explaining the rationale — the subagent creates this file itself.
- **When a phase completes**:
  1. **Assess QA level** from the phase's change scope (files changed, nature of changes) per the QA Scaling table above.
  2. Invoke 품질관리팀 accordingly:
     - **Light/Standard**: 1 agent. Prompt must include: the step log file names for THIS phase (in dev_logs/), the log directory path, the list of changed source files, and the review output file name. For Light mode, explicitly pass `model: 'sonnet'` when invoking 품질관리팀.
     - Example: "Review this phase in code review mode. Log dir: [path]. Step logs for this phase: [file list]. Changed source files: [file list]. Write review results to: [path]/_internal/dev_reviews/phase_01.md. Return the file path and a one-line verdict only."
     - **Thorough**: 2-3 agents in parallel (single message, multiple Agent tool calls). Same base prompt, each with a different focus suffix and output file name. Pass `model: 'sonnet'` for the B (consistency) agent; A (correctness) and C (safety) use default opus.
     - **Adversarial**: same as Thorough, plus 1× `codex-review-team` agent in the same parallel batch. Codex prompt: "Run adversarial-review on the current changes. Write results to: {log_dir}/_internal/dev_reviews/phase_{NN}_codex.md. Return the file path and a one-line verdict."
     - `mkdir -p {log_dir}/_internal/dev_reviews` before first invocation.
     - The 품질관리팀 reads step logs (including Decision fields) and source files directly, then writes the review report to the specified file.
  2. **Read the review file** (skill-level read — permitted per DESIGN_PRINCIPLES 3.3) to determine next action:
     - 🟡 only: log in checklist and continue.
     - 🔴 minor: fix once via 개발팀 → re-verify (output `phase_{NN}_fix.md`). If still 🔴, treat as major.
     - 🔴 major: **auto-rollback phase and continue** (no user gating — per the family-wide "no autonomy gating" policy):
       1. Delegate rollback to 개발팀 — restore every `old_string` from the phase's step logs.
       2. If rollback fails: read `$SAFETY_COMMIT` from checklist header → `git checkout .` (reverts ALL uncommitted changes including prior phases). Mark ALL steps `[FAIL]` ("Reverted by git checkout due to rollback failure in Phase N"). **Stop and go to Final Report.**
       3. If rollback succeeded: mark all steps in this phase `[FAIL]` with reason.
       4. Continue to the next phase. If it depends on the failed phase, mark those steps `[SKIP-DEP]`.

> Record each rollback decision per the Decision Point Logging Rule. Decisions propagate up to the pipeline skill's pipeline_summary.md.

- For plans ≤3 steps, skip phase grouping — invoke reviewer once after all steps complete.
- **On Total Failure** (ALL steps `[FAIL]`/`[SKIP-DEP]` after Plan Status Update): **auto-rollback to safety commit** (no user gating).
  Read `$SAFETY_COMMIT` → `git diff --name-only $SAFETY_COMMIT HEAD -- ':!.claude_reports'` → `git checkout $SAFETY_COMMIT -- <changed files>` (preserves `.claude_reports/`). Verify with `git status`. Note in Final Report.

## Safety Rules (CRITICAL)
- CRITICAL: Before changing any function signature (args, return type, dict keys, tensor shapes): (1) grep all call sites, (2) update every caller, (3) check implicit contracts (None checks, `.shape` assumptions, dict key access).
- CRITICAL: If a step causes cascading errors beyond the plan's scope: mark `[FAIL]`, rollback via step log, continue to next step.
- Do NOT change code outside the plan's scope unless required by a signature change.

## Final Report
After all phases are processed, read the English checklist and report a summary to the user:
- List only `[FAIL]` and `[SKIP-DEP]` steps with their reasons.
- If all steps are `[x]`: report success, no need to list individual steps.
- At the end of the report, recommend the user run `/code-test <plan file path>` to verify functional correctness.
- This is the only progress report the user sees in standalone invocation. Include FAIL/SKIP-DEP reasons, overall verdict, and next command. For success-only runs a single-line verdict is sufficient; scale length with failure count.

## Plan Status Update
- When all steps are marked `[x]`: change the English plan's frontmatter `status` to `done`.
- When some steps are `[x]` and some are `[FAIL]`/`[SKIP-DEP]`: change status to `partial` and add a `failed_steps` field listing the failed step numbers.
- When ALL steps are `[FAIL]`/`[SKIP-DEP]` (no `[x]` steps): change status to `failed` and add a `failed_steps` field listing all step numbers.

## Task
Execute the plan at: $ARG
