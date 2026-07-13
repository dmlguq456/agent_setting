# depth-2 stage worker — code-execute (harness-installer 사이클 3)

당신은 depth-2 stage worker 입니다. worktree `/home/Uihyeop/agent_setting-wt/harness-installer-hooks` (브랜치 `harness-installer-hooks`) 에서 **code-execute** 스테이지만 수행하고 산출물 파일만 남긴 뒤 종료합니다. depth-3 분사 금지.

## 입력 (반드시 Read — 이전 스테이지 대화가 아니라 이 파일들에서만 정보를 얻으세요)

- `.agent_reports/plans/2026-07-13_harness-installer-hooks/plan/plan.md` (code-plan 이 작성한 상세 구현 계획 — Phase 1~4)
- `.agent_reports/plans/2026-07-13_harness-installer-hooks/plan/checklist.md` (체크리스트 — 항목별로 완료 시 `[x]` 로 갱신하세요)
- `.agent_reports/spec/harness-installer/prd.md` (spec-read 게이트 — 세션 내 실제 Read 필요)
- `adapters/claude/bin/sync-native-plugin.py` (수정 대상)

## 작업

plan.md 의 **Phase 1~3**을 구현하세요 (Phase 4 는 code-test 스테이지 몫 — 손대지 마세요):

- Phase 1: hook 3종 재확인(코드 재검증, plan 의 결정이 맞는지 확인 — 틀렸으면 STOP+보고, 즉흥 변경 금지)
- Phase 2: `adapters/claude/bin/sync-native-plugin.py` 확장 (checklist 2.1~2.12) — `HOOK_ADOPT`+3, `UTILITIES_SOURCE`/`UTIL_BUNDLE`/`_HOOK_EVENTS`/`_HOOK_DATA_HOME` 상수, `_HOOK_MATCHERS`/`_HOOK_SHELLS` 확장, `hooks_json()` 다중이벤트+DATA env-prefix, `sync()` utilities 복사, `check()` utilities 커버, 주석/docstring 동기화. 스크립트 실행해 생성물 materialize, idempotent 확인, `git diff` 로 canonical `hooks/*.sh` 무수정 확인.
- Phase 3: `.agent_reports/spec/harness-installer/_internal/hooks_inventory.md` defer→adopt 갱신, code-report 핸드오프용 PRD/state 갱신 포인터는 기록만(prd.md·pipeline_state.yaml 직접 편집 금지 — 이 스테이지 권한 밖).

**불변식(위반 시 STOP+보고, 즉흥 처리 금지)**:
- canonical `hooks/*.sh` 본체 **한 줄도 수정 금지**. plan 의 env-prefix wrapper 방식이 불가능하다는 반증을 코드로 발견하면, 억지로 다른 방법을 시도하지 말고 무엇이 막혔는지 정확히 기록하고 종료.
- write 는 `adapters/claude/bin/sync-native-plugin.py`(생성기) + `adapters/claude/plugin-marketplace/`(생성물, 생성기 실행 결과) + `.agent_reports/spec/harness-installer/_internal/hooks_inventory.md` + 이 plans 폴더의 checklist/dev_logs 로 한정.
- `spec/prd.md`·`pipeline_state.yaml` 편집 금지.
- 이 스테이지는 테스트 스위트를 새로 작성/실행하지 않습니다(생성기 자체 실행·`--check`·`git diff` 같은 즉석 확인은 구현 중 당연히 하되, code-test 스테이지의 격리 테스트 스크립트는 작성하지 마세요).

## 산출물

- 코드 변경 (git diff 로 확인 가능한 상태로 두되 커밋은 하지 마세요 — code-report 스테이지가 일괄 커밋합니다)
- `.agent_reports/plans/2026-07-13_harness-installer-hooks/plan/checklist.md` 의 Phase 1~3 항목을 `[x]` 로 갱신
- `.agent_reports/plans/2026-07-13_harness-installer-hooks/dev_logs/step_01_hook_reconfirm.md` (Phase 1 결정 재확인 기록 — 코드 라인 인용)
- `.agent_reports/plans/2026-07-13_harness-installer-hooks/dev_logs/step_02_generator_extension.md` (Phase 2 구현 로그 — 변경 diff 요약, 실행 결과)
- `.agent_reports/spec/harness-installer/_internal/hooks_inventory.md` 갱신

완료 후 짧게 보고하고 종료하세요(코드-테스트는 다음 스테이지가 이어받습니다).
