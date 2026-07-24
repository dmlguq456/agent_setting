# pipeline summary — framing-2way-topology-v4

- **작업**: registry v4 다중 replication 앵커 + autopilot-code `frame` 스테이지
  신설 + framing 앵커 5종 standard 2-way + plan strong 2-way(plan-check 중재)
  — SD-82, stage-dispatch PRD v26.
- **결과**: 완료. 관련 스위트 9종 + CI 체크 4종 전부 통과.
- **의도 복원**: SD-76이 review 전용으로 좁혔던 2-way를, 사용자 원 의도
  (서로 다른 모델의 독립 방향 탐색·듀얼 플랜 상호보완)대로 방향 결정 지점에
  배선. 처방적 recipe는 명시적 비대상.
- **산출물**: capabilities/topologies.json(v4) · roles/units/plan/frame.md ·
  tools/capability_topology.py · utilities/capability-route.py · core/CONVENTIONS.md
  §1.1/§3.5/§3.12 · core/WORKFLOW.md · capabilities/autopilot-code.md ·
  skills/autopilot-code/references/dev-pipeline.md(Step 0) ·
  .agent_reports/spec/stage-dispatch/prd.md §13.16.
- **남은 사항**: frame 스테이지 첫 live standard 사이클에서 두 leg 배치·brief
  품질 실측(다음 code 사이클이 자연 드릴). fleet 브레드크럼은 route 기록을 그대로
  따라 `frame(2-way)`로 접혀 표시됨(F-28b 일반 규칙, 코드 변경 불필요).
