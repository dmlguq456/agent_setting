# run-test

> 본 README는 Notion 페이지 [🧪 run-test](https://www.notion.so/34987c2bb75381b2bed4e46395413623)의 미러. `/sync-skills`로 양방향 동기화. 권위 있는 동작 명세는 `SKILL.md`.

## 개요
execute-plan 이후 또는 온디맨드로 기능 테스트를 실행해 코드 정확성을 검증하는 skill. **항상 Thorough 모드** (2 병렬 QA 팀 강제), Codex 가용 시 자동 Adversarial로 상향.

## 호출 형식
```
/run-test <plan name, path, or test scope>
```

## Plan Resolution (canonical)
1. `.md` → 그대로
2. 디렉토리 → `/plan/plan.md`
3. 퍼지 검색 → `_audit`/`_fix_` 없는 폴더 우선. **없으면 fallback**: 인자를 파일/디렉토리 경로로 간주하여 직접 테스트

## 위임 — 품질관리팀 (test 모드)
프롬프트 유형별:
- **plan 파일 경로**: "Run graduated tests for plan: {$ARG}. Read verification sections and checklist.md. Execute Level 1→2→3→4→5, stop on first failure."
- **파일/디렉토리**: "Run graduated tests on: {$ARG}. Execute Level 1→5, stop on first failure. Skip levels that don't apply."
- **비어있음**: "Run graduated tests on recently changed files. Use `git diff --name-only HEAD~1`."

### 테스트 로그 요구 (필수)
```
Write a detailed test log to: {log_dir}/test_logs/test_report.md

Format:
## Level N: [Level Name]
### Test N.1: [description]
**Command:** [exact command]
**Output:** [stdout/stderr]
**Verdict:** PASS / FAIL — [reason]
```

## QA 요구 (Thorough 강제, Codex 가용 시 Adversarial)
**`qa_level` 플래그 적용 안 됨** — 테스트 엄격도는 협상 불가.

**Adversarial 자동 상향**: QA launch 전 `codex --version 2>/dev/null` 실행. Codex 가용 시 자동 상향. 없으면 Thorough.

**항상 2 QA agents 병렬 (opus)**:
- Agent A (**coverage**): 모든 변경 파일 테스트됐나? 미테스트 코드 경로/엣지 케이스? 실데이터 사용? before/after 비교?
  - `test_reviews/test_review_coverage.md`
- Agent B (**accuracy**): 실패 진단이 올바른가(pre-existing 오진 아님)? 올바른 engine_mode? 명령이 변경 경로와 일치? 부정 테스트 존재?
  - `test_reviews/test_review_accuracy.md`

**Adversarial 추가**:
- Agent C (Codex): `codex-review-team` (`adversarial-review --wait --scope auto`) → `test_review_codex.md`

ANY agent의 이슈 처리 필수.

## Post-Test — QA Review
품질관리팀 (test 모드) 반환 후:
1. 테스트 로그 읽기
2. **2× 품질관리팀 병렬**
3. 양쪽 리뷰 읽기. 이슈 발견 → 품질관리팀 (test 모드) 재호출 (test_report.md에 append). 둘 다 통과 → 결과 보고

## 결과 보고
1. 요약 테이블로 테스트 결과 전달
2. 모든 레벨 통과 + QA 승인:
   - `git status`로 미커밋 확인. 변경 존재 시 **auto-commit** (사용자 질문 없음)
   - 성공 리포트 + 중단
3. 실패 시 **Hotfix Loop** (최대 2 시도)

### Hotfix Loop
> 단일 run-test 호출 내 self-contained. 상위 파이프라인 retry 시 이 루프 리셋.

1. **Attempt 1** (자동 — 저위험): 개발팀 auto mode subagent, 실패 level + 에러 + 파일 제공. "Auto mode. Hotfix: fix this test failure."
2. 실패 level부터 재호출
3. 통과 + QA 승인 시 auto-commit + 성공 리포트
4. **Attempt 2** (자동 — bounded retry budget): 새 에러 컨텍스트로 재시도
5. 여전히 실패 → 원본 에러, 시도한 내용, 권장 조치 리포트

## 로그 디렉토리 규칙
- plan 파일: 로그 dir = task root (plan/plan.md의 조부모)
- plan 없음: `.claude_reports/tests/` + 날짜 스탬프 서브디렉토리

---
*원본: `~/.claude/skills/run-test/SKILL.md`*
