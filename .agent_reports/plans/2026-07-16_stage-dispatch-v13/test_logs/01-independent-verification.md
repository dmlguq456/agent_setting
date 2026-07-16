# stage-dispatch v13 — test 스테이지 독립 검증 로그

- 스테이지: code-test / intensity=standard / mode=dev / model role=deep reviewer / depth-2
- 판정 기준: `spec/stage-dispatch/prd.md §13.5`(SD-54·55·56 acceptance) + §13.4 불변식 + §14 경계
- 검증 방식: execute의 주장을 **신뢰하지 않고 전부 재실행**. 추가로 fixture가 회귀를 실제로
  잡는지 확인하기 위해 **mutation test**(결함을 인위적으로 되살려 fixture가 실패하는지)를 수행.
  mutation은 worktree 소스를 건드리지 않고 `/tmp` 사본에서만 했다(경계 준수).
- worktree: `/home/Uihyeop/agent_setting-wt/stage-dispatch-v13`, 기점 main `98308ec4`

---

## 0. 최종 verdict

**PASS** — spec §13.5의 acceptance 조항 SD-54 ①②③ / SD-55 ①②③ / SD-56 ①②③④⑤ 전 항목이
충족되고, execute가 보고한 모든 스위트 결과가 재현되며, 회귀 0·경계 위반 0이다.

다만 **merge 전 처리를 권고하는 결함 1건(major)** 과 기록성 소견 3건이 있다. 이들은 acceptance
불충족이 아니라 **회귀 보호(테스트 내구성)와 롤아웃 운영**의 문제이므로 PASS를 뒤집지 않는다.
재분사 여부는 conductor 판단 영역이며, 아래 §5-F1에 재현 절차와 즉시 사용 가능한 probe를 남겼다.

| 축 | 결과 |
|---|---|
| 초점 스위트 재실행 | 전부 재현 — execute 주장과 일치 |
| acceptance ①~⑩ 대조 | 10/10 충족 (fixture 코드 정독 기준) |
| fixture 무력화 여부 | ①④⑦ mutation으로 **진짜 가드임을 증명**. ②는 부분 무력(F1) |
| 불변식 보존 | atomic transition·terminal immutability·fencing/lease·spawn 전 row·cap 부재·v1 소급 부재·3어댑터 parity 전부 보존 |
| 회귀 (359 baseline) | PASS=359 FAIL=0 — v12 baseline 동일 |
| 사전존재 실패 4건 | **베이스라인 대조로 독립 확증** — 이번 변경과 무관 |
| 경계 (live broker·spec·worktree) | 위반 0 |

---

## 1. 초점 스위트 재실행 — 원문 출력

함정 회피: 워커 세션 env에서 broker 테스트가 setUp exit 76으로 전멸하는 것은 코드 결함이 아니라
`dispatch-broker.py`의 "워커는 broker를 준비할 수 없다" 가드(`:604`)다. dev_logs가 기록한 우회
커맨드를 그대로 사용했다. (zsh에서 `TESTENV` 변수 확장이 깨져 `env`를 직접 호출했다.)

```bash
cd /home/Uihyeop/agent_setting-wt/stage-dispatch-v13
env -u AGENT_SESSION_ROLE -u AGENT_DISPATCH_CHILD -u AGENT_DISPATCH_BROKER_INSTANCE \
    -u AGENT_DISPATCH_BROKER_ROOT -u AGENT_DISPATCH_JOBS python3 utilities/dispatch_broker.test.py -v
```

```
test_claim_crash_restarts_only_unregistered_attempt ... ok
test_concurrent_duplicate_request_creates_one_attempt ... ok
test_depth0_can_rotate_to_new_canonical_fixture_registry ... ok
test_duplicate_request_is_idempotent ... ok
test_fenced_recovery_holds_under_parallel_inflight ... ok
test_four_parent_child_placements_use_one_external_broker ... ok
test_missing_broker_fails_closed ... ok
test_slow_target_does_not_block_other_requests ... ok
test_spawn_crash_recovers_registered_attempt_without_relaunch ... ok
test_tampered_inherited_instance_fails_closed ... ok
test_unknown_request_fields_are_rejected_without_registry_row ... ok
test_v2_record_survives_broker_rollover ... ok
test_v2_record_without_live_broker_fails_closed ... ok
test_zero_staleness_threshold_reports_stale_identity ... ok

Ran 14 tests in 29.352s

OK
```

