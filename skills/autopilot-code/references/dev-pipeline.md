## Pipeline: Mode dev
You orchestrate the stages below. Stage graph is selected by `--intensity` before QA. `direct` skips this full pipeline and performs produce + sanity/report only; `quick` uses inline micro-plan + plan-check-lite and focused verification — **both run inline** (no stage dispatch). `standard+` uses the full durable pipeline below. Step 2 (plan review as user proxy) is used only when the selected graph calls for it; UI/visual → `디자인팀`, 그 외 → `연구팀`; Step 6 (meta-report) = 연구팀.

> **Stage-dispatch orchestration (`standard+` default, 2026-07-10 — OPERATIONS §5.10 ③④, spec/stage-dispatch SD-1·SD-2)**: for `standard+`, the depth-1 owner runs as a **thin conductor**. Instead of invoking each stage skill in-session via the Skill tool, it **dispatches each stage as its own depth-2 headless session** with `adapters/claude/bin/dispatch-headless.py --depth 2 --parent <conductor-slug> --worker-role code-<stage> --owner autopilot-code --model-role <stage role, CONVENTIONS §2.3>` (codex/opencode: `bin/preflight.sh dispatch` 동형). The dispatch prompt carries only {sub-skill name, **input artifact absolute paths**, output artifact contract, qa/intensity, slug} — never plan bodies or prior-stage conversation; each stage reads its inputs from files (§2.1). The conductor reads only verdict/status (plan frontmatter `status`, `test_report.md` Level) to drive gate branches, not stage bodies. Register each stage in `.dispatch/jobs.log`, watch liveness (§5.10 stealth-death), and keep `Σ(conductor + active stage) ≤ 5`. Micro-stages that write no new artifact or emit a one-line verdict (plan-check self-check, ≤3-step integration review) stay inline.
>
> **one-shot wait (SD-14)**: the conductor is a one-shot process — ending the turn ends the process, so a background completion notification never arrives. After dispatching a stage, do **not** end the turn on a Monitor/notification wait; poll in the same turn with `sh <agent-home>/utilities/dispatch-wait.sh --parent <conductor-slug>` (exit 0 = stage done → harvest; exit 2 = still alive → call it again; exit 3 = SUSPECT/DEAD → diagnose via dispatch-liveness + transcript tail, then re-dispatch, do not keep waiting). `<agent-home>` = `$(utilities/agent-home.sh)`.
>
> **In-session Skill fallback = closed two-condition set** (not an open escape hatch): the in-session Skill path is used **only when [a] intensity is `direct`/`quick` (micro-stages, no dispatch) or [b] the runtime has no headless dispatch (codex/opencode `preflight.sh` reports unavailable)**. In all other `standard+` cases, dispatch is **mandatory, not optional** — the stage skills are the same contract either way.
>
> **usage-aware cross-harness dispatch (SD-16 — OPERATIONS §5.10 ⑧)**: stages are not pinned to Claude. Before dispatching, the conductor checks both harnesses' limit state deterministically with `sh <agent-home>/utilities/usage-check.sh` (per-harness `ok | limited(<reset>) | unknown`; a conservative jobs.log dead-limit-marker + reset-cache read — no scriptable official usage API exists as of 2026-07, so `ok` means "no known block", not a guarantee). Route **complementarily**: (a) **usage failover** — avoid a `limited` harness, route the stage to the one with headroom (Claude blocked → dispatch the stage via codex `preflight.sh dispatch`; and vice-versa), when both are free, weight the split by the capacity bias (the `bias <harness>` line of usage-check — `HARNESS_CAPACITY_BIAS`, default `claude` while the Claude Code quota exceeds Codex's, a mutable assumption, never hardcoded): bulk stages ride the bias harness, the other harness is saved for high-value spots (cross-family checks, failover); (b) **strength placement** — put a stage on the harness/model that fits it, and prefer to **cross the model family for the check stage** (a code-test/review worker on a different family than the code-execute maker — different failure modes = review diversity, the codex-review-team precedent). Initial conservative weighting = limit-avoidance > fit > spread (SD-OPEN-3). Cross-harness stage rows keep the same `--depth 2 --parent <conductor-slug> --worker-role …` shape and carry `harness=`/`owner_harness=`/`parent_sid` so the fleet view stays continuous across harnesses.
>
> **limit-death is self-closing (SD-15 — OPERATIONS §5.10 ⑨)**: if a dispatched stage dies at launch on a session/usage limit, `dispatch-headless.py` closes its own `.dispatch/jobs.log` row `done,note=dead-<reason>` (with `reset=<time>` when the log shows one) and prints `early_death=<reason>`; `dispatch-wait`/`dispatch-liveness` also read the dispatch log's limit pattern as a DEAD basis. The wrapper does **not** retry — on a surfaced `early_death`/DEAD, the conductor decides re-dispatch vs. cross-harness failover (above), it is not automatic.

