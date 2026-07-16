---
slug: stage-dispatch-v13
capability: autopilot-code
mode: dev
intensity: standard
qa: standard
route_id: rt-5fd84b9bcf8a799c
route_hash: sha256:5fd84b9bcf8a799cdf306ef8e90eef6261b919925d03c8c5da4d2c1744779243
spec: .agent_reports/spec/stage-dispatch/prd.md §13.5 (SD-54·SD-55·SD-56)
source_commit: 98308ec4182d913238ca31733683ae9126df03c0
worktree: /home/Uihyeop/agent_setting-wt/stage-dispatch-v13
status: complete
stage: code-plan
---

# stage-dispatch v13 구현 계획

규범 스코프는 `spec/stage-dispatch/prd.md §13.5` 뿐이다 (SD-54·SD-55·SD-56). §13.4(v12 broker 계약)의 불변식은 전부 유지 대상이고, §14는 규칙/의미 경계의 판정 기준이다. 이 계획 밖의 항목(O2 worker no-commit, O3 digest pin, resource-runner canonical registry)은 v14 후보로 남긴다.

---

## 0. Execute가 첫 5분에 알아야 할 것 (읽지 않으면 반드시 막힌다)

### 0.1 ★ 테스트는 워커 세션 환경에서 전부 실패한다 — 코드 문제가 아니다

execute·test 스테이지는 **워커 세션**이다. 워커 env가 살아 있으면 broker/fallback 테스트가 **전부 setUp에서 exit 76**으로 죽는다. 이 사이클에서 실측했다:

```
# 워커 env 그대로 (= execute 스테이지의 기본 상태)
$ python3 utilities/dispatch_broker.test.py
Ran 10 tests ... FAILED (errors=10)
  subprocess.CalledProcessError: ... dispatch-broker.py ensure ... exit status 76

# 워커 env 제거
$ env -u AGENT_SESSION_ROLE -u AGENT_DISPATCH_CHILD \
      -u AGENT_DISPATCH_BROKER_INSTANCE -u AGENT_DISPATCH_BROKER_ROOT \
      -u AGENT_DISPATCH_JOBS python3 utilities/dispatch_broker.test.py
Ran 10 tests in 14.454s ... OK
```

원인은 `utilities/dispatch-broker.py:604`다:

```python
def ensure(root, jobs, stale_seconds, timeout):
    if os.environ.get("AGENT_SESSION_ROLE") == "worker" or os.environ.get("AGENT_DISPATCH_CHILD") == "1":
        raise BrokerError("broker-ensure-worker-forbidden", "only depth 0 may prepare the broker")
```

워커 세션은 `AGENT_SESSION_ROLE=worker`·`AGENT_DISPATCH_CHILD=1`을 갖고, 테스트의 `setUp`은 fixture broker를 `ensure`로 띄운다(`utilities/dispatch_broker.test.py:43`). 따라서 **모든 dispatch 테스트 실행에 아래 prefix를 반드시 붙인다**:

```bash
TESTENV='env -u AGENT_SESSION_ROLE -u AGENT_DISPATCH_CHILD -u AGENT_DISPATCH_BROKER_INSTANCE -u AGENT_DISPATCH_BROKER_ROOT -u AGENT_DISPATCH_JOBS'
```

이 사실은 §5의 모든 커맨드에 이미 반영돼 있다. **이 실패를 회귀로 오인해 코드를 고치지 말 것.** 이것은 v13 이전부터 존재하는 테스트 하니스의 환경 의존성이며, 본 사이클의 스코프가 아니다(§8에 이월 후보로 기록).

### 0.2 ★ live broker는 절대 건드리지 않는다

live broker = `/home/Uihyeop/agent_setting/.dispatch/broker` (instance `brk-d25176b21a134c10a6f6d1608ffc3af4`). **shutdown·restart·변조 금지.** 롤오버는 merge 후 depth-0 main이 수행한다(§13.5.4). 모든 fixture는 `--root <tempdir>/broker`로 **자기 전용 broker만** 띄운다 — 기존 `dispatch_broker.test.py:42-56` 패턴 그대로다. 실제 `claude`/`codex`/`opencode` 세션 스폰·signal도 금지다.

### 0.3 ★ `skills/`는 byte-equivalent 미러다 — 3부 동기화 필수

`dev-pipeline.md`는 저장소에 **3부** 존재하며 전부 동일해야 한다 (`diff -r` 실측으로 IDENTICAL 확인):

1. `adapters/claude/skills/autopilot-code/references/dev-pipeline.md` ← 원본(편집 대상)
2. `skills/autopilot-code/references/dev-pipeline.md` ← 호환 미러
3. `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-code/references/dev-pipeline.md`

`core/ADAPTATION.md:16`이 "`skills/` byte-equivalent to `adapters/claude/skills/` — guarded against drift"로 규정한다. 하나만 고치면 projection census/adaptation boundary가 깨진다.

### 0.4 산출물 경계

- 소스 수정: worktree `/home/Uihyeop/agent_setting-wt/stage-dispatch-v13` 만.
- 산출물 쓰기: `artifact_root` = `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_stage-dispatch-v13/` 만 (SD-25 — worktree에 산출물 금지).
- `spec/` 수정 금지. drift 발견 시 `_internal/carryover.md`에 이월만.
- `capabilities/topologies.json` 수정 금지 — 수정하면 `registry_digest`가 바뀌어 자기 route record가 stale-digest로 거부된다(= v12 O3 관찰의 재현). 이번 사이클은 registry를 건드리지 않는다.

---

## 1. SD-54 — broker 동시성 분리 (HOL blocking 해소)

### 1.1 현행 구조 실측

`utilities/dispatch-broker.py:444-523` — `process_request` **전체**가 단일 전역 락 `self.request_guard` 안에 있다:

```python
444  def process_request(self, request: dict) -> dict:
445      with self.request_guard:                       # ← 전역 뮤텍스 획득
446          request_id = str(request.get("request_id", ""))
...          # 접수 / dedup / claim / registry reconcile
456          normalized = validate_request(...)
463          digest = "sha256:" + hashlib.sha256(canonical(normalized)).hexdigest()
465          if path.is_file():                          # dedup 분기
469              if state.get("status") in TERMINAL: return {..., "duplicate": True}
471              row = registry_attempt(self.jobs, state["attempt_id"])
473              if row is not None: return self.recovered_response(state, row)
474              lease = float(state.get("lease_expires_epoch", 0.0) or 0.0)
475              if state.get("broker_instance") == self.instance_id and lease > time.time():
476                  raise BrokerError("broker-request-inflight", ...)   # ← 재사용할 로직
491          state = self.transition(state, "claimed", ..., lease_expires_epoch=time.time()+self.stale_seconds)
500          command = adapter_command(normalized, self.instance_id)
501          state = self.transition(state, "running", ...)
502          env = {...}
510          result = subprocess.run(command, cwd=ROOT, env=env, ...)   # ★ 락을 쥔 채 자식 전 생애 동기 대기
522          state = self.transition(state, terminal, response=response, ...)
523          return {"ok": True, "state": state}
```

`serve`는 이미 연결당 스레드를 띄운다(`:573` `threading.Thread(target=self.handle, ...)`). 즉 **병렬성을 막는 유일한 원인은 `request_guard` 하나**이며, 이를 제거하면 즉시 병렬화된다. 실측 피해: 워커 1개가 12분 실행 → 전 fabric 12분 차단, 대기 스레드 6개(`fleet-v10-process-view/final_report.md §5.1`).

### 1.2 목표 구조

전역 락 → **per-request 락**. 접수·검증·dedup·claim·transition = short critical section, `subprocess.run` = **무락(no lock held)**.

```
process_request(request):
  # (A) 락 없음 — 순수 CPU + 읽기전용 파일 I/O
  request_id  = extract & REQUEST_ID_RE 검증
  prior_recovery / allowed_instances 계산          (현행 447-455 그대로)
  normalized  = validate_request(...)              (현행 456-462 그대로)
  digest      = sha256(canonical(normalized))

  # (B) per-request 락 — short critical section
  with self.request_lock(request_id):
      ... 현행 465-490 dedup/재개 분기 그대로 ...
      state   = transition(state, "claimed", ..., lease_expires_epoch=now+lease_ttl)
      command = adapter_command(normalized, self.instance_id)
      state   = transition(state, "running", ...)
      env     = {...}

  # (C) 락 없음 — target 실행 생애
  renewer = start_lease_renewer(request_id)        # 신규
  try:
      result = subprocess.run(command, cwd=ROOT, env=env, ...)
  finally:
      renewer.stop()

  # (D) per-request 락 — terminal 전이
  with self.request_lock(request_id):
      state = transition(state, terminal, response=response, terminal_at=utcnow())
  return {"ok": True, "state": state}
```

서로 다른 `request_id`는 **어떤 락도 공유하지 않는다** → 완전 병렬. 동일 `request_id`는 per-request 락에서 잠깐 직렬화된 뒤 status/lease로 판정된다.

### 1.3 착수점 — 함수 단위

**(a) `BrokerServer.__init__` (`:367-387`)**
- `self.request_guard = threading.Lock()` (`:385`) → **제거**하고 아래로 교체:
  ```python
  self.locks_guard = threading.Lock()          # request_locks dict 만 보호 (마이크로초)
  self.request_locks: dict[str, threading.Lock] = {}
  ```
- `self.meta_guard`(`:386`)는 그대로 둔다 (heartbeat meta 쓰기 보호, 별개 범위).

