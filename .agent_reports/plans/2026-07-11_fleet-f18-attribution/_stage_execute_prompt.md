sub-skill: code-execute (개발팀 refactor/new-lib 모드 — tools/fleet 는 파이썬 CLI/라이브러리 코드)

입력 plan (정본, 그대로 구현 — plan 재생성 금지):
/home/Uihyeop/agent_setting-wt/fleet-f18-attribution/.agent_reports/plans/2026-07-11_fleet-f18-attribution/plan.md

청사진 (spec 게이트용 Read 만): /home/Uihyeop/agent_setting-wt/fleet-f18-attribution/.agent_reports/spec/agent-fleet-dashboard/prd.md §4.6 F-18

작업 범위: plan.md "편집 파일 요약"(§ 하단 1~5)의 5개 파일을 plan 대로 구현한다 — Phase 1(F-18b) → Phase 2(F-18a).
1. tools/fleet/model.py — Session.mem_worker: bool = False (additive 1필드)
2. tools/fleet/collectors/procscan.py — scan() environ 마커 태깅(기존 read_environ 재사용), _scan_disk nt 미적용 주석
3. tools/fleet/collectors/dispatch.py — _DRILL_SLUG_RE/_DRILL_CWD_COMP_RE·_drill_case_from_slug/_drill_case_from_cwd·_reconcile_drill_rows 신규 + collect() 1줄 호출
4. tools/fleet/render.py — _build_lines mem 제외·🧠N badge·legend·_mem_row 헬퍼·a-토글 분기
5. tools/fleet/tests/test_f18_attribution.py — 신규 테스트 (plan 검증 V1 케이스 전부)

불변식 (반드시 준수 — 위반 시 STOP):
- DispatchJob 필드 additive only (F-18a 는 기존 pid/liveness 재사용, 신규 필드 없음). Session 신규는 mem_worker 1개뿐.
- fleet.py --json additive only, registry(jobs.log) 무write (F-18a 는 읽기·메모리 병합만).
- render.py 모듈 레벨 curses.A_* 신규 참조 금지 — 기존 "dim"/_A_DIM/_COLOR["dim"] 재사용.
- Windows no-curses import 경로 회귀 없음 — _scan_disk(nt) 는 mem_worker default False 유지.
- F-14~F-17 계약 유지 (usage 행·title·분사 row·detached·child-job 로직 불변).
- drill g9/g10/g_stage_dispatch assert 가 fleet.collectors.dispatch 를 임포트 → 기존 함수 시그니처 불변.

주의: plan.md 의 line 번호는 참고용 — 실제 코드의 현 위치를 grep 으로 확인해 정확한 seam 에 삽입한다. plan 의 코드 스니펫이 정본 의도.

출력 계약:
- 위 5개 파일을 브랜치 fleet-f18-attribution 워크트리에 편집·생성 (커밋은 하지 말 것 — code-report 스테이지가 커밋).
- 편집 후 최소 sanity: `cd tools && python3 -c "import fleet.collectors.dispatch, fleet.collectors.procscan, fleet.model, fleet.render"` 임포트 OK, `python3 -m fleet.fleet --json >/dev/null` 크래시 없음 확인.
- 실행 요약: 변경 파일 목록 + 각 파일 핵심 편집 지점(파일:라인) + sanity 결과를 간결 한국어로 반환.
- 산출물 요약을 .agent_reports/plans/2026-07-11_fleet-f18-attribution/execute_summary.md 에 기록.

qa=standard, intensity=standard, slug=fleet-f18-code-execute
