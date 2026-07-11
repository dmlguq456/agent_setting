sub-skill: code-report (코드 작업 사이클 결과 요약·보고 + 커밋)

입력 산출물 (전부 절대경로):
- plan: /home/Uihyeop/agent_setting-wt/fleet-f18-attribution/.agent_reports/plans/2026-07-11_fleet-f18-attribution/plan.md
- execute 요약: /home/Uihyeop/agent_setting-wt/fleet-f18-attribution/.agent_reports/plans/2026-07-11_fleet-f18-attribution/execute_summary.md
- test 보고: /home/Uihyeop/agent_setting-wt/fleet-f18-attribution/.agent_reports/plans/2026-07-11_fleet-f18-attribution/test_report.md

상태: 구현 완료 + code-test verdict=PASS (신규 14/14, 회귀/discovery 139/139 green, 결함 없음). 커밋 전 워크트리 상태.

작업 (브랜치 fleet-f18-attribution 워크트리 /home/Uihyeop/agent_setting-wt/fleet-f18-attribution):
1. `git add` — F-18 소스 변경 5파일(tools/fleet/model.py, collectors/procscan.py, collectors/dispatch.py, render.py, tests/test_f18_attribution.py) + 산출물 폴더 .agent_reports/plans/2026-07-11_fleet-f18-attribution/ 를 스테이징.
2. `git commit` — 한국어 커밋 메시지. 제목: F-18 구현: loop·drill·mem-워커 귀속 정밀화 (F-18a dedup·F-18b mem-태깅). 본문: F-18a(drill registry↔proc 이중표시 1행 병합)·F-18b(mem distiller/refresher 태깅·기본 제외·🧠 요약) 요지, 검증 결과(14/14 신규·139/139 green), 불변식 준수 요약. 커밋 메시지 말미에 Co-Authored-By 트레일러 규약 있으면 따르되 없으면 생략.
3. .agent_reports/plans/2026-07-11_fleet-f18-attribution/pipeline_summary.md 작성 — 이번 사이클(plan→execute→test→report) 요약: 변경 파일, 검증 명령/결과, 산출물 경로, verdict.

주의:
- merge·push·worktree 정리는 하지 마라 (메인 오케스트레이터 몫). 커밋까지만.
- 커밋 전 `git -C <워크트리> status`로 detached HEAD·merge 진행 중 아님을 확인. 브랜치는 fleet-f18-attribution 이어야 함.
- 산출물 폴더 안 _stage_*_prompt.md 임시 프롬프트 파일은 커밋에 포함해도 무방(산출물 폴더 전체 add).

출력 계약: 커밋 해시 + 변경 파일 목록 + pipeline_summary.md 경로를 간결 한국어로 반환.

qa=standard, intensity=standard, slug=fleet-f18-code-report