**(b) 신규 `BrokerServer.request_lock(self, request_id) -> threading.Lock`**
```python
def request_lock(self, request_id: str) -> threading.Lock:
    with self.locks_guard:
        lock = self.request_locks.get(request_id)
        if lock is None:
            lock = self.request_locks[request_id] = threading.Lock()
        return lock
```
- dict은 terminal 후에도 남는다. request_id는 route/node/slug 파생 해시(`stage-dispatch-fallback.py:78-81`)라 카디널리티가 낮고, broker는 재시작으로 리셋된다 → 무한 증가 아님. **명시적 GC를 넣지 말 것** (terminal 직후 삭제하면 동시 재제출이 새 락을 얻어 직렬화가 깨진다).

**(c) 신규 `lease_ttl`**
- 현행 claim lease는 `time.time() + self.stale_seconds`(`:498`), `stale_seconds` 기본 15.0(`:39`).
- ★ **병렬화하면 여기서 중복 launch 버그가 생긴다**: 12분짜리 target이 도는 동안 lease는 15초에 만료된다. 현행에서는 두 번째 제출이 전역 락에 12분 갇혀 있다가 registry row를 보고 recover하므로 드러나지 않지만, 병렬에서는 t=20s의 재제출이 "lease 만료"로 읽고 **재-claim → 재-launch**한다. registry row가 이미 있으면 `:471` reconcile이 잡지만, spawn 직후~row 기록 사이 창에서는 못 잡는다.
- 해법 = **lease 갱신**. `running` 동안 백그라운드로 lease를 계속 연장한다.

**(d) 신규 `BrokerServer.renew_lease(self, request_id, stop_event)`**
```python
def renew_lease(self, request_id: str, stop_event: threading.Event) -> None:
    interval = max(0.5, self.stale_seconds / 3.0)
    while not stop_event.wait(interval):
        with self.request_lock(request_id):
            path = self.request_path(request_id)
            if not path.is_file():
                return
            state = read_json(path)
            if state.get("status") in TERMINAL or state.get("broker_instance") != self.instance_id:
                return                                   # terminal immutability 존중
            state["lease_expires_epoch"] = time.time() + self.stale_seconds
            state["updated_at"] = utcnow()
            atomic_json(path, state)
```
- `transition()`을 쓰지 않는다 — `transition`은 status를 인자로 강제하고 terminal에서 예외를 던진다. 갱신은 status 불변 + lease만 미는 것이므로 직접 `atomic_json`이 맞다. **atomic write는 유지**(`atomic_json`은 `:70-79`에서 tmp+fsync+`os.replace`).
- terminal 체크를 락 안에서 하므로 (D)의 terminal 전이와 경합하지 않는다.

**(e) `process_request` (`:444-523`) 재작성** — §1.2 구조대로. 유의점:

★★ **`:471-476`의 순서를 반드시 뒤집어라 — dedup 분기를 "로직 변경 없이" 옮기면 조기-terminal 버그가 생긴다.** (plan-check B3에서 발견·실측 확인)

현행 순서는 **registry reconcile(`:471-473`) → lease/inflight(`:474-476`)**다. 전역 락 하에서는 "이 instance에서 running 중"인 상태를 두 번째 제출이 관찰할 수 없었기에 안전했지만, 병렬화하면 다음이 실제로 일어난다:

1. Thread 1: (B)에서 claimed→running, 락 해제, (C)에서 12분 target 실행 중.
2. Thread 2: 동일 `request_id` 재제출 → (B) 진입 → `:471` `registry_attempt`가 **row를 찾는다**. SD-52가 요구하는 "spawn 전 canonical registry row" 때문에 반드시 찾는다 — 실측: `adapters/claude/bin/dispatch-headless.py:728` `append_job(jobs, args)`가 `:768` `subprocess.Popen`보다 **앞**이다.
3. `:472-473` → `recovered_response` → `transition(state, "done", ...)` → **target이 아직 도는데 request가 `done`으로 종결**된다.
4. Thread 1이 (D)에서 자기 stale in-memory `state`(status=`running`)로 terminal 전이 → `transition:417`은 **인자로 받은 in-memory state**를 검사하므로 통과 → **on-disk terminal을 덮어쓴다** = §13.4.2 terminal immutability 위반.

게다가 `:471` reconcile이 `:475` inflight보다 먼저라 SD-54가 §13.5.1에서 **명시적으로 요구한** "claimed/running 재제출 = `broker-request-inflight` 거부"에 **도달할 수 없다**.

따라서 (B) 안의 순서는:
```python
state = read_json(path)
if state.get("request_hash") != digest:
    raise BrokerError("broker-request-id-conflict", normalized["request_id"])
if state.get("status") in TERMINAL:
    return {"ok": True, "state": state, "duplicate": True}

# ★ inflight 먼저 — 이 instance가 살아서 lease를 갱신 중이면 재제출을 거부한다.
lease = float(state.get("lease_expires_epoch", 0.0) or 0.0)
if state.get("broker_instance") == self.instance_id and lease > time.time():
    raise BrokerError("broker-request-inflight", normalized["request_id"])

# ★ reconcile은 fenced recovery 경로에만 — predecessor instance이거나 lease가 만료된 경우.
row = registry_attempt(self.jobs, state["attempt_id"])
if row is not None:
    return self.recovered_response(state, row)
state["recovered_after_fence"] = True
state["prior_lease_expires_epoch"] = lease
```
- 이 순서에서 `recovered_response`는 원래 의도된 대상(= 죽은 broker가 남긴 launch된 attempt)에만 적용된다. AC5 fenced recovery 의미는 보존된다 — crash한 broker는 lease를 갱신하지 않으므로 lease가 만료돼 있고, inflight 조건의 `broker_instance == self.instance_id`도 거짓이다.
- `:475`의 조건 자체는 그대로. lease 갱신(§1.3d) 덕에 running 내내 참이 되어 SD-54의 inflight 의미론이 성립한다.

★ **(D) terminal 전이는 on-disk state를 재독한 뒤 수행하라**:
```python
with self.request_lock(request_id):
    current = read_json(self.request_path(request_id))
    if current.get("status") in TERMINAL:
        return {"ok": True, "state": current}       # 남이 이미 닫았다 — 덮어쓰지 않는다
    state = self.transition(current, terminal, response=response, terminal_at=utcnow())
```
in-memory `state`를 그대로 쓰면 §1.5의 terminal immutability 보존이 **거짓**이 된다. `transition`의 `:417` 검사는 인자 state만 보므로 stale 판단을 막지 못한다.

- (C)에서 예외가 나면 `finally`로 renewer를 반드시 멈춘다(daemon 스레드 + `stop_event.set()` 후 `join(timeout)`). `subprocess.run` 자체가 던지는 경우(OSError 등) `handle()`의 `except Exception`(`:543`)이 `broker-internal-error`로 닫는다 — 이때 state는 `running`으로 남고 lease 갱신이 멈춰 만료되면 다음 제출이 fenced recovery 경로로 들어간다. 기존 crash 의미론과 동일하므로 추가 처리 불필요.

**(f) `recovered_response` (`:426-442`)**: 변경 없음. 단 호출부가 per-request 락 안이 되도록 (B) 안에 유지한다.

### 1.4 넣지 말아야 할 것

- **broker 동시성 cap 금지** (§13.5.1). `self.sock.listen(16)`(`:563`)은 accept 백로그이지 cap이 아니다 — **건드리지 말 것**. 모델 워커 동시성·budget은 SD-40 governor(`utilities/model-worker-governor.py`)가 소유한다. broker에 세마포어를 넣으면 이중 상한이 된다.
- `ensure`의 `broker-replacement-active` 검사(`:633-638`)는 그대로. 병렬 running request가 있으면 교체를 거부하는 것이 맞다.

### 1.5 v12 불변식 보존 논거

| 불변식 (§13.4.2) | 병렬화 후에도 성립하는 이유 |
|---|---|
| atomic transition | `transition`→`atomic_json`(tmp+fsync+`os.replace`)은 파일 단위 원자성이며 락과 무관. request별 파일이 분리돼 있어 교차 오염 없음 |
| terminal immutability | ★ `transition:417-418`의 검사는 **인자로 받은 in-memory state**만 본다 — 병렬에서는 이것만으로 **불충분**하다(§1.3e). 보존 근거는 세 가지의 결합이다: (1) per-request 락, (2) (D)에서 on-disk state **재독** 후 전이, (3) 갱신 스레드도 락 안에서 terminal 확인 후 return |
| PID/start-ticks + heartbeat/lease + fencing | meta는 `meta_guard`로 별도 보호(`:405-407`), heartbeat 스레드 무관. lease는 per-request로 승격되고 **갱신**으로 running 생애를 덮음 |
| spawn 전 canonical registry row | registry row는 target wrapper가 기록. `adapter_command`/env 구성 순서 불변 |
| idempotency (AC4) | per-request 락 + status/lease 판정으로 보존. 동시 제출 = 락 직렬화 → `broker-request-inflight`; 순차 terminal 재제출 = `duplicate: True` 기존 상태 반환 |
| fenced recovery (AC5) | registry reconcile(`:471-473`)이 락 안에서 먼저 실행. lease 만료 + row 부재일 때만 재개 |

### 1.6 ★ 기존 테스트 기대값 변경 (반드시 확인)

**(a) `test_concurrent_duplicate_request_creates_one_attempt` (`dispatch_broker.test.py:278`)**

현행 전역 락 하에서 두 번째 제출은 직렬화된 뒤 **registry row를 보고 `recovered_response`(ok=True)**를 받는 경로를 탄다. §1.3(e)의 B3 수정(inflight를 reconcile 앞으로) + lease 갱신 후에는 두 번째 제출이 **`broker-request-inflight`(ok=False)**를 받는다 — SD-54가 §13.5.1에서 명시적으로 요구한 의미론이다.