```
$ ... python3 utilities/capability_route.test.py -v
test_ambiguous_quick ... ok
test_direct_all_and_stable ... ok
test_hash_detects_mutation ... ok
test_nested_surface_and_fallback_order ... ok
test_promotion_standard ... ok
test_tracked_gate_evidence_is_required ... ok
test_tracking_is_independent_and_never_escalates ... ok
test_unknown_nested_tuple_fails_closed ... ok
test_v12_route_binds_broker_and_legacy_v11_route_still_verifies ... ok
test_v1_record_keeps_instance_binding_rules ... ok
test_write_once_and_completion ... ok

Ran 11 tests in 0.165s

OK

$ ... python3 utilities/dispatch_completion_marker.test.py -v
test_complete_writes_canonical_marker ... ok
test_marker_absence_is_not_a_failure ... ok
test_reharvest_preserves_history_and_latest_is_authoritative ... ok
test_start_without_dependency_marker_fails_closed ... ok

Ran 4 tests in 4.762s

OK
```

나머지 초점 스위트(전부 마지막 줄):

```
stage_dispatch_fallback:         OK
dispatch_contract:               OK
worker_route_guard:              OK
dispatch_adapters_v11:           OK
```

**판정: execute가 보고한 14/14 · 11/11 · 4/4 및 나머지 스위트 전부 재현됨.**

---

## 2. acceptance ①~⑩ 대조 — fixture 코드 정독 기준

통과 여부가 아니라 **fixture가 무엇을 단언하는지**를 코드로 확인했다. `①④⑦`은 추가로
mutation test(§3)로 "회귀를 실제로 잡는다"를 증명했다.