> **자료팀 위임 (옵션)** — task 가 _결과 시각화·실험 log plot·result table 정리_ 같은 분석 자료를 요구하면 code-execute / code-report 단계 안에서 `Agent(자료팀, "<spec>")` 직접 호출. _훈련·실험 실행_ 자체는 autopilot-code 본 영역, 결과의 _후처리·시각화_ 만 자료팀 영역. 자료팀이 figure / 스크립트 / 표 한 묶음 생성 후 dev_logs/ 의 해당 step 안에 결과 자산 경로 박음.

### Step 1: code-plan
Skip entirely for `intensity=direct`; use inline micro-plan only for `quick`.

For `standard+`, **dispatch** code-plan as its own depth-2 session (do not invoke it in-session). First ensure the **SD-13 spec precondition**: the target repo has an artifact root and a `spec/` (or `/track` untracked) — a stage session runs full ceremony including the artifact-guard create-order gate, so catch a missing precondition here (free) rather than inside the stage (a wasted re-dispatch). Then:

```
AGENT_HOME=$(utilities/agent-home.sh)
REPORTS_DIR=.agent_reports; [ -d .claude_reports ] && [ ! -d .agent_reports ] && REPORTS_DIR=.claude_reports
python3 "$AGENT_HOME/adapters/claude/bin/dispatch-headless.py" --start \
  --worktree "$PWD" --slug <cycle-slug> \
  --capability code-plan --mode dev --qa <qa> --intensity <intensity> \
  --depth 2 --parent <cycle-slug> --worker-role code-plan --owner autopilot-code \
  --model-role "deep maker" --profile code-plan \
  --prompt-text "<sub-skill contract + input artifact ABSOLUTE paths + output contract + slug>"
```

Then poll + harvest in the **same turn** (one-shot wait contract, SD-14):

```
sh "$AGENT_HOME/utilities/dispatch-wait.sh" --parent <cycle-slug>   # exit 0=done · 2=re-call · 3=diagnose
```

Loop the dispatch-wait call until exit 0, then read only the plan frontmatter `status` + plan paths (verdict/status, not the plan body) to drive Step 2. On exit 3, diagnose via `dispatch-liveness.sh` + transcript tail → re-dispatch that stage (reuse existing artifacts, SD-6). **The dispatch prompt carries input artifact paths only — never the plan body or prior-stage conversation.**

**[direct/quick] or [headless-unavailable runtime] fallback**: invoke Skill `code-plan` with the task description as args (in-session), then proceed.

### Step 2: plan-check / optional code-refine

This step exists only for durable `standard+` graphs. `direct` has no plan-check and `quick` already performed inline `plan-check-lite` before produce.

> **Inline micro-stage** (SD-6): the plan-check self-check is **not a dispatched stage** — it writes no new durable artifact and emits a one-line verdict, so the conductor runs it inline. When it decides an *independent* review is warranted, that review is a bounded depth-2 review sub-worker (§5.10 ④(a)), distinct from the code-* stage-workers. A blocking finding triggers a `code-refine` correction (Step 6-style memo loop), not a full re-dispatch here.

1. Resolve plan paths from code-plan output: `en_plan_path`, `ko_plan_path`, `log_dir`.
2. Decide whether the selected graph calls for independent plan review:
   - `standard`: one lightweight construction/domain review when risk warrants it.
   - `strong`: one independent review at the riskiest point.
   - `thorough|adversarial`: bounded depth2 or multi-axis reviewers may run; each reviewer gets one focus axis and returns a short memo/log.
   - UI/visual plan risk uses 디자인팀 critic; research/domain risk uses 연구팀 plan-review; construction quality uses 품질관리팀 plan-review.
3. If memos or blocking findings exist:
   - if `--user-refine` is set, pause with `paused_at_stage: refine` and print the resume command.
   - otherwise invoke `code-refine` once per selected correction budget. Do not open repeated QA loops merely because `--qa` is high.
4. If no memos or no independent review was selected, proceed to Step 3.

