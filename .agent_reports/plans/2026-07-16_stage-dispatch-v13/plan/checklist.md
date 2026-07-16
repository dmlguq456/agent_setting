# stage-dispatch v13 — execute 체크리스트

계획 본문: `plan/plan.md`. 각 항목의 §참조는 그 문서 기준.
worktree: `/home/Uihyeop/agent_setting-wt/stage-dispatch-v13` (소스만). 산출물은 artifact_root.

```bash
cd /home/Uihyeop/agent_setting-wt/stage-dispatch-v13
TESTENV='env -u AGENT_SESSION_ROLE -u AGENT_DISPATCH_CHILD -u AGENT_DISPATCH_BROKER_INSTANCE -u AGENT_DISPATCH_BROKER_ROOT -u AGENT_DISPATCH_JOBS'
```

## 0. 착수 전 (§0)

- [x] `plan/plan.md` §0 전체를 읽었다 — 특히 §0.1(워커 env로 테스트 전멸), §0.2(live broker 금지), §0.3(`skills/` 3부 미러).
- [x] baseline 재확인: `$TESTENV python3 utilities/dispatch_broker.test.py` → **10 OK**. (prefix 없이 돌리면 10 errors — 정상이며 회귀 아님)
- [x] live broker root(`/home/Uihyeop/agent_setting/.dispatch/broker`)를 건드리는 커맨드를 쓰지 않기로 확인했다.
- [x] `capabilities/topologies.json`은 수정하지 않는다(§0.4).

## 1. SD-54 — broker 동시성 분리 (§1)

- [x] `dispatch-broker.py:385` `self.request_guard` 제거 → `self.locks_guard` + `self.request_locks` dict 도입 (§1.3a). `meta_guard`는 유지.
- [x] `BrokerServer.request_lock(request_id)` 추가 (§1.3b). **terminal 후 dict GC 넣지 말 것.**
- [x] `BrokerServer.renew_lease(request_id, stop_event)` 추가 (§1.3d) — 주기 `max(0.5, stale_seconds/3)`, terminal/instance 확인 후 `atomic_json`으로 lease만 연장. `transition()` 쓰지 말 것.
- [x] `process_request`(`:444-523`) 재작성 (§1.2/§1.3e):
  - [x] (A) 검증·dedup 준비를 **락 밖**으로: `prior_recovery`/`allowed_instances`(현행 447-455), `validate_request`(456-462), `digest`(463)
  - [x] (B) `with self.request_lock(request_id):` 안에 dedup 분기 + claimed/running transition + `adapter_command` + env 구성
  - [x] ★ **(B) 안에서 `:474-476` inflight 검사를 `:471-473` registry reconcile 앞으로 옮겼다** — "로직 변경 없이 이동"하면 조기-terminal + terminal 덮어쓰기 버그가 재현된다(§1.3e). reconcile은 fenced recovery 경로 전용.
  - [x] (C) **락 밖**에서 renewer 시작 → `subprocess.run` → `finally` renewer 정지(daemon + `stop_event.set()` + `join(timeout)`)
  - [x] ★ (D) `with self.request_lock(request_id):` 안에서 **on-disk state 재독** 후 terminal 여부 확인 → 이미 terminal이면 그대로 반환, 아니면 전이. in-memory state로 전이하면 terminal immutability가 깨진다.
- [x] broker에 동시성 cap/세마포어를 **넣지 않았다** (§1.4). `sock.listen(16)` 미변경.
- [x] fixture ①: `dispatch_broker.test.py`에 `fake_agent_home()` 헬퍼 + `test_slow_target_does_not_block_other_requests` (§4.0/§4.2①).
  - [x] ★ 가짜 adapter가 sleep **전에** `started-<slug>.marker`를 쓴다
  - [x] ★ `fast` 제출 **전에** `started-slow.marker` 폴링 **배리어**를 넣었다 — 없으면 회귀를 못 잡는다(거짓 음성)
  - [x] 단언: fast가 done일 때 `done-slow.marker` **부재**
