---
name: code-execute
description: "plan 단계별 구현 실행 — 개발팀 디스패치 sub-skill"
argument-hint: "<plan name or path>"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "plan 단계별 구현 실행 — 개발팀 디스패치 sub-skill"
---

> **Stage-session entry (`standard+` dispatch, spec/stage-dispatch SD-2)**: runs either in-session (Skill tool) or as its own depth-2 headless session dispatched by the autopilot-code conductor. Input = the plan path (args) resolved below; it reads `plan/plan.md` from files, never prior-stage conversation. This is the **only source-mutating stage**; write class = source code + `plan/checklist.md`·`dev_logs/`·`_internal/dev_reviews/`·plan frontmatter `status`. 개발팀 delegation stays **inside** this session (its own in-session parallel dev-team is depth-uncounted).

> **Plan Resolution**: `$ARG`→plan 경로 해석은 [autopilot-code/references/arguments-and-decisions.md#plan-resolution](../autopilot-code/references/arguments-and-decisions.md) 단일 authority — 로드해 그 절차대로 해석한다.

> **Language Rule**: 사용자-facing 출력은 자연스러운 한국어. 단일 SoT = [arguments-and-decisions.md#language-rule](../autopilot-code/references/arguments-and-decisions.md).

## Commit Message Convention
- Safety checkpoint: `chore: Safety checkpoint before {plan-name} execution`
- Success commit: `{type}: {description}\n\n{bullet list of key changes}` — type: `feat`/`fix`/`refactor`/`chore`

## Git Safety Checkpoint
Before any code changes, ensure the working tree is clean and up-to-date:
0. **git working-state 게이트** ([OPERATIONS.md §5.9](../../core/OPERATIONS.md#59-git-working-state-preflight-worktreemerge-가드-canonical)) — 체크포인트 생성 _전_, 그리고 **각 success commit 직전** 재실행. merge/rebase/cherry-pick 진행 중·detached HEAD = STOP(사용자 보고, 자동 abort 안 함); 다른 worktree 동일 브랜치·upstream 앞섬·진입 시 dirty = WARN. 진입 시 `HEAD` 기억 → commit 직전 HEAD 가 바뀌었거나 새 `MERGE_HEAD` 생겼으면(밑에서 머지됨) STOP. worktree 여러 개로 작업하다 merge 끼는 자리를 닫는다.
1. Run `git fetch && git pull` to sync with the remote.
   - If pull fails due to merge conflicts: abort the pull (`git merge --abort`), warn the user, and stop. Do NOT proceed with execution.
2. Run `git status` to check for uncommitted changes.
3. If there are uncommitted changes:
   - **먼저 merge/rebase 진행 중인지 확인** — `git rev-parse -q --verify MERGE_HEAD` 성공 또는 `$(git rev-parse --git-dir)/rebase-merge`·`rebase-apply` 존재 시: `git add -A && git commit` 을 **하지 않는다** (반쯤 머지된 트리를 restore point 로 굳히는 사고). STOP 하고 사용자에 보고 (resume·직접 진입으로 step 0 게이트를 건너뛴 자리의 in-place 자기방어).
   - 진행 중인 머지가 없을 때만: `git add -A && git commit` with a commit message that accurately describes the current uncommitted changes (analyze the diff to write a meaningful message).
   - This commit serves as a restore point if rollback fails later.
4. Record the current commit hash: `git rev-parse HEAD` → save as `$SAFETY_COMMIT`.
   - `$SAFETY_COMMIT` is persisted into the checklist header during Initialization.

## Initialization
- Read the plan file at $ARG.
- The log directory is the task root folder (two levels up from `plan/plan.md`).
  - Example: `<artifact-root>/plans/2026-03-18_refactor_engine/plan/plan.md` → log dir is `<artifact-root>/plans/2026-03-18_refactor_engine/`
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
  - plan files (English/Korean) 는 실행 중 불변 — checklist 만 추적 갱신.

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
- 처리 가능한 모든 step 을 `[x]`/`[FAIL]` 까지 진행한다.

## QA Scaling
`qa_level` in plan frontmatter overrides auto-detect for ALL phases. Otherwise, detect per phase.

| Level | Auto-detect condition | Action |
|---|---|---|
| **Quick** | (via `--intensity quick` — inherited from autopilot-code) | 1× fast reviewer (Claude adapter: 품질관리팀 `model: "sonnet"`), single pass; major 🔴 issues are logged but the pipeline does NOT branch to rollback retry — issues propagate to `pipeline_summary.md` Decision Points instead |
| **Light** | ≤3 units, mechanical, single-variant | 1× fast reviewer |
| **Standard** | 4–10 units, logic changes, single module | 1× deep reviewer |
| **Thorough** | >10 units, cross-module/variant, architectural | 2–3× reviewers in parallel: A=correctness (deep), B=consistency (fast), C=safety (deep, >20 files) |
| **Adversarial** | Cross-variant (SE+SS+CSS), shared modules (utils/, network.py), or >20 files with architectural impact — **AND external adversary available** | Thorough-level 품질관리팀 + 1× external adversary (`codex-review-team` in Claude adapter) in parallel |

Thorough mode — A: bugs/logic/signature mismatches (deep); B: naming/conventions/dead code (fast); C: tensor shapes/None edge cases (deep). Each writes to `_internal/dev_reviews/phase_{NN}_{focus}.md`. All 🔴 from ANY agent must be addressed.

Adversarial mode — runs all Thorough agents PLUS an additional external adversary in the same parallel batch. Claude adapter uses `codex-review-team`, which runs `adversarial-review --wait --scope auto` and writes adapter-specific external review logs. All 🔴 from ANY agent must be addressed.

**External adversary availability check**: Before selecting Adversarial, run the adapter availability check (Claude adapter: `codex --version`, suppress stderr). If unavailable, fall back to Thorough silently. This check is skipped if `--intensity adversarial` is explicitly specified (fail loudly instead).

## Change Log & Phase Review
- Each 개발팀 subagent writes its own step log file in `{log_dir}/dev_logs/`.
  - See Initialization section for log directory convention.
  - The log contains exact old/new per Edit with a `Decision:` field explaining the rationale — the subagent creates this file itself.
- **When a phase completes**:
  1. **Assess QA level** from the phase's change scope (files changed, nature of changes) per the QA Scaling table above.
  2. Invoke 품질관리팀 accordingly:
     - **Light/Standard**: 1 agent. Prompt must include: the step log file names for THIS phase (in dev_logs/), the log directory path, the list of changed source files, and the review output file name. For Light mode, use fast reviewer (Claude adapter: pass `model: 'sonnet'` when invoking 품질관리팀).
     - Example: "Review this phase in code review mode. Log dir: [path]. Step logs for this phase: [file list]. Changed source files: [file list]. Write review results to: [path]/_internal/dev_reviews/phase_01.md. Return the file path and a one-line verdict only."
     - **Thorough**: 2-3 agents in parallel (single message, multiple Agent tool calls). Same base prompt, each with a different focus suffix and output file name. Use fast reviewer for the B (consistency) agent and deep reviewer for A (correctness) and C (safety).
     - **Adversarial**: same as Thorough, plus 1× external adversary (`codex-review-team` in Claude adapter) in the same parallel batch. External prompt: "Run adversarial-review on the current changes. Write results to: {log_dir}/_internal/dev_reviews/phase_{NN}_external.md (or adapter legacy path). Return the file path and a one-line verdict."
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
  Read `$SAFETY_COMMIT` → `git diff --name-only $SAFETY_COMMIT HEAD -- ':!<artifact-root>'` → `git checkout $SAFETY_COMMIT -- <changed files>` (preserves `<artifact-root>/`). Verify with `git status`. Note in Final Report.

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
