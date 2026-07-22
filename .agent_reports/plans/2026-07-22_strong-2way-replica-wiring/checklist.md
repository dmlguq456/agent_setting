# Checklist — strong+ 2-way replica wiring

- [x] 1. topologies.json: 10개 recipe에 `standard_plus.replication` 선언 (note 제외)
- [x] 2. capability_topology.py: replication 블록 검증 + 테스트 셀
- [x] 3. capability-route.py: `_expand_replication` + compile/composed-verify 배선
- [x] 4. capability_route.test.py: strong 확장·standard 비확장·composed 왕복·출력 충돌 방지 셀
- [x] 5. skills 정합: owner-execution / arguments-and-decisions / dev-pipeline / capabilities/autopilot-code.md
- [x] 6. spec/stage-dispatch/prd.md v21 (SD-76) 등재
- [x] 7. 투영 재생성: sync-entry-skill-layer + generate + 형제 어댑터, generated-projections/routing-contract 가드
- [x] 8. 회귀: capability_topology.test.py / capability_route.test.py / compose_route.test.py 전부 green
- [x] 9. 커밋 (validated harness change)