- [x] fixture ②: 기존 `:269`/`:278` 기대값을 §1.6(a)대로 조정 — **`broker-request-inflight`를 정확히 단언**(관대한 "둘 중 하나" 단언 금지) + row 1개 + attempt_id 1종. (결정론화를 위해 fixture broker의 2초 sleep 대상으로 전환 — 실제 register 대상은 ms 단위로 끝나 겹침을 보장 못 함을 실측.)
- [x] ★ `:404` `test_tampered_inherited_instance_fails_closed`를 **v1 record로 고정**했다 (§1.6b) — 방치하면 B1 수정 시점에 갑자기 실패로 전환된다. (SD-55가 compile_route 기본값을 v2로 바꾼 시점에 정확히 실패 전환을 실측 확인 후 `route_v1()` 헬퍼로 고정.)
- [x] fixture ③: 기존 `:322`/`:356` 유지 + `test_fenced_recovery_holds_under_parallel_inflight` 추가.
- [x] `$TESTENV python3 utilities/dispatch_broker.test.py -v` → 10 + 신규 전부 OK. (SD-55까지 반영된 최종 상태 14/14 OK)

## 2. SD-56 — completion marker (§3)

- [x] ★ `utilities/dispatch_contract.py`에 **검증형 `resolve_agent_home()`** 공유 헬퍼 추가 (§3.2.1) — `adapters/claude/bin/dispatch-headless.py:546-558`의 `core/CORE.md` 검증 선호 순서를 옮긴다. **`os.environ.get("AGENT_HOME", ROOT)` 금지** (ROOT=worktree → registry split 재발).
- [x] `capability-route.py`: `completion_dir(route_id)`(= 공유 `resolve_agent_home()` 사용) + `atomic_write(path, payload)` + `write_completion_marker(...)` 추가 (§3.2).
- [x] `complete` 분기(`:233-240`)를 canonical 경로로 전환. `--output` override 유지, `<evidence>.completion.json` 기본값 제거.
- [x] 재수확 규칙 구현: 동일 evidence sha256 → no-op / 변경 시 `<node_id>.<seq>.json` write-once + canonical 원자 교체.
- [x] `utilities/dispatch_contract.py`에 `completion_marker_gate(route_file, route_node, action, agent_home)` 추가 (§3.3). **어댑터별 3중 구현 금지.** `agent_home`은 명시 인자 — 함수 안에서 env를 다시 읽지 말 것.
  - [x] `action != "start"` → 미적용
  - [x] `route_file` 없음 → 미적용
  - [x] `broker_contract_version != 2` → 미적용 (v1 소급 강제 금지)
  - [x] `depends_on` 전 노드 marker 존재 + `route_id`/`route_hash` 일치 검사 → 부재 시 `DispatchContractError("completion-marker-missing")`
- [x] 어댑터 3종 `validate_route_record` 성공 return 직전에 gate 호출 + `fail(e.reason, 65, detail=..., child_spawned="0")`:
  - [x] `adapters/claude/bin/dispatch-headless.py:607` (+ ★ `main:615` 직후 `args.action = action` **및 `args.agent_home = resolve_agent_home()`** 세팅 — `agent_home`은 현행 `:672`에서야 계산돼 gate 시점에 scope에 없다. `:672`는 `args.agent_home` 재사용으로 정리)
  - [x] `adapters/codex/bin/dispatch-headless.py:~701` (동형)
  - [x] `adapters/opencode/bin/dispatch-headless.py:~608` (동형)
