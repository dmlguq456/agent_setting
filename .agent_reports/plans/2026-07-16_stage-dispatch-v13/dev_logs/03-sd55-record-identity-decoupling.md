# SD-55 — record ↔ broker-identity 결합 해제 실행 로그

## 무엇을 왜

immutable route record가 mutable `broker_instance`를 고정해, broker rollover 후 그 route의
ordinal-1 hop이 영구 불가했다(fleet v10 conductor가 plan 이후 native-subagent로 열화한
근본 원인). 계획 §2대로 record는 `broker_root`(stable identity)만 고정하고, `broker_instance`는
hop 시점에 live 해석하도록 결합을 해제했다(`broker_contract_version: 2`).

## ★ 설계 결정 두 가지 (구현 재량 아님 — plan-check가 못박은 것)

1. **spec 문언은 `ensure`, 구현은 `status`-only.** `ensure`는 워커에서 항상 거부되고
   (`dispatch-broker.py:604`), 비-워커에선 없어야 할 broker를 Popen한다(`:665-673`).
   `stage-dispatch-fallback.py`의 실제 호출자는 depth-1 워커이므로 `ensure`는 (a) 호출자에게
   아무 능력도 안 주고 (b) 금지된 컨텍스트(테스트 하니스)에서만 부작용을 만든다. `status`는
   `ensure`의 healthy 경로와 관측이 같고 ping까지 더해 더 보수적이다. → spec 문언 정정은
   `_internal/carryover.md`에 이월(spec 파일 미수정).
2. **env 정제는 두 지점 모두**(`resolve_live_instance` + `submit_broker`). 한쪽만 하면
   `dispatch-broker.py:749`의 fall-through(`request` 서브커맨드에서도 `broker_status` 호출)가
   낡은 env를 보고 `broker-instance-mismatch`로 죽는다(plan-check B1, 작성자 실측 재확인).

## 무엇을 어떻게 바꿨나

### `utilities/capability-route.py`

- `BROKER_FIELDS_V2 = {"broker_root"}`, `BROKER_CONTRACT_VERSION = 2` 추가.
- `_validate_dispatch_evidence(evidence, contract_version=BROKER_CONTRACT_VERSION)`:
  v2는 `broker_root`만 normalize, `broker_instance`는 입력에 있어도 **strip**(depth-0
  probe 출력이 그대로 들어와도 v2 record가 나와야 함). `broker_root` 부재 시 `ValueError`.
