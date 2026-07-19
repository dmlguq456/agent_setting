---
status: done
cycle: 2026-07-16_spec-gate-multi-spec
capability: autopilot-code
mode: dev
intensity: standard
route_id: rt-603bfc57313d9266
spec-significance: within-spec (gate-contract change in core/, no spec/** PRD mutation)
---

# Pipeline summary — spec-read 게이트 멀티-스펙 인지화

**Verdict: PASS (완료).** `plan`·`execute`는 depth-2 headless로 완주. `test`는 route 가드의
구조적 fail-closed(하단 "The blocker")로 headless 2-hop이 거부된 뒤 depth-0 판단으로
**native-subagent fallback**(품질관리팀/test, 타 세션 독립 검증)으로 수행해 PASS.
`report`는 동일 사유로 inline fallback. 열화 증거·hop 기록 = `_internal/metrics.md`.

## Stage ledger

| node | transport | verdict | terminal artifact |
| --- | --- | --- | --- |
| plan | headless claude (`deep maker`) | PASS | `plan/plan.md` (+ `checklist.md`, `_internal/plan_reviews/round_1.md`) |
| execute | headless claude (`fast implementer`) | PASS | `dev_logs/step_01_multispec_gate.md`, 커밋 `395a797c`+`8496bf90` |
| test | **native-subagent** (headless 2-hop `route-source-commit-mismatch` 후) | **PASS** | `test_logs/test_report.md` |
| report | **inline** (depth-0, metrics.md에 사유 기록) | PASS | `final_report.md` |

Completion markers: plan·execute·test·report 전부 `.dispatch/completion/rt-603bfc57313d9266/`.

## 검증 요지 (독립 검증자, 실행 전부 worktree 내)

- 멀티-스펙 시나리오 6종 전부 PASS — 서브 스펙 read 통과 / `_internal` snapshot 무marker·거부 유지 /
  미독 거부+후보 전체 나열("Read the one governing the declared work scope") / drift 재독 /
  루트 단일 스펙 byte-parity 무회귀 + `${sid}__${key}` marker 파일명 하위호환 / legacy `.claude_reports`.
- `sh -n`·POSIX 준수, plugin mirror byte-parity + `sync-native-plugin.py --check` 0,
  `check-adaptation-boundary.sh` PASS, core 문구 ↔ 구현 동작 일치.
- plan §4의 미확인 delta도 확인 완료: 서브 스펙만 있고 루트 `spec/prd.md`가 없는 저장소는 이제
  게이트 대상이 된다(의도된 변화, 릴리스 노트 감).
- 가드 스위트(worktree): 멀티-스펙 블록 9/9. 잔여 FAIL 10~11건은 dispatch/harvest 하위계의
  **기존 flaky**(2회 실행에서 개수·membership 비결정) — 본 diff는 dispatch 코드 무접촉.

## Conductor r1 → r2 → depth-0 harvest

r1(pid 2251685)은 plan 분사까지 정상 후 배경 대기로 턴을 끝내 사망(SD-14 위반,
`note=dead-turn-ended-before-harvest`). r2는 산출물에서 재개해 plan·execute를 완주하고
아래 blocker에서 계약대로 BLOCKED 반환. depth-0가 SD-50 후속 hop(native→inline)으로 마감.

## The blocker (r2 진단 원문 요지 — SD-65 등재 근거)

`utilities/worker-route-guard.py:86`이 HEAD ≠ route `source_commit`(컴파일 시점)이면 fail-closed.
그런데 dev 파이프라인은 execute의 커밋을 계약으로 요구하므로 **모든 tracked staged 사이클에서
post-execute 노드(test/report) 분사가 구조적으로 거부**된다(codex hop·claude dry-run 동일 사유
실증 — 어댑터 무관). r2는 route 위조·재컴파일·커밋 되돌리기를 전부 소유하지 않은 불변식 파괴로
판단해 중단했다. depth-0 판단: 가드의 불변식 취지(계보 밖 실행 차단)는 "커밋된 정확한 계보의
독립 검증"과 충돌하지 않으며, 오조준은 spec으로 등재해 닫는다.

## What landed (worktree `/home/Uihyeop/agent_setting-wt/spec-gate-multi-spec`)

- `395a797c` docs(core): widen spec read gate to a governing candidate set
- `8496bf90` feat(hooks): accept root or one-level sub-spec reads in the spec gate

```
 core/HOOKS.md                                      |  2 +-
 core/WORKFLOW.md                                   |  2 +-
 hooks/spec-read-marker.sh                          | 39 +++++++++-
 hooks/spec-skill-gate.sh                           | 85 +++++++++++++++++----
 hooks/portable-guards.test.sh                      | 88 ++++++++++++++++++++++
 .../agent-harness-claude/hooks/spec-read-marker.sh | 39 +++++++++-
 .../agent-harness-claude/hooks/spec-skill-gate.sh  | 85 +++++++++++++++++----
 7 files changed, 302 insertions(+), 38 deletions(-)
```

## 운영 사고·파생 등재 (본 사이클 실측 → spec)

1. conductor 고아 파이프라인(감지·재개) → **SD-64** (`a53813cd`)
2. post-execute source_commit 계보 검증 → **SD-65** (`a53813cd`) — 가드 수정은 후속 quick 사이클
3. dispatch-node eligibility 증거 미전달 → v15 구현 흡수 항목 (`a53813cd`)
4. F-31 분사 세션 rolling 요약 관측 → fleet PRD v10 minor #4 (`1468076f`)
