# Task brief — depth-2 `--start` 자격 증거 자동 바인딩 (evidence-autobind)

- capability: autopilot-code / mode dev / intensity standard / QA standard
- route: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-17_evidence-autobind/_internal/route.json`
  (route_id `rt-babd26fbb4f65d1b`, dispatch_contract_version 3)
- worktree (소스 편집 유일 위치): `/home/Uihyeop/agent_setting-wt/evidence-autobind`
  (branch `evidence-autobind`, base `origin/main` @ `5972a61d`)
- canonical plan root (산출물 유일 위치): `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-17_evidence-autobind/`
- spec-significance: **within-spec** — governing item: `spec/stage-dispatch/prd.md` §13.7.6
  "v15 구현 흡수: dispatch-node.py가 record dispatch_evidence의 checked tuple을 wrapper 인자로
  결정론 전달" + acceptance ③ "dispatch-node 경유 분사가 추가 인자 없이 eligibility 검증 통과".
  canonical spec 경로: `/home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch/prd.md`

## 배경 실측 (2026-07-16, g10 드릴 2회)

depth-2 `--start`가 evidence 플래그 없이는 `nested-eligibility-evidence-missing`(exit 69)로
fail-closed하고, 워커가 문서 절차대로 probe를 돌려 플래그를 보충하면 런타임 권한 분류기가 그
명령을 "게이트 우회"로 오판해 차단한다. 자동 바인딩이 이 이중 구속을 원천 제거한다.

## 구현 범위

### (1) `utilities/dispatch-node.py` — record evidence 자동 전달 (핵심)

- route record의 `dispatch_evidence.tuples`(및 노드의 `dispatch_fallback` candidates)에서 대상
  adapter(child_harness)와 hop에 맞는 **checked tuple을 선택**해 wrapper 인자
  `--launch-authority --parent-harness --parent-transport --parent-sandbox
  --nested-eligibility --eligibility-source`로 자동 전달한다.
- 호출자가 같은 플래그를 명시하면: record와 **일치**할 때만 통과(명시 우선이되 중복 무해),
  **모순**이면 fail-loud(사유 + 양쪽 값 출력). 조용한 덮어쓰기 금지.
- depth-1 dispatch(route 노드 아님)와 record 없는 호출은 현행 동작 불변.

### (2) adapter 래퍼 3종 — evidence 부재 시 내부 probe 바인딩

`adapters/{claude,codex,opencode}/bin/dispatch-headless.py`: depth-2 `--start`에서 evidence
인자가 비었으면 `utilities/nested-dispatch-eligibility.py`를 **래퍼 내부에서** 실행해 checked
결과를 바인딩한다. 결과가 `supported`가 아니면 기존
`nested-child-spawn-<status>` / `nested-eligibility-evidence-missing` fail-closed 유지 —
**게이트 약화 절대 금지**(probe 실패·unknown을 supported로 합성하지 않는다). probe 실행 사실과
결과는 wrapper 출력(`eligibility_probe=internal`, tuple 필드)과 registry pipe에 기록.
parent_harness/transport/sandbox의 자기 판정은 각 래퍼의 기존 runtime 감지 로직
(CODEX_THREAD_ID·AGENT_DISPATCH_* env 등)을 재사용하고, 감지 불가면 기존대로 fail-closed.

### (3) 테스트

- dispatch-node: record→인자 자동 전달, 명시-일치 통과, 명시-모순 fail-loud, record 없는 경로
  불변 — 단위 테스트(신규 또는 기존 스위트 확장).
- 래퍼: evidence 부재 depth-2 start에서 내부 probe 경유 성공(mock/fixture로 probe 결정론화),
  probe unsupported 시 fail-closed, evidence 명시 시 probe 미실행(현행 경로 회귀 0).
- 기존 스위트 회귀 0: `dispatch_contract.test.py`, 래퍼 SD-15(`sd15.test.sh`)·SD-45(`sd45.test.py`)
  3종, `stage_dispatch_fallback.test.py`, `nested_dispatch_eligibility.test.py`(직접 실행),
  `dispatch-route.test.sh`.

### (4) g10 드릴 케이스 원형 유지

`loops/drill/cases_growing/g10_claude_opencode_depth2_start/`의 prompt/assert에 evidence 플래그를
추가하지 마라 — 자동 바인딩이 케이스를 성립시키는 것이 이 작업의 수용 기준이다. 드릴 실행 자체는
이 사이클 범위 밖(depth-0 main이 수확 후 통합 검증으로 실행).

## 범위 밖 (건드리지 말 것)

권한 분류기 튜닝, route compile / `capability-route.py` 변경, broker 잔재 정리, `spec/**` 편집,
dispatch-defaults config 의미 변경.

## 운영 제약

- guard/테스트 스위트는 **task worktree 안에서만** 실행. primary checkout에서 guard 금지.
- 소스 편집은 worktree만; 산출물은 canonical plan root에만.
- main 머지/push 금지. task 브랜치 커밋은 정상(safety commit + 구현 커밋).
- execute 노드는 source_commit `5972a61d` 정확 일치 pin. execute 재시도가 필요해지면
  `git reset --hard` 금지(분류기가 차단, 실측) — 남은 결함을 fix-forward 목록으로 정리해
  정직하게 마감한다.