- `_fallback_chain(evidence, contract_version)`: 존재 검사(§13.5.2 "no supported depth-0
  launch broker tuple") 버전 분기 — v2는 `broker_root`만 필수.
- `_verify_fallback_chain(node, contract_version=None)`: **bool → 3상태 버전 정수**로
  전환. v1=`broker_root` and `broker_instance` 필수(기존 그대로). v2=`broker_root` 필수
  **and** `broker_instance` **부재**여야 함(있으면 `ValueError` — "v2 candidate must not
  carry broker_instance"). `None`(레거시/헤드리스 아님)은 미검사. 기존 `:191` 호출부가
  `route.get("broker_contract_version")==1`이라는 bool을 넘겨 v2에서 `False`가 되어 검사
  자체가 사라지던 결함(plan-check M-발견)을 이 시그니처 전환으로 닫았다.
- `compile_route`: dispatch_evidence 검증·fallback chain 생성에 `BROKER_CONTRACT_VERSION`
  전달, `broker_contract_version` 필드를 `BROKER_CONTRACT_VERSION if checked_dispatch is not
  None else None`으로 — **신규 compile은 이제 전부 v2**.
- `verify_route`: `route.get("broker_contract_version")`을 그대로 `_validate_dispatch_evidence`/
  `_verify_fallback_chain`에 전달(레거시 None/v1/v2 3상태 모두 대응).

### `utilities/stage-dispatch-fallback.py`

- 신규 `broker_env(contract)` — v2는 `AGENT_DISPATCH_BROKER_INSTANCE`를 os.environ 사본에서
  제거, v1(또는 None)은 `dict(os.environ)` 그대로(회귀 0).
- 신규 `resolve_live_instance(broker_root, jobs)` — **status-only**(`ensure` 미호출).
  `dispatch-broker.py status --root ... --jobs ...`를 `env=broker_env(2)`로 실행, 실패 시
  빈 문자열 반환.
- `main()`: `p.parse_args()` 직후 `explicit_broker_root = args.broker_root is not None`
  포착(기본값 대입 전 — plan-check m1). `route.get("broker_contract_version")`을 `contract`로
  저장. v1(`contract != 2`)은 기존 `broker-binding-unset` 검사 **한 줄도 안 바뀜**(회귀 0).
- 후보 루프(`for row in hop.get("candidates", [])`) **안에서** v2 해석: `row["broker_root"]`를
  candidate별로 확정 → explicit override가 있는데 route의 broker_root와 다르면
  `broker-root-mismatch` → `resolve_live_instance(row_root, jobs)` → 빈 문자열이면
  `broker-unavailable`. 루프 밖에서 해석하면 candidate root와 어긋난다는 것이 plan-check
  지적이었다.
- `submit_broker(args, envelope, broker_root, contract)`: 시그니처에 `broker_root`/`contract`
  추가, `subprocess.run`에 `env=broker_env(contract)` 신규 추가(**기존엔 `env=` 자체가 없어
  낡은 env를 그대로 상속**했다 — B1의 핵심 결함).
- `broker_envelope(..., live_instance=None)`: `broker_instance` 필드를
  `live_instance or row["broker_instance"]`로 — v2는 `live_instance`가 유일한 출처(v2
  candidate엔 `broker_instance` 키 자체가 없으므로), v1은 `live_instance=None`이라 기존
  `row["broker_instance"]` 그대로.
- 성공 출력에 `broker_root={submit_root}`(기존 `args.broker_root`가 아니라 실제 제출에
  쓰인 루트로 정정 — v2에서 args.broker_root는 기본값일 뿐 candidate root와 다를 수 있음)
  + v2일 때 `broker_instance_source=live-status` 관측 라인 추가.

### `utilities/dispatch-broker.py`

- `validate_route`의 candidate 매칭(`:243` 부근)에 `contract = route.get("broker_contract_version")`
  분기: `(contract == 2 or row.get("broker_instance") == request["broker_instance"])` —
  v2 candidate엔 instance가 없으므로 이 조건을 건너뛰지 않으면 모든 v2 hop이
  `broker-route-mismatch`로 전멸했다(plan §2.6). `validate_request:285-290`의
  envelope↔현재 instance 대조는 **건드리지 않았다**(SD-55가 "사라지지 않는다"고 못박은
  검증).

## 기존 테스트 파급 — v2 기본값 전환의 다운스트림

compile_route가 v2를 기본 생성하게 되면서, v1을 가정하던 여러 헬퍼/테스트가 즉시 깨졌다
(예상된 파급이었음, plan §6가 SD-55를 마지막에 두라고 한 이유와 일치):

- `capability_route.test.py`:
  - `test_v12_route_binds_broker_and_legacy_v11_route_still_verifies` — v2 기본값 확인으로
    갱신(instance 부재 확인 추가), "missing" 변형을 `broker_instance` pop → `broker_root`
    pop으로 교체(v2에서 검사 대상이 바뀌었으므로), legacy(레거시, contract 필드 자체 없음)
    분기는 그대로 유지.
  - 신규 `test_v1_record_keeps_instance_binding_rules`(fixture ⑤) — v2 compile → 손수
    `broker_contract_version=1` + `broker_instance` 재주입 → rehash. v1 규칙(instance 필수)
    유지 확인 + v2 record에 instance를 넣으면 거부되는지(§2.4d 신규 규칙) 확인.
- `dispatch_broker.test.py`:
  - `self.request()`/`fixture_broker_request()` 헬퍼가 `row["broker_instance"]`를 직접
    읽던 지점 전부 `live_instance=self.meta["broker_instance"]` 명시 전달로 교체(v2
    candidate엔 그 키가 없어 `KeyError`였다).
  - `test_unknown_request_fields_are_rejected_without_registry_row`의 손수 구성 payload도
    동일하게 `self.meta["broker_instance"]`로 교체.
  - ★ `test_tampered_inherited_instance_fails_closed`, `test_missing_broker_fails_closed` —
    신규 `route_v1()` 헬퍼로 **v1 record 고정**(§1.6b, plan-check M1이 정확히 예견한 시점:
    "B1을 고치기 전엔 우연히 통과, 고치는 순간 실패로 전환"). v2 기본값에서는 (a) env
    tamper가 무의미해지고(§2.3 의도대로) (b) explicit `--broker-root` mismatch가
    `broker-root-mismatch`라는 다른 사유로 막혀(§2.5d) 두 테스트의 v1-only 원래 의도가
    성립하지 않게 되므로 v1 record로 고정해 원래 의도를 보존했다.
  - 신규 `test_v2_record_survives_broker_rollover`(fixture ④) — fixture broker(setUp의
    self.broker_root)만 stop/ensure. env에 낡은 instance를 **일부러** 주입 →
    `check=ok`+`selected_hop=same-harness-headless`+`fallback_ordinal=1`+`check=degraded`
    부재+재로드 후 `route_hash` 불변 단언.
  - 신규 `test_v2_record_without_live_broker_fails_closed`(fixture ⑩, plan-check M4가
    초안 미커버로 지적한 acceptance ③ 전용) — (a) 존재한 적 없는 broker root, (b) 살아있다
    stop된 fixture broker, 양쪽 다 `reason=broker-unavailable`+`child_spawned=0`+jobs.log
    row 0건+**broker.json 미생성**(status-only 결정의 수호자) 단언.

## 실행 커맨드 및 결과

```
$ unset AGENT_SESSION_ROLE AGENT_DISPATCH_CHILD AGENT_DISPATCH_BROKER_INSTANCE AGENT_DISPATCH_BROKER_ROOT AGENT_DISPATCH_JOBS
$ python3 utilities/capability_route.test.py -v      # Ran 11 tests ... OK
$ python3 utilities/dispatch_broker.test.py -v        # Ran 14 tests ... OK
$ python3 utilities/stage_dispatch_fallback.test.py -v # Ran 3 tests ... OK
$ python3 utilities/dispatch_completion_marker.test.py -v # Ran 4 tests ... OK (SD-56과 교차 확인)
$ python3 utilities/dispatch_contract.test.py -v       # Ran 5 tests ... OK
$ python3 utilities/worker_route_guard.test.py -v      # Ran 3 tests ... OK
$ python3 utilities/dispatch_adapters_v11.test.py -v   # Ran 1 test ... OK
```

## 전체 회귀 (§5 전체)

인접 회귀(§5.2):
```
$ python3 utilities/spec_transaction.test.py -v         # OK
$ python3 utilities/model_worker_governor.test.py -v     # OK
$ python3 utilities/resource_runner.test.py -v           # OK
$ python3 tools/capability_topology.test.py -v            # OK
$ bash utilities/dispatch-route.test.sh                  # PASS
$ bash utilities/dispatch-liveness.test.sh                # PASS
$ bash utilities/dispatch-wait.test.sh                    # PASS
```

**사전 존재(pre-existing) 실패, 우리 변경과 무관 — `git stash -u`로 원 커밋(98308ec4) 상태와
diff 없이 재현 확인**:
- `utilities/dispatch-artifact-root.test.py` — 3건 실패(`artifact_root=` 값이 워커 세션의
  실제 `AGENT_ARTIFACT_ROOT` 환경을 흡수해 fixture가 기대한 임시 경로와 어긋남). 베이스라인
  동일 3건 실패로 재현.
- `bash utilities/dispatch-concurrency.test.sh` — "(2) expected 3 ALIVE, got 1" — 워커
  세션의 실제 동시 프로세스 상태를 관찰하는 fixture라 실제 fleet 상태에 좌우됨. 베이스라인
  동일 재현.
- `bash utilities/artifact-root.test.sh` — "linked worktree resolves primary artifact
  root" 1건. 베이스라인 동일 재현.
- `bash tools/generated-projections.test.sh` — "legacy artifact root was not selected for
  orientation" 1건. 베이스라인 동일 재현.

**전체 portable guards + 투영/경계**:
```
$ bash hooks/portable-guards.test.sh
# PASS=359 FAIL=0   (재실행 시 재현 확인 — 최초 1회 관측된 FAIL=2는 "codex doctor --runtime"
#                     계열의 일시적 flake였고, git stash -u 베이스라인에서도 동일 flake가
#                     재현되어 우리 변경과 무관함을 확인했다. 재실행 시 양쪽 다 FAIL=0)
$ python3 tools/build-manifest.py --check
# manifest up-to-date; delta baselines bound
$ bash tools/check-adaptation-boundary.sh
# 최초: FAIL - 신규 dispatch_completion_marker.test.py가 adapters/claude/utilities/에
#   symlink 미투영 + tools/check-adaptation-boundary.sh의 UTILITY_DEFERRED 목록(2곳) 미등재.
#   v12 사이클이 동일 패턴을 밟았던 것과 일치(§7 리스크 표 실현).
# 조치: adapters/claude/utilities/dispatch_completion_marker.test.py symlink 생성
#   (다른 dispatch_*.test.py와 동일 패턴), UTILITY_DEFERRED 2곳에 파일명 추가.
# 재실행: OK: adaptation boundary checks passed (WARN 84건은 기존 Claude/model 참조
#   경고로 v12 이전부터 존재 — 우리 스코프 아님)
$ bash tools/generated-projections.test.sh    # 상기 사전 존재 실패 1건, 베이스라인 동일
$ bash tools/routing-contract.test.sh          # routing-contract: all checks passed
$ git diff --check                             # 클린 (rc=0)
```

## live broker / spec 무결성 확인

```
$ cat /home/Uihyeop/agent_setting/.dispatch/broker/broker.json | python3 -c \
    "import json,sys; d=json.load(sys.stdin); print(d['instance_id'], d['pid'])"
brk-d25176b21a134c10a6f6d1608ffc3af4 3574735   # 사이클 시작 시점과 동일 — shutdown/restart/변조 없음
$ git status --short spec/
# (출력 없음 — spec/ 미수정)
```