| # | acceptance (spec §13.5) | fixture | 판정 |
|---|---|---|---|
| ① | slow-target 실행 중 둘째 request가 첫 target 생애와 독립 완주 | `test_slow_target_does_not_block_other_requests` | **충족**. `started-slow.marker` 폴링 배리어로 slow가 실행 창에 진입했음을 보장한 뒤 fast 제출 → fast가 `done` + **`done-slow.marker` 부재** 단언 → slow join 후 완주 확인. 배리어가 있어 거짓 음성이 구조적으로 불가(plan-check M2 요구 반영). mutation-증명 §3.2 |
| ② | 동일 `request_id` 동시·순차 재제출 = attempt/target 정확히 1 | 동시: `test_concurrent_duplicate_request_creates_one_attempt` / 순차: `test_duplicate_request_is_idempotent` | **충족(단 F1 보완 권고)**. 동시: 스레드 기반 동시 `communicate()`로 진짜 겹침을 만들고 `ok` 정확히 1 + 나머지 1이 `broker-request-inflight`임을 단언(관대한 "둘 중 하나" 단언 폐기 확인). 순차: 실 adapter로 registry row 1개 + attempt_id 단언(무변경). **F1**: 동시 fixture가 fake adapter라 registry row를 쓰지 않아 B3(reconcile-before-inflight) 회귀를 못 잡는다 |
| ③ | claim 직후·spawn 직후 crash fenced recovery, 중복 launch 0 | `test_claim_crash_restarts_only_unregistered_attempt`(무변경) + `test_spawn_crash_recovers_registered_attempt_without_relaunch`(무변경) + 신규 `test_fenced_recovery_holds_under_parallel_inflight` | **충족**. 기존 2건이 claim/spawn crash 본체를 유지하고, 신규 1건이 병렬 부하에서 victim row 1개 + `recovered_after_fence=True`를 단언. 병렬 request는 `assertLessEqual(rows,1)`= "중복 launch 0"에 정확히 대응(소견 F2) |
| ④ | rollover 후 v2 record ordinal-1 hop 성공, fallback 하강 0, record hash 불변 | `test_v2_record_survives_broker_rollover` | **충족**. `broker_contract_version==2` 확인 → restart로 instance 변경 확인 → **낡은 instance를 env에 고의 주입** → `check=ok` + `selected_hop=same-harness-headless` + `fallback_ordinal=1` + `check=degraded` **부재** + `broker_instance==새 instance` + 재로드 `route_hash` 불변. mutation-증명 §3.3 |
| ⑤ | v1 record 기존 거동 회귀 0 | `test_v1_record_keeps_instance_binding_rules` + `route_v1()`로 고정된 `test_tampered_inherited_instance_fails_closed`·`test_missing_broker_fails_closed` | **충족**. v1은 instance 필수 규칙 유지 + v2 record에 instance를 넣으면 거부(신규 §2.4d 규칙)까지 단언. 소스에서도 v1 분기 무변경 확인(§4.2) |
| ⑥ | marker 생성·필드가 record와 일치 | `test_complete_writes_canonical_marker` | **충족**. canonical `<agent-home>/.dispatch/completion/<route_id>/<node_id>.json` 존재 + 6필드(route_id/route_hash/registry_digest/node_id/completion_gate/evidence.sha256) 전부 record 대조 |
| ⑦ | 선행 marker 부재 시 gate fail-closed (spawn 0 + structured failure) | `test_start_without_dependency_marker_fails_closed` | **충족**. 3어댑터 parametrize로 `reason=completion-marker-missing` + `child_spawned=0` + **jobs.log 미생성**(row 0건) 단언 → marker 작성 후 재실행 시 그 사유가 아님을 단언. 비어있지 않음(gate가 실제로 발화)이 단언 자체로 증명됨. mutation-증명 §3.4 |
| ⑧ | marker 부재를 실패로 읽는 소비자 0 (negative) | `test_marker_absence_is_not_a_failure` | **충족**. (a) v1 record `--start` (b) record 미결합 `--start` 양쪽 3어댑터 동적 확인 + (c) `utilities/`·`adapters/`·`tools/fleet/` 정적 스캔으로 gate 헬퍼·어댑터 중계 지점 외 `completion-marker-missing` 문자열 부재 확인 |
| ⑨ | 재수확 이력 보존 + 최신 authoritative | `test_reharvest_preserves_history_and_latest_is_authoritative` | **충족**. 동일 evidence 재실행 = no-op(`plan.2.json` 미생성) / evidence 변경 시 새 이력 + **기존 이력 파일 내용 불변** 단언 + canonical이 최신(sequence 2, 새 sha256)을 가리킴 |
| ⑩ | broker 부재 시 structured `broker-unavailable` fail-closed | `test_v2_record_without_live_broker_fails_closed` | **충족**. (a) 존재한 적 없는 root (b) 살아있다 stop된 fixture broker 두 변형 모두 `reason=broker-unavailable` + `child_spawned=0` + jobs.log 미생성 + **`broker.json` 미생성**(status-only 결정의 수호자) |

---

## 3. mutation test — fixture가 회귀를 실제로 잡는가

통과는 무력화를 배제하지 못한다. worktree 사본을 `/tmp`에 만들고 결함을 되살려 fixture가
**실패하는지** 확인했다. (`tar -cf - --exclude=.git . | (cd /tmp/mutN && tar -xf -)`)

### 3.1 sanity — 미변형 사본은 통과
```
Ran 2 tests in 9.682s
OK
```

### 3.2 전역 락 부활 → fixture ① **실패** (진짜 가드 ✓)

`request_lock()`이 단일 공유 락을 반환하도록 바꾸고 target `subprocess.run`을 그 락 안으로
되돌림(= v12 HOL 형태):

```
FAIL: test_slow_target_does_not_block_other_requests
  File "utilities/dispatch_broker.test.py", line 521, in test_slow_target_does_not_block_other_requests
    self.assertFalse((self.artifact / "done-slow.marker").exists())
AssertionError: True is not false
FAILED (failures=1)
```
→ 배리어 + `done-slow.marker` 부재 단언이 HOL blocking 회귀를 **결정론적으로 잡는다**.

### 3.3 v2 hop이 낡은 env instance를 신뢰하도록 변형 → fixture ④ **실패** (진짜 가드 ✓)

