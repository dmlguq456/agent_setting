# skill-design-refactor 파이프라인 요약

## 최종 판정

**GREEN (Pocock scope).** Ponytail을 제외한 Pocock 4축+Predictability 설계 정합 작업은 완료됐다.

- **Invocation:** P1 runtime gate 결과에 따라 13 parent/pipeline skill을 model-invoked로 유지하고 registry/g7로 강제했다. P4는 누락된 `autopilot-ship`까지 보강해 13 entry-router 모두 `Use when…` 트리거를 가진다.
- **Information Hierarchy:** `autopilot-design` 등 장문 본문을 1-depth references로 추출했고 모든 skill이 500줄 미만이다.
- **Steering:** P8의 순수 anti-pattern negation 2건만 positive executable instruction으로 전환했다. 배포·쓰기·검증 경계의 safety negation은 유지했다.
- **Pruning:** Plan Resolution·시각 검증·Language Rule·artifact-root·Reference Index를 단일 authority+pointer로 정리했고 `autopilot-ship` 중복도 제거했다.
- **Predictability:** `no-op=0`, `sediment=0`, `premature-completion=0`, `variance-bug=0` 회귀 판정을 유지한다.

## 최종 closure

- capability `--qa` drift 14개는 commit `1e77a34`, merge `016a883`에서 이미 main에 반영됐다.
- `tools/skill-conformance`는 Claude concrete tool tree에 project했다. Codex/OpenCode는 native Skills가 portable capabilities에서 생성되므로 selective tool projection에서 deferred로 명시했다.
- invocation registry는 13 entry-router + 13 parent-invoked = 26개 분류를 강제한다.
- 양 Claude skill tree는 `.sync_state.json`을 제외하고 byte parity다. Claude native plugin, manifest, Codex/OpenCode native skill projections도 current다.

## 검증

- `tools/skill-conformance/check.sh`: PASS — 26 classifications.
- g7 static regression: PASS — live gate + parent/user-only 양방향 failure controls.
- P4 scanner/mirror: PASS — 13/13 entry-router `Use when…`, 양 트리 parity.
- P8 semantic diff: PASS — `design-components`의 지정 2문장만 양 트리에서 동일 전환.
- focused adaptation boundary: PASS — `skill-conformance` 관련 failure 0.
- 전체 `tools/check-adaptation-boundary.sh`: 기존 `INSTALL_LAYOUT.md` 문서 drift만 남아 exit 1. Pocock/skill-conformance 범위 실패는 아니며 이번 완료 판정에 포함하지 않는다.
- standard 독립 reviewer는 headless runtime projection mismatch로 실행하지 못해 `qa-policy` fallback에 따라 inline evidence review로 보고한다.

## 범위 경계

- **제외:** Ponytail, Codex depth-2/liveness, installed Codex hooks 복구, repo-wide `INSTALL_LAYOUT.md` parity.
- 최종 사이클 증거: `.agent_reports/plans/2026-07-13_pocock-finalization/`.
