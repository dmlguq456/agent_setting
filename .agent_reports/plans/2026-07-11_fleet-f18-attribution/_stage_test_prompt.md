sub-skill: code-test (품질관리팀 test 모드 — graduated verification syntax→import→smoke→functional→integration)

입력 산출물:
- plan (검증 기준의 정본): /home/Uihyeop/agent_setting-wt/fleet-f18-attribution/.agent_reports/plans/2026-07-11_fleet-f18-attribution/plan.md
- execute 요약: /home/Uihyeop/agent_setting-wt/fleet-f18-attribution/.agent_reports/plans/2026-07-11_fleet-f18-attribution/execute_summary.md
- 청사진 (게이트 Read): /home/Uihyeop/agent_setting-wt/fleet-f18-attribution/.agent_reports/spec/agent-fleet-dashboard/prd.md §4.6 F-18

이미 브랜치 워크트리에 구현 완료 (변경: tools/fleet/model.py, collectors/procscan.py, collectors/dispatch.py, render.py, 신규 tests/test_f18_attribution.py). 커밋 전 상태. 검증만 수행(read-only 원칙, 필요 시 테스트 실행), 소스 수정 금지 — 결함 발견 시 보고만.

검증 계획 (plan §"검증 계획" V1~V5 전부 실행):
(a) tests 전체 green:
    cd tools && python3 -m unittest fleet.tests.test_f18_attribution -v
    cd tools && python3 -m unittest fleet.tests.test_f15_rows fleet.tests.test_f17_title_refresh fleet.tests.test_dispatch fleet.tests.test_f14_title -v
    (드릴 회귀·기존 fleet 테스트 전부 PASS 확인. tools/fleet/tests 하위 다른 테스트도 있으면 함께 돌려라.)
(b) 라이브 스모크:
    cd tools && python3 -m fleet.fleet --once            # 기본 — mem-워커 미노출 + 🧠 요약(살아있는 distiller 있을 때)
    cd tools && python3 -m fleet.fleet --once --all      # a-토글 동치 — mem dim row 노출
    cd tools && python3 -m fleet.fleet --json | python3 -c "import sys,json; d=json.load(sys.stdin); print('mem_worker key:', ('mem_worker' in d['sessions'][0]) if d.get('sessions') else 'no-sessions')"
    (F-18a 병합은 라이브 drill 이 없으면 test_f18_attribution 의 mock registry fixture 단위검증으로 충족 — 그 케이스가 PASS 인지 확인.)
(c) drill 임포트 표면 회귀 없음:
    cd tools && python3 -c "import fleet.collectors.dispatch as d; print(d._drill_case_from_slug, d._reconcile_drill_rows, d.collect)"
(d) no-curses import OK:
    cd tools && python3 -c "import fleet.render; print('render import (no curses tty) OK')"

불변식 확인 (위반 발견 시 FAIL 근거로 보고): DispatchJob 필드 additive only · --json additive only · registry 무write · render.py 모듈 레벨 curses.A_* 신규 참조 없음(grep 확인) · nt _scan_disk mem_worker default False · F-14~F-17 계약 유지.

출력 계약:
- verdict: PASS / PASS-with-notes / FAIL — 근거(실행한 명령 + 결과 요약) 포함.
- 각 검증 항목 (a)~(d) 별 결과와 테스트 카운트(green/total).
- 발견된 결함이 있으면 파일:라인 + 재현 명령.
- 검증 결과를 .agent_reports/plans/2026-07-11_fleet-f18-attribution/test_report.md 에 기록.
- 간결 한국어 verdict 요약 반환.

qa=standard, intensity=standard, slug=fleet-f18-code-test
