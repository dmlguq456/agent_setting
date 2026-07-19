# metrics — 2026-07-19_retry-lineage

## depth-0 fix-forward (round 2, 2026-07-19)

- inline reason (§5.10 exception): the round-1 audit fully specified a 2-line prose-only
  fix; SD-67 is not yet merged so an in-cycle execute retry stays structurally blocked
  (the very gap this cycle implements). Dispatch overhead clearly exceeds the stage.
  Commit `9196282a`.
- regression: worker_route_guard 13 OK, dispatch_contract OK, dispatch_node 17 OK,
  stage_dispatch_fallback OK, capability_route OK, dispatch-route PASS, sd45 ×3 (9 OK),
  sd15 ×3 PASS (bash), boundary guard exit 0. Worktree clean after removing
  test-generated `__pycache__` (recurring; 3 dirs).
- core-first: adapter-mirror edit blocked once by the core-first gate; re-read
  `core/OPERATIONS.md §5.10` (rule already correct — no core change), then mirrored.

## 하네스 선택 실측 (config affinity 소비 기록)

- plan: config 미지정 → deep-maker affinity로 codex 선택 — PASS.
- execute: config `codex` 준수 → **BLOCKED** (codex workspace-write 샌드박스에서
  linked worktree git metadata read-only, index.lock 생성 불가) → conductor가
  사유 기록 후 claude로 재선택, 새 attempt id로 PASS. **config execute=codex는
  샌드박스 수리 전까지 mutation 스테이지에서 실효 불가라는 1차 운용 데이터.**
- test: diverse(execute=claude와 다른 하네스) → codex — 검증 완료했으나
  `.spec-grounding` read-only로 아티팩트 영속화 BLOCKED, conductor가 salvage.
- report: conductor 자체 종합(별도 워커 미분사, FAIL 종료 경로).

## SD-64 실측 (2회차 사고 기록)

- r1 conductor(claude -p, opus): plan 분사 후 "Monitor 대기"로 턴 종료 → 사망(6분).
  프롬프트 경고 존재에도 재발 — 지침 계층 방어 불충분 3회째 실측.
- depth-0 복구: plan 워커는 고아 상태로 완주(PASS) → row 마감 + marker 수동 작성,
  죽은 conductor row `dead-parent-orphaned` 표기, r2 재개 프롬프트(최상단 liveness
  계약 + Monitor 금지 명시)로 대체 분사 → r2는 완주.
- r2의 registry 위생 위반: execute row 2개(BLOCKED/PASS)를 flip하지 않고 test 분사
  → depth-0가 정리. 후속 제안: `capability-route.py complete`가 marker 작성 시
  해당 노드 open row 자동 마감(결정론화).