`resolve_live_instance`가 `AGENT_DISPATCH_BROKER_INSTANCE`를 먼저 반환하도록 변형:
```
broker_root=/tmp/tmpnykdzc0w/broker
child_spawned=0
FAILED (failures=1)
```
→ SD-55의 핵심(record→hop identity 이동)이 무력화되면 fixture ④가 잡는다.

### 3.4 completion gate 무력화 → fixture ⑦ **실패** (진짜 가드 ✓)

`completion_marker_gate` 본문 최상단에 `return` 삽입:
```
AssertionError: 'reason=completion-marker-missing' not found in
  'check=failed\nreason=global-registry-unset\ndetail=nested --start requires inherited AGENT_DISPATCH_JOBS\nchild_spawned=0\n'
FAILED (failures=3)
```
→ gate가 없으면 다음 관문(`global-registry-unset`)까지 흘러가고 fixture ⑦이 3건 실패로 잡는다.
부수 확인: gate가 registry 해석보다 **앞**에 있음이 이 출력으로 재확인됨(spawn 0 구조적 보장).

### 3.5 ★ B3 순서 수정 되돌림 → **14/14 전부 통과** (가드 부재 — F1)

`process_request`의 inflight 검사와 registry reconcile 순서를 v12(결함) 순서로 되돌림:
```
######## MUTATION 1 (B3 ordering reverted) — FULL broker suite ########
..............
Ran 14 tests in 29.529s
OK
```
→ plan-check가 "★가장 중대"로 지목한 blocker의 수정이 **어떤 fixture로도 보호되지 않는다**.

이것이 진짜 결함인지(수정이 무의미한 no-op이 아닌지) probe로 확증했다 — fake target이
**registry row를 먼저 쓰고**(SD-52의 "spawn 전 row" 불변식이 B3 경합을 도달 가능하게 만드는
바로 그 조건) 6초 sleep, 그 사이 동일 request 재제출:

| 트리 | 재제출 응답 | target 상태 |
|---|---|---|
| **수정본(as-shipped)** | `ok=False`, `reason=broker-request-inflight` | 실행 중 |
| **되돌린 본(B3 결함)** | `ok=True`, **`status=done`**, `recovered_from_registry=True` | **여전히 실행 중** |

```
######## FIXED (as-shipped) ########
RESUBMIT_OK= False
RESUBMIT_REASON= broker-request-inflight
TARGET_STILL_RUNNING= True
######## MUTATED (B3 order reverted) ########
RESUBMIT_OK= True
RESUBMIT_REASON= None
RESUBMIT_STATUS= done
TARGET_STILL_RUNNING= True
```

**결론: 구현은 정확하다**(수정본이 B3를 정확히 차단). 문제는 그 수정이 회귀 테스트로 고정돼
있지 않다는 것 — 미래의 누군가 순서를 되돌려도 스위트는 초록이다. 상세·재현 probe는 §5-F1.

---

## 4. 불변식 보존 — 소스 직접 검토

### 4.1 SD-54 불변식

| 불변식 | 판정 | 근거 |
|---|---|---|
| **atomic transition** | 보존 | `transition()` 호출이 전부 `request_lock` 안(B/D 블록·`recovered_response`). `renew_lease`는 락 안에서 `atomic_json` 직접 기록 |
| **terminal immutability** ★ | **보존** | plan-check B3가 "in-memory state 검사(`:417`)만으로는 병렬에서 깨진다"고 지적한 위험이 실제로 차단됨. (D)가 `current = read_json(path)`로 **on-disk 재독** 후 `TERMINAL`이면 그대로 반환 → 덮어쓰기 불가. `renew_lease`도 락 안에서 `TERMINAL` 확인 후에만 기록하므로 `join(timeout=2.0)` 초과 시에도 terminal 이후 lease 기록 불가 |
| **fencing/lease** | 보존 | lease가 claim 시점 **락 안에서** `time.time()+stale_seconds`로 설정되고(`:529`), renewer가 `max(0.5, stale/3)` 주기로 갱신 → claim부터 target 종료까지 inflight 창에 빈틈 없음. `renew_lease`는 `broker_instance != self.instance_id`면 즉시 종료(fencing 존중) |
| **spawn 전 registry row** | 보존 | 해당 로직은 어댑터 측(`append_job:728` → `Popen:768`)이며 이번 diff가 건드리지 않음 |
| **동시성 cap 미추가 (SD-40 이중 상한 금지)** | **보존** | `grep -n "Semaphore\|BoundedSemaphore\|max_workers\|ThreadPool\|listen("` → `608: self.sock.listen(16)` 단 1건이며 **미변경**. `utilities/model-worker-governor.py`는 diff에 존재하지 않음 |

