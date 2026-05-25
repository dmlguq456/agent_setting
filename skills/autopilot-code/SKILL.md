---
name: autopilot-code
description: "Unified code pipeline — dev/debug modes. Orchestrates code-plan → code-refine → code-execute → code-test → code-report with mode-specific behavior."
argument-hint: "--mode dev|debug <task/plan/error description> [--from <step>] [--qa quick|light|standard|thorough|adversarial] [--user-refine]"
---

> **산출물 폴더 컨벤션**: [CONVENTIONS.md §5](../../CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier: T1 root / T2 named subdir / T3 `_internal/`). plan/ + checklist는 T1 (root). dev_logs/, test_logs/는 T2 (root). reviewer 로그(plan_reviews, dev_reviews, test_reviews)는 모두 `_internal/` 하위.

## Default Invocation Rule (메인 Claude 자동 라우팅)

본 skill 은 글로벌 [`CLAUDE.md`](../../CLAUDE.md) §6 "autopilot-* 호출 패턴" 의 _컨펌 의무_ 적용 대상. 메인 Claude 가 사용자 발화에서 아래 trigger 신호를 인지하면, 옵션 자동 구성 + 자연어 요약 컨펌 거쳐 invoke.

### Trigger 신호 (자연어 발화 예시)

**dev 모드**:
- "X 기능 만들어줘" / "Y 추가해줘" / "Z 구현해줘"
- "이 모듈 리팩토링" (단, 한두 줄 rename 은 `Agent(개발팀)` 우회)
- 기존 plan 폴더 발견 + 재개 신호 ("이어서 진행", "다음 stage 부터")

**debug 모드**:
- "이 에러 디버그해봐" / "X 가 안 돌아" / "왜 안 되지"
- 에러 로그 / traceback 첨부
- 테스트 fail 보고서 첨부

### Default 옵션 권장값 (컨펌 시 메인 Claude 가 제안)

- `--mode`: 발화 신호로 dev/debug 자동 추론. cwd 가 plan 폴더 + 최근 dev_log 있으면 dev 우세, 에러 로그·traceback 있으면 debug 우세.
- `--qa`: dev=thorough, debug=standard (default — global §6 high-stakes 신호 시 adversarial 자동 상향)
- `--from`: 자동 추론 (`pipeline_state.yaml` 발견 시 마지막 성공 stage 다음부터)
- `--user-refine`: **off** (글로벌 §4 — "사용자 검토 끼워" / "memo 추가하게 멈춰줘" 같은 명시 신호 있을 때만 켬)

### Override 1순위 — autopilot 우회

- 작은 작업 (한 줄 수정·rename·cleanup) — `Agent(개발팀)` 직접 호출 또는 직접 Edit
- 단발성 코드 리뷰 — `Agent(품질관리팀)` 직접 호출
- `/autopilot-code <args>` slash 직접 입력 — 컨펌 skip 하고 즉시 invoke

> 본 섹션은 `/sync-skills` 가 `~/.claude/README.md` 운영 룰 안내로 자동 반영.

## Language Rule
- When explaining something to the user, write in Korean.

## Argument Parsing

### --mode (REQUIRED)
- `--mode dev` — development pipeline (default if omitted)
- `--mode debug` — debug pipeline for runtime error diagnosis and fix
- If omitted: treat as `--mode dev` and warn: "모드가 지정되지 않았습니다. dev 모드로 기본 설정합니다."
- If invalid value: report error and stop.

### --from <step> (mode-specific)
- dev: plan|refine|execute|test|report (5 points)
  - **stage ↔ step 매핑**: `plan` = Step 1 (code-plan) / `refine` = Step 2 (code-refine + 연구팀 memos) / `execute` = Step 3 (code-execute) / `test` = Step 4 (code-test) / `report` = Step 5 (code-report)
- debug: not supported — always starts from diagnosis
- If --from is used with debug mode: warn "debug 모드에서는 --from이 지원되지 않습니다. 진단부터 시작합니다." and ignore.

### --qa <level>

