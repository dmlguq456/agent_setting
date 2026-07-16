# micro-plan — fleet gate-통과 표시 (autopilot-code / quick / depth-1)

- 규범: `spec/agent-fleet-dashboard/prd.md` §4.9 "gate 통과 증거 소스 (2026-07-16 확정, v10 minor #2)"
- 재개 근거: `plans/2026-07-15_fleet-v10-process-view/_internal/carryover.md` §1 — route.py node dict에 자리 확보됨(additive)
- 브랜치: `fleet-gate-passed` / 기준선 테스트 519 OK

## 1. 판정 계약

canonical marker = `<agent-home>/.dispatch/completion/<route_id>/<node_id>.json`

- **통과** = 파일 존재 + marker `route_id` == record `route_id` + marker `route_hash` == record `route_hash`
- **무주장(None)** = 부재 / route_id 불일치 / hash 불일치 / garbage json / 읽기 실패
  → 미통과·실패로 렌더 금지 (F-28 tolerant 원칙)
- 이력 파일 `<node_id>.<seq>.json` 존재 시: canonical이 있으면 canonical이 authoritative
  (writer가 항상 최신을 canonical에 atomic replace), canonical 부재 시 최대 seq 이력만 사용.
- read-only. mtime+size 캐시 = 기존 `route._CACHE` record 캐시 패턴 재사용.
- 실물 marker 스키마(rt-5fd84b9bcf8a799c 실측)에 `sequence`/`completed_at`/`schema_version`이
  **없다** → 필수 필드로 요구하지 않는다. 요구 필드는 route_id/route_hash뿐.

## 2. 순수성 경계 유지

`route.build_views()`는 PURE 계약(문서화됨). marker 읽기는 I/O이므로:

- `resolve_gate_marks(records)` → `{route_id: {node_id: True}}` — 새 impure 진입점
  (`resolve_records()`의 형제)
- `build_views(jobs, node_evidence, records, now, gate_marks=None)` — 5번째 optional 인자
  (기존 4-positional 호출부/테스트 전부 무변경)
- `collect_views()`가 두 impure 단계를 묶는다.

## 3. 표시 (상태 글리프와 독립 차원)

- 과정 뷰 노드 텍스트: 통과 노드만 노드명 뒤에 dim `⊸` — `_route_node_text()`가 상태별
  글리프(✓●○✕)를 만든 뒤 gate 표식은 별도 dim seg로 붙인다(색상 차원 분리).
- `a` 토글 상세: 기존 `gates: <name>, ...` 한 줄을 `gates: plan-gate ⊸, exec-gate …` 형태로
  통과 여부만 덧댄다. 새 줄 추가 없음(과하게 만들지 말 것).
- `--json`: route 노드에 `gate_passed` additive (`true` | `null`). 기존 키 무변경.

## 4. 변경 파일 (예상)

- `tools/fleet/route.py` — marker 로더 + `resolve_gate_marks` + node dict `gate_passed` + summary
- `tools/fleet/render.py` — `_route_node_text` 표식, `a` 상세 gates 줄
- `tools/fleet/tests/test_f30_gate_passed.py` — 신규
- `adapters/claude/tools/fleet/` — mirror 동기

## 5. 검증

1. 신규 테스트: 통과 / route_id 불일치 / hash 불일치 / 부재 / garbage / 이력 최신 우선 / 캐시
2. 전체 회귀 `python3 -m unittest discover -s tools/fleet/tests -t .` — 519 → 519+N, 회귀 0
3. `--json` 스모크: 기존 키 diff 0 + `gate_passed` 존재
4. `COLUMNS={60,120,168} fleet.py --once --view process` 넘침 0
5. mirror parity: `rsync -a --delete` 후 `diff -r` 무출력
6. 금지: 실세션 스폰/signal, live `.dispatch/completion/` 쓰기, route record 쓰기