단언은 **`broker-request-inflight`를 정확히** 요구하라. (초안은 "recovered done 또는 inflight 중 하나"라는 관대한 단언을 권했으나, 그것은 B3의 조기-terminal defect를 그대로 통과시키므로 **철회한다**.) B3 수정 후 이 경로는 결정론적이다: reconcile이 inflight 뒤에 있고 lease가 갱신되므로 running 중 재제출이 recovered-done으로 샐 수 없다.

AC4의 본질(**`attempt`/`target process` 정확히 1개**)은 별도로 단언하라 — `registry_attempt` row 1개 + `attempt_id` 1종.

**(b) ★ `test_tampered_inherited_instance_fails_closed` (`dispatch_broker.test.py:404`)** (plan-check M1)

이 테스트는 `chain(..., instance="brk-tampered")`로 `reason=broker-instance-mismatch`를 단언한다. 그런데 §2.4(e) 이후 `chain`이 쓰는 record가 **v2**가 되면 §2.3이 **의도적으로 env를 무시**하므로 이 방어가 v2 경로에서 무효화된다. 위험한 것은 타이밍이다: **B1을 고치기 전에는 우연히 통과하고, B1(`submit_broker` env 정제)을 고치는 순간 실패로 전환**된다 — 최악의 진단 순서다.

정정: 이 테스트를 **v1 record로 고정**하라(§4.2⑤의 손수 구성 방식 재사용). v1에서 env 신뢰는 유지되는 계약이므로 단언이 그대로 성립한다. 그리고 v2의 env-tamper 의미론("live 해석이 출처이므로 env 변조는 무주장")은 fixture ④가 이미 커버한다(낡은 instance를 env에 넣고도 성공).

---

## 2. SD-55 — record ↔ broker-identity 결합 해제

### 2.1 현행 결합 지점 실측

**`utilities/capability-route.py`**
```python
18   BROKER_FIELDS = {"broker_root", "broker_instance"}
65       normalized_row={key:row[key] for key in sorted(NESTED_FIELDS)}
66-68    for key in BROKER_FIELDS:
             if key in row: normalized_row[key]=row[key]      # instance를 record에 박는다

84-89  # _fallback_chain — 컴파일 시 instance 필수
       if not any(row["status"]=="supported" and row["launch_authority"]=="ancestor-broker"
                  and row.get("broker_root") and row.get("broker_instance")
                  for row in same+cross):
           raise ValueError("no supported depth-0 launch broker tuple")

97-107 # _verify_fallback_chain(node, require_broker_binding=False)
103        and (not require_broker_binding or (candidate.get("broker_root") and candidate.get("broker_instance")))

171    "broker_contract_version":1 if checked_dispatch is not None else None
191        if node.get("depth")==2: _verify_fallback_chain(node, route.get("broker_contract_version")==1)
```

**`utilities/stage-dispatch-fallback.py`**
```python
190  if not os.environ.get("AGENT_DISPATCH_BROKER_INSTANCE"):
191      return fail("broker-binding-unset", 76, broker_root=str(args.broker_root), child_spawned="0")
118      "broker_root": row["broker_root"],
119      "broker_instance": row["broker_instance"],      # record에서 읽는다 = rollover 후 영구 실패
```

**`utilities/dispatch-broker.py:243`** — `validate_route`가 candidate 매칭에 instance를 포함:
```python
242      and row.get("broker_root") == request["broker_root"]
243      and row.get("broker_instance") == request["broker_instance"]
```

### 2.2 ★ 설계 결정: hop 시점 해석은 `ensure`가 아니라 **`status`-only**다

§13.5.2는 "client가 `dispatch-broker.py ensure`를 idempotent 실행해 live instance를 확보"라고 쓴다. 그런데 **`ensure`는 워커에서 항상 거부된다** (`dispatch-broker.py:604`, §0.1에서 exit 76으로 실측). `stage-dispatch-fallback.py`를 호출하는 주체는 depth-1 conductor이고 **conductor는 워커 세션**이다. 문자 그대로 구현하면 v2 hop이 100% 실패한다.

해법 — client는 **`status`만** 부른다 (`ensure`는 부르지 않는다):

- broker가 살아 있으면(롤오버 후 새 instance 포함) `status`가 live instance를 즉시 반환 → **acceptance ① 충족**, depth-0 권한 불필요.
- broker가 죽어 있으면 `status` 실패 → structured **`broker-unavailable`** fail-closed → **acceptance ③ 충족**.

★ **`ensure`-fallback을 넣지 말 것** (plan-check B2에서 발견). 이유 두 가지:
1. **실제 호출자에게 아무 능력도 추가하지 않는다** — 계약상 호출자는 워커이고 거기서 `ensure`는 **항상** `broker-ensure-worker-forbidden`이다.
2. **금지된 컨텍스트에서만 부작용을 만든다** — 비-워커(예: 테스트 하니스)에서 `ensure`는 `:665-673`으로 **실제 broker를 Popen한다**. 구체적 파괴: `dispatch_broker.test.py:396` `test_missing_broker_fails_closed`는 존재하지 않는 broker root로 `chain()`을 호출해 fail-closed를 단언하는데, §2.4(e) 이후 그 record는 v2가 되고 `TESTENV`가 워커 env를 걷어낸 상태이므로 **ensure가 성공해 없어야 할 broker를 새로 띄운다** → v12 AC3(§13.4.4-3)과 SD-55 acceptance ③이 동시에 회귀한다.

계약 이탈이 **아니다**: `ensure()`의 healthy 경로는 `broker_status(root, jobs, stale_seconds)`를 그대로 반환한다(`:607-608`). 즉 broker가 살아 있는 한 `status`와 `ensure`의 관측 결과는 같고, `status`는 여기에 ping(`:731-737`)까지 더해 **더 보수적**이다(= fail-closed 방향이라 안전). SD-51의 "broker만 target을 시작한다"는 권한 경계도 그대로 지켜진다 — client는 broker를 **기동하지 않고 조회만 한다**. §14 규칙 구간의 "hop 시점 ensure 해석"이 요구하는 결정론도 유지된다.

→ spec 문언(`ensure`)과 구현(`status`-only)의 간극은 **`_internal/carryover.md`에 spec 문언 정정 후보로 이월**하라. spec 파일은 수정 금지다.

### 2.3 ★ 설계 결정: `AGENT_DISPATCH_BROKER_INSTANCE` env를 v2의 **두 지점 모두에서** 제거해야 한다

`broker_status`(`:160-162`)는 env를 신뢰한다:
```python
160  expected = os.environ.get("AGENT_DISPATCH_BROKER_INSTANCE")
161  if expected and expected != meta.get("instance_id"):
162      raise BrokerError("broker-instance-mismatch", ...)
```
conductor env에는 **낡은 instance**가 박혀 있다(이 워커 세션이 그 증거다 — `AGENT_DISPATCH_BROKER_INSTANCE=brk-d25176b21a134c10a6f6d1608ffc3af4`). 롤오버 후 이 env를 그대로 두고 status를 부르면 `broker-instance-mismatch`가 나서 **v10 열화가 그대로 재현된다.**

★ **제거 지점은 하나가 아니라 둘이다** (plan-check B1에서 발견·실측 확인). live 해석에서만 env를 걷어내면 **제출 단계에서 그대로 죽는다**:

- `stage-dispatch-fallback.py:142-149` `submit_broker`의 `subprocess.run(command, cwd=ROOT, ...)`에는 **`env=` 인자가 없다** → 낡은 env를 그대로 상속한다.
- `dispatch-broker.py:749` `meta = broker_status(root, jobs, args.stale_seconds)`는 `serve` 분기(`:738-748`) 뒤의 **fall-through라서 `request` 서브커맨드에서도 실행된다**(실측 확인).
- → `broker_status:160-162`가 낡은 env를 보고 `broker-instance-mismatch` → exit 76.

따라서 env 정제를 **헬퍼 하나로 뽑아** live 해석과 제출이 **공유**하게 하라:
```python
def broker_env(contract: int | None) -> dict:
    """v2 hop resolves the live instance at submit time, so an inherited
    AGENT_DISPATCH_BROKER_INSTANCE from a pre-rollover conductor is stale
    evidence, not authority.  v1 keeps trusting it (SD-55 backward compat)."""
    if contract != 2:
        return dict(os.environ)
    return {k: v for k, v in os.environ.items() if k != "AGENT_DISPATCH_BROKER_INSTANCE"}
```
`resolve_live_instance`(§2.5a)와 `submit_broker`(§2.5e) **양쪽**이 이 헬퍼를 쓴다. v1은 `dict(os.environ)` 그대로 → 회귀 0. (fixture ④가 이 경로를 정확히 겨냥한다.)

### 2.4 착수점 — `utilities/capability-route.py`

**(a) 상수 (`:18`)**
```python
BROKER_FIELDS = {"broker_root", "broker_instance"}      # v1 전용
BROKER_FIELDS_V2 = {"broker_root"}                      # 신규
BROKER_CONTRACT_VERSION = 2                             # 신규 컴파일 기본
```

**(b) `_validate_dispatch_evidence(evidence, contract_version=BROKER_CONTRACT_VERSION)` (`:52-75`)**
- v2: `normalized_row`에 `broker_root`만 복사하고 **`broker_instance`는 넣지 않는다**. 입력에 instance가 있어도 **strip**한다 — depth-0 호출자의 probe 출력(`dispatch-broker.py ensure` → `broker_instance=`)이 그대로 들어와도 v2 record가 나와야 하기 때문. strip은 조용한 손실이 아니라 계약이다("stable identity만 고정").
- v2: `broker_root` 부재 시 `ValueError("v2 dispatch evidence requires broker_root")`.
- v1: 현행 `:66-68` 그대로 (소급 변환 금지).