### Step 3: code-execute
For `standard+`, **dispatch** code-execute as its own depth-2 session — same `dispatch-headless.py --start` template as Step 1 with `--capability code-execute --worker-role code-execute --model-role "fast implementer" --profile code-execute`. Input = the `plan/plan.md` absolute path (carried in the dispatch prompt, not the plan body). Poll + harvest with `dispatch-wait --parent <cycle-slug>` in the same turn; on exit 3, diagnose → re-dispatch.

After harvest, the conductor reads the plan frontmatter `status` from the **file** (the Status Check below now reads the file, not an in-session return).

**[direct/quick] or [headless-unavailable runtime] fallback**: invoke Skill `code-execute` with the plan name/path as args (in-session).

#### Status Check (between Step 3 and Step 4)
After code-execute completes, read the English plan's frontmatter `status` field:
- `done` → proceed to Step 4.
- `partial` → proceed to Step 4 (test what succeeded).
- `failed` → code-execute already rolled back source code. **STOP the pipeline.** Write pipeline_summary.md (status: failed) FIRST, then report failure to the user with the checklist summary. Do NOT proceed to code-test or code-report.

### Step 4: code-test
For `standard+`, **dispatch** code-test as its own depth-2 session — same `dispatch-headless.py --start` template with `--capability code-test --worker-role code-test --model-role "fast reviewer" --profile code-test` (the conductor may raise the role to a deeper reviewer at strong+). Input = the `plan.md` verification section + `checklist.md` paths. Poll + harvest with `dispatch-wait --parent <cycle-slug>`; then the conductor reads `test_logs/test_report.md` Level verdict from the **file** to drive the retry branch. On exit 3, diagnose → re-dispatch.

**[direct/quick] or [headless-unavailable runtime] fallback**: invoke Skill `code-test` with the plan name/path as args (in-session).

## Retry Budget (Caller-Owned)
- `code-test` is read-only final verification and does not hotfix.
- Mode dev retry loop: max 1 bounded pipeline-level retry when the selected assurance allows it.
- `quick` does not retry automatically; it reports the failed verify-lite result.

#### Test Failure → Retry Loop (max 1 pipeline-level retry; quick = no retry)
**`--qa quick` short-circuit**: if `qa_level == quick` and code-test reports failure, do NOT retry. Skip the retry loop below and go directly to Step 5 (code-report) with status reflecting the test failure. Log to pipeline_summary Decision Points: `Step 4 | test failure, no retry (qa=quick) | auto | proceed to code-report`.

Otherwise (qa_level != quick), if code-test reports failure and the selected graph allows a fix-loop, auto-retry once:

1. **Collect failure context**: Note the test failure verdict from code-test's return. Failure details are in `test_logs/test_report.md` and `_internal/test_reviews/` — these will be consumed by code-refine's agent, not by the orchestrator.

2. **Rollback source code only** (preserve plan/log files):
   - Read Safety commit hash from `plan/checklist.md` header: `Safety commit: {hash}`
   - Run: `git checkout <safety-commit> -- <changed paths>` (NOT `<artifact-root>/`)
   - Verify with `git status`

3. **Write failure memos into Korean plan**: Append `<!-- memo: [테스트 실패] code-test 실패. 상세: test_logs/test_report.md, _internal/test_reviews/. 대안 필요. -->` at relevant steps in `plan/plan_ko.md`.

4. **Reset checklist**: Reset all step marks in `plan/checklist.md` to `[ ]`.

5. **Loop back to Step 2**:
   - **`--user-refine` pause**: if the flag is set, update plan frontmatter (`user_refine: true`, `paused_at_stage: refine`), print the resume command (`/autopilot-code --mode dev --from refine <plan>`), and exit. The user can review the failure memos plus add their own before re-resuming.
   - Otherwise: invoke Skill `code-refine` with the plan path using the selected correction budget. Do not open a repeated QA loop by default.

   The conductor-side rollback (`git checkout <safety-commit> -- <changed paths>`) stays conductor-side: it reads the Safety commit from `plan/checklist.md` (a file read, fine for the thin conductor).

6. **Re-execute**: For `standard+`, **re-dispatch** code-execute (same Step 3 dispatch template + dispatch-wait harvest) with the same plan path. Fallback (direct/quick or headless-unavailable): invoke Skill `code-execute`.

7. **Re-test**: If plan status is not `failed`, **re-dispatch** code-test (same Step 4 dispatch template + dispatch-wait harvest); fallback = invoke Skill `code-test`.
   - **Pass** → continue to Step 5 (code-report).
   - **Fail again** → rollback, **STOP**. Write pipeline_summary.md (status: failed, note both attempts) FIRST, then report to user. Do NOT proceed to code-report.