`request_locks` dict는 GC 없이 누적된다(설계 의도, plan 명시). request_id가 route/node/slug
해시 파생이라 카디널리티가 낮고 broker 재시작으로 리셋되므로 실질 위험 없음.

### 4.2 SD-55 불변식

- **envelope↔현재 instance 대조 존치**: `validate_request`의
  `if request.get("broker_instance") not in allowed_instances: raise BrokerError("broker-instance-mismatch", ...)`
  가 **무변경**. spec §13.5.2의 "identity 검증은 사라지지 않고 record(불변)에서 hop(실시간)으로
  이동"이 코드로 성립한다. `validate_route`의 candidate 매칭만 `contract == 2` 분기로 완화됐고,
  이는 v2 candidate에 `broker_instance` 키 자체가 없기 때문에 필연이다(완화 아님).
- **v1 소급 강제 부재**: `_verify_fallback_chain`이 bool→3상태 정수로 전환되어 v1(root+instance
  필수)·v2(root 필수·instance 부재)·`None`(레거시 미검사)이 분리됐다. 레거시(`None`) 분기는
  기존 `require_broker_binding=False` 거동과 논리적으로 동일(`supported` 존재만 검사) → 회귀 0.
  `stage-dispatch-fallback.py`의 v1 `broker-binding-unset` 검사는 `if contract != 2:`로 감싸였을
  뿐 **한 줄도 변경되지 않았다**.
- **request_id 안정성**: `request_identity`가 `broker_instance`를 digest 입력에 넣지 않으므로
  (route_id/node/slug/parent/target/ordinal만), rollover 전후로 request_id가 불변 → v2에서
  idempotency가 rollover를 가로질러 성립한다. 설계상 정합.
- **3어댑터 wrapper parity**: claude/codex/opencode 3종 모두 `validate_route_record`의 동일 지점
  (worker-route-guard 성공 직후, 최종 `return 0` 직전)에 동일 코드
  (`completion_marker_gate(args.route_file, args.route_node, args.action, args.agent_home)` +
  `fail(e.reason, 65, detail=e.detail, child_spawned="0")`)를 갖고, `main`에서 동일하게
  `args.action`/`args.agent_home`을 세팅한다. **완전 동형**.

### 4.3 SD-56 불변식

- `resolve_agent_home()`이 `core/CORE.md` 검증 선호 순서를 쓰고 `os.environ.get("AGENT_HOME", ROOT)`
  패턴을 쓰지 않음 → writer(conductor)와 reader(gate)의 루트 분열(SD-14b②) 재발 차단.
  `agent_home`이 gate의 **명시 인자**라 함수 내 env 재독이 구조적으로 불가.
- gate 미적용 조건이 `action != "start"` / `route_file` 없음 / `broker_contract_version != 2`
  3종으로, spec의 "기존 v1 record·record 없는 launch는 이 gate의 대상이 아니다"와 정확히 일치.

---

## 5. 발견 사항

### F1 (major, 테스트 내구성) — B3 순서 수정이 회귀 테스트로 보호되지 않음

- **무엇**: `process_request`에서 inflight 검사를 registry reconcile **앞으로** 옮긴 수정
  (plan-check B3, "★가장 중대" blocker)이 어떤 fixture로도 고정돼 있지 않다. 순서를 되돌려도
  `dispatch_broker.test.py`는 **14/14 통과**한다(§3.5).
