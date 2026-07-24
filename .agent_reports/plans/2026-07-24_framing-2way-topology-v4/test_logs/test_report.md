# test report — framing-2way-topology-v4 (SD-82)

일시: 2026-07-24 · 실행: inline (dispatch-infra self-modification)

| Suite | 결과 |
|---|---|
| tools/capability_topology.test.py (19) | OK |
| utilities/capability_route.test.py (35) | OK |
| utilities/compose_route.test.py (9) | OK |
| utilities/worker_route_guard.test.py (13) | OK |
| utilities/stage_dispatch_fallback.test.py (11) | OK |
| utilities/stage_dispatch_capacity.test.py (10) | OK |
| tools/entry-skill-layer.test.py | PASS (trees=3 entries=13) |
| tools/generated-projections.test.sh | PASS |
| tools/fleet/tests/test_f28_breadcrumb.py | OK |
| tools/generate.py --check | 15 groups OK |
| tools/check-adaptation-boundary.sh | OK |
| tools/check-model-config.py | OK |
| tools/check-unit-config.py | OK |

## 새 경계 셀

- topology: `replications` 배열 선언 검증(legacy 단일 키 거부·중복 앵커·kind
  어휘·비-review 하류 소비자·pipeline-stage 중재자·glob 규칙·schema v3 read-only),
  framing 앵커 5종/처방적 recipe 비대상 전수 선언 검사.
- route: standard가 frame replica 쌍을 전개하고 plan이 두 brief를 입력으로 받는
  셀, strong의 plan-replica + plan-check 중재 배선 셀, spec research shard
  `-replica` 트리 전개 셀, frame 노드 wrapper 투영(worker-type support,
  contract autopilot-code) 셀.

## 수동 확인

- registry digest 갱신: `python3 tools/capability_topology.py validate` OK
  (capabilities=10, recipes=22 불변).
- 기존 strong 노드열은 frame/plan replica 추가 외 순서 불변
  (impl-review verdict-merge 계약 SD-76 그대로).
