# SD-54 — broker 동시성 분리 실행 로그

## 무엇을 왜

`utilities/dispatch-broker.py`의 `process_request`가 접수·검증·dedup·claim·전이부터 target
`subprocess.run`까지 **전역 락(`request_guard`)** 하나로 직렬화하고 있었다(HOL blocking, fleet
v10 실측 12분 차단). 계획 §1대로 접수/검증/claim/전이 = short critical section, target 실행
생애 = 무락으로 재구성했다.

## 무엇을 어떻게 바꿨나

`utilities/dispatch-broker.py`:
- `BrokerServer.__init__`: `self.request_guard` 제거 → `self.locks_guard`(dict 보호용) +
  `self.request_locks: dict[str, threading.Lock]` 도입.
- 신규 `BrokerServer.request_lock(request_id)` — 요청별 락을 지연 생성. **GC 없음**(설계
  의도 — terminal 후에도 남긴다. 락 카디널리티는 route/node/slug 해시라 낮고 broker
  재시작으로 리셋된다).
- 신규 `BrokerServer.renew_lease(request_id, stop_event)` — `stale_seconds/3` 주기로
  락 안에서 lease만 연장(`transition()` 미사용, terminal/instance 확인 후 `atomic_json`
  직접 기록).
- `process_request` 재작성:
  - (A) 검증·dedup 준비(구 447-455/456-462/463)는 락 밖.
  - (B) `with self.request_lock(...)`: dedup 분기 + claimed/running 전이 + `adapter_command`
    + env 구성. **★ `:474-476` inflight 검사를 `:471-473` registry reconcile 앞으로 이동**
    (plan §1.3e의 B3 수정 — "로직 변경 없이 이동"하면 조기-terminal + terminal 덮어쓰기가
    재현된다는 것이 plan-check에서 실측 확인된 defect였다). reconcile은 fenced recovery
    (predecessor instance 또는 lease 만료) 전용으로 좁혔다.
  - (C) 락 밖에서 lease renewer 스레드 시작 → `subprocess.run` → `finally`로 renewer 정지
    (`stop_event.set()` + `join(timeout=2.0)`).
  - (D) `with self.request_lock(...)`: **on-disk state 재독** 후 이미 terminal이면 그대로
    반환, 아니면 전이. in-memory state로 전이하면 terminal immutability가 병렬에서
    깨진다(§1.3e).
- 동시성 cap 미추가 — `sock.listen(16)` 미변경, SD-40 governor 소유 유지(§1.4).
- `dispatch-broker.py:243` `validate_route` candidate 매칭에 `contract == 2` 분기 추가
  (v2 candidate는 broker_instance가 없음 — SD-55 배선, 아래 03 로그 참조).

## fixture 4종 (`utilities/dispatch_broker.test.py`)

- 신규 `fake_agent_home()` — `core/CORE.md` + 가짜 `adapters/claude/bin/dispatch-headless.py`
  (sleep 전 `started-<slug>.marker`, sleep 후 `done-<slug>.marker` 기록). sleep 초는
  `AGENT_ARTIFACT_ROOT/sleep-seconds.json`에서 slug별로 읽음(계획 원안의 단일 sleep_seconds
  인자 대신 slug 기반 config — 동일 브로커 세션에서 slow/fast 두 다른 지속시간이 필요했기
  때문. 의도 보존, API만 조정).
- 신규 `test_slow_target_does_not_block_other_requests` (fixture ①) — slow 제출 →
  `started-slow.marker` 폴링 배리어(§4.2① M2 반영) → fast 제출 → fast가 `done-slow.marker`
  **부재** 상태에서 완주함을 단언 → slow join 후 정상 완주 확인.
- `test_concurrent_duplicate_request_creates_one_attempt` (fixture ②) — §1.6(a)대로
  "관대한 단언" 폐기, **`broker-request-inflight`를 정확히 단언**. 결정론화를 위해
  fixture broker(2초 sleep)로 전환 — 실측: 실제 `--register` 대상이 두 자리 ms로 끝나
  진짜 겹침을 보장 못 함(최초 시도에서 duplicate로 새는 것을 확인). 추가로 `communicate()`를
  list comprehension으로 순차 호출하던 기존 패턴이 두 프로세스를 사실상 순차 실행시키는
  버그였음을 발견 — 스레드 기반 동시 `communicate()`로 교체.
- `test_fenced_recovery_holds_under_parallel_inflight` (fixture ③ 추가) — claim-crash
  시나리오 + 동시 무관 request가 영향받지 않음을 확인(row 개수 비교).
- `test_tampered_inherited_instance_fails_closed` — ★ v1 record로 고정(§1.6b, M1) —
  신규 `route_v1()` 헬퍼로 손수 v1 구성. SD-55가 compile_route 기본값을 v2로 바꾸면서
  이 잠금이 실제로 필요해졌다(아래 03 로그).
- `test_missing_broker_fails_closed` — 마찬가지로 v1 잠금(§2.5d의 explicit-root-mismatch
  분기가 v2에서 이 시나리오의 의미를 바꾸기 때문 — 아래 03 로그 "발견" 참고).
- 신규 `test_v2_record_survives_broker_rollover`(fixture ④), `test_v2_record_without_live_broker_fails_closed`
  (fixture ⑩)는 SD-55 배선 이후 커밋 — 03 로그에 상세.

## 실행 커맨드 및 결과

```
$ cd /home/Uihyeop/agent_setting-wt/stage-dispatch-v13
$ unset AGENT_SESSION_ROLE AGENT_DISPATCH_CHILD AGENT_DISPATCH_BROKER_INSTANCE AGENT_DISPATCH_BROKER_ROOT AGENT_DISPATCH_JOBS
$ python3 utilities/dispatch_broker.test.py -v
```
최종(SD-55까지 반영된 상태): **14/14 OK**(§1 단계 완료 시점 기준 12/12 OK — 이후 SD-55가
fixture ④⑩ 2건을 추가해 14개).

## 회귀 근거

- baseline 재확인: 워커 env 제거 시 기존 10 tests 전부 OK(§0.1 그대로).
- `test_concurrent_duplicate_request_creates_one_attempt`/`test_tampered_inherited_instance_fails_closed`/
  `test_missing_broker_fails_closed`는 기대값을 조정했으나 각각 §1.6/plan-check가 요구한
  변경이며, 조정 근거를 인라인 주석으로 남겼다.