- **원인**: 이 경합은 *"request가 running이고 그 attempt의 registry row가 이미 존재한다"* 는
  조건에서만 도달 가능하다(SD-52의 "spawn 전 row" 때문에 실전에선 항상 성립). 그런데 fixture ②가
  결정론화를 위해 실 adapter → fake adapter로 전환되면서 **fake adapter가 registry row를 쓰지
  않게 되어** reconcile 분기 자체가 도달 불가능해졌다. v12 원본 fixture는 실 `--register`를 써서
  row가 생겼고 `rows == 1`을 단언했으나, 그 단언이 `assertFalse(self.jobs.exists())`로 대체됐다.
  즉 **결정론을 얻는 대가로 B3 경합 조건을 잃었다** — 그리고 dev_log 01은 fixture ②를 §1.6(a)/B3
  대응으로 기술해 실제 보호 범위를 과대 진술한다.
- **영향**: 현재 구현은 **정확하다**(probe로 확증). 미래 회귀에 대한 보호만 부재하다.
  acceptance ②("attempt/target 정확히 1")는 충족되므로 spec 불충족은 아니다.
- **재현 절차**:
  1. `utilities/dispatch-broker.py`의 `process_request`에서 inflight 블록과 reconcile 블록의
     순서를 맞바꾼다(v12 순서로 복원).
  2. `env -u AGENT_SESSION_ROLE ... python3 utilities/dispatch_broker.test.py` → **14/14 OK**.
  3. 아래 probe를 돌리면 되돌린 본에서 `RESUBMIT_STATUS=done` + `TARGET_STILL_RUNNING=True`
     (= 실행 중 request 조기 종결)가 관측된다.
- **권고**: 신규 fixture 1건 — fake target이 **`--attempt-id`/`--jobs`로 registry row를 먼저 쓴 뒤
  sleep**하게 하고, started 배리어 후 동일 request를 재제출해 `broker-request-inflight`(ok=False)를
  단언. 즉시 사용 가능한 probe 전문은 `_internal/test_reviews/01-fixture-review.md §3`에 있다.
  재분사 여부는 conductor 판단.

### F2 (minor) — fixture ③의 병렬 단언이 공허 통과 가능

`test_fenced_recovery_holds_under_parallel_inflight`의 `assertLessEqual(len(parallel_rows), 1)`은
0건도 허용한다. "중복 launch 0"에는 정확히 대응하지만, 병렬 request가 아예 착지하지 못해도
통과한다(`parallel_results["reply"]`의 성공 여부를 단언하지 않음). victim 측 단언
(`rows == 1` + `recovered_after_fence=True`)이 본체를 지키므로 acceptance ③은 충족.

### F3 (minor) — fixture ②가 v12의 registry-row 단언을 잃음

spec ②의 "attempt/target 정확히 1개"가 이제 **응답 개수 추론**(ok 1 + rejected 1)으로만 확인되고,
실제 target 실행 횟수나 row 개수로 관측되지 않는다. fake adapter가 `started-<slug>.marker`를 쓰므로
launch 횟수를 셀 수 있는데 세지 않는다. 순차 경로(`test_duplicate_request_is_idempotent`)는 실
adapter로 `rows == 1`을 유지하므로 acceptance ②는 충족. F1과 같은 뿌리.

### F4 (롤아웃 운영 — 결함 아님, conductor 인지 필요)

`compile_route`가 이제 **기본 v2**를 생성한다 → merge 후 신규 standard+ headless route는 전부
gate 활성이다. **reader(gate)는 코드 강제이나 writer(conductor의 `capability-route.py complete`)는
문서 강제**(`dev-pipeline.md`)다. conductor가 marker를 쓰지 않으면 다음 스테이지 `--start`가
`completion-marker-missing`으로 fail-closed되어 파이프라인이 정지한다. 이는 spec §13.5.3이 의도한
설계("의무를 문서 vigilance로 남기지 않고 다음 노드 launch의 전제조건으로 규칙화")이지만,
**merge 후 첫 사이클의 conductor가 반드시 알아야 하는 운영 사실**이다.

