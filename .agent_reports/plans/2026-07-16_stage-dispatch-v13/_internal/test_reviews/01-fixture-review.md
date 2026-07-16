# stage-dispatch v13 — test 스테이지 코드 리뷰 소견

리뷰어: depth-2 test 워커(deep reviewer role) / 대상: `git diff 98308ec4` 전체 + 신규 fixture 2종
관점: **fixture 품질 · 무력화 여부 · 불변식 위험**. 판정 근거·재실행 원문은
`test_logs/01-independent-verification.md`.

---

## 1. 총평

구현 품질이 높다. plan-check가 잡아낸 blocker 4건이 산문이 아니라 **코드에 실재**하고, 각 결정에
근거 주석이 남아 있다. 특히 다음 세 가지는 이 사이클의 강점이다.

1. **B3(terminal immutability) 처방의 3중 결합** — per-request 락 + (D)의 on-disk 재독 +
   renewer의 락 내 terminal 확인. 어느 하나만으로는 부족한데 셋 다 있다. 되돌리기 실험으로
   수정의 유효성을 실측 확인했다(§3).
2. **fixture ①의 배리어** — `started-<slug>.marker` 폴링이 없었다면 "전역 락이 되살아나도 통과"
   하는 거짓 음성이었다(plan-check M2). 실제로 전역 락을 부활시켜 fixture가 실패함을 확인했다.
3. **v1 고정(`route_v1()`)의 타이밍 판단** — plan-check M1이 "B1을 고치는 순간 실패로 전환"이라
   예견한 지점에서 정확히 실패 전환을 실측하고 v1으로 고정했다. 테스트를 통과시키려는 조정이
   아니라 **원래 의도를 보존하는** 조정이며, 이것이 무력화가 아님은 §2에서 검증했다.

무력화(테스트를 통과시키려 단언을 약화한 흔적)는 **발견되지 않았다**. 다만 결정론을 얻는 과정에서
**의도치 않게 커버리지를 잃은 지점 1건**이 있다(§3, F1).

---

## 2. "기대값 조정" 3건은 무력화인가 — 개별 판정

execute가 기대값을 바꾼 테스트 3건은 무력화 의심 1순위다. 전부 소스 대조로 판정했다.

### 2.1 `test_tampered_inherited_instance_fails_closed` → v1 고정 — **정당**

v2에서는 `broker_env(2)`가 `AGENT_DISPATCH_BROKER_INSTANCE`를 **의도적으로** 제거하므로(§2.3의
설계 목표 그 자체) env tamper라는 공격 벡터가 성립하지 않는다. 테스트를 v2로 두면 "무엇을 검사하는지
모르는 테스트"가 된다. v1으로 고정해 v1의 env-trust 계약을 계속 검사하는 것이 옳다.

**핵심 확인 — 방어가 사라지지 않았는가**: `validate_request`의
`if request.get("broker_instance") not in allowed_instances: raise BrokerError("broker-instance-mismatch")`
가 **무변경**으로 살아 있다. 즉 broker 측 envelope↔현재 instance 대조는 그대로이고, 손으로 위조한
envelope는 v2에서도 거부된다. spec §13.5.2의 "identity 검증은 사라지지 않고 record에서 hop으로
이동한다"가 코드로 성립한다. 이 검사는 v1 경로(tamper 테스트)로 계속 실행되므로 죽은 코드도 아니다.

`validate_route`의 candidate 매칭에 추가된 `(contract == 2 or row.get("broker_instance") == ...)`
분기는 완화처럼 보이지만, **v2 candidate에는 `broker_instance` 키 자체가 없다**(`_validate_dispatch_evidence`가
strip). 이 분기가 없으면 모든 v2 hop이 `broker-route-mismatch`로 전멸한다. 필연이며 완화가 아니다.

### 2.2 `test_missing_broker_fails_closed` → v1 고정 — **정당**

v2에서는 명시 `--broker-root`가 route의 broker_root와 어긋나면 `broker-root-mismatch`(§2.5d)라는
**다른 사유**로 먼저 막혀 이 테스트의 원래 의미(`broker-unavailable`)가 성립하지 않는다. v1 고정이
원의도를 보존한다. 그리고 v2의 `broker-unavailable` 경로는 **fixture ⑩이 신설되어 커버**한다
(존재한 적 없는 root + stop된 broker 2변형 + `broker.json` 미생성까지). 커버리지 순증이다.

