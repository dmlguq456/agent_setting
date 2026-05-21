# execute-plan

> 본 README는 Notion 페이지 [▶️ execute-plan](https://www.notion.so/34987c2bb753813fbe07dec64db8796e)의 미러. `/sync-skills`로 양방향 동기화. 권위 있는 동작 명세는 `SKILL.md`.

## 개요
구현 계획을 progress tracking과 함께 실행하는 skill. dev-team 서브에이전트에 step별 위임, phase마다 품질관리팀 리뷰, Git Safety Checkpoint 설정.

## 호출 형식
```
/execute-plan <plan name or path>
```

## Plan Resolution (canonical)
1. `.md` 접미사 → 그대로
2. 디렉토리 → `/plan/plan.md`
3. 퍼지 검색 → `_audit`/`_fix_` 없는 폴더 우선

## 커밋 메시지 규칙
- Safety checkpoint: `chore: Safety checkpoint before {plan-name} execution`
- Success: `{type}: {description}\n\n{key changes}` — type: feat/fix/refactor/chore

## Git Safety Checkpoint
1. `git fetch && git pull` — merge conflict 시 abort + 사용자 경고 후 중단
2. `git status` — uncommitted 있으면 diff 분석 후 의미 있는 commit 생성 (rollback 거점)
3. `git rev-parse HEAD` → `$SAFETY_COMMIT`으로 저장 → checklist 헤더에 기록

## 초기화
- plan 파일 읽기
- **로그 디렉토리 = plan/plan.md의 조부모** (예: `.claude_reports/plans/2026-03-18_refactor/`)
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
| Quick | `--qa quick` 명시 시 (autopilot-code에서 전파) | 1× 품질관리팀 (sonnet), 1-pass; 🔴 이슈는 `pipeline_summary.md` Decision Points에 기록만 |
| Light | ≤3 units, 기계적, 단일 variant | 1× 품질관리팀 (sonnet) |
| Standard | 4-10 units, 로직, 단일 모듈 | 1× (opus) |
| Thorough | >10 units, cross-module, 아키텍처 | 2-3× 병렬 (opus): A 정확성 / B 일관성 / C 안전 |
| Adversarial | Cross-variant, shared modules, >20 files + Codex | Thorough + 1× codex-review-team |

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
- 끝에 `/run-test <plan path>` 권장

## Plan Status Update
- 모든 `[x]` → `status: done`
- 일부 `[x]` + 일부 `[FAIL]`/`[SKIP-DEP]` → `status: partial` + `failed_steps` 추가
- 모두 `[FAIL]`/`[SKIP-DEP]` → `status: failed`

---
*원본: `~/.claude/skills/execute-plan/SKILL.md`*
