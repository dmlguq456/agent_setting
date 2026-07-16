# stage-dispatch v13 — 파이프라인 요약

route: `rt-5fd84b9bcf8a799c` / route_hash `sha256:5fd84b9bcf8a799c...` / 기점 main `98308ec4` /
spec `spec/stage-dispatch/prd.md §13.5`(SD-54·SD-55·SD-56) / worktree
`/home/Uihyeop/agent_setting-wt/stage-dispatch-v13`.

---

## 1. 스테이지별 산출물·판정·소요·수확 근거

| 스테이지 | 산출물 | 판정 | 수확 근거(evidence) |
|---|---|---|---|
| plan | `plan/plan.md`(867줄) + `plan/checklist.md` + `_internal/plan_reviews/plan_check.md` | 완료 — blocker B1~B4·M1~M4 전부 계획 본문에 반영 | `plan/plan.md`(sha256 `a95dbc0...`) |
| execute | `dev_logs/01~03` 3편 | 완료 — SD-54→SD-56→SD-55 순으로 구현, 각 로그에 실행 커맨드·회귀 근거 기록 | `dev_logs/03-sd55-record-identity-decoupling.md`(sha256 `03a403c...`) |
| test | `test_logs/01-independent-verification.md` + `_internal/test_reviews/01-fixture-review.md` | **PASS** — 독립 재실행 + acceptance 10/10 대조 + mutation test 4건 + 사전존재 실패 4건 베이스라인 대조 | `test_logs/01-independent-verification.md`(sha256 `be29eda...`) |
| report(본 산출물) | `pipeline_summary.md` + `final_report.md` | 작성 중 | — |

**completion marker 4건**은 route `rt-5fd84b9bcf8a799c` 아래 canonical 경로에 실재한다(저장소 사상 최초):

```
/home/Uihyeop/agent_setting/.dispatch/completion/rt-5fd84b9bcf8a799c/plan.json
/home/Uihyeop/agent_setting/.dispatch/completion/rt-5fd84b9bcf8a799c/execute.json
/home/Uihyeop/agent_setting/.dispatch/completion/rt-5fd84b9bcf8a799c/test.json
/home/Uihyeop/agent_setting/.dispatch/completion/rt-5fd84b9bcf8a799c/report.json  (본 스테이지 완료 후 conductor가 기록)
```

각 필드 대조(plan 예시, 나머지 동형):

```json
{
  "route_id": "rt-5fd84b9bcf8a799c",
  "route_hash": "sha256:5fd84b9bcf8a799c...",
  "registry_digest": "sha256:161b5539ad48d...",
  "node_id": "plan",
  "completion_gate": "code-plan",
  "evidence": {"path": ".../plan/plan.md", "sha256": "a95dbc0..."}
}
```

이 route 자신은 `broker_contract_version: 1`이므로 SD-56 gate는 **이 사이클 자신에는 적용되지 않는다**(소급 강제 금지, §13.5.3) — 4건의 marker는 gate 강제 없이 conductor가 규범(문서 의무, `dev-pipeline.md`)을 도그푸딩한 결과다.

---

## 2. spec §13.5 acceptance 대조표

### SD-54 — broker 동시성 분리

| # | acceptance | fixture | 판정 | mutation 확증 |
|---|---|---|---|---|
| ① | slow target 실행 중 다른 request가 그 생애와 독립 완주(HOL 해소) | `test_slow_target_does_not_block_other_requests` | 충족 | 전역 락 부활 → **실패**(진짜 가드) |
| ② | 동일 request_id 동시·순차 재제출 = attempt/target 정확히 1 | `test_concurrent_duplicate_request_creates_one_attempt` + `test_duplicate_request_is_idempotent` | 충족(단 F1 — 아래 §4) | 미실시(F1로 대체 기록) |
| ③ | claim/spawn 직후 crash = fenced recovery, 중복 launch 0 | 기존 2건 + 신규 `test_fenced_recovery_holds_under_parallel_inflight` | 충족 | — |

### SD-55 — record ↔ broker-identity 결합 해제

| # | acceptance | fixture | 판정 | mutation 확증 |
|---|---|---|---|---|
| ① | rollover 후 v2 record ordinal-1 hop 성공, 하강 0, route_hash 불변 | `test_v2_record_survives_broker_rollover` | 충족 | live-instance 해석이 낡은 env를 신뢰하도록 되돌림 → **실패**(진짜 가드) |
| ② | v1 record 기존 거동 회귀 0 | `test_v1_record_keeps_instance_binding_rules` + v1 고정된 `test_tampered_inherited_instance_fails_closed`·`test_missing_broker_fails_closed` | 충족 | — |
| ③ | broker 부재 시 `broker-unavailable` fail-closed | `test_v2_record_without_live_broker_fails_closed`(plan-check M4로 후발 추가 — 초안 미커버 조항) | 충족 | — |

### SD-56 — completion 통과 marker 배선

| # | acceptance | fixture | 판정 | mutation 확증 |
|---|---|---|---|---|
| ① | canonical marker 생성 + 필드가 record와 일치 | `test_complete_writes_canonical_marker` | 충족 | — |
| ② | 선행 marker 부재 시 spawn 0 + structured failure | `test_start_without_dependency_marker_fails_closed`(3어댑터 parametrize) | 충족 | gate 본문 최상단 `return` 삽입 → **3건 실패**(진짜 가드) |
| ③ | marker 부재를 실패로 읽는 소비자 0(negative) | `test_marker_absence_is_not_a_failure` | 충족 | — |
| ④ | 재수확 이력 보존 + 최신 authoritative | `test_reharvest_preserves_history_and_latest_is_authoritative` | 충족 | — |
| ⑤ | v1 record·record 미결합 launch에는 미적용(소급 강제 금지) | ⑦⑧ 동일 fixture 내 분기 | 충족 | — |