**(c) `_fallback_chain(evidence, contract_version)` (`:77-95`)**
- `:84-89`의 존재 검사를 버전 분기: v2는 `row.get("broker_root")`만, v1은 `broker_root and broker_instance`.

**(d) `_verify_fallback_chain(node, contract_version)` (`:97-107`)**
- 현행 시그니처는 `require_broker_binding: bool`이고 호출부(`:191`)가 `route.get("broker_contract_version")==1`을 넘긴다 → **v2에서 `False`가 되어 broker_root 검사까지 통째로 사라진다.** 이는 v2 record를 무검증으로 만든다. bool → **version 정수**로 바꿔 3상태로:
  - v1 → `broker_root` **and** `broker_instance` 필수 (기존 거동 그대로)
  - v2 → `broker_root` 필수, `broker_instance` **부재**여야 함 (있으면 `ValueError`)
  - `None`(headless 아님) → 현행대로 미검사
- 호출부 `:191`을 `_verify_fallback_chain(node, route.get("broker_contract_version"))`로 수정.

**(e) `compile_route` (`:148-154`, `:171`)**
- `:150-151` → `_validate_dispatch_evidence(dispatch_evidence, BROKER_CONTRACT_VERSION)` / `_fallback_chain(checked_dispatch, BROKER_CONTRACT_VERSION)`
- `:171` → `"broker_contract_version": BROKER_CONTRACT_VERSION if checked_dispatch is not None else None`

**(f) `verify_route` (`:188-191`)**
- `_validate_dispatch_evidence(route.get("dispatch_evidence"), route.get("broker_contract_version"))`로 버전 전달.
- ★ `route_hash`는 payload 전체 해시(`:24-26`)이므로 `broker_contract_version` 값이 해시에 포함된다. v1 record는 파일에 v1이 박혀 있어 재해시해도 그대로 통과한다 — **소급 변환 0, 회귀 0**. v2로 새로 컴파일한 record는 새 hash를 갖는다(정상).

### 2.5 착수점 — `utilities/stage-dispatch-fallback.py`

**(a) 신규 `resolve_live_instance(broker_root: Path, jobs: Path) -> str`** — **status-only**(§2.2)
```python
def resolve_live_instance(broker_root, jobs):
    """v2 hop: resolve the live broker instance at submit time.

    status-only: a healthy broker (including a post-rollover instance) answers
    without depth-0 authority.  We never run `ensure` here — the contractual
    caller is a depth-1 worker, where ensure is always refused
    (dispatch-broker.py:604), so ensure would add no capability to the real
    caller while creating a broker as a side effect in the very contexts that
    must fail closed (SD-52 / v12 AC3).
    """
    result = subprocess.run(
        [sys.executable, str(ROOT / "utilities/dispatch-broker.py"), "status",
         "--root", str(broker_root), "--jobs", str(jobs)],
        cwd=ROOT, text=True, capture_output=True, check=False, env=broker_env(2),
    )
    if result.returncode:
        return ""
    fields = dict(l.split("=", 1) for l in result.stdout.splitlines() if "=" in l)
    return fields.get("broker_instance", "")
```
- `status`가 `broker_status` + ping을 모두 수행하므로(`:731-737`) live 판정으로 충분하다.
- 반환 `""` → 호출부에서 `fail("broker-unavailable", 76, broker_root=..., child_spawned="0")`.

**(b) `--broker-root` 명시 여부를 먼저 포착하라** — `p.parse_args()`(`:175`) **직후**:
```python
explicit_broker_root = args.broker_root is not None
```
`:186-189`가 `args.broker_root`에 **기본값을 대입한 뒤**에는 명시 여부를 알 수 없다.

**(c) `main` (`:186-191`) 버전 분기**
```python
contract = route.get("broker_contract_version")
...
if contract == 2:
    pass                                                   # live 해석은 후보 루프 안에서 (d)
else:
    if not os.environ.get("AGENT_DISPATCH_BROKER_INSTANCE"):      # 현행 :190 — v1 전용으로 축소
        return fail("broker-binding-unset", 76, broker_root=str(args.broker_root), child_spawned="0")
```
- v1 경로는 **한 줄도 바뀌지 않는다** (회귀 0).

**(d) 후보 루프 (`:198` `for row in hop.get("candidates", [])`) 안에서 v2 해석**

`broker_root`는 **hop candidate별 필드**이므로 root 확정과 live 해석은 **루프 안**이어야 한다(루프 밖에서 `args.broker_root`로 해석하면 candidate의 root와 어긋난다):
```python
if contract == 2:
    row_root = Path(row["broker_root"]).resolve()
    if explicit_broker_root and args.broker_root != row_root:
        return fail("broker-root-mismatch", 76, expected=str(row_root),
                    observed=str(args.broker_root), child_spawned="0")
    submit_root = row_root
    live_instance = resolve_live_instance(submit_root, args.jobs)
    if not live_instance:
        return fail("broker-unavailable", 76, broker_root=str(submit_root), child_spawned="0")
else:
    submit_root = args.broker_root
    live_instance = None
```
- broker는 envelope의 `broker_root`와 자기 root를 대조한다(`:283-284`) → 둘을 일치시켜야 한다.
- `submit_broker`에 `submit_root`를 넘기도록 시그니처를 조정하라(현행은 `args.broker_root`를 직접 읽는다, `:135-137`).

**(e) `submit_broker`도 정제된 env를 써야 한다** (§2.3 / plan-check B1)
```python
142  result = subprocess.run(
143      command, cwd=ROOT, text=True,
         env=broker_env(contract),          # ★ 신규 — 현행엔 env= 자체가 없다
144      input=json.dumps(envelope, ensure_ascii=False), capture_output=True, check=False,
145  )
```
`contract`를 `submit_broker`의 인자로 넘긴다. 이것이 없으면 `dispatch-broker.py:749`의 `broker_status`가 낡은 env를 보고 `broker-instance-mismatch`로 죽는다.

**(f) `broker_envelope(args, route, node, row, ordinal, live_instance=None)` (`:84-127`)**
```python
118  "broker_root": row["broker_root"],
119  "broker_instance": live_instance or row["broker_instance"],
```
- v2 record의 row에는 `broker_instance`가 없으므로 `live_instance`가 유일한 출처다. v1은 `live_instance=None` → 현행 그대로 `row["broker_instance"]`.
- 호출부 `:211`에 `live_instance` 인자를 넘긴다.
- envelope 스키마(`schema_version: 1`)는 **바뀌지 않는다** — `broker_instance`는 여전히 필수 필드다. 바뀐 것은 그 값의 **출처**뿐(record → live 해석). broker의 `validate_request`(`:285-290`) instance 대조는 그대로 성립한다.

**(g) 성공 출력 (`:231`)**: `broker_instance={response.get('broker_instance','-')}`는 broker 응답에서 오므로 변경 불필요. 관측성을 위해 v2일 때 `broker_instance_source=live-status` 한 줄 추가를 권장(선택).

### 2.6 착수점 — `utilities/dispatch-broker.py`

**`validate_route` (`:235-248`)** — candidate 매칭의 `:243` `row.get("broker_instance") == request["broker_instance"]`:
- v2 record의 candidate에는 instance가 없다 → 이 조건이 항상 거짓 → **모든 v2 hop이 `broker-route-mismatch`로 거부된다.** 반드시 버전 분기하라:
```python
contract = route.get("broker_contract_version")
...
and row.get("broker_root") == request["broker_root"]
and (contract == 2 or row.get("broker_instance") == request["broker_instance"])
```
- `validate_route`는 이미 `route`를 파싱해 갖고 있다(`:212`) → 추가 I/O 없음.
- **envelope↔현재 instance 대조는 건드리지 않는다** — `validate_request:285-290`의 `allowed_instances` 검사가 SD-55가 "사라지지 않는다"고 못박은 그 검증이다. 그대로 둔다.

### 2.7 acceptance 대응

| SD-55 acceptance | 충족 경로 |
|---|---|
| ① rollover 후 v2 ordinal-1 성공, 하강 0, hash 불변 | §2.5(a) status-first + §2.3 env 무시 + §2.6 v2 분기. hash는 record 파일이 안 바뀌므로 자명 |
| ② v1 record 회귀 0 | §2.4(b)(c)(d) 전부 v1 분기 유지, §2.5(b) v1 경로 무변경 |
| ③ ensure 실패 시 `broker-unavailable` fail-closed | §2.5(a) 반환 `""` → `fail("broker-unavailable", 76, child_spawned="0")` |

---

## 3. SD-56 — completion 통과 marker 배선

### 3.1 현행 실측

`utilities/capability-route.py:233-240` — `complete` 서브커맨드는 존재하나 **아무도 호출하지 않는다** (repo 전역 marker 0건, `carryover.md §1` 실측):
```python
233  else:
234      evidence=Path(a.evidence).resolve()
235      if not evidence.is_file(): raise SystemExit("completion evidence missing")
236      marker={"route_id":route["route_id"],"route_hash":route["route_hash"],"registry_digest":route["registry_digest"],
237              "node_id":a.node,"completion_gate":node["completion_gate"],
238              "evidence":{"path":str(evidence),"sha256":hashlib.sha256(evidence.read_bytes()).hexdigest()}}
239      write_once(a.output or evidence.with_suffix(evidence.suffix+".completion.json"),marker)
```
`write_once`(`:194-201`)는 `O_EXCL`로 열고, 이미 있으면 **내용이 다를 때 `ValueError`**를 던진다 → 재수확 시 충돌한다.

