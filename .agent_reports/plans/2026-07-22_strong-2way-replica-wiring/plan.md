---
status: done
created: 2026-07-22
intensity: standard
mode: dev
---

# strong+ 2-way cross-harness replicate-and-merge 실행 배선

## Goal

2026-07-21 사용자 지침으로 core에 등재된 계약 — "cross-harness 2-way
replicate-and-merge는 `strong` 이상 기본" (`core/CONVENTIONS.md §3.5/§3.12`,
`core/WORKFLOW.md:253`, `core/DESIGN_PRINCIPLES.md:194`) — 을 실행 표면에
배선한다. 현재 enforced route compiler는 standard/strong/thorough/adversarial을
전부 동일한 `standard_plus` 선형 그래프로 컴파일하며(실측:
`plans/2026-07-22_codex-headless-context-parity/_internal/route.json`
requested=strong, effective=strong, 노드는 standard와 동일), skill 문서도 옛
정의("strong = standard + 리뷰 1회")를 유지한다.

## Root cause (승계 진단)

- 9b4e81b2 (7/21)는 core 문서 + QA stance만 갱신 — skill/topology 미전파.
- 63f521c8 (C6, 7/22)가 owner 스텝을 "컴파일 route와 일치화"하면서 복제 없는
  그래프가 오히려 정본으로 고착.
- pending `cdc13b`: 타 세션이 동일 원인 확인, route compiler 수정은 사용자
  확인 대기 → 본 세션에서 사용자 착수 지시로 인수 (2026-07-22).

## Design

1. **Registry** (`capabilities/topologies.json`): 각 recipe `standard_plus`에
   선택적 `replication` 블록 — `{"node": <review-node-id>, "min_intensity":
   "strong", "ways": 2, "independence_axis": "cross-harness"}`. 대상: apply→
   verify, code→impl-review, design→critic-review, draft→fact-verify,
   lab(setup)→smoke, lab(eval)→independent-verify, refine→review, research→
   claim-verify, ship→release-review, spec→review. `autopilot-note`는
   review-worker 노드가 없어 선언 없음(정직한 carve-out — 새 스테이지 발명은
   범위 외, CONVENTIONS §3.2).
2. **Validator** (`tools/capability_topology.py`): replication 블록 검증 —
   노드 실존·kind=review-worker·ways==2·axis=cross-harness·min_intensity는
   standard+ tier·outputs 비-glob.
3. **Compiler** (`utilities/capability-route.py`): `_expand_replication()` —
   effective ≥ min_intensity일 때 대상 노드를 복제. 복제 노드: id `<id>-replica`,
   `replica_group=<id>`(원본에도 부여), `independence_axis` 부여, outputs는
   `name.ext → name.replica.ext` 변환(런타임 파일 충돌 방지), 하류 노드
   depends_on에 replica 추가. 기존 fallback-chain/seal 기계는 depth-2 노드로
   그대로 적용. composed route 검증(`verify_route`)도 동일 함수로 확장 후 비교.
   fallback 사슬 순서는 계약 고정(FALLBACK_ORDER)이므로 cross-harness 선호는
   노드 메타데이터(`independence_axis`) + conductor 계약으로 실현: 두 leg를
   서로 다른 harness/model family로 분사, 불가 시 same-harness 독립 세션
   fallback + 독립성 저하 보고 (DESIGN_PRINCIPLES §, 기존 계약 그대로).
4. **Skills**: `skills/autopilot-code/references/{owner-execution,
   arguments-and-decisions,dev-pipeline}.md` + `capabilities/autopilot-code.md`
   의 strong 정의를 계약과 정합화. merge는 conductor의 verdict-수준 병합
   (stricter-wins, blocking findings 합집합) — SD-1 thin conductor 유지.
5. **Spec**: `spec/stage-dispatch/prd.md`에 v21(SD-76) 등재 — 근거는 7/21
   사용자 지침 + 본 배선.
6. **투영/검증**: sync-entry-skill-layer, generate --check, 형제 어댑터 투영
   sync, topology/route/composed 회귀 + 신규 테스트 셀.

## Checklist

`checklist.md` 참조.

## Non-goals

- autopilot-note에 리뷰 스테이지 신설 (별도 결정 필요).
- thorough/adversarial N-way 확장 기계화 (현행 prose 계약 유지; 2-way가 하한).
- drill 자동 실행 (사용자 정책).
- `codex-headless-context-parity` plan 실행 (별도 소유·별도 확인 대기).