QA 5 단계 정의 + 모델·round 매트릭스는 [`CONVENTIONS.md §1`](../../CONVENTIONS.md#1-qa-levels-canonical) 단일 source. 본 skill 적용:

- Supported: `quick` / `light` / `standard` / `thorough` (default) / `adversarial`
- Mode-specific:
  - dev: 5 levels 모두 accept. default `thorough`.
  - debug: `adversarial` 받으면 `thorough` 로 downgrade + warn. default `standard` (빠른 root-cause 우선).
- 유효하지 않은 값 → `standard` fallback + warn ("유효하지 않은 QA level '{value}'. standard 로 기본 설정합니다.")
- Auto-detect: omitted 시 각 sub-skill 이 scope 기반 추정
- **Propagation**: `--qa <level>` 를 code-plan / code-refine 에 flag 로 전달. code-execute / code-test / code-report 는 plan frontmatter `qa_level: <level>` 로
- **Mid-pipeline switching**: Step 2+ 에서 `--qa` 명시 시 plan frontmatter 갱신. 명시 안 하면 frontmatter 값 보존 (없으면 `thorough`)
- **`quick` interactions**: `--user-refine` silently ignored (refine skip). `--from refine` 으로 재개 시 frontmatter `qa_level == quick` 이면 abort ("qa_level=quick 에서는 refine 단계가 skip 됩니다. --qa <level> 을 다른 값으로 명시해 재개하세요.")

### --user-refine (boolean flag — opt-in only)

**Default: false. The orchestrator (메인 Claude) MUST NOT add this flag on its own — it is set only when the user typed `--user-refine` (or an explicit Korean equivalent like "사용자 검토 끼워" / "memo 추가하게 멈춰줘") in the original prompt.** Inferring this flag from generic "신중히 진행해 줘" / "한 번 봐줘" / 길고 복잡한 task 같은 신호로 자동 추가하는 행동 금지 — 그 경우 사용자가 의도하지 않은 pause 가 걸려 작업이 멈춘다.

When present, the orchestrator **pauses** at refine points so the user can add their own `<!-- memo: ... -->` comments on top of 연구팀's memos before code-refine runs.

- Applies to: **dev mode only** (Step 2 plan refine, and the failure-loop refine after test failure).
- Debug mode: 연구팀 review skipped → flag ignored with one-line warning.

**Pause behavior** (dev mode):
1. After 연구팀 writes memos at Step 2 (or after failure memos are written in the test-failure retry loop), do NOT invoke code-refine.
2. Update plan frontmatter: `user_refine: true`, `paused_at_stage: refine`.
3. Print to user (Korean) the memo file path and the resume command:
   ```
   연구팀 메모가 {ko_plan_path}에 기록되었습니다.
   직접 메모를 추가한 뒤 다음 명령으로 재개하세요:
       /autopilot-code --mode dev --from refine <plan-name>
   ```
4. Exit. Do NOT write pipeline_summary.md (pipeline is paused, not terminated).

**Resume behavior**: When invoked with `--from refine`, the orchestrator skips Step 1 and goes directly to Step 2's code-refine invocation, then continues normally.

**Persistence**: `user_refine: <true|false>` lives in the English plan's YAML frontmatter (same place as `qa_level`). On `--from` resume, if `--user-refine` is not re-specified, preserve the frontmatter value.

When `--from` is used together with `--user-refine` (dev only), `--from refine` is the natural resume point after a user-refine pause.

The remaining text (after removing flags) is the task description, plan name, or error description (depending on mode).

**When starting from Step 2+** (dev mode), the argument must be a plan name (not a task description). Use the Plan Resolution section below to locate the plan folder.

## Decision Defaults (no autonomy gating)

The pipeline runs with sane defaults and only pauses on genuinely ambiguous or destructive situations. There is no autonomy-level dial.

| Decision Point | Default Behavior |
|---|---|
| Test failure (after code-test internal hotfix loop) | Auto-retry once (mode dev). |
| Pipeline-level catastrophic failure (plan status = failed) | Stop and report; no retry. |
| Final retry failure | Auto-stop, write pipeline_summary(failed), report. |
| Research team adds many memos | Auto-refine (or pause if `--user-refine` is set). |
| code-plan: existing plan with status `active` | **Always ask** — no safe default; user must choose resume vs. create new. |
| code-plan: existing plan with status `done` / `failed` | Auto-create a new plan (note the previous one for reference). |
| code-plan: existing plan with status `partial` | Auto-create a new plan covering the failed steps (read `failed_steps` from frontmatter). |
| debug: confirm diagnosis before fix | Auto-proceed unless root cause is ambiguous. |
| debug: ambiguous root cause (multiple possible) | **Always ask** — list candidates, ask which to investigate first. |
| debug: fix verification failed | Auto-rollback + report. |
| debug: environment issue (not code bug) | Auto-report env-fix steps; do not modify code. |

**Logging**: When the pipeline pauses (active-plan ambiguity, ambiguous root cause, or `--user-refine`), record the event for the Decision Points table in `pipeline_summary.md`. Auto-decisions are not individually logged.

## Plan Resolution (canonical — keep in sync with code-execute, code-test, code-report, code-refine)
Resolve `$ARG` to a plan file path:
1. If it ends with `.md` → use as-is
2. If it's a directory path → append `/plan/plan.md`
3. Otherwise, fuzzy search: `ls -d .claude_reports/plans/*$ARG* 2>/dev/null`
   - **1 match** → use `{match}/plan/plan.md`
   - **Multiple matches** → prefer folder without `_audit`/`_fix_` suffix; if still multiple, ask user
   - **No match** → report error

## Pipeline: Mode dev
You (the main Claude) orchestrate by invoking each skill directly via the Skill tool. All tasks go through the full pipeline. The **연구팀** (research-team) agent is invoked only for Step 2 (plan review as user proxy) and Step 6 (meta-report).

> **자료팀 위임 (옵션, 2026-05-22 신설)** — task 가 _결과 시각화·실험 log plot·result table 정리_ 같은 분석 자료를 요구하면 code-execute / code-report 단계 안에서 `Agent(자료팀, "<spec>")` 직접 호출. _훈련·실험 실행_ 자체는 autopilot-code 본 영역, 결과의 _후처리·시각화_ 만 자료팀 영역. 자료팀이 figure / 스크립트 / 표 한 묶음 생성 후 dev_log 의 해당 step 안에 결과 자산 경로 박음.

### Step 1: code-plan
Invoke Skill: `code-plan` with the task description as args.
Wait for completion before proceeding.

### Step 2: code-refine (연구팀 as user proxy)
**`--qa quick` short-circuit**: if `qa_level == quick`, skip the entire 연구팀 review + code-refine invocation. Log to pipeline_summary Decision Points: `Step 2 | refine skipped (qa=quick) | auto | proceed to Step 3`. Proceed directly to Step 3.

Otherwise:
1. Resolve plan paths from code-plan output: `en_plan_path`, `ko_plan_path`, `log_dir`.
2. **Detect task type** before invoking 연구팀 (this hint provides the type-specific lens — see `agents/research-team.md` Role 1 Step 3 table):
   - Read the plan's "## Change Plan" target files. If any target is under `~/.claude/skills/*` / `~/.claude/agents/*` / `~/.claude/README.md` / `~/.claude/skills/.sync_state.json` → `task_type=meta-skill`.
   - If targets are under `~/.claude/settings.json` / `keybindings.json` / hooks → `task_type=infra/config`.
   - If targets are project source code (`.py`, `.cpp`, etc.) → `task_type=paper-driven code`.
   - If targets are under `.claude_reports/documents/*` → `task_type=paper-driven doc`.
   - If targets are under `.claude_reports/research/*` → `task_type=research artifact`.
   - Mixed → `task_type=mixed`.

   **By `qa_level`** (reviewer 수·model 매트릭스는 [CONVENTIONS.md §1.1](../../CONVENTIONS.md#11-5단계-공통-정의) 단일 source — 본 sub-skill 은 그 spec 을 instance·axis 분담으로 풀어씀):
   - **quick / light** — 1× / 2× sonnet single pass, all task-type axes 단일 prompt 로:
     ```
     Invoke 연구팀: "Review this plan as user proxy. **Task type: {task_type}** — apply ALL Role 1 Step 3 axes for this task type (no Focus axis). Korean plan: {ko_plan_path}. English plan: {en_plan_path}. Review log: {log_dir}/_internal/plan_reviews/research_review.md. Weight task-type-specific axes heavily (for meta-skill: family-level naming conflict + cross-skill scope overlap + sync-skills downstream + frontmatter validity)."
     ```
   - **standard / thorough / adversarial** — **axis-decomposed parallel 연구팀**: dispatch N parallel instances (standard = 1× opus + 2× sonnet, thorough/adversarial = 2× opus + 2× sonnet). 각 invocation 에 `Focus axis: <axis_name>` 포함해 single lens 로 제한. axis list 와 task-type 별 axis 매핑은 `agents/research-team.md` Role 1 _Multi-axis parallel mode_ 표 single source. opus instance 는 _깊이 axis_ (correctness / methodology / domain), sonnet instance 는 _coverage axis_ (completeness / style / cross-ref / test gap). 각 instance 는 `[<axis_name>]` prefix 메모 + separate review log (`{log_dir}/_internal/plan_reviews/research_review_<axis_name>.md`) 작성. 모든 parallel 완료 후 메모 merge + dedup → code-refine. adversarial 은 추가로 `Agent(codex-review-team)` external review parallel.
   - **Why decomposition at standard+**: 단일 instance 가 많은 axis 를 다루면 주의가 분산. parallel decomposition 으로 각 instance 가 좁게 집중해 사용자가 직접 잡아낼 만한 자리 (naming conflict / test coverage gap / style drift) 전부 커버.
3. If memos added:
   - **`--user-refine` pause**: if the flag is set (CLI or plan frontmatter), update plan frontmatter (`user_refine: true`, `paused_at_stage: refine`), print the resume command, and exit. Do NOT invoke code-refine.
   - Otherwise: invoke Skill `code-refine` with the Korean plan path.
4. If no memos: skip to Step 3.

### Step 3: code-execute
Invoke Skill: `code-execute` with the plan name/path as args.
Wait for completion before proceeding.

#### Status Check (between Step 3 and Step 4)
After code-execute completes, read the English plan's frontmatter `status` field:
- `done` → proceed to Step 4.
- `partial` → proceed to Step 4 (test what succeeded).
- `failed` → code-execute already rolled back source code. **STOP the pipeline.** Write pipeline_summary.md (status: failed) FIRST, then report failure to the user with the checklist summary. Do NOT proceed to code-test or code-report.

### Step 4: code-test
Invoke Skill: `code-test` with the plan name/path as args.
Wait for completion before proceeding.

## Retry Budget (Total)
- code-test internal hotfix loop: max 2 attempts per test run
- Mode dev retry loop: max 1 pipeline-level retry
- Total theoretical maximum: 2 (first code-test) + 2 (second code-test after retry) = 4 hotfix attempts
- At each code-test invocation, the hotfix counter resets.

#### Test Failure → Retry Loop (max 1 pipeline-level retry; quick = no retry)
**`--qa quick` short-circuit**: if `qa_level == quick` and code-test reports failure, do NOT retry. Skip the retry loop below and go directly to Step 5 (code-report) with status reflecting the test failure. Log to pipeline_summary Decision Points: `Step 4 | test failure, no retry (qa=quick) | auto | proceed to code-report`.

Otherwise (qa_level != quick), if code-test reports failure (after its internal hotfix loop of 2 attempts), auto-retry once:

1. **Collect failure context**: Note the test failure verdict from code-test's return. Failure details are in `test_logs/test_report.md` and `_internal/test_reviews/` — these will be consumed by code-refine's agent, not by the orchestrator.

2. **Rollback source code only** (preserve plan/log files):
   - Read Safety commit hash from `plan/checklist.md` header: `Safety commit: {hash}`
   - Run: `git checkout <safety-commit> -- <changed paths>` (NOT `.claude_reports/`)
   - Verify with `git status`

3. **Write failure memos into Korean plan**: Append `<!-- memo: [테스트 실패] code-test 실패. 상세: test_logs/test_report.md, _internal/test_reviews/. 대안 필요. -->` at relevant steps in `plan/plan_ko.md`.

4. **Reset checklist**: Reset all step marks in `plan/checklist.md` to `[ ]`.

5. **Loop back to Step 2**:
   - **`--user-refine` pause**: if the flag is set, update plan frontmatter (`user_refine: true`, `paused_at_stage: refine`), print the resume command (`/autopilot-code --mode dev --from refine <plan>`), and exit. The user can review the failure memos plus add their own before re-resuming.
   - Otherwise: invoke Skill `code-refine` with the plan path (QA review loop runs as usual, max 3 rounds).

6. **Re-execute**: Invoke Skill: `code-execute` with the same plan path.

7. **Re-test**: If plan status is not `failed`, invoke Skill: `code-test`.
   - **Pass** → continue to Step 5 (code-report).
   - **Fail again** → rollback, **STOP**. Write pipeline_summary.md (status: failed, note both attempts) FIRST, then report to user. Do NOT proceed to code-report.

### Step 5: code-report
Invoke Skill: `code-report` with the plan name/path as args.

### Step 6: Pipeline Summary Report
Write `pipeline_summary.md` per the **Pipeline Summary Template (mode=dev)** (see below).
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
Invoke Skill: `code-plan` with a fix task description:
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
- QA review still runs via code-plan's built-in Post-Plan Review Loop.
- If QA has 🔴 issues, let the review loop resolve them (max 3 rounds as usual).

### Step 4: Execute fix
Invoke Skill: `code-execute` with the fix plan path.
- Status check: if `failed`, report to user and stop.

### Step 5: Verify fix
Invoke Skill: `code-test` with the fix plan path.

**Additional verification**: After code-test passes, reproduce the original error scenario:
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
Invoke Skill: `code-report` with the fix plan path.

**pipeline_summary.md must be written BEFORE reporting to the user, regardless of success/failure path.** This is the first action upon reaching any terminal state (fixed, partial, unresolved, or stop). On failure path (Step 5 rollback), pipeline_summary.md is written as part of that failure path — do NOT skip it.

Write `pipeline_summary.md` per the **Pipeline Summary Template (mode=debug)** (see below).
Report to user: summary + verdict.

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
- Do NOT skip testing — always verify.
- Do NOT intervene in individual skill execution — let each skill handle its own QA loops.

### Mode dev
(No additional mode-specific rules beyond common.)

### Mode debug
- **Minimal scope**: Fix the bug only. Do not refactor, improve, or clean up surrounding code.
- **Preserve existing behavior**: The fix should not change behavior for cases that were already working.
- If the root cause is ambiguous (multiple possible causes), list them and ask the user which to investigate first — this is the only debug-mode pause point.
- If the root cause is an environment issue (not a code bug), auto-report env fix steps; do not modify code.
