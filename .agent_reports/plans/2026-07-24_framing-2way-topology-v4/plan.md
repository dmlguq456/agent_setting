---
status: done
created: 2026-07-24
---

# framing 2-way topology v4 (SD-82)

## Goal

사용자 근본 의도(서로 다른 모델의 독립 방향 탐색) 를 registry 전반에 배선:
framing 앵커 standard 2-way, plan 앵커 strong 2-way, registry v4 다중 앵커.

## 근거

- 2026-07-24 사용자 지침: "2-way에서 내가 하고 싶은 건 서로 다른 모델이
  독립적으로 plan을 수립함으로써의 근본적인 상호 보완성", "plan 전에 근본적인
  진단·방향성 탐색 단계(pre)를 강화하고 여기서는 standard부터 2-way" —
  방향 오판이 hotfix/patch 연쇄·비용 폭증의 근원.
- 실측 갭: v3 스키마는 recipe당 단일 review-worker 앵커만 허용
  (`tools/capability_topology.py` 구 294행) — 듀얼 플랜 의도가 미배선.
- code-plan 계약에 진단/방향 내용 0건 — pre 단계 부재.

## Phases

- Phase 1 — registry v4: `replications` 배열, autopilot-code `frame` 노드 신설
  (map-worker · unit `plan/frame` · gate `code-frame`), framing 앵커 5종
  (code frame / spec research / draft material-strategy / design refs /
  research retrieval, 전부 min_intensity standard), plan@strong,
  기존 review 앵커 유지, 처방적 recipe(apply·refine·ship·lab·note) framing 비대상.
- Phase 2 — validator/compiler: kind 확장(review-worker·map-worker·pipeline-stage),
  비-review 하류 소비자·pipeline-stage review 중재자 요구, map-worker `<dir>/**`
  glob 전개(`-replica` 트리), 비-review 앵커의 하류 inputs 확장, 선언 순서 결정론.
- Phase 3 — 규범/계약: CONVENTIONS §1.1 표·§1.1(2)·§3.5·§3.12, WORKFLOW intensity
  표·code 라우팅 행, capabilities/autopilot-code.md, dev-pipeline.md Step 0/1/2,
  roles/units/plan/frame.md 신규, harness-manifest units 등재, PRD v26 §13.16.
- Phase 4 — 검증: topology/route/compose/guard/fallback/capacity 스위트,
  generate.py --check 포함 checks 4종, projections 재생성.

## Risks

- plan 중재(승자/graft) 실체화는 기존 code-refine 경로 재사용 — 새 mutation
  표면을 열지 않음. plan-check read-only 불변.
- standard 비용 증가는 framing 앵커 1쌍(map-worker, brief 1건)에 한정.

## Verification

- `python3 tools/capability_topology.test.py` / `utilities/capability_route.test.py`
  / `utilities/compose_route.test.py` / `utilities/worker_route_guard.test.py`
  / `utilities/stage_dispatch_fallback.test.py` / `utilities/stage_dispatch_capacity.test.py`
- `python3 tools/generate.py --check`, `tools/check-adaptation-boundary.sh`,
  `tools/check-model-config.py`, `tools/check-unit-config.py`