호환성 확인: 현재 live에 존재하는 이 사이클의 marker
(`/home/Uihyeop/agent_setting/.dispatch/completion/rt-5fd84b9bcf8a799c/{plan,execute}.json`)는
main 체크아웃의 **구 코드**(`write_once(a.output or ...)`)로 `--output` 명시해 작성돼 신규 필드
(`sequence`/`completed_at`)와 이력 파일이 없다. 그러나 gate는 `route_id`/`route_hash`만 읽으므로
**구 marker도 gate를 통과한다** → merge 시 파손 없음. (이 사이클 route는 `broker_contract_version=1`
이라 애초에 gate 미적용 — "소급 강제 금지"가 실환경에서 그대로 관측됨.)

### F5 (기록) — spec §13.5.2 문언(`ensure`) ↔ 구현(`status`-only) 불일치

carryover §1의 이월 사항을 독립 확인했다. 근거는 타당하다: `ensure`는 워커에서 항상 거부되고
(`dispatch-broker.py:604`), 비-워커에선 없어야 할 broker를 Popen해(`:665-673`) fixture ⑩과 v12 AC3을
동시에 파괴한다. `status`는 healthy 경로 관측이 동일하고 ping까지 더해 더 보수적이다. fixture ⑩의
`broker.json` 부재 단언이 이 결정의 수호자로 작동함도 확인했다. **다만 spec 문언은 여전히
`ensure`이므로, 문자 그대로의 §13.5.2 acceptance와 구현은 형식적으로 어긋난다** — 승인된 이탈로
보고 PASS를 유지하되, spec 정정 사이클로 반드시 해소해야 한다.

---

## 6. 회귀 스위트

### 6.1 portable guards — v12 baseline 대조

```bash
env -u AGENT_SESSION_ROLE ... bash hooks/portable-guards.test.sh
```
```
PASS=359 FAIL=0
```
**execute 주장(PASS=359 FAIL=0, v12 baseline 동일) 재현됨.** execute가 기록한 "최초 1회 FAIL=2는
`codex doctor --runtime` 계열 flake"는 내 실행에서 재현되지 않았다(1회 실행, FAIL=0).

### 6.2 경계·투영·계약

```
$ bash tools/check-adaptation-boundary.sh      → OK: adaptation boundary checks passed
$ python3 tools/build-manifest.py --check      → manifest up-to-date; delta baselines bound
$ bash tools/routing-contract.test.sh          → routing-contract: all checks passed
$ git diff --check                             → rc=0 (클린)
$ diff -r skills/autopilot-code adapters/claude/skills/autopilot-code   → 차이 없음
$ diff skills/.../dev-pipeline.md adapters/claude/plugin-marketplace/.../dev-pipeline.md → 차이 없음
```
투영 확인: `adapters/claude/utilities/dispatch_completion_marker.test.py ->
../../../utilities/dispatch_completion_marker.test.py` symlink 존재. **3부 미러 전부 동기.**

### 6.3 ★ 사전존재 실패 4건 — 베이스라인 독립 대조

execute의 "이번 변경의 회귀가 아니다"를 검증하기 위해 `git stash -u`로 worktree를 `98308ec4`
상태로 되돌려 동일 커맨드를 재실행했다.

| 스위트 | 현재 트리 (v13 적용) | **베이스라인 98308ec4** | 판정 |
|---|---|---|---|
| `utilities/dispatch-artifact-root.test.py` | `FAILED (failures=3)` | `FAILED (failures=3)` | **동일 — 회귀 아님** |
| `bash utilities/dispatch-concurrency.test.sh` | `FAIL (3) — 병렬 drift 발견` | `FAIL (3) — 병렬 drift 발견` | **동일 — 회귀 아님** |
| `bash utilities/artifact-root.test.sh` | `not ok - linked worktree resolves primary artifact root` | 동일 | **동일 — 회귀 아님** |
| `bash tools/generated-projections.test.sh` | `not ok - legacy artifact root was not selected for orientation` | 동일 | **동일 — 회귀 아님** |

