# stage-dispatch v13 — carryover (execute 스테이지 산출)

execute 스테이지에서 이월이 확정된 항목. spec 파일(`spec/stage-dispatch/prd.md`)은 이 사이클에서
수정하지 않았다 — 아래는 향후 spec 정정/후속 사이클 후보로만 기록한다.

## 1. SD-55 문언 정정 후보 — `ensure` → **status-only**

`spec/stage-dispatch/prd.md §13.5.2`는 "client(stage-dispatch-fallback)는 request 제출
직전 record의 `broker_root`에 대해 `dispatch-broker.py ensure`를 idempotent 실행해 live
instance를 확보"라고 쓴다. 실제 구현은 **`status`-only**다(`utilities/stage-dispatch-fallback.py`의
`resolve_live_instance`).

**근거**: `ensure`는 워커 세션에서 항상 거부된다(`dispatch-broker.py:604`
`broker-ensure-worker-forbidden`). `stage-dispatch-fallback.py`의 실제 호출자는 depth-1
conductor이고 이는 워커 세션이다. 문언 그대로 구현하면:
- 실제 호출자(워커)에게는 **항상** 실패한다 — 아무 능력도 추가하지 않는다.
- 비-워커(예: 테스트 하니스)에서는 `ensure`가 healthy 아닌 broker root에 대해 실제로
  broker를 Popen한다(`:665-673`) — fail-closed여야 할 자리(`dispatch_broker.test.py:396`
  `test_missing_broker_fails_closed` 및 신규 fixture ⑩)에서 없어야 할 broker가 생겨
  v12 AC3(§13.4.4-3)과 SD-55 acceptance ③이 동시에 회귀한다.

`ensure()`의 healthy 경로는 `broker_status(root, jobs, stale_seconds)`를 그대로 반환하므로
(`:607-608`), broker가 살아 있는 한 `status`와 `ensure`의 관측 결과는 동일하다. `status`는
ping(`:731-737`)까지 더해 더 보수적(fail-closed 방향)이다. 권한 경계도 그대로 지켜진다 —
client는 broker를 **기동하지 않고 조회만 한다**.

**후속 조치**: spec 문언을 "client는 `dispatch-broker.py status`를 실행해 live instance를
확보한다(비-워커에서도 broker를 새로 세우지 않는다)"로 정정하는 것을 v14 이전 spec 정정
사이클 후보로 제안한다.

## 2. SD-56 쓰기 의무의 부분 배선 — quick/inline capability owner 경로 미배선

`spec/stage-dispatch/prd.md §13.5.3`은 쓰기 의무자를 "conductor(**또는 quick/inline의
capability owner**)"라고 쓴다. 이번 구현은 `adapters/claude/skills/autopilot-code/references/dev-pipeline.md`
(standard+ 파이프라인 문서, 3부 동기화 완료)만 배선했다. quick/inline capability owner 경로의
marker 쓰기 의무는 **이번 사이클에서 무주장으로 남는다** — 의도된 축소다.

**후속 조치**: v14에서 quick/inline 문서 표면(관련 skill의 quick 경로 안내)에 동일한
`capability-route.py complete` 호출 의무를 확장하는 것을 후보로 제안한다.

## 3. 테스트 하니스의 워커 env 의존성

`dispatch_broker.test.py`·`stage_dispatch_fallback.test.py`·`capability_route.test.py`·
`dispatch_completion_marker.test.py`는 워커 세션 env(`AGENT_SESSION_ROLE=worker`,
`AGENT_DISPATCH_CHILD=1` 등)가 살아 있으면 `setUp`의 fixture broker `ensure`가
`broker-ensure-worker-forbidden`(exit 76)으로 전부 실패한다. 이는 v13 이전부터 존재하던
테스트 하니스의 환경 의존성이며 이번 사이클의 회귀가 아니다(§0.1에서 실측 확인).

`hooks/portable-guards.test.sh:38-40`은 이미 "D-42 hermeticity"로 이 env를 걷어내는데,
python `unittest` 기반 테스트 파일들엔 같은 방어가 없다.

**후속 조치**: v14 후보로, 각 테스트 파일의 진입점(또는 공용 conftest 격 헬퍼)에서
`AGENT_SESSION_ROLE`/`AGENT_DISPATCH_CHILD`/`AGENT_DISPATCH_BROKER_INSTANCE`/
`AGENT_DISPATCH_BROKER_ROOT`/`AGENT_DISPATCH_JOBS`를 자체적으로 unset하도록 하드닝해,
`TESTENV` prefix 없이도 워커 세션에서 안전하게 실행되도록 하는 것을 제안한다.

## 4. v12 잔여 — O2/O3/O4 (v14 유지)

- **O2** worker no-commit — v14 후보로 유지.
- **O3** digest pin — v14 후보로 유지.
- **O4** resource-runner canonical registry — v14 후보로 유지.

이 사이클(v13)은 `spec/stage-dispatch/prd.md §13.5`(SD-54·55·56)만 스코프이며 이 3건은
계획 §0에서부터 스코프 밖으로 명시됐다.

## 5. (execute 스테이지 발견) 인접 회귀 스위트의 사전 존재 실패 4건 — 비회귀 확인

`git stash -u`로 원 커밋(98308ec4) 상태와 diff 없이 동일하게 재현되는, 이번 사이클과 무관한
사전 존재 실패:

- `utilities/dispatch-artifact-root.test.py` — 3건(`artifact_root=`가 워커 세션의 실제
  `AGENT_ARTIFACT_ROOT`를 흡수).
- `bash utilities/dispatch-concurrency.test.sh` — "(2) expected 3 ALIVE, got 1"(실제 fleet
  동시 프로세스 상태에 좌우).
- `bash utilities/artifact-root.test.sh` — "linked worktree resolves primary artifact root".
- `bash tools/generated-projections.test.sh` — "legacy artifact root was not selected for
  orientation".

test 스테이지가 독립 재검증 시 이 4건이 v13 변경과 무관함을 다시 확인할 수 있도록,
`dev_logs/03-sd55-record-identity-decoupling.md`에 실측 커맨드를 남겼다.

---

## 6. (test 스테이지 산출) 독립 검증에서 발견한 이월 후보

test 스테이지가 execute 주장을 전부 재실행·재검증한 결과(상세: `test_logs/01-independent-verification.md`,
`_internal/test_reviews/01-fixture-review.md`). **최종 verdict는 PASS**이며 아래는 acceptance
불충족이 아니라 회귀 보호·운영·하드닝 항목이다.

### 6.1 ★ B3 회귀 가드 부재 — merge 전 처리 권고 (conductor 판단 필요)

plan-check가 "★가장 중대"로 지목한 B3(실행 중 request의 조기 종결) 수정 —
`process_request`에서 inflight 검사를 registry reconcile 앞으로 옮긴 것 — 이 **어떤 fixture로도
고정돼 있지 않다**. 순서를 v12(결함) 순서로 되돌려도 `dispatch_broker.test.py`가 **14/14 통과**한다
(mutation test 실측).

원인: fixture ②가 결정론화를 위해 fake adapter로 전환되면서 **registry row를 쓰지 않게 되어**
B3 경합의 전제 조건(running + row 존재)이 도달 불가능해졌다. v12 원본은 실 adapter를 써서
`rows == 1`을 단언했으나 그 단언이 `assertFalse(self.jobs.exists())`로 대체됐다.

구현 자체는 **정확하다**(probe로 확증: 수정본은 `broker-request-inflight`로 차단, 되돌린 본은
target 실행 중에 `status=done`으로 조기 종결). 회귀 보호만 부재하다.

**후속 조치**: `_internal/test_reviews/01-fixture-review.md §3`에 작성·검증 완료된 fixture
(`test_resubmit_while_running_with_registry_row_is_inflight`)를 그대로 추가하면 닫힌다.
merge 전 execute 재분사로 반영할지, v14 이월할지는 conductor 판단.

### 6.2 fixture 하드닝 후보 (v14) — acceptance 영향 없음

- `test_fenced_recovery_holds_under_parallel_inflight`의 `assertLessEqual(parallel_rows, 1)`이
  0건도 허용 → 병렬 request가 착지 못해도 통과. `reply`의 `check=ok` 동반 단언 권고.
- fixture ②가 "attempt/target 정확히 1개"를 응답 개수 추론으로만 확인 → fake adapter의
  `started-<slug>.marker`를 append 모드로 바꿔 launch 횟수를 직접 세는 편이 낫다.
- fixture ⑧(c) 정적 스캔이 `rglob("*.py")`만 본다 → fleet 표시 배선(F-28 재개) 시 셸 소비자가
  스캔 밖이라 가드가 침묵할 수 있다.
- `BrokerServer.request_lock()`의 "GC 없음"이 **의도**임이 plan에만 있고 코드 주석에 없다 →
  미래의 "메모리 누수 수정" 오해 방지용 한 줄 주석 권고.

### 6.3 merge 후 운영 사실 — conductor 전달 필요 (결함 아님)

`compile_route`가 이제 **기본 v2**를 생성하므로, merge 후 신규 standard+ headless route는 전부
completion gate 활성이다. **reader(gate)는 코드 강제, writer(conductor의 `capability-route.py
complete`)는 문서 강제**(`dev-pipeline.md`)라는 비대칭이 남는다 — spec §13.5.3이 의도한 설계지만,
merge 후 첫 사이클의 conductor가 marker를 쓰지 않으면 다음 스테이지 `--start`가
`completion-marker-missing`으로 fail-closed되어 **파이프라인이 정지**한다.

파손 위험은 없음을 확인했다: 이 사이클 route는 `broker_contract_version=1`이라 gate 미적용이고,
live의 구 marker(`sequence`/`completed_at` 없이 구 코드로 작성됨)도 gate가 `route_id`/`route_hash`
만 읽으므로 통과한다. quick/inline(§2)은 `broker_contract_version=None`이라 gate 밖이므로 미배선의
실효 위험도 없다.

### 6.4 §1(spec 문언 `ensure`→`status`) 독립 확인 결과 — 이월 유지

test 스테이지가 근거를 독립 확인했고 **타당하다**(워커에서 `ensure` 항상 거부 `:604`, 비-워커에선
없어야 할 broker를 Popen `:665-673`, fixture ⑩의 `broker.json` 부재 단언이 수호자로 작동). 다만
spec 문언이 여전히 `ensure`이므로 **문자 그대로의 §13.5.2 acceptance와 구현은 형식적으로 어긋난다**.
승인된 이탈로 보아 PASS를 유지했으나, spec 정정 사이클로 반드시 해소해야 한다.