**acceptance 10개 전 항목 충족.** ①④⑦(spec 번호가 아니라 fixture 표 §4.1 번호)은 mutation test로 "결함을 되살리면 fixture가 실패한다"까지 증명됨 — 통과가 무력화의 결과가 아님을 뒷받침.

---

## 3. 불변식 보존 대조

| 불변식 | 판정 | 근거 |
|---|---|---|
| atomic transition | 보존 | `transition()` 호출 전부가 `request_lock` 안(B/D 블록·`recovered_response`); `renew_lease`도 락 안에서 `atomic_json` 직접 기록 |
| terminal immutability | **보존**(3중 결합) | (1) per-request 락 (2) (D)에서 on-disk state **재독** 후 terminal이면 그대로 반환 (3) `renew_lease`도 락 안에서 terminal 확인 후에만 기록. 되돌리기 실험(§2 mutation)으로 실측 확인 |
| fencing/lease | 보존 | lease는 claim 시점 락 안에서 설정, `renew_lease`가 `max(0.5, stale_seconds/3)` 주기로 갱신 — claim→target 종료 구간에 만료 창 없음. `broker_instance != self.instance_id`면 renewer 즉시 종료(fencing 존중) |
| spawn 전 canonical registry row | 보존 | 어댑터 측 로직(`append_job` → `Popen`) 무변경, 이번 diff가 건드리지 않음 |
| idempotency(AC4) | 보존 | per-request 락 + status/lease 판정. 동시 재제출 = `broker-request-inflight`; 순차 terminal 재제출 = `duplicate: True` |
| fenced recovery(AC5) | 보존 | registry reconcile이 inflight 검사 **뒤**로 좁혀져 predecessor instance·lease 만료 경로 전용 |
| broker 동시성 cap 부재(governor 이중 상한 금지) | 보존 | `grep -n "Semaphore\|BoundedSemaphore\|max_workers\|ThreadPool\|listen("` → `sock.listen(16)` 1건, 미변경. `model-worker-governor.py`는 diff에 부재 |
| v1 record 소급 강제 부재 | 보존 | `completion_marker_gate`가 `broker_contract_version != 2`면 미적용; `_verify_fallback_chain`이 v1/v2/None 3상태로 분리돼 v1 규칙 무변경 |
| 3어댑터 parity | 보존 | claude/codex/opencode 3종 모두 `validate_route_record` 동일 지점에 동일 `completion_marker_gate` 호출 + `args.action`/`args.agent_home` 세팅 — 완전 동형 |

---

## 4. 회귀

```
$TESTENV bash hooks/portable-guards.test.sh   → PASS=359 FAIL=0   (v12 baseline과 동일값)
```

사전존재 실패 4건 — `git stash -u`로 기점(98308ec4) 상태와 diff 없이 동일 재현, 이번 사이클과 무관:

| 스위트 | 현재 트리 | 베이스라인(98308ec4) | 판정 |
|---|---|---|---|
| `utilities/dispatch-artifact-root.test.py` | `FAILED (failures=3)` | `FAILED (failures=3)` | 동일 — 회귀 아님 |
| `bash utilities/dispatch-concurrency.test.sh` | FAIL(병렬 drift) | 동일 | 동일 — 회귀 아님 |
| `bash utilities/artifact-root.test.sh` | `not ok - linked worktree resolves primary artifact root` | 동일 | 동일 — 회귀 아님 |
| `bash tools/generated-projections.test.sh` | `not ok - legacy artifact root was not selected for orientation` | 동일 | 동일 — 회귀 아님 |

원인: 워커 세션의 실제 env/fleet 동시 프로세스 상태를 흡수하는 하니스 환경 의존성(`carryover.md §5`) — v13 스코프 밖.

기타 계약/투영 검증: `tools/build-manifest.py --check` 통과, `bash tools/check-adaptation-boundary.sh` 통과(신규 `dispatch_completion_marker.test.py`의 `adapters/claude/utilities/` symlink 투영 + `UTILITY_DEFERRED` 목록 2곳 등재 후), `bash tools/routing-contract.test.sh` 통과, `git diff --check` 클린, `dev-pipeline.md` 3부 `diff -r` 무차이.

---

## 5. 남은 사항 (test 스테이지 발견, PASS를 뒤집지 않음)

| ID | 요지 | 등급 | 처리 |
|---|---|---|---|
| F1 | B3(inflight-before-reconcile) 순서 수정이 fixture ②의 fake-adapter 전환으로 registry row 경합 조건을 잃어 어떤 fixture로도 고정돼 있지 않음(순서를 되돌려도 14/14 통과). 구현 자체는 probe로 정확함이 확증됨 | major(테스트 내구성) | `_internal/test_reviews/01-fixture-review.md §3`에 즉시 사용 가능한 fixture 작성·검증 완료. 재분사 여부는 conductor 판단 |
| F2 | `test_fenced_recovery_holds_under_parallel_inflight`의 `assertLessEqual(rows,1)`이 0건도 허용 | minor | v14 하드닝 후보 |
| F3 | fixture ②가 launch 횟수를 직접 세지 않고 응답 개수로만 추론 | minor | v14 하드닝 후보 |
| F4 | merge 후 gate가 코드 강제인 반면 conductor의 marker 쓰기는 문서 강제 — 첫 사이클에서 안 쓰면 fail-closed 정지 | 운영 사실(결함 아님) | `final_report.md` §롤아웃 경계에 명시 |
| F5 | spec §13.5.2 문언(`ensure`) ↔ 구현(`status`-only) 불일치 | 기록 | `carryover.md`에 spec 정정 후보로 이월(spec 미수정) |
