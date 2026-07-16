# 사이클 철회 기록 — broker-nested-reachability (2026-07-16 16:1x)

## 판정

- **철회 사유**: 병행 Codex 세션의 broker 폐기 결정이 spec v15(commit b50e4524, SD-61~63)로 등재되어 본 사이클(SD-57 구현)과 정면 충돌. v15 §13.7.4가 "SD-57의 broker reachability/spool 구현은 취소한다"를 명시.
- **철회 시점 상태**: 구현 미착수 — 소스 변경 0. 산출물은 plan/checklist/metrics(진단 기록)뿐. 워크트리 `agent_setting-wt/broker-nested-reachability`는 무변경 상태로 제거.
- **충돌 세부**:
  - SD-57의 file-spool transport(inbox 소비·replies poll)는 v15 검증자가 명시한 anti-pattern("spool 감시자·inbox 소비자·heartbeat·상주 supervisor = broker를 다른 이름으로 재발명")과 정확히 일치 — 구현했다면 즉시 폐기 대상이었음.
  - SD-57의 생존증거 위계는 제거 예정 컴포넌트(broker)의 수리 — direct headless 전환 후 무의미.

## 존속하는 산출물 (v15로 이관되는 가치)

1. **근본 원인 진단** (plan.md §Problem, spec v14 입력 등재): `broker_status()`의 `/proc/<pid>/stat` 단일 하드 게이트가 PID-네임스페이스 격리에서 산 broker를 `broker-unavailable`로 오판, `ensure`는 flock-상실 spawn 루프로 `broker-start-timeout`. 이 fragility 실증은 broker 폐기 결정(v15)의 근거 자료로 유효.
2. **SD-58(진행 감시·O5 흡수)·SD-59(capacity failover)·SD-60(registry 위생)**: v14 등재분은 broker-독립 계약으로 v15 §13.7.4가 명시 유지 — direct wrapper/Fleet 후속 사이클의 입력.
3. 사용자 진단 항목 4(portable verification wrapper)·5(worktree build isolation)·6(browser harness)의 라우팅(core 규약/별도 spec)은 v14 §13.6 rollout boundary에 기록됨 — 미착수, 유효.

## 후속 연결

- `plans/2026-07-16_fleet-depth2-retry-liveness`의 broker 복구 항목(구현 §3)도 같은 이유로 무효화 — F-25 attempt identity·newest-attempt 항목은 v15 SD-63(하나의 logical stage, 하나의 attempt identity)과 정합해 그 사이클/후속에서 처리.
- 사용자 개선 순서 2(watchdog)·3(capacity)·7(registry)은 v15 direct headless 구현 완료 후 SD-58~60 기반 후속 사이클로 진행.

## 후속 완료 기록 — 2026-07-16

- 후속 사이클 `plans/2026-07-16_direct-headless-resilience`에서 broker와
  독립적인 SD-58, SD-59, SD-60 구현을 완료했다.
- SD-58은 direct wrapper/stage heartbeat와 동기식 watchdog으로 구현했으며
  resident watcher나 broker 대체 authority를 추가하지 않았다.
- SD-59는 wrapper의 capacity 탐지/기록과 conductor의 1회 대체 모델 선택으로
  구현했다. wrapper는 모델을 선택하지 않는다.
- SD-60은 canonical registry의 selected current view와 locked exact
  reconciliation으로 구현했다.
- `fleet-depth2-retry-liveness`의 F-25 attempt identity·newest-attempt 항목은
  존속·완료됐고, broker stop/ensure 복구 및 broker fixture 항목은 계속 무효다.
- 실제 Codex headless 재귀 smoke는
  `root -> depth-1 owner -> depth-2 stage`로 통과했으며 결과에
  `selected_hop=same-harness-headless`, `launch_authority=conductor`,
  `broker_lifecycle=retired`가 기록됐다.
