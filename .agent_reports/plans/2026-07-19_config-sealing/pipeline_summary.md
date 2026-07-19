# pipeline_summary — SD-68 dispatch-defaults route-record 봉인 배선

- **capability**: autopilot-code · **mode**: dev · **intensity**: standard · **QA**: standard
- **route**: `rt-d57cbb149952fd3d` (`sha256:d57cbb14…`) · dispatch contract v3
- **spec-significance**: within-spec — `spec/stage-dispatch/prd.md` §13.9.2 SD-68 (v17, 2026-07-19)
- **worktree**: `/home/Uihyeop/agent_setting-wt/config-sealing` (branch `config-sealing`) · base `ecd3acd8`
- **overall verdict**: **PASS** — acceptance ①~⑤ 전부 PASS, 회귀 0

## Stage ledger

| Stage | harness (role) | attempt | verdict | gate marker |
|---|---|---|---|---|
| plan | codex (deep maker) | att-1c8768cc… | BLOCKED (read-only spec-marker) → fallback | — |
| plan | **claude** (deep maker, fallback) | att-5666bd3e… | **PASS** | ✓ `plan.json` |
| execute | **claude** (fast implementer; config=codex, deviated) | att-77ec6c36… | **PASS** | ✓ `execute.json` |
| test | codex (deep reviewer) | att-40d41581… | BLOCKED artifact-persist → conductor salvage + 독립 재검증 | ✓ `test.json` |
| report | claude (fast writer) | att-f6ffccce… | **PASS** | ✓ `report.json` |

모든 completion gate marker(plan/execute/test/report) 기록됨(SD-56).

## What shipped

- `utilities/capability-route.py`: `compile_route`가 depth-2 노드에 `harness_affinity` 스탬프 +
  record 상단 `dispatch_defaults_digest`(정규화 파싱 config canonical-JSON sha256, 부재 시 null)를
  `route_hash` 계산 **이전**에 삽입 → hash가 봉인. `verify_route`는 어휘·digest 포맷만 검사, config
  재로드 없음, 구 route 하위호환. `registry_digest`와 별도 필드.
- `utilities/dispatch-defaults.py`: `query_stage_affinity` 헬퍼(record-seal 어휘, 스키마 불변).
- `utilities/dispatch-node.py` + `adapters/{claude,codex,opencode}/bin/dispatch-headless.py`:
  `--harness-affinity` passthrough를 registry row까지(soft, 게이트 아님).
- `core/OPERATIONS.md` §5.10: record affinity 소비 한 문장(core-first 커밋).

## Commits (core-first)

1. `3fbbd1e3` — spec: SD-68 record affinity 소비 규칙 현행화 (`core/OPERATIONS.md` §5.10)
2. `9130c437` — feat(dispatch): SD-68 봉인 배선 (utilities + wrapper 3종 + tests)

## Verification (conductor 독립 재검증 — test codex BLOCKED-persist salvage)

- `capability_route.test.py` 18 · `dispatch_node.test.py` 20 · `dispatch_contract.test.py` 10 ·
  `worker_route_guard.test.py` 13 — 전부 pass.
- sd15 ×3 PASS · `dispatch-route.test.sh` PASS(selector 1단계 불변).
- sd45 ×3 각 1건 실패(`test_route_consumer_and_missing_evidence_refusal`, exit 73) —
  **base `ecd3acd8` detached worktree에서 동일 재현 → 사전 존재, 회귀 아님**.
- 라이브 acceptance 스모크: ①(plan=unspecified/execute=codex/test=diverse/report=claude, digest≠registry_digest)
  ②(값 변경→hash 변화, 주석만→hash 불변) ③(사후 config 변경에도 verify 통과, 재로드 없음)
  absent(digest null + 전 노드 unspecified) 확인.

## 알려진 잔여물 (이번 사이클 범위 밖)

- namespace-local dead attempt row 3건(plan-codex, plan-claude, test-codex)이 reconcile 없이
  `open` audit 기록으로 존치. reconcile이 terminal heartbeat 없는 namespace-local pid에 대해
  fail-close하는 알려진 갭 — v18/SD-70·71 소관, SD-68 범위 아님. depth-0 reconcile 대상.

## Out of scope (미변경 확인)

selector 캐스케이드 의미, `dispatch-defaults.yaml` 값, worker-route-guard, wrapper 신규 게이트,
권한 분류기, `spec/**` 편집.

## Handoff

작업 완료. main 머지·push·worktree 정리는 depth-0/권한 경계 소관(worker는 수행 안 함).