- [x] gate가 `shutil.which(...)`(claude `:669`)·registry(`:674`)·broker ensure(`:682`)보다 **앞**임을 확인했다 → spawn 0건.
- [x] ★ gate **앞의 선행 게이트 2종**을 인지했다 (§3.3): `validate_nested_eligibility`(`:652`, exit 69) → `worker-route-guard.py`(`:596-602`) → completion gate. fixture ⑦ 커맨드가 이를 통과하도록 구성해야 한다.
- [x] `utilities/dispatch-node.py`: `completion_marker=<canonical path>` 출력 한 줄 + `import os` 추가 (§3.4). **관측 편의이며 acceptance 요구 아님 — 생략 가능.** (저위험이라 포함)
- [x] `dev-pipeline.md:24` 뒤에 conductor `complete` 의무 문단 추가 (§3.5) — **3부 전부**:
  - [x] `adapters/claude/skills/autopilot-code/references/dev-pipeline.md`
  - [x] `skills/autopilot-code/references/dev-pipeline.md`
  - [x] `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-code/references/dev-pipeline.md`
  - [x] `diff -r skills/autopilot-code adapters/claude/skills/autopilot-code` → 차이 없음
- [x] 신규 `utilities/dispatch_completion_marker.test.py` 작성 — fixture ⑥⑦⑧⑨ (§4.2).
  - [x] ⑥ canonical 경로 + 6필드가 record와 일치
  - [x] ⑦ 3어댑터 parametrize, `reason=completion-marker-missing` + `child_spawned=0` + jobs.log row 0건. ★ `--parent-harness/--parent-transport/--parent-sandbox/--nested-eligibility supported/--eligibility-source` 포함 필수(§4.2⑦)
  - [x] ⑧ (a) v1 record start·(b) record 미결합 start → gate 미적용 + (c) gate 헬퍼 밖에 `completion-marker-missing` 매핑 부재 정적 단언
  - [x] ⑨ 이력 보존 + 최신 authoritative + 동일 evidence no-op
- [x] `$TESTENV python3 utilities/dispatch_completion_marker.test.py -v` → 전부 OK.
- [x] (후속) 투영 census: `adapters/claude/utilities/dispatch_completion_marker.test.py` symlink 생성 + `tools/check-adaptation-boundary.sh`의 `UTILITY_DEFERRED` 목록(2곳) 등재 — v12와 동일 패턴 재발, `--check` 출력 지시대로 해소.

## 3. SD-55 — record ↔ identity 결합 해제 (§2)