### 2.3 `test_concurrent_duplicate_request_creates_one_attempt` → fake adapter 전환 — **부분 정당**

단언 자체는 **강화**됐다: 관대한 "둘 중 하나" → `broker-request-inflight` 정확 단언. 스레드 기반
동시 `communicate()`로 교체한 것도 실제 결함 수정이다(list comprehension이 두 프로세스를 사실상
순차 실행시키던 것을 발견한 진단은 정확하다 — `communicate()`가 블로킹이므로).

그러나 fake adapter 전환의 **부작용**이 §3의 F1이다.

---

## 3. ★ F1 — B3 회귀 가드 부재 (major, merge 전 처리 권고)

### 무엇이 문제인가

`process_request`에서 inflight 검사를 registry reconcile **앞으로** 옮긴 수정(plan-check가
"★가장 중대"로 지목한 B3)이 **어떤 fixture로도 고정돼 있지 않다**. 순서를 v12(결함) 순서로
되돌려도 `dispatch_broker.test.py`는 **14/14 통과**한다.

### 왜 안 잡히는가

B3 경합은 다음 조건에서만 도달 가능하다:

> request가 `running`이고, **그 attempt의 registry row가 이미 존재한다**

두 번째 조건은 SD-52의 "spawn 전 canonical registry row" 불변식(`append_job:728` → `Popen:768`)
때문에 실전에서는 **항상** 성립한다 — 그래서 B3가 위험했다. 그런데 fixture ②가 결정론화를 위해
실 adapter → fake adapter로 바뀌면서 **fake adapter가 registry row를 쓰지 않게 되어**
`registry_attempt(...)`가 언제나 `None`을 반환한다. reconcile 분기가 도달 불가능해지므로
순서를 어떻게 두든 결과가 같다.

v12 원본 fixture는 실 `--register`를 호출해 row가 생겼고 `rows == 1` + `attempt_id`를 단언했다.
그 단언이 `self.assertFalse(self.jobs.exists())`로 대체되면서 **결정론을 얻는 대가로 B3 경합
조건을 잃었다**. dev_log 01이 fixture ②를 "§1.6(a)대로 ... `broker-request-inflight`를 정확히
단언"으로 기술한 것은 사실이나, 이를 B3 대응으로 읽히게 서술한 부분은 **실제 보호 범위를 과대
진술**한다.

### 이것이 진짜 결함임을 확증한 probe 결과

| 트리 | 재제출 응답 | target 상태 |
|---|---|---|
| 수정본(as-shipped) | `ok=False`, `reason=broker-request-inflight` | 실행 중 |
| 되돌린 본(B3 결함) | `ok=True`, **`status=done`**, `recovered_from_registry=True` | **여전히 실행 중** |

→ 구현은 정확하다. **회귀 보호만 없다.**

### 권고 fixture (즉시 사용 가능 — 아래 probe가 이미 동작 확인됨)

fake target이 `--attempt-id`/`--jobs`로 **registry row를 먼저 쓴 뒤** sleep하게 하고, started
배리어 후 동일 request를 재제출해 `ok=False` + `reason=broker-request-inflight`를 단언한다.
`dispatch_broker.test.py`의 기존 헬퍼(`fixture_broker_request`/`submit_to`)를 그대로 재사용한다.