### 3.2 canonical 경로 + write_once 충돌 해법

```
<agent-home>/.dispatch/completion/<route_id>/<node_id>.json          ← 최신 authoritative (원자적 교체)
<agent-home>/.dispatch/completion/<route_id>/<node_id>.<seq>.json    ← 이력 (write-once, 불변)
```

설계 근거 — 두 요구가 충돌한다: "이력 보존"(불변 필요)과 "최신 authoritative"(교체 필요). **한 파일로 둘 다 할 수 없다** → 역할을 분리한다:
- 이력 파일: `O_EXCL` write-once 유지. 한 번 쓰인 판정은 절대 바뀌지 않는다.
- canonical 파일: `atomic_json` 스타일(tmp + fsync + `os.replace`)로 교체. 외부 관찰자는 `(route_id, node_id)`만으로 결정론적으로 도출 가능(§13.5.3).

`complete` 알고리즘:
```
1. marker = {route_id, route_hash, registry_digest, node_id, completion_gate,
             evidence:{path, sha256}, sequence, completed_at}
2. canonical = <agent-home>/.dispatch/completion/<route_id>/<node_id>.json
3. if canonical 존재 and 그 evidence.sha256 == 새 sha256:
       → no-op, 기존 marker 출력, exit 0            # 멱등 재실행은 이력을 더럽히지 않는다
4. seq = 기존 <node_id>.*.json 개수 + 1 ; marker["sequence"] = seq
5. write_once(<node_id>.<seq>.json, marker)         # 충돌 시 seq+1 재시도 (최대 몇 회)
6. atomic replace canonical ← marker
7. print(json)
```
- 3단계가 "동일 evidence 재호출 = no-op"을 보장해 §13.4.2 idempotency 정신과 정합한다. **evidence가 바뀐 재판정만** 새 이력을 만든다("노드 재실행 후 재판정", §13.5.3).
- `completed_at`(타임스탬프) 때문에 재실행마다 내용이 달라지는 문제는 3단계의 sha256 비교가 흡수한다(비교 대상이 타임스탬프가 아니라 evidence sha256).
- 필수 6필드 = `route_id`/`route_hash`/`registry_digest`/`node_id`/`completion_gate`/`evidence.sha256`. `sequence`·`completed_at`은 이력 순서를 결정론적으로 읽기 위한 **가산 필드**이며 소비 계약(§13.5.3 "marker 존재 + route_id/route_hash 일치만 통과로 읽는다")을 바꾸지 않는다.

### 3.2.1 ★ agent-home 해석은 반드시 **검증형 리졸버**를 공유하라

`Path(os.environ.get("AGENT_HOME", ROOT))`로 쓰지 **말 것** (plan-check B4). `capability-route.py:7`의 `ROOT = parents[1]`은 **worktree**이고, 이는 저장소가 **이미 겪고 고친 버그 패턴**이다. `adapters/claude/bin/dispatch-headless.py:546-553`의 주석이 그대로 경고한다 (실측 인용):

> When AGENT_HOME is unset, falling straight back to ROOT (=worktree) **split the registry**: the wrapper wrote jobs.log under the worktree while the readers looked under `$HOME/agent_setting/.dispatch` — so the liveness/Stop layer never saw the rows the wrapper appended (SD-14b② registry gap).

그래서 `resolve_agent_home()`(`:546-558`)은 `core/CORE.md` 존재를 검증하는 **선호 순서**를 쓰고, `dispatch-broker.py:29-31`도 동일하게 방어한다. marker에서 이 방어를 빠뜨리면 **writer(worktree의 conductor)와 reader(agent-home 기준 gate)가 다른 디렉터리를 보게 되어 모든 record-bound `--start`가 `completion-marker-missing`으로 fail-closed** → 전 fabric dispatch 중단. 덤으로 worktree 산출물 금지(§0.4/SD-25) 위반이다.

→ **`utilities/dispatch_contract.py`에 검증형 `resolve_agent_home()`을 공유 헬퍼로 두고, writer(`capability-route.py`)와 reader(gate) 양쪽이 같은 헬퍼를 쓴다.** `adapters/claude/bin/dispatch-headless.py:546-558`의 선호 순서(`AGENT_HOME` → `CLAUDE_HOME` → `~/agent_setting`, 각각 `core/CORE.md` 검증)를 그대로 옮기고, 어댑터는 기존 로컬 구현을 유지하거나 이 헬퍼로 위임하라(위임 시 3어댑터 동작 동일성을 회귀로 확인).

**착수점 — `utilities/capability-route.py`**
- 신규 `def completion_dir(route_id) -> Path`: `resolve_agent_home() / ".dispatch" / "completion" / route_id` — **위 공유 헬퍼 사용**.
- 신규 `def atomic_write(path, payload)`: `write_once`(`:194`) 옆에. tmp + `os.fsync` + `os.replace`, mode 0o600 — `dispatch-broker.py:70-79`의 `atomic_json` 패턴을 그대로 따른다.
- 신규 `def write_completion_marker(route, node, node_id, evidence) -> dict`: 위 알고리즘.
- `main`의 `complete` 분기(`:233-240`) → `write_completion_marker` 호출. **`--output`은 유지**(fixture/디버깅용 명시적 override); 미지정 시 canonical. 기존 `<evidence>.completion.json` 기본값은 **제거**한다 — carryover §1이 실측한 대로 그 경로엔 파일이 0건이므로 깨질 소비자가 없다.

### 3.3 gate — wrapper 3종 `--start`

**공통 구현 위치 = `utilities/dispatch_contract.py`.** 3어댑터가 이미 여기서 `ensure_launch_broker`를 import한다(`adapters/claude/bin/dispatch-headless.py:24`, `codex:24`, `opencode:25`) → **여기 한 곳에 넣으면 parity가 구조적으로 보장**된다. 어댑터별로 3번 구현하지 말 것.

신규 `dispatch_contract.completion_marker_gate(route_file, route_node, action, agent_home)`:
```
1. action != "start"        → return (미적용)
2. route_file 없음          → return (record 미결합 launch, 소급 강제 금지)
3. route = json.load(route_file)
4. route.get("broker_contract_version") != 2 → return   # v1 record 미적용 (§13.5.3)
5. node = nodes 중 id == route_node ; 없으면 return (기존 route 검증이 이미 처리)
6. for dep in node.get("depends_on", []):
       marker = agent_home / ".dispatch/completion" / route["route_id"] / f"{dep}.json"
       missing 이거나 marker["route_id"] != route["route_id"]
                   또는 marker["route_hash"] != route["route_hash"]  → missing 목록에 추가
7. missing 있으면 raise DispatchContractError("completion-marker-missing", detail=",".join(missing))
```
- ★ `agent_home`은 **명시 인자**다 (plan-check B4). 함수 안에서 env를 다시 읽지 말 것 — writer/reader가 같은 뿌리를 쓴다는 보장이 시그니처에 드러나야 한다.
- `depends_on`이 빈 리스트(예: `plan` 노드)면 검사 0건 → 통과. route record 실측: `plan: []`, `execute: ["plan"]`, `test: ["execute"]`, `report: ["test"]`.
- 대조는 `route_id`/`route_hash`만 (§13.5.3 소비 계약). `registry_digest`는 marker에 담되 gate 판정에 쓰지 않는다.

**wrapper 3종 배선** — `validate_route_record` 끝(성공 return 직전)에 삽입:
- `adapters/claude/bin/dispatch-headless.py:607` (`args.route_validation=result.stdout.strip(); return 0`)
- `adapters/codex/bin/dispatch-headless.py:~701` 부근 동일 지점
- `adapters/opencode/bin/dispatch-headless.py:~608` 부근 동일 지점

```python
try:
    completion_marker_gate(args.route_file, args.route_node, args.action, args.agent_home)
except DispatchContractError as e:
    return fail(e.reason, 65, detail=e.detail, child_spawned="0")
```
- ★ **`agent_home`을 gate보다 앞으로 끌어올려야 한다.** claude는 `agent_home = resolve_agent_home()`을 **`:672`**에서야 계산하는데 gate는 `:607`(= `:660` 호출)에서 돈다 → 그 시점에 scope에 없다. `main:615`(`action` 계산 직후)에 `args.action = action`과 `args.agent_home = resolve_agent_home()`을 함께 세팅하고, `:672`는 `args.agent_home`을 재사용하도록 정리하라(중복 호출 제거). codex/opencode도 동형으로.

**★ spawn 0건 보장 근거 (claude 기준, 3어댑터 동형)** — 실측 확인:
```
652  validate_nested_eligibility(...)  ← ★ gate보다 앞선 게이트 #1 (exit 69)
660  rc=validate_route_record(args)   ← 안에서: worker-route-guard(:596-602) → ★ completion gate
661  if rc != 0: return rc
663  args.resolved_model_settings = resolve_model_settings(args)
669  if args.start and shutil.which("claude") is None: ...     ← claude 존재 확인조차 이 뒤
674  registry = resolve_global_registry(...)                   ← registry row 이 뒤
682  broker = ensure_launch_broker(...)                        ← broker ensure 이 뒤
```
gate가 registry row·broker ensure·프로세스 기동 **전부보다 앞**이다 → **spawn 0건 + row 0건**이 구조적으로 보장된다. 이것이 fixture ⑦이 실제 `claude` 바이너리 없이도 `--start`로 검증 가능한 이유다.

