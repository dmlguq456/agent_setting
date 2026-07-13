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

The plan folder will be: `<artifact-root>/plans/{YYYY-MM-DD}_fix_{short-error-name}/`

### Step 3: Review fix plan (plan-check only)
- Skip 연구팀 review by default — debugging fixes should be fast and minimal.
- Run a focused plan-check on the fix plan only when the selected assurance/risk requires it.
- If blocking issues appear, apply one bounded correction; do not open the old multi-round code-plan QA loop.

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

## Pipeline: Mode audit

_코드베이스/앱 "전수 자체점검 + 자율 수정"_ 자리. 발화 예: "전수 점검해서 더 효율적·효과적인 동작/UI 까지 컨펌없이 고쳐", "병렬 검토 많이 돌려". dev=새 기능 / debug=에러 진단 과 구분 — audit = _있는 것 전반을 훑어 개선_.

> **audit mode vs 빌트인 `audit` 스킬**: 본 mode = _소스 코드·UI·동작_ 점검+수정. 빌트인 `audit` 스킬 = `<artifact-root>/{plans,documents,research}` _산출물_ 린트 (대상 다름). 앱 점검은 본 mode.

오케스트레이션은 main, 리뷰·수정은 fan-out. 산출물 `plans/<date>_audit/` (findings·triage·fixes·flagged).

### Step 1: Review fan-out (병렬, 읽기전용)
`Workflow` 로 다수 병렬 리뷰어 — _영역 × 차원_. 규모는 요청에 맞춤 ("많이/전수" → 10~16+).
- UI·시각·반응형·a11y → `agentType: 디자인팀` (render-aware). 코드·동작·perf·일관성·데이터레이어 → `agentType: 품질관리팀` (code-review).
- 각 리뷰어: 코드 직접 읽고(+가능 시 렌더) 구조화 finding — `{title, severity, category, files, proposed_fix, risk(low/med/high), confidence}`. **읽기전용 — finding 만 작성.** 코드로 확인한 것만 보고 (모호하면 제외).

### Step 2: Triage (1 에이전트)
중복 병합, 저가치·과도·모호·confidence<0.6 드롭. 남은 것 분류:
- **autofix** — `risk=low` + 개선 명확 (토큰·문구·일관성·a11y 속성·단순 중복 추출 등). **파일 겹침 없는 클러스터로** 묶음 (병렬 수정 충돌 방지).
- **flagged** — `risk med/high` (동작 변경·구조·스키마·데이터·판단 필요) → 자동수정 말고 보고.

### Step 3: Fix (autofix 클러스터)
**⚠️ worktree 는 _현재 main(HEAD)_ 에서 판다** — `git worktree add <repo>-wt/audit-<key> -b <branch> main`. **`Workflow` 의 `isolation:'worktree'` 를 자율수정 fan-out 에 쓰지 말 것** (실측 2026-06-15: isolation worktree 가 32커밋 뒤 stale base 로 잡혀 머지 시 그간 작업을 revert — 5000줄+ 삭제 diff. review/triage 는 isolation 무방, _수정_ 만 명시 current-main worktree 로). 심링크(node_modules·.cache·<artifact-root>·.env.local) 후 클러스터별 헤드리스 `claude -p "/autopilot-code …"` 분사(또는 팀 위임).
- 각 fixer: 그 클러스터만 적용 (scope creep 금지·토큰 계약 준수) → **검증: `tsc --noEmit` 0 + full `next build`(DB 있어야 page-data 통과 → `.cache` 심링크 필수) + UI 변경은 디자인팀 verifier 실화면(light/dark/mobile390)** → 커밋. merge 안 함.

### Step 4: Harvest + Report
오케스트레이터(main)가 검증된 fix 브랜치를 **순차 머지** (§5.10 — 클러스터 비겹침이라 충돌 0, diff 실내용 확인 후) → `:3020` 등 full build 재확인. flagged 는 묶어 보고 (사용자 결정 또는 후속 dev/debug cycle). pipeline_summary 에 findings·autofix·flagged·dropped 수 기록.

### audit mode 규율
- 자율 (per-fix 컨펌 X) 이되 **검증 게이트 필수** — 미검증 머지 금지. risky 는 _자동수정 말고 flag_.
- 리뷰 = 읽기전용. 수정 base = 현재 HEAD (stale 금지). 머지 = 오케스트레이터. 사용자는 flagged 결정만.