```python
def test_resubmit_while_running_with_registry_row_is_inflight(self):
    # SD-54 §1.3e / plan-check B3: SD-52 writes the registry row BEFORE spawn,
    # so a resubmit of a still-running request WILL find a row. The inflight
    # check must therefore precede the registry reconcile -- otherwise the
    # resubmit reconciles against that row and terminates the request while
    # its target is still executing (terminal immutability + AC2 both break).
    # Reverting the order leaves every other fixture green, so this one is the
    # only guard.
    home = self.base / "b3-home"
    (home / "core").mkdir(parents=True)
    (home / "core" / "CORE.md").write_text("fixture\n", encoding="utf-8")
    adapter_dir = home / "adapters" / "claude" / "bin"
    adapter_dir.mkdir(parents=True)
    script = adapter_dir / "dispatch-headless.py"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import argparse, os, time\n"
        "from pathlib import Path\n"
        "p=argparse.ArgumentParser()\n"
        "p.add_argument('--slug'); p.add_argument('--jobs'); p.add_argument('--attempt-id', dest='att')\n"
        "a,_=p.parse_known_args()\n"
        # the canonical spawn-time row -- exactly what makes the B3 race reachable
        "row='2026-07-16T00:00:00Z\\trunning\\t2\\towner\\t'+a.slug+'\\tattempt_id='+a.att+',note=live'\n"
        "Path(a.jobs).parent.mkdir(parents=True, exist_ok=True)\n"
        "with open(a.jobs,'a') as fh: fh.write(row+'\\n')\n"
        "art=Path(os.environ['AGENT_ARTIFACT_ROOT'])\n"
        "(art/('started-'+a.slug+'.marker')).write_text('1')\n"
        "time.sleep(6)\n"
        "(art/('done-'+a.slug+'.marker')).write_text('1')\n",
        encoding="utf-8",
    )
    os.chmod(script, 0o755)
    broker_root = self.base / "b3-broker"
    env = dict(os.environ)
    for key in ("AGENT_SESSION_ROLE", "AGENT_DISPATCH_CHILD", "AGENT_DISPATCH_BROKER_INSTANCE",
                "AGENT_DISPATCH_BROKER_ROOT", "AGENT_DISPATCH_JOBS"):
        env.pop(key, None)
    env["AGENT_HOME"] = str(home)
    ensured = subprocess.run(
        [sys.executable, str(ROOT / "utilities/dispatch-broker.py"), "ensure",
         "--root", str(broker_root), "--jobs", str(self.jobs)],
        text=True, capture_output=True, check=True, env=env,
    )
    meta = dict(line.split("=", 1) for line in ensured.stdout.splitlines() if "=" in line)
    try:
        request = self.fixture_broker_request("b3", broker_root, meta["broker_instance"])
        results = {}
        first = threading.Thread(target=lambda: results.__setitem__(
            "first", self.submit_to(request, broker_root, meta["broker_instance"])))
        first.start()
        started = self.artifact / "started-b3.marker"
        deadline = time.monotonic() + 15
        while not started.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertTrue(started.exists(), "target never started")
        time.sleep(0.4)  # let the row land

        second = self.submit_to(request, broker_root, meta["broker_instance"])
        reply = json.loads(second.stdout)
        # the target must still be running -- otherwise this asserts nothing
        self.assertFalse((self.artifact / "done-b3.marker").exists())
        self.assertFalse(reply.get("ok"), reply)
        self.assertEqual(reply.get("reason"), "broker-request-inflight", reply)
        first.join(timeout=30)
    finally:
        subprocess.run(
            [sys.executable, str(ROOT / "utilities/dispatch-broker.py"), "stop",
             "--root", str(broker_root), "--jobs", str(self.jobs)],
            text=True, capture_output=True, check=False, env=env,
        )
```

검증됨: 수정본에서 통과, B3 순서를 되돌리면 `assertFalse(reply.get("ok"))`에서 실패
(되돌린 본은 `ok=True`, `status=done`을 반환).

---

## 4. 그 밖의 fixture 품질 소견

| # | 소견 | 심각도 |
|---|---|---|
| **F2** | `test_fenced_recovery_holds_under_parallel_inflight`의 `assertLessEqual(len(parallel_rows), 1)`은 0건도 허용해 병렬 request가 아예 착지 못해도 통과한다. `parallel_results["reply"]`의 성공 여부도 단언하지 않는다. "중복 launch 0"에는 정확히 대응하므로 acceptance ③ 충족에는 영향 없으나, 병렬 경로가 실제로 살아있음을 확인하려면 `reply`의 `check=ok`를 함께 단언하는 편이 낫다 | minor |
| **F3** | fixture ②가 spec의 "attempt/target 정확히 1개"를 **응답 개수 추론**으로만 확인한다. fake adapter가 `started-<slug>.marker`를 쓰므로 launch 횟수를 셀 수 있는데(예: 마커를 append 모드로) 세지 않는다. F1과 같은 뿌리 | minor |
| **F6** | fixture ⑦ 2단계가 marker 작성 후 "그 사유가 **아님**"만 단언한다. 실 바이너리 부재로 더 강한 단언이 불가하다는 주석이 있어 정당하나, `--dry-run`이나 `--register`로 gate 통과 후 진행됨을 더 강하게 볼 여지는 있다 | minor(수용 가능) |
| **F7** | fixture ⑧(c) 정적 스캔이 `rglob("*.py")`만 본다. 셸 소비자(`tools/fleet/*.sh` 등)는 스캔 밖이다. 현재 fleet 표시 연결이 별도 사이클로 미뤄져(spec §13.5.3) 소비자가 없으므로 실질 위험은 없지만, fleet 배선 시 이 가드가 침묵할 수 있다 | minor |

