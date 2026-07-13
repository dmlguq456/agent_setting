# code-execute

> 본 README 는 Claude adapter skill 요약. 권위 있는 Claude runtime 동작 명세는 같은 폴더의 `SKILL.md`; portable capability 의미는 `<agent-home>/capabilities/`.

## 개요
구현 계획을 progress tracking과 함께 실행하는 skill. dev-team 서브에이전트에 step별 위임, phase마다 품질관리팀 리뷰, Git Safety Checkpoint 설정.

## 호출 형식
```
/code-execute <plan name or path>
```

## Plan Resolution
> `$ARG`→plan 경로 해석 단일 authority = [autopilot-code/references/arguments-and-decisions.md#plan-resolution](../autopilot-code/references/arguments-and-decisions.md).

## 커밋 메시지 규칙
- Safety checkpoint: `chore: Safety checkpoint before {plan-name} execution`
- Success: `{type}: {description}\n\n{key changes}` — type: feat/fix/refactor/chore

## Git Safety Checkpoint
1. `git fetch && git pull` — merge conflict 시 abort + 사용자 경고 후 중단
2. `git status` — uncommitted 있으면 diff 분석 후 의미 있는 commit 생성 (rollback 거점)
3. `git rev-parse HEAD` → `$SAFETY_COMMIT`으로 저장 → checklist 헤더에 기록

## 초기화
- plan 파일 읽기
- **로그 디렉토리 = plan/plan.md의 조부모** (예: `<artifact-root>/plans/2026-03-18_refactor/`)
- **기존 로그 디렉토리 확인**:
  - `checklist.md`에 `[x]`/`[FAIL]`/`[SKIP-DEP]` 있음 → **resume**: Safety commit 업데이트, 완료 step skip, 첫 `[ ]`부터
  - 그 외 → 신규 실행
- `mkdir -p {log_dir}/dev_logs {log_dir}/dev_reviews`
- `checklist.md` 작성

## 규칙
- 각 step 전에 checklist 읽기
- **개발팀 subagent에 step 단위 위임** (auto mode, 파일·변경 구체 명시, dev_logs 경로 포함)
- 독립 step은 subagent 병렬 launch
- step 완료 시 `[x]` 또는 `[FAIL]` 마킹
- 처리 가능 step 모두 끝날 때까지 중단 금지

## QA Scaling
plan frontmatter의 `qa_level`이 모든 phase auto-detect를 override.

| Level | 조건 | 행동 |
|---|---|---|
| Quick | `--intensity quick` 시 (autopilot-code에서 전파) | 1× fast reviewer, 1-pass; 🔴 이슈는 `pipeline_summary.md` Decision Points에 기록만 |
| Light | ≤3 units, 기계적, 단일 variant | 1× fast reviewer |
| Standard | 4-10 units, 로직, 단일 모듈 | 1× deep reviewer |
| Thorough | >10 units, cross-module, 아키텍처 | 2-3× 병렬: A 정확성(deep) / B 일관성(fast) / C 안전(deep) |
| Adversarial | Cross-variant, shared modules, >20 files + external adversary | Thorough + 1× external adversary |

## Change Log & Phase Review
각 개발팀 subagent가 `dev_logs/step_*.md` 작성 (old/new + `Decision:` 필수).

**phase 완료 시**:
1. QA level 평가 → 품질관리팀 호출
2. 리뷰 파일 확인:
   - 🟡: 로그 후 계속
   - 🔴 minor: 개발팀 1회 수정 → 재검증. 여전히 🔴이면 major로 승격
   - 🔴 major: **auto-rollback + continue** (사용자 질문 없음)
3. 롤백 절차:
   1. 개발팀에 롤백 위임 (step log의 old_string 복원)
   2. 실패 시 `$SAFETY_COMMIT` → `git checkout .` (모든 미커밋 revert, 이전 phase 포함). 모든 step `[FAIL]` → Final Report
   3. 성공 시 phase step `[FAIL]` + 다음 phase. 의존 step은 `[SKIP-DEP]`

- ≤3 steps → phase 그룹핑 생략, 모든 step 완료 후 한 번 리뷰
- **Total Failure**: **auto-rollback to safety commit** (사용자 질문 없음)

## 안전 규칙 (중요)
- 시그니처 변경 전: grep 모든 call site, 모든 caller 업데이트, 묵시적 계약 확인
- cascading 에러가 plan 범위를 초과하면: `[FAIL]` 마킹, step log로 롤백, 다음 step
- plan 범위 밖 코드 변경 금지 (시그니처 변경 요구 시는 예외)

## Final Report
모든 phase 처리 후 사용자 보고:
- `[FAIL]` / `[SKIP-DEP]` step + 이유만 리스트
- 모두 `[x]`면 성공만 리포트
- 끝에 `/code-test <plan path>` 권장

## Plan Status Update
- 모든 `[x]` → `status: done`
- 일부 `[x]` + 일부 `[FAIL]`/`[SKIP-DEP]` → `status: partial` + `failed_steps` 추가
- 모두 `[FAIL]`/`[SKIP-DEP]` → `status: failed`

---
*Claude adapter realization: `<agent-home>/adapters/claude/skills/code-execute/SKILL.md`; compatibility reference: `<agent-home>/skills/code-execute/SKILL.md`*
