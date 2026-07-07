# code-test

> 본 README 는 Claude adapter skill 요약. 권위 있는 Claude runtime 동작 명세는 같은 폴더의 `SKILL.md`; portable capability 의미는 `<agent-home>/capabilities/`.

## 개요
code-execute 이후 또는 온디맨드로 concrete verification evidence를 기록하는 skill. `code-test`는 read-only final verify stage이며, hotfix·commit·parallel QA fan-out을 자체적으로 열지 않는다. 선택된 `intensity`/`qa_level`이 테스트 폭과 test-adequacy review 여부를 정한다.

## 호출 형식
```
/code-test <plan name, path, or test scope> [--qa quick|light|standard|thorough|adversarial]
```

## Plan Resolution (canonical)
1. `.md` → 그대로
2. 디렉토리 → `/plan/plan.md`
3. 퍼지 검색 → `_audit`/`_fix_` 없는 폴더 우선. 없으면 인자를 파일/디렉토리 경로로 간주하여 직접 테스트

## 위임 — 품질관리팀 (test 모드)
프롬프트 유형별로 Level 1→5 graduated verification을 실행하고, 첫 실패에서 멈춘다. 사용자-facing surface 변경이면 selected assurance가 허락할 때 Level 5b behavioral runtime observation을 추가한다.

### 테스트 로그 요구
모든 실행은 `{log_dir}/test_logs/test_report.md`에 exact command, stdout/stderr excerpt, PASS/FAIL/SKIP/BLOCKED reason을 남긴다.

## Assurance
- `quick`: 가장 좁은 concrete check 1개와 skip reason.
- `light`: focused syntax/import/smoke 또는 caller explicit command.
- `standard`: 적용 가능한 graduated levels + command evidence.
- `thorough`: 더 넓은 target coverage와 surface 변경 시 runtime observation, 필요 시 test-adequacy review.
- `adversarial`: selected graph/risk가 요구할 때 security/failure-mode/external adversary evidence 추가.

## 결과 보고
성공/실패 verdict와 report path를 caller에게 반환한다. 실패하면 caller/orchestrator가 bounded retry/fix stage를 결정한다. `code-test`는 source 수정, hotfix agent 호출, auto-commit을 하지 않는다.

---
*Claude adapter realization: `<agent-home>/adapters/claude/skills/code-test/SKILL.md`; compatibility reference: `<agent-home>/skills/code-test/SKILL.md`*