- [x] `capability-route.py:18`: `BROKER_FIELDS_V2 = {"broker_root"}` + `BROKER_CONTRACT_VERSION = 2` 추가.
- [x] `_validate_dispatch_evidence(evidence, contract_version)` — v2는 `broker_root`만 normalize하고 `broker_instance`를 **strip**; `broker_root` 부재 시 `ValueError`. v1 분기 현행 유지 (§2.4b).
- [x] `_fallback_chain(evidence, contract_version)` — `:84-89` 존재 검사 버전 분기 (§2.4c).
- [x] `_verify_fallback_chain(node, contract_version)` — **bool → version 3상태** (§2.4d): v1=root+instance, v2=root 필수·instance 부재, None=미검사. 호출부 `:191` 수정.
- [x] `compile_route`: `:150-151` 버전 전달, `:171` → `BROKER_CONTRACT_VERSION`.
- [x] `verify_route:188-191`: `route.get("broker_contract_version")` 전달.
- [x] ★ `stage-dispatch-fallback.py`: `broker_env(contract)` 헬퍼 추가 (§2.3) — v2면 `AGENT_DISPATCH_BROKER_INSTANCE` 제거, v1이면 `dict(os.environ)` 그대로.
- [x] `resolve_live_instance(broker_root, jobs) -> str` 추가 (§2.5a) — **status-only**. ★ `ensure`-fallback을 **넣지 말 것**: 비-워커에서 실제 broker를 Popen해(`:665-673`) `:396` fail-closed 테스트를 파괴한다. 실패 시 `""`.
- [x] `p.parse_args()` **직후** `explicit_broker_root = args.broker_root is not None` 포착 (§2.5b) — `:186-189`가 기본값을 대입한 뒤엔 명시 여부를 알 수 없다.
- [x] `main`: v1 → 현행 `:190` `broker-binding-unset` **무변경** (§2.5c).
- [x] **후보 루프 안**(`:198`)에서 v2 해석 (§2.5d): `row_root` 확정 → `explicit_broker_root`면 불일치 시 `broker-root-mismatch` → `resolve_live_instance(row_root, jobs)` → `""`면 `fail("broker-unavailable", 76, child_spawned="0")`. 루프 밖에서 해석하면 candidate root와 어긋난다.
- [x] ★ `submit_broker`에 `env=broker_env(contract)` 추가 (§2.5e) — **현행엔 `env=` 자체가 없다**. 빠뜨리면 `dispatch-broker.py:749` fall-through의 `broker_status`가 낡은 env를 보고 `broker-instance-mismatch`로 죽는다. `submit_root`도 인자로 전달.
- [x] `broker_envelope(..., live_instance=None)`: `:119` → `live_instance or row["broker_instance"]`. envelope `schema_version`은 1 유지.
- [x] `dispatch-broker.py:243` `validate_route` candidate 매칭 버전 분기 (§2.6) — v2면 instance 대조 생략. **`validate_request:285-290`의 envelope↔현재 instance 대조는 건드리지 말 것.**
- [x] fixture ④: `test_v2_record_survives_broker_rollover` — fixture broker만 stop/ensure; env에 **낡은 instance** 주입; `check=ok`+`fallback_ordinal=1`+`degraded` 부재+`route_hash` 불변 (§4.2④). `self.broker_root`가 temp임을 테스트 안에서 assert.
- [x] fixture ⑤: `capability_route.test.py`에 `test_v1_record_keeps_instance_binding_rules` — v1 손수 구성 후 `ROUTE.route_hash`로 재해시 (§4.2⑤).
- [x] ★ fixture ⑩: `test_v2_record_without_live_broker_fails_closed` (§4.2⑩) — SD-55 acceptance ③은 초안에서 **미커버**였다. `reason=broker-unavailable` + `child_spawned=0` + row 0건 + **broker가 생기지 않았음**(`broker.json` 부재).
- [x] `$TESTENV python3 utilities/capability_route.test.py -v` / `stage_dispatch_fallback.test.py -v` / `dispatch_broker.test.py -v` → 전부 OK.

## 4. 전체 회귀 (§5)

- [x] §5.1 초점 스위트 7종 전부 통과
- [x] §5.2 인접 회귀 10종 — 6종 통과, 4종 사전 존재(pre-existing) 실패를 `git stash -u` 베이스라인 대조로 확인(우리 변경과 무관): `dispatch-artifact-root.test.py`(3건), `dispatch-concurrency.test.sh`, `artifact-root.test.sh`, `generated-projections.test.sh`. 상세는 dev_logs/03 참조.
- [x] `$TESTENV bash hooks/portable-guards.test.sh` → `FAIL=0` (PASS=359, v12 baseline과 동일)
- [x] `python3 tools/build-manifest.py --check` → 통과
- [x] `bash tools/check-adaptation-boundary.sh` → PASS (신규 test 파일 symlink 투영 + UTILITY_DEFERRED 등재 후)
- [x] `bash tools/generated-projections.test.sh` → 사전 존재 실패 1건(베이스라인 동일, 우리 스코프 아님)
- [x] `bash tools/routing-contract.test.sh` → PASS
- [x] `git diff --check` → 클린

## 5. 마무리

- [x] live broker를 건드리지 않았음을 확인 (`git status` + broker.json 미변경). 롤오버는 merge 후 depth-0 main의 몫.
- [x] `spec/` 미수정 확인.
- [x] `_internal/carryover.md`에 §8의 이월 4건 기록: (1) SD-55 문언 정정(ensure→**status-only**), (2) SD-56 quick/inline owner 경로 미배선, (3) 테스트 하니스 워커 env 의존성, (4) v12 잔여 O2/O3/O4.
- [x] `dev_logs/`에 단계별 실행 로그 기록 (write_scope 준수).