`test_write_once_and_completion`은 이름에 "completion"이 있으나 실제로는 route 불변성
(`write_once`)만 검사하며 marker writer를 호출하지 않는다. 따라서 (a) 구 기본 경로
(`<evidence>.completion.json`) 제거로 인한 커버리지 손실이 없고 (b) 테스트가 live agent home을
오염시키지도 않는다(실측 확인).

---

## 5. 불변식 위험 — 잔여 검토

### 5.1 위험 없음으로 판정한 것

- **renewer와 (D)의 경합**: `renew_stop.set()` + `join(timeout=2.0)`이 (D)보다 앞이라 정상
  경로에선 경합이 없다. join이 타임아웃해도 renewer는 락 안에서 `status in TERMINAL`을 재확인한
  뒤에만 기록하므로 **terminal 이후 lease 기록이 불가능**하다. 방어가 이중이다.
- **lease 공백**: lease가 claim 시점 **락 안에서** 설정되고(`:529`) renewer가 `stale/3` 주기로
  갱신하므로 claim→target 종료 구간에 만료 창이 없다. 둘째 제출은 결정론적으로 inflight.
- **fenced recovery 경로**: 새 instance에서는 `state.broker_instance != self.instance_id`라
  inflight 검사를 건너뛰고 reconcile로 간다 — 의도대로. lease 만료 경로도 동일.
- **request_id의 rollover 내성**: `request_identity`가 `broker_instance`를 digest에 넣지 않아
  rollover 전후 request_id가 불변 → v2 idempotency가 rollover를 가로질러 성립한다. 정합.
- **SD-40 이중 상한**: broker에 semaphore/cap 없음. `listen(16)` 미변경, governor 파일은 diff에
  부재. 위반 없음.

### 5.2 설계 의도로 수용한 것

- **`request_locks` GC 부재** — plan이 명시한 의도. request_id가 route/node/slug 해시 파생이라
  카디널리티가 낮고 broker 재시작으로 리셋된다. 장수 broker에서 단조 증가하지만 Lock 객체는
  경량이며 실질 위험 없음. 다만 "GC 없음"이 **의도**임을 코드 주석이 아니라 plan에만 남긴 점은
  아쉽다 — `request_lock()`에 한 줄 주석이 있으면 미래의 "메모리 누수 수정" 오해를 막는다.

### 5.3 운영 위험 (F4 재기술)

`compile_route`가 기본 v2를 생성하므로 merge 후 신규 standard+ headless route는 전부 gate 활성이다.
**reader는 코드 강제, writer는 문서 강제**라는 비대칭이 남는다 — 이는 spec §13.5.3이 의도한 설계
(gate가 writer를 강제한다)이지만, 실무적으로는 **merge 후 첫 사이클의 conductor가
`capability-route.py complete`를 호출하지 않으면 execute `--start`에서 파이프라인이 정지**한다.

완화 요인:
- 이 사이클 route는 `broker_contract_version=1`이라 gate 미적용(소급 강제 금지가 실환경에서 관측됨).
- live의 구 marker(`sequence`/`completed_at` 없음)도 gate는 `route_id`/`route_hash`만 읽으므로
  통과한다 → merge 시 파손 없음.
- conductor가 이미 이 사이클에서 marker를 손으로 쓰고 있다(dogfooding 중).

권고: report 스테이지가 **merge 후 첫 사이클의 conductor에게 marker 쓰기 의무가 실효 발생함**을
명시적으로 전달할 것. carryover §2(quick/inline 미배선)는 quick이 `broker_contract_version=None`
이라 gate 밖이므로 실효 위험이 없음을 함께 확인했다.

---

## 6. 리뷰 결론

- **무력화 없음.** 기대값이 바뀐 3건은 전부 원의도 보존을 위한 정당한 조정이며, 각각의 방어가
  다른 곳에서 살아있음을 소스로 확인했다(§2). ①④⑦은 mutation으로 진짜 가드임을 증명했다.
- **merge 전 처리 권고: F1 하나.** plan-check가 최대 blocker로 지목한 B3의 수정이 무방비다.
  §3의 fixture를 추가하면 닫힌다(작성·검증 완료 상태로 위에 첨부). 재분사 여부는 conductor 판단.
- 나머지(F2·F3·F6·F7)는 acceptance에 영향 없는 기록성 소견이며 v14 하드닝 후보다.