**execute의 사전존재 주장은 확증됨 — 4건 전부 베이스라인에서 동일 재현.** 이들은 워커 세션의
실제 env/fleet 상태를 흡수하는 하니스 환경 의존성이며(carryover §3와 정합), v13 스코프 밖이다.
참고로 `dispatch-concurrency`의 실패 하위번호는 execute 기록 `(2)`과 달리 내 실행에선 `(3)`이었다 —
실 fleet 동시 프로세스 상태에 좌우된다는 진단 자체를 뒷받침한다.

**worktree 복원 검증** (stash가 무손실이었음을 증명):
```
$ md5sum /tmp/preimage.diff   → bf8aed8c8fbe3af83745ec99e5df2280
$ md5sum /tmp/postimage.diff  → bf8aed8c8fbe3af83745ec99e5df2280
RESTORED: byte-identical
STATUS: identical
stash list after: 0
```
복원 후 `dispatch_broker.test.py` 재실행 → `OK` (14/14 유지).

---

## 7. 경계 준수 — 직접 확인

| 경계 | 확인 방법 | 결과 |
|---|---|---|
| **live broker 불가침** | 검증 전/후 `broker.json` 대조 + 프로세스 확인 | **무결**. `instance_id=brk-d25176b21a134c10a6f6d1608ffc3af4`, `pid=3574735`, `state=running` — 검증 전후 **동일**. `ps -p 3574735` → ALIVE(etime 11:20:17). shutdown/restart/변조 없음. `broker.json` mtime만 갱신되는데 이는 broker 자신의 heartbeat이며 내 접촉이 아니다(instance/pid 불변이 증거) |
| 실제 세션 스폰 금지 | fixture는 전부 임시 `--root` 전용 broker + fake adapter. mutation은 `/tmp` 사본에서만 | 준수 — 실제 claude/codex/opencode 스폰 0건 |
| **소스 수정 금지** | `git diff 98308ec4` md5 검증 전후 동일(`bf8aed8c...`), `git status --porcelain` 동일 | 준수 — worktree 소스 무변경(stash pop 후 byte-identical) |
| `spec/`·`topologies.json` 미수정 | `git status --porcelain spec/ capabilities/topologies.json` | 출력 없음 — **미수정** |
| **worktree 산출물 미기록 (SD-25)** | `git status --porcelain \| grep -E "\.agent_reports\|\.claude_reports"` | 출력 없음. untracked는 `utilities/dispatch_completion_marker.test.py`와 그 symlink 2건뿐 — **정당한 소스** |
| write scope 준수 | 산출물은 `test_logs/`·`_internal/test_reviews/`에만 | 준수 |
| 테스트의 live home 오염 | `/home/Uihyeop/agent_setting/.dispatch/completion/` 감사 | **오염 없음**. `rt-5fd84b9bcf8a799c`(conductor가 이 사이클용으로 작성한 실제 marker) 1개뿐이며, 내 반복 실행이 디렉터리를 늘리지 않았다. `capability_route.test.py`의 `test_write_once_and_completion`은 이름과 달리 route 불변성만 검사하고 marker writer를 호출하지 않는다 |

---

## 8. report 스테이지를 위한 판정 근거 요약

- **spec §13.5 acceptance 10개 조항 전부 충족.** fixture는 통과만 하는 게 아니라 acceptance를
  실제로 겨냥하며, ①④⑦은 mutation test로 "결함을 되살리면 실패한다"를 증명했다.
- **plan-check가 지목한 blocker 4건이 코드에 실재 반영됐다.** 특히 B3(terminal immutability /
  실행 중 request 조기 종결)는 probe로 "수정본은 `broker-request-inflight`로 차단, 되돌린 본은
  `status=done`으로 조기 종결"을 실측 대조해 수정의 유효성을 확증했다.
- **회귀 0.** portable-guards 359/0 재현, 경계·투영·계약 전부 통과, 인접 실패 4건은 베이스라인
  동일 재현으로 비회귀 확증.
- **경계 위반 0.** live broker 무결(동일 instance/pid), spec·topologies 미수정, worktree 무오염.
- **남은 것**: F1(B3 회귀 가드 부재 — merge 전 fixture 1건 추가 권고), F4(merge 후 conductor의
  marker 쓰기 의무가 실효 발생), F5(spec 문언 `ensure`→`status` 정정 필요).