★ **단, gate 앞에 두 개의 선행 게이트가 있다** (plan-check M3) — fixture ⑦은 이 둘을 먼저 통과해야 `completion-marker-missing`에 **도달**한다:
1. `validate_nested_eligibility`(`:652`, codex `:735`) — `depth=2, action=start`면 `dispatch_contract.py:212-215`가 `parent_harness`/`parent_transport`/`parent_sandbox`/`eligibility_source` 부재 또는 `status != "supported"`를 **exit 69**로 닫는다.
2. `worker-route-guard.py`(`:596-602`) — route record가 완전 유효해야 한다(registry_digest 일치 등). 아니면 `worker-route-validation-failed`가 선행한다.

fixture ⑦ 커맨드는 §4.2⑦대로 eligibility 인자를 반드시 포함하라.

**exit code**: `65` (route-record 계열과 동일 — `route-record-required:590`, `route-metadata-missing:595`가 65). `child_spawned="0"` 필드를 함께 출력해 SD-52 실패 표기와 정합시킨다.

### 3.4 착수점 — `utilities/dispatch-node.py`

gate는 wrapper가 소유하므로 `dispatch-node.py`는 **기능상 변경이 불필요**하다 (`:14`에서 이미 `--route-file`을 넘긴다 → gate 자동 적용). 아래 한 줄은 **어떤 acceptance도 요구하지 않는 관측 편의**이며, §13.5.4가 이 파일을 스코프 목록에 넣었다는 이유만으로 정당화되지 않는다(plan-check m5 — 정직하게 표기). conductor가 marker 위치를 찾기 쉬워지는 실익만 있고 저위험이므로 유지하되, 시간이 없으면 **생략 가능**하다:
- `:12` resource-runner 분기 뒤, `:14` argv 구성 전에:
  ```python
  print("completion_marker="+str(Path(os.environ.get("AGENT_HOME", ROOT))/".dispatch/completion"/route["route_id"]/(node["id"]+".json")))
  ```
- `import os` 추가 필요(`:3`은 `argparse, json, subprocess, sys`만 import).
- 이 출력이 기존 파서를 깨지 않는지 확인하라 — `dispatch-node.py`는 `subprocess.run(argv)`로 wrapper stdout을 그대로 흘리므로 `key=value` 한 줄 추가는 관례에 부합한다.

### 3.5 착수점 — conductor 의무 명문화

`adapters/claude/skills/autopilot-code/references/dev-pipeline.md:24`가 정확한 자리다. 현행:
> After harvest, change the stage row from `open` to `done` before dispatching the next stage. An open harvested row orphans the pipe and keeps Fleet and dispatch-wait active.

바로 뒤에 문단 추가 (영문 — 이 문서는 영문 harness 계약 문서다):
```markdown
After judging a stage's artifact contract complete, write its completion marker before
dispatching the next stage:

```bash
python3 <agent-home>/utilities/capability-route.py complete \
  --route <route-file> --node <node-id> --evidence <stage terminal artifact>
```

The marker lands at `<agent-home>/.dispatch/completion/<route_id>/<node_id>.json`. Evidence is
the stage's contractual terminal artifact (`plan/plan.md`, the final dev log, the test verdict,
`final_report.md`). The pass judgement stays semantic and belongs to the conductor; the marker
only makes its *result* deterministic. A record-bound `--start` for a node whose `depends_on`
markers are absent fails closed with `completion-marker-missing` and spawns nothing. Marker
absence is *no claim*, never a failure.
```
**§0.3대로 3부 전부 동기화하라.**

### 3.6 acceptance 대응

| SD-56 acceptance | 충족 경로 | fixture |
|---|---|---|
| ① canonical marker 생성 + 필드 일치 | §3.2 | ⑥ |
| ② 선행 marker 부재 시 spawn 0 + structured failure | §3.3 | ⑦ |
| ③ marker 부재를 실패로 읽는 소비자 0 | §3.3 4단계(v1 skip) + 소비 계약 | ⑧ |
| ④ 재수확 이력 보존 + 최신 authoritative | §3.2 | ⑨ |
| ⑤ v1 record·record 미결합 launch 미적용 | §3.3 2·4단계 | ⑦⑧ |

---

## 4. Fixture 9종 — 배치와 형태

`TESTENV`(§0.1)를 모든 실행에 적용한다. 모든 fixture는 **자기 전용 broker**(`--root <tempdir>/broker`)만 띄운다.

### 4.0 ★ 느린/가짜 target을 만드는 법 (fixture ①의 전제)

실제 `claude` 세션 스폰은 금지다. broker의 target 경로는 `adapter_command`(`:317-324`)가 **`ROOT`에서** 구성한다:
```python
29  SOURCE_ROOT = Path(__file__).resolve().parents[1]
30  _agent_home = Path(os.environ.get("AGENT_HOME", SOURCE_ROOT)).expanduser().resolve(strict=False)
31  ROOT = _agent_home if (_agent_home / "core/CORE.md").is_file() else SOURCE_ROOT
320     command = [sys.executable, str(ROOT / "adapters/claude/bin/dispatch-headless.py")]
```
→ **fixture용 `AGENT_HOME`**을 temp에 만들어 `core/CORE.md`(빈 파일이면 충분)와 가짜 `adapters/claude/bin/dispatch-headless.py`(N초 sleep 후 마커 파일 쓰고 exit 0)를 두면, broker는 그 가짜를 실행한다. `ensure`가 serve를 Popen할 때 env가 상속되므로(`:665-673`) `AGENT_HOME`을 fixture 값으로 주고 `ensure`를 부르면 된다.

주의: 이 fixture broker는 실제 dispatch-headless를 부르지 않으므로 registry row가 생기지 않는다 → `registry_attempt` reconcile 경로가 비활성이다. 이는 ①이 겨냥하는 병렬성 검증에는 무관하지만, ②③은 **기존 setUp(실제 AGENT_HOME + `--register` action)**을 그대로 쓰라.

신규 헬퍼를 `dispatch_broker.test.py`에 추가: `def fake_agent_home(self, sleep_seconds) -> Path`.

### 4.1 배치표

| # | 검증 대상 | 파일 | 형태 |
|---|---|---|---|
| ① | slow-target 병렬 | `utilities/dispatch_broker.test.py` | 신규 `test_slow_target_does_not_block_other_requests` |
| ② | request_id 동시·순차 idempotency | `utilities/dispatch_broker.test.py` | 기존 `:269` `test_duplicate_request_is_idempotent` · `:278` `test_concurrent_duplicate_request_creates_one_attempt` **기대값 조정**(§1.6) |
| ③ | claim/spawn 직후 crash fenced recovery | `utilities/dispatch_broker.test.py` | 기존 `:322` `test_claim_crash_restarts_only_unregistered_attempt` · `:356` `test_spawn_crash_recovers_registered_attempt_without_relaunch` **+ 병렬 부하 하 재확인** |
| ④ | rollover 후 v2 ordinal-1 hop | `utilities/dispatch_broker.test.py` | 신규 `test_v2_record_survives_broker_rollover` |
| ⑤ | v1 record 회귀 0 | `utilities/capability_route.test.py` | 신규 `test_v1_record_keeps_instance_binding_rules` |
| ⑥ | marker 생성·필드 일치 | `utilities/dispatch_completion_marker.test.py` **(신규 파일)** | `test_complete_writes_canonical_marker` |
| ⑦ | 선행 marker 부재 → gate fail-closed | `utilities/dispatch_completion_marker.test.py` | `test_start_without_dependency_marker_fails_closed` (3어댑터 parametrize) |
| ⑧ | marker 부재를 실패로 읽는 소비자 0 | `utilities/dispatch_completion_marker.test.py` | `test_marker_absence_is_not_a_failure` |
| ⑨ | 재수확 이력 보존 + 최신 authoritative | `utilities/dispatch_completion_marker.test.py` | `test_reharvest_preserves_history_and_latest_is_authoritative` |
| ⑩ | **v2 `broker-unavailable` fail-closed** (SD-55 accept ③) | `utilities/dispatch_broker.test.py` | 신규 `test_v2_record_without_live_broker_fails_closed` |

### 4.2 개별 설계

**① slow-target 병렬** — `dispatch_broker.test.py`
- fixture `AGENT_HOME`(§4.0): 가짜 adapter가 `--slug`를 읽어 sleep **전에** `<tmp>/started-<slug>.marker`를, sleep **후에** `<tmp>/done-<slug>.marker`를 쓴다. slug `slow` → 5초 sleep, slug `fast` → 즉시.
- 두 route/envelope를 만들되 **`request_id`가 달라야** 한다 — `request_identity`(`stage-dispatch-fallback.py:68-81`)가 `slug`를 해시에 넣으므로 slug만 다르면 충분하다.
- ★ **배리어 필수** (plan-check M2). "`done-slow.marker` 부재 확인" 만으로는 **회귀를 못 잡는다**: 그것은 A가 claim/실행에 진입했음을 증명하지 않으므로, 메인의 `fast`가 A의 accept보다 앞서면 **전역 락이 되살아나도** `fast`가 락을 먼저 잡고 완주해 단언이 통과한다(거짓 음성 + flaky).
- 올바른 순서:
  1. 스레드 A로 `slow` 제출
  2. **`started-slow.marker`가 나타날 때까지 폴링**(deadline 10s) ← 배리어. A가 실행 구간에 진입했음이 보장된다. (대안: slow의 state 파일이 `status == "running"`이 될 때까지 폴링)
  3. 메인에서 `fast` 제출 → 동기 완주
