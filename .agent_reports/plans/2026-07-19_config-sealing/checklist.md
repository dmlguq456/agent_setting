# Checklist — SD-68 dispatch-defaults route record 봉인

Safety commit: (execute 스테이지가 착수 시 기록)
Route: rt-d57cbb149952fd3d
Commit order: **core-first** — Phase 0 커밋을 Phase 1 앞에 둔다.

## Phase 0 — core 지침 현행화 (먼저 커밋)
- [ ] Step 0.1 — `core/OPERATIONS.md §5.10` line 129 SD-66 소비 문장 뒤에 record
      `harness_affinity`/`dispatch_defaults_digest` 소비 한 문장 추가 (soft·차단 없음,
      verify 재로드 금지·registry_digest 분리 명시).
- [ ] Step 0.2 — **커밋 1 (core만)**: `git commit core/OPERATIONS.md` — utilities 편집 전.

## Phase 1 — 로더 봉인 헬퍼
- [ ] Step 1.1 — `utilities/dispatch-defaults.py`에 `query_stage_affinity(config, capability,
      stage)` 추가 (미지정→`unspecified`). 기존 `query_affinity`·스키마·어휘·CLI 불변.

## Phase 2 — compile/verify 봉인 (핵심)
- [ ] Step 2.1 — `capability-route.py` 상단에 `DEFAULTS` 모듈 import(importlib) +
      `VALID_AFFINITY = DEFAULTS.AFFINITY_VALUES | {"unspecified"}`.
- [ ] Step 2.2 — `_seal_dispatch_defaults(nodes, capability)` 헬퍼 추가: config 로드→depth-2
      노드 `harness_affinity` 스탬프 + digest 반환. 부재→전부 unspecified+None. 손상→
      `DefaultsConfigError`를 `ValueError`로 승격(fail-loud). env(`DISPATCH_DEFAULTS_CONFIG`)
      존중 = `default_config_path()` 재사용.
- [ ] Step 2.3 — `compile_route`에서 nodes 확정 직후·`route_hash` 계산 전에 헬퍼 호출,
      payload에 `dispatch_defaults_digest` 필드 추가(`registry_digest`와 분리, 병합 금지).
- [ ] Step 2.4 — `verify_route`에 어휘 유효성(필드 있을 때만) + digest 포맷 검사 추가.
      **config 재로드 금지.** 필드 없는 구 route 하위호환 통과.

## Phase 3 — dispatch-node row 계측
- [ ] Step 3.1 — `dispatch-node.py`: `node.get("harness_affinity")` 있으면 argv에
      `--harness-affinity <값>` 추가. 필드 없으면 불변.
- [ ] Step 3.2 — `adapters/claude/bin/dispatch-headless.py`: `--harness-affinity` 인자 +
      pipe 키 튜플(line~420)에 `"harness_affinity"` 추가.
- [ ] Step 3.3 — `adapters/codex/bin/dispatch-headless.py`: 동형(line~517).
- [ ] Step 3.4 — `adapters/opencode/bin/dispatch-headless.py`: 동형(line~483).
- [ ] Step 3.5 — 차단 장치 없음 확인: explicit `--adapter`≠affinity도 비교/거부 없이 통과.

## Phase 4 — 테스트
- [ ] Step 4.1 — `capability_route.test.py`: acceptance ①(어휘 스탬프) ②(값변경→hash변화,
      주석변경→hash불변) ③(사후 config변경에도 verify통과) + 구route 하위호환 + 위조어휘
      실패 + 부재(digest None/unspecified) + 손상 fail-loud.
- [ ] Step 4.2 — `dispatch_node.test.py`: acceptance ④(argv에 --harness-affinity) ⑤(adapter≠
      affinity launch 통과) + 필드없는 노드 불변.
- [ ] Step 4.3 — 회귀 0: capability_route/dispatch_node/dispatch_contract/worker_route_guard
      (.py) + sd45 3종(python3) + sd15 3종(bash) + dispatch-route.test.sh(bash). 전량 통과.

## Phase 5 — 마감 위생
- [ ] Step 5.1 — `adapters/**/__pycache__` 삭제(커밋 전, boundary guard).
- [ ] Step 5.2 — **커밋 2 (utilities + wrappers + tests)** — core 커밋 뒤.
- [ ] Step 5.3 — guard/테스트 전량 worktree 안에서만 수행 확인(primary checkout guard 금지).

## Acceptance ↔ Step 매핑
| acceptance | 검증 Step |
|---|---|
| ① depth-2 전 노드 유효 어휘 harness_affinity | 2.2/2.3, 4.1 |
| ② config 값 변경 → route_hash 변화 | 2.3(봉인), 4.1 |
| ③ 스탬프 route는 사후 config 변경에도 verify 통과 | 2.4(재로드 금지), 4.1 |
| ④ dispatch-node 경유 row에 harness_affinity | 3.1~3.4, 4.2 |
| ⑤ explicit --adapter≠affinity launch 통과(soft) | 3.5, 4.2 |
| 구 route 하위호환 + 회귀 0 | 2.4, 4.1~4.3 |
