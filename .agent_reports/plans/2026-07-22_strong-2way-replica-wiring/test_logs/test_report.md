# Test report — strong+ 2-way replica wiring

실행 환경: primary checkout, HEAD ec5b1ebe, 2026-07-22.

## Concrete verification (all green)

| Command | Result |
|---|---|
| `python3 tools/capability_topology.test.py` | OK — 19 tests (신규 2: replication 선언 실측, fail-closed 6변형 subTest) |
| `python3 utilities/capability_route.test.py` | OK — 33 tests (신규 3: strong 확장/standard 비확장, replica fallback+seal 축, thorough·adversarial 확장) |
| `python3 utilities/compose_route.test.py` | OK — 9 tests (composed strong 왕복이 확장 경로 통과) |
| `python3 tools/generate.py` + `--check` | 14 core projection groups green; manifest/hub 재생성 |
| `bash tools/generated-projections.test.sh` | PASS |
| `bash tools/routing-contract.test.sh` | all checks passed |
| `python3 tools/entry-skill-layer.test.py` | PASS (3 trees × 13 entries) |
| `bash tools/check-adaptation-boundary.sh` | OK |

## Behavior evidence

- 수정 전 실측(승계): `plans/2026-07-22_codex-headless-context-parity/_internal/route.json`
  — requested=strong, effective=strong, 노드 그래프는 standard와 동일(복제 없음).
- 수정 후: `test_strong_expands_replica_pair_and_standard_does_not`가 동일 컴파일
  경로에서 strong 노드열 `plan, plan-check, execute, impl-review,
  impl-review-replica, test, report`와 `verify_route` 왕복을 증명. standard는
  기존 6-노드 그래프 불변, direct/quick 회귀 셀 전부 불변(§3.2 보존).
- stale 정의 스윕: `grep -rn "one risk-focused" adapters/ skills/ capabilities/`
  → 0건 (core/CONVENTIONS.md:31은 이미 신계약 문언).

## Skipped

- dispatch liveness 계열 실행 테스트(브로커/프로세스 스폰) — 본 변경은 컴파일
  층이며, 실행 층 계약(fallback 사슬·seal·marker)은 기존 경로를 그대로 재사용.
  drill 자동 실행 금지(사용자 정책).
