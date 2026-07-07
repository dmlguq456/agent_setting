## Language Rule
- When explaining something to the user, write in Korean.

## Argument Parsing

### --mode (REQUIRED)
- `--mode dev` — development pipeline (default if omitted)
- `--mode debug` — debug pipeline for runtime error diagnosis and fix
- `--mode audit` — 코드베이스/앱 전수 자체점검 → 병렬 리뷰 fan-out → 트리아지 → 저위험 자동수정(검증) + 위험건 플래그. 상세 = "Pipeline: Mode audit".
- If omitted: treat as `--mode dev` and warn: "모드가 지정되지 않았습니다. dev 모드로 기본 설정합니다."
- If invalid value: report error and stop.

### --from <step> (mode-specific)
- dev: plan|refine|execute|test|report (5 points)
  - **stage ↔ step 매핑**: `plan` = Step 1 (code-plan) / `refine` = Step 2 (code-refine + 연구팀 memos) / `execute` = Step 3 (code-execute) / `test` = Step 4 (code-test) / `report` = Step 5 (code-report)
- debug: not supported — always starts from diagnosis
- If --from is used with debug mode: warn "debug 모드에서는 --from이 지원되지 않습니다. 진단부터 시작합니다." and ignore.

### --intensity <level>

Pipeline intensity is the stage-graph selector (canonical: [CONVENTIONS.md §1](../../core/CONVENTIONS.md#1-pipeline-intensity-stage-graph-and-assurance-canonical)).

- `direct`: `intake -> produce -> sanity/report`; no code-plan, no plan-check, no durable plan artifact.
- `quick`: `intake -> orient-lite -> micro-plan -> plan-check-lite -> produce -> verify-lite -> report`; no independent QA after every stage.
- `standard`: durable `code-plan -> plan-check -> code-execute -> code-test -> code-report`.
- `strong`: standard plus one risk-focused independent review.
- `thorough` / `adversarial`: depth-1 owner may open bounded depth-2 planner/verifier/adversary workers and must synthesize short reports.

`plan-check` is required for every non-`direct` graph, but expensive independent QA is not repeated after every sub-stage by default.

### --qa <level>

QA assurance policy는 [`CONVENTIONS.md §1.1`](../../core/CONVENTIONS.md#11-qa-assurance-levels-canonical)이 단일 source다. `--qa`는 stage graph 선택자가 아니라 `plan-check`, selected independent review, final `code-test`의 강도 override다. Depth2 dispatch는 `--qa thorough`가 아니라 `--intensity thorough|adversarial`에서만 열린다.

- Supported: `quick` / `light` / `standard` / `thorough` / `adversarial`.
- Code track에는 fact-checker가 없다. Ground truth는 코드, tests, runtime behavior, API/CLI surface, security review다.
- `quick`: inline micro-plan + plan-check-lite + produce + verify-lite. `code-plan`, `code-refine`, 반복 independent QA, durable `plans/{date}_{slug}/`는 기본적으로 열지 않는다.
- `standard`: durable `code-plan -> code-execute -> code-test -> code-report` with lightweight plan-check and concrete verification.
- `strong`: standard graph plus one risk-focused independent review at the riskiest point.
- `thorough|adversarial`: depth-1 owner may open bounded depth2 planner/verifier/adversary workers and must synthesize their short reports before write-back.
- Security review: auth / crypto·secrets / external input / api_contract / deserialization changes under adversarial risk may add `roles/modes/qa/security-review.md`; claim it only if the pass actually ran.
- Invalid value: fall back to the selected intensity's default assurance and warn.

Propagation: durable `standard+` cycles store the selected `qa_level` and `intensity` in plan/frontmatter or pipeline state. `code-plan`, optional `code-refine`, and `code-test` inherit that context. Mid-pipeline `--qa` can raise/lower assurance for future checks, but it must not rewrite the stage graph by itself.

### --user-refine (boolean flag — opt-in only)

**Default: false. The orchestrator (메인 에이전트) MUST NOT add this flag on its own — it is set only when the user typed `--user-refine` (or an explicit Korean equivalent like "사용자 검토 끼워" / "memo 추가하게 멈춰줘") in the original prompt.**
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
| Test failure after code-test verdict | Caller/orchestrator may open one bounded retry/fix stage in mode dev. |
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
3. Otherwise, fuzzy search (project-keyed — search across all projects): `ls -d <artifact-root>/plans/*/*$ARG* 2>/dev/null`
   - **1 match** → use `{match}/plan/plan.md`
   - **Multiple matches** → prefer folder without `_audit`/`_fix_` suffix; if still multiple, ask user
   - **No match** → report error
