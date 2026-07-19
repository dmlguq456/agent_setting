# 최종 보고서 — spec-read 게이트 멀티-스펙 인지화

상태: **완료 (PASS)**
기준 커밋: `4272eba8` → 구현 `395a797c` + `8496bf90` (branch `spec-gate-multi-spec`)
primary capability: `autopilot-code` · `dev/standard` · route `rt-603bfc57313d9266`

## 무엇이 바뀌었나

멀티-스펙 저장소(루트 `spec/prd.md` + `spec/<slug>/prd.md`)에서 spec-read 하드 게이트가
루트 PRD 하나만 알던 오조준을 고쳤다. 실측 사례: fleet 작업 세션이 지배 스펙
(`spec/agent-fleet-dashboard/prd.md`)을 읽고 있었는데도 게이트가 무관한 루트 PRD(Unified
Memory) 읽기를 형식 충족용으로 강제했다.

1. `hooks/spec-read-marker.sh` — 서브 스펙 `spec/<slug>/prd.md` Read도 marker 기록
   (1-depth 한정, `_internal` 제외, worktree→canonical 정규화 유지). 루트 marker 파일명
   `${sid}__${key}`는 그대로(하위호환), 서브 스펙은 `__<slug>` suffix.
2. `hooks/spec-skill-gate.sh` — 판정을 "후보 스펙(루트+서브) 중 **하나 이상**을 이번 세션에서
   신선하게(각 후보별 mtime 비교) 읽었는가"로 변경. 거부 메시지가 후보 prd.md 경로 전체를
   나열하고 지배 스펙을 읽으라고 안내. 아무것도 안 읽으면 여전히 거부(fail-closed 불변).
   어느 스펙이 지배하는가의 의미 판단은 §0.5대로 에이전트 몫(route record `spec_read.source`).
3. `core/HOOKS.md`·`core/WORKFLOW.md` §7.0 — portable 계약 문구를 governing-candidate-set
   의미로 동기(core-first 커밋 순서).
4. `hooks/portable-guards.test.sh` +88줄 — 멀티-스펙 시나리오 9 테스트.
5. Claude plugin mirror 2종 재동기(byte-parity).

의도된 동작 변화 한 가지(릴리스 노트 감): 서브 스펙만 있고 루트 prd.md가 없는 저장소는
이전에 "spec-backed 아님"으로 통과했지만 이제 게이트 대상이 된다.

## 검증

독립 검증자(native-subagent, 실행 전부 worktree 내)가 시나리오 6종 전부, 구문/POSIX,
mirror parity, adaptation boundary, core 문구 정합을 PASS 판정. 가드 스위트의 잔여 FAIL
10~11건은 dispatch/harvest 하위계의 기존 flaky(비결정 membership)로 본 diff와 무관 —
`test_logs/test_report.md`.

## 운영 사고 3건과 스펙 등재 (부수 성과)

이 사이클 자체가 dispatch 인프라의 결함 3건을 실측으로 드러냈고, 전부 spec에 등재했다:

| 실측 | 등재 |
| --- | --- |
| r1 conductor가 배경 대기로 턴 종료 → 사망, plan 워커 고아 (SD-14 위반, 지침-단독 불충분 실증) | stage-dispatch **SD-64** — 고아 파이프라인 결정론 감지(attempt 사망∧marker 미완∧자식 잔존)·자동 표기·depth-0 표면, 재개는 record+marker (`a53813cd`) |
| route 가드 `head==source_commit` 정확 일치 × execute 커밋 계약 모순 → post-execute 분사 전면 거부 | stage-dispatch **SD-65** — post-execute 노드는 source_commit 후손 허용(first-parent 계보), 발산 fail-closed 유지 (`a53813cd`) |
| dispatch-node.py가 record의 eligibility 증거 미전달 → fail-closed | v15(broker retirement) 구현 흡수 항목 (`a53813cd`) |

같은 트랜잭션에서 fleet PRD v10 minor #4(**F-31** 분사 세션 rolling 요약 관측 — 사용자 확정)도
등재 (`1468076f`).

## 후속

- **quick 사이클(권고)**: worker-route-guard 계보 검증(SD-65) + 필요시 dispatch-node 증거
  전달 — v15 broker-retirement 사이클이 dispatch-node를 어차피 재작성하므로 그쪽 흡수도 가능.
- **F-31 구현 사이클**: watcher 유틸 + cheap-tier 요약 워커 + render 소비.
- **SD-64 구현**: SD-60(registry reconcile) 구현 사이클과 결합 권고.

## Artifacts

`plan/plan.md` · `checklist.md` · `dev_logs/step_01_multispec_gate.md` ·
`test_logs/test_report.md` · `_internal/{route.json,metrics.md,plan_reviews/,conductor-prompt.md,conductor-r2-prompt.md}` ·
`pipeline_summary.md`