### Step 5: code-report
For `standard+`, **dispatch** code-report as its own depth-2 session — same `dispatch-headless.py --start` template with `--capability code-report --worker-role code-report --model-role "fast writer" --profile code-report`. Input = plan/checklist/dev_logs/test_logs/_reviews paths. Poll + harvest with `dispatch-wait --parent <cycle-slug>`; the conductor reads the report path/headline from the file.

**[direct/quick] or [headless-unavailable runtime] fallback**: invoke Skill `code-report` with the plan name/path as args (in-session).

### Step 6: Pipeline Summary Report
> **동시성 가드 (공유 `<artifact-root>`)**: `pipeline_summary.md`·`pipeline_state.yaml` 등 `spec/` 공유 단일파일 쓰기 _직전_ **OPERATIONS.md §5.8** `.pipeline-lock` 획득, 쓰기 직후 해제(짧게 보유). spec-drift 로 prd.md 갱신(§ "Spec 영향 변경 감지" → autopilot-spec update) 시도 lock 경유(해당 skill 이 자체 획득). `plans/<cycle>/` 쓰기는 경로 분리라 비-lock. BLOCKED(`exit 3`) 면 쓰기 멈추고 사용자 보고.

Write `pipeline_summary.md` per the **Pipeline Summary Template (mode=dev)** (see below).
Then report to the user: pipeline_summary.md path + 2-3 line verdict.

### Step 7: analysis_project/code/ 영향 자리 자동 update (혼합 분기)

코드 변경 후 `<artifact-root>/analysis_project/code/` 자료가 _drift_ 빠지지 않게 — autopilot-code 가 _final-report 직후_ 영향 범위 검사 + 분기.

#### 7-1. 영향 범위 검사

`dev_logs/` 또는 `git diff <safety-commit>..HEAD --name-only` 으로 변경 파일 list 추출. 다음 분류:

| 변경 종류 | 분기 |
|---|---|
| 한 module 안 함수·class·signature·rename / 한 줄 자리 수정 / 작은 logic 추가 | **(A) 직접 Edit** — autopilot-code 가 `analysis_project/code/<module>.md` 의 _interface_reference_ 표 / docstring 자리 직접 Edit (별도 skill 호출 X) |
| 새 module 추가 / 새 모델 폴더 추가 / module 삭제·rename / cleanup 큰 자리 / config 메커니즘 변경 / preferred layer 변경 / train·eval 분리 / seed·reproducibility 자리 변경 | **(B) analyze-project 자동 호출** — `/analyze-project --mode code` invoke (incremental 자동 — `_last_run.yaml` 발견 시 변경 자리만 재분석, `--skip-qa` 가벼움) |

판단 — _변경 파일 N 자리_ + _영향 받는 산출물 자리 종류_:
- 변경 파일 ≤ 3 + 한 module 안 + interface_reference 만 영향 → (A)
- 변경 파일 ≥ 4 또는 module 추가/삭제 또는 4 종 실험 자료 영향 → (B)
- 애매한 자리 → (B) 안전 default

#### 7-2. (A) 직접 Edit 대상

| 산출물 자리 | autopilot-code 가 직접 update |
|---|---|
| `analysis_project/code/<module>.md` 의 _interface_reference_ 표 | 변경 함수·class 한 행 추가·수정·제거 (Called by 컬럼 포함) |
| `analysis_project/code/<module>.md` 의 _Role / 본문_ | signature 변경 자리만 한 줄 정도 — 큰 본문 재작성 자리는 (B) |

#### 7-3. (B) analyze-project 자동 호출

```bash
/analyze-project --mode code --skip-qa
# default incremental — _last_run.yaml 발견 시 변경 파일만 재분석
# --skip-qa — autopilot-code 의 final-report 가 이미 검증된 자리, 추가 QA cost 절감
```

호출 결과:
- 변경 module 분석 .md update
- 4 종 실험 자료 영향 자리 update
- `_last_run.yaml` 갱신
- 사용자에게 _한 줄 보고_ — "analysis_project/code/ 자료 N 자리 자동 갱신"

#### 7-4. 사용자 skip 옵션

사용자 발화 `"분석 자료 update skip"` / `"--no-analyze-update"` 명시 시 본 Step 7 skip.

#### 7-5. mode debug 자리

debug 의 _수정 자리_ 도 동일 logic 적용 (Step 6 후) — 보통 _작은 변경_ 자리라 (A) 직접 Edit 우세.