- 단언 (타이밍이 아니라 상태로):
  - `fast` 응답 `ok=True`, `state.status == "done"`
  - `fast` 완료 시점에 `done-slow.marker`가 **아직 없다** ← HOL blocking 해소의 결정적 증거
  - 그 뒤 A join → `slow` 도 `ok=True`, `done` (첫 target 생애와 독립 완주)
- 회귀 방지: 배리어가 A의 락 보유를 보장하므로, 전역 락이 되살아나면 `fast`가 5초 뒤에야 끝나고 `done-slow.marker`가 이미 존재해 **단언이 결정론적으로 실패**한다.
- `sleep`은 5초로 고정하고 total timeout을 넉넉히(30s) — CI 지터에 강건.

**② idempotency** — §1.6의 단언으로 조정. 핵심 불변: `registry_attempt` row 1개, `attempt_id` 1종, target process 1개.
- ★ **§1.3(e) B3 수정 후에는 "running 중 재제출 = `broker-request-inflight`"가 결정론적**이다 — reconcile이 inflight 뒤로 갔고 lease가 갱신되므로 recovered-done 경로로 샐 수 없다. 따라서 §1.6의 관대한 단언("둘 중 하나")을 쓰지 말고 **`broker-request-inflight`를 정확히 단언**하라. 관대한 단언은 B3의 조기-terminal defect를 그대로 통과시킨다(plan-check 지적).
- 순차 terminal 재제출은 `{"ok": True, "duplicate": True}` + 기존 state 반환을 단언.

**③ fenced recovery** — 기존 두 테스트 유지 + 각 crash 시나리오를 **다른 request_id의 request가 병렬로 running인 상태**에서 재수행하는 케이스를 1개 추가(`test_fenced_recovery_holds_under_parallel_inflight`). 단언: 중복 launch 0(registry row 수 불변), 병렬 request는 영향 없이 terminal.

**④ rollover v2** — 시나리오:
1. `setUp`의 fixture broker `ensure` → `instance_1`
2. v2 route 컴파일(`ROUTE.compile_route(...)`) → `route_hash_before` 기록
3. `dispatch-broker.py stop --root <fixture broker>` → 종료 대기
4. `ensure` 재실행 → `instance_2` (`!= instance_1`)
5. `stage-dispatch-fallback.py --register` 실행. **env에 `AGENT_DISPATCH_BROKER_INSTANCE=instance_1`(낡은 값)을 일부러 넣는다** ← §2.3이 겨냥한 경로
6. 단언: `check=ok`, `selected_hop=same-harness-headless`, `fallback_ordinal=1`, `check=degraded` **부재**(하강 0), route 파일 재로드 시 `route_hash == route_hash_before`
- ★ 이 테스트는 `stop`/`ensure`를 부르므로 **반드시 fixture broker root**여야 한다. live broker root가 새면 §0.2 위반이다 — `self.broker_root`가 temp임을 테스트 안에서 assert하라.
- `ensure`는 테스트 프로세스(비-워커)에서 도므로 §0.1의 `TESTENV`가 걷어낸 env 하에 정상 동작한다.

**⑤ v1 회귀** — `capability_route.test.py`
- compile은 이제 v2만 생산하므로 v1 record는 **손으로 구성**한다: v2 record를 컴파일 → `broker_contract_version`을 1로, 모든 tuple/candidate에 `broker_instance`를 주입 → `ROUTE.route_hash(payload)`로 **재해시** → `route_hash`/`route_id` 갱신.
- 단언: `verify_route(v1)` 통과; instance를 뺀 v1 → `ValueError`(기존 규칙 그대로); v2 record에 instance를 넣으면 → `ValueError`(§2.4(d)).
- fallback 거동 회귀는 기존 `stage_dispatch_fallback.test.py`(3/3)가 커버한다 — v1 경로 무변경이므로 그대로 통과해야 한다.

**⑥ marker 필드** — 신규 파일
- temp `AGENT_HOME` 설정 → v2 route 컴파일 → evidence 파일 작성 → `capability-route.py complete --route --node plan --evidence <f>`
- 단언: `<AGENT_HOME>/.dispatch/completion/<route_id>/plan.json` 존재; `route_id`/`route_hash`/`registry_digest`가 record와 일치; `node_id=="plan"`; `completion_gate == node["completion_gate"]`(=`code-plan`); `evidence.sha256 == sha256(파일)`.

**⑦ gate fail-closed** — 신규 파일, 3어댑터 parametrize
- v2 route + `execute` 노드(`depends_on: ["plan"]`, 실측 확인) 선택. marker **없는** 상태에서:
  ```
  python3 adapters/<h>/bin/dispatch-headless.py --start --route-file <r> --route-node execute \
      --route-id .. --route-hash .. --registry-digest .. --write-scope .. --completion-gate code-execute \
      --depth 2 --parent <c> --worktree <repo> --slug .. --capability autopilot-code --intensity standard \
      --parent-harness claude --parent-transport headless --parent-sandbox fixture \
      --nested-eligibility supported --eligibility-source fixture-broker \
      --launch-authority ancestor-broker ...
  ```
- ★ **eligibility 인자가 없으면 `completion-marker-missing`에 도달하지 못한다** (plan-check M3): `validate_nested_eligibility`가 `:652`에서 **먼저** 돌아 `dispatch_contract.py:212-215`가 exit 69(`nested-eligibility-evidence-missing`)로 닫는다. 초안 커맨드에는 이 인자들이 없었다.
- 마찬가지로 gate는 `validate_route_record` **끝**에 있으므로 `worker-route-guard.py`(`:596-602`)를 먼저 통과해야 한다 → fixture route는 `registry_digest` 일치 등 **완전 유효**해야 한다. 아니면 `worker-route-validation-failed`가 선행한다. (`ROUTE.compile_route`로 만들면 자동 충족.)
- 단언: exit != 0, stdout에 `reason=completion-marker-missing`, `child_spawned=0`, jobs.log row **0건**, 프로세스 스폰 0.
- §3.3의 순서 근거대로 `shutil.which("claude")`(`:669`)보다 **앞**에서 막히므로 실제 바이너리 부재/존재 무관하게 결정론적이다.
- 그 다음 `plan` marker를 쓰고 재실행 → gate 통과(이후 다른 사유로 실패해도 무방; `reason=completion-marker-missing`이 **아님**만 단언).
- codex/opencode는 인자 표면이 다르다(`--model`/`--reasoning`, `--model`/`--variant`) — `portable-guards.test.sh:864`(codex)·`:3043`(opencode)의 호출 예시를 그대로 참고해 맞춰라.

**⑧ negative: 소비자 0** — 신규 파일
- (a) **v1 record + `--start`, marker 없음** → `completion-marker-missing`이 **나오지 않음** 단언 (소급 강제 금지).
- (b) **record 미결합 `--start`**(`--route-file` 없음) → 동일 단언.
- (c) 정적 단언: `utilities/`·`adapters/*/bin/`·`tools/fleet/` 소스를 스캔해 `completion` marker 부재를 `failed`/`status=failed`로 매핑하는 코드가 없음을 확인. 구현: gate 헬퍼(`dispatch_contract.completion_marker_gate`) **외부**에 `completion-marker-missing` 문자열이 등장하지 않음을 단언(어댑터 3종의 `fail(e.reason, ...)` 전달 경로는 예외 허용 목록으로).
- 이 (c)가 §13.5.3 "marker 부재는 실패가 아니라 무주장"의 결정론적 수호자다.

**⑩ v2 broker-unavailable fail-closed** — `dispatch_broker.test.py` (plan-check M4로 추가)
- SD-55 acceptance ③은 초안의 ①~⑨ **어디에도 커버되지 않았다**. `resolve_live_instance`가 `""`를 반환하는 경로는 **전량 신규 코드**이며 미검증이었다. 기존 `:396` `test_missing_broker_fails_closed`는 v1 시절 증거일 뿐이고, §2.2의 status-only 결정이 그 테스트를 **보존**하는 것이지 ③을 증명하지는 않는다.
- 시나리오: v2 route + **존재하지 않는(또는 stop된) broker root** → `stage-dispatch-fallback.py --register`
- 단언: `check=failed`, `reason=broker-unavailable`, `child_spawned=0`, jobs.log row **0건**, 그리고 **그 broker root에 broker가 생기지 않았다**(`broker.json` 부재) ← status-only 결정(§2.2)의 수호자
- 변형 2: 살아 있던 fixture broker를 `stop`한 뒤 동일 단언 (stale/dead 경로)

**⑨ 재수확** — 신규 파일
- evidence v1 작성 → `complete` → canonical + `plan.1.json` 확인
- **동일 evidence로 `complete` 재실행** → no-op 단언: 이력 파일 여전히 1개(`plan.2.json` 부재)
- evidence를 **수정** → `complete` → `plan.2.json` 생성, `plan.1.json` **내용 불변**(이력 보존), canonical의 `evidence.sha256 == sha256(수정본)`(최신 authoritative), `sequence == 2`

---

## 5. 검증 — 실행 커맨드

작업 디렉터리는 worktree 루트. **모든 dispatch 계열 테스트에 `TESTENV` prefix 필수** (§0.1).

```bash
cd /home/Uihyeop/agent_setting-wt/stage-dispatch-v13
TESTENV='env -u AGENT_SESSION_ROLE -u AGENT_DISPATCH_CHILD -u AGENT_DISPATCH_BROKER_INSTANCE -u AGENT_DISPATCH_BROKER_ROOT -u AGENT_DISPATCH_JOBS'
```

### 5.1 초점 스위트 (v13이 직접 바꾸는 표면)

| 커맨드 | v12 기준 baseline |
|---|---|
| `$TESTENV python3 utilities/dispatch_broker.test.py -v` | **10/10** (이 사이클 재실측 OK) |
| `$TESTENV python3 utilities/stage_dispatch_fallback.test.py -v` | **3/3** (이 사이클 재실측 OK) |
| `$TESTENV python3 utilities/capability_route.test.py -v` | **10/10** (이 사이클 재실측 OK) |
| `$TESTENV python3 utilities/dispatch_contract.test.py -v` | 5/5 |
| `$TESTENV python3 utilities/worker_route_guard.test.py -v` | 3/3 |
| `$TESTENV python3 utilities/dispatch_adapters_v11.test.py -v` | 1/1 |
| `$TESTENV python3 utilities/dispatch_completion_marker.test.py -v` | **신규** |

### 5.2 인접 회귀

```bash
$TESTENV python3 utilities/spec_transaction.test.py -v
$TESTENV python3 utilities/model_worker_governor.test.py -v
$TESTENV python3 utilities/resource_runner.test.py -v
$TESTENV python3 utilities/dispatch-artifact-root.test.py -v
$TESTENV python3 tools/capability_topology.test.py -v
$TESTENV bash utilities/dispatch-route.test.sh
$TESTENV bash utilities/dispatch-concurrency.test.sh
$TESTENV bash utilities/dispatch-liveness.test.sh
$TESTENV bash utilities/dispatch-wait.test.sh
$TESTENV bash utilities/artifact-root.test.sh
```

### 5.3 전체 portable guards + 투영/경계

```bash
$TESTENV bash hooks/portable-guards.test.sh          # 기대: PASS=359 FAIL=0
python3 tools/build-manifest.py --check              # 투영 census — 신규 test 파일 분류 필요할 수 있음 (§7 리스크)
bash tools/check-adaptation-boundary.sh
bash tools/generated-projections.test.sh
bash tools/routing-contract.test.sh
git diff --check
```

`portable-guards.test.sh`는 마지막에 `PASS=<n> FAIL=<n>`을 출력하고 `FAIL != 0`이면 non-zero로 종료한다(스크립트 말미). 359는 v12 사이클(`plans/2026-07-15_stage-dispatch-v12-broker/test_logs/verification.md`)과 v10 사이클이 함께 기록한 값이다. **PASS가 359보다 늘어나는 것은 정상**(가드 추가 시); 줄거나 FAIL>0이면 회귀다.

### 5.4 금지

- live broker(`/home/Uihyeop/agent_setting/.dispatch/broker`, `brk-d25176b21a134c10a6f6d1608ffc3af4`)에 대한 `stop`/`ensure`/변조 — **절대 금지**.
- 실제 `claude`/`codex`/`opencode` 세션 스폰·signal — 금지. 모든 fixture는 `--register`/`--dry-run` 또는 §4.0 가짜 adapter를 쓴다.
- `capabilities/topologies.json` 수정 — 금지(§0.4).

---

## 6. 실행 순서

SD-54 → SD-56 → SD-55 순을 권한다. 근거: SD-54는 다른 둘과 파일이 겹치지 않아 독립 검증이 가능하고, SD-55는 `capability-route.py`·`stage-dispatch-fallback.py`·`dispatch-broker.py:243`에 걸쳐 있어 **SD-54의 broker 변경과 같은 파일을 만진다** → 마지막에 두면 충돌 진단이 쉽다. SD-56은 표면이 가장 넓지만(어댑터 3종 + 문서 3부) 다른 둘과 논리적으로 독립이다.

1. **SD-54** — `dispatch-broker.py` 재구조화 → fixture ①②③ → 초점 스위트
2. **SD-56** — `capability-route.py` complete + `dispatch_contract.py` gate + 어댑터 3종 + `dispatch-node.py` + 문서 3부 → fixture ⑥⑦⑧⑨
3. **SD-55** — `capability-route.py` v2 + `stage-dispatch-fallback.py` + `dispatch-broker.py:243` → fixture ④⑤
4. 전체 회귀(§5.3) → 산출물 기록

---

## 7. 리스크와 롤백

| 리스크 | 신호 | 대응 |
|---|---|---|
| **조기 terminal / terminal 덮어쓰기** (병렬화의 최대 함정) | 동일 request_id 재제출이 target 실행 중 `done`을 받음; terminal이 되돌아감 | §1.3(e) — inflight를 reconcile **앞**으로 + (D) on-disk 재독. dedup 분기를 "그대로 이동"하면 반드시 재현된다 |
| **lease 만료로 중복 launch** | fixture ①에서 slow target이 두 번 뜸; registry row 2개 | §1.3(d) lease 갱신 스레드가 방어. 갱신 주기 = `stale_seconds/3`. 이 스레드를 빠뜨리면 12분 워커에서 15초 뒤 재-claim된다 |
| **v2 hop이 `broker-route-mismatch`로 전멸** | fixture ④가 `check=degraded`로 하강 | `dispatch-broker.py:243` 버전 분기 누락(§2.6). v2 candidate엔 instance가 없다 |
| **v2 hop이 `broker-instance-mismatch`** | rollover fixture 실패 | `broker_status:160` env 신뢰(§2.3). live 해석 **과 `submit_broker` 양쪽**에서 `AGENT_DISPATCH_BROKER_INSTANCE` 제거 필수 — 한쪽만 하면 `dispatch-broker.py:749` fall-through에서 죽는다 |
| **`ensure`-fallback이 fail-closed 테스트를 파괴** | `:396` `test_missing_broker_fails_closed` 실패 + 없어야 할 broker 생성 | §2.2 — **status-only**. `ensure`는 비-워커에서 실제로 broker를 Popen한다(`:665-673`) |
| **marker 경로 분열로 전 fabric 중단** | 모든 record-bound `--start`가 `completion-marker-missing` | §3.2.1 — 검증형 `resolve_agent_home()` 공유. `os.environ.get("AGENT_HOME", ROOT)` 금지(ROOT=worktree) |
| **`_verify_fallback_chain`이 v2를 무검증 통과** | 잘못된 v2 record가 verify를 통과 | §2.4(d) — bool→version 3상태. 현행 `:191`은 v2에서 `False`를 넘겨 broker_root 검사까지 없앤다 |
| **워커 env로 인한 대량 오탐** | broker/fallback 테스트 전부 setUp 에러(exit 76) | §0.1. **코드를 고치지 말 것.** `TESTENV` prefix 사용 |
| **`skills/` 미러 drift** | `check-adaptation-boundary.sh` 또는 projection census 실패 | §0.3 — `dev-pipeline.md` 3부 동기화 후 `diff -r`로 확인 |
| **신규 test 파일이 투영 census에 미등재** | `tools/build-manifest.py --check` 실패 | v12가 똑같이 밟았다(verification.md "Projection census initially lacked the two new utilities"). `--check` 출력이 지시하는 분류를 따르라 |
| **registry digest 경합(자기수정)** | route record가 stale-digest로 거부 | `capabilities/topologies.json` 미변경(§0.4). v12 O3 관찰 그대로 |
| **`complete` 재실행이 이력 오염** | `plan.N.json`이 무한 증가 | §3.2 3단계 evidence sha256 비교 no-op |

**롤백**: 세 SD가 파일 단위로 대체로 분리된다 — SD-54는 `dispatch-broker.py`의 `process_request`/`__init__`, SD-56은 `capability-route.py` complete + `dispatch_contract.py` + 어댑터/문서, SD-55는 `capability-route.py` 검증부 + `stage-dispatch-fallback.py` + `dispatch-broker.py:243`. 단계별 커밋을 쌓으면 개별 revert가 가능하다. 겹치는 두 지점은 `capability-route.py`(SD-55·56)와 `dispatch-broker.py`(SD-54·55)이며, 각각 함수가 달라 충돌 위험은 낮다.

**merge 후 depth-0 main의 몫**: live broker 롤오버(in-flight 0 대기 → `stop` → `ensure`). 이 사이클의 어떤 스테이지도 수행하지 않는다(§13.5.4).

---

## 8. 이월 후보 (`_internal/carryover.md`에 기록할 것 — spec 수정 금지)

1. **SD-55 문언 정정**: "client가 `ensure`를 실행" → `ensure`는 워커에서 거부되므로(`dispatch-broker.py:604`) 실제 구현은 **`status`-only**다. broker가 살아 있는 한 관측 결과는 동일하고 `status`가 ping까지 더해 더 보수적이다. spec 문언을 그대로 구현하면 (a) 실제 호출자(워커)에겐 항상 실패하고 (b) 비-워커에선 fail-closed여야 할 자리에 broker를 생성한다.
2. **SD-56 쓰기 의무의 부분 배선**: §13.5.3은 "conductor(**또는 quick/inline의 capability owner**)"라고 쓰지만, 이번 구현은 `dev-pipeline.md`(standard+ 파이프라인)만 배선한다. quick/inline owner 경로의 marker 쓰기는 **무주장으로 남는다** — 의도된 축소이며 v14에서 quick/inline 문서 표면에 확장할 후보다.
3. **테스트 하니스의 워커 env 의존성**: `dispatch_broker.test.py`·`stage_dispatch_fallback.test.py`가 워커 세션에서 setUp 실패한다. `portable-guards.test.sh:38-40`은 이미 "D-42 hermeticity"로 env를 걷어내는데, python 테스트 파일들엔 같은 방어가 없다. 테스트 내부에서 `AGENT_SESSION_ROLE`/`AGENT_DISPATCH_CHILD`를 unset하도록 하드닝하는 것이 v14 후보다.
4. **v12 잔여**: O2(worker no-commit), O3(digest pin), O4(resource-runner canonical registry) — v14 유지.
