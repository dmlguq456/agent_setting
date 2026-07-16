# plan-check — stage-dispatch v13 (standard intensity)

- 대상: `plan/plan.md`, `plan/checklist.md`
- 규범: `spec/stage-dispatch/prd.md §13.5` (SD-54·55·56) + §13.4 불변식 + §14 경계
- 리뷰 방식: **독립 리뷰어**(품질관리팀 plan-review, deep reviewer role)에게 계획·spec·소스를 넘겨 작성 관점과 분리된 검토를 수행. 리뷰어에게 "동의하지 말고 능동적으로 결함을 찾으라"고 지시하고, 계획의 산문이 아니라 **실제 코드 대조**를 요구했다.
- 초기 판정: **FAIL** — blocker 4, major 4, minor 5
- 반영 후 판정: **PASS-WITH-CHANGES** — blocker 4/4 + major 4/4 + minor 5/5 전부 계획에 반영. 개정된 계획으로 execute 착수 가능.

리뷰어가 지적한 blocker 중 **3건은 계획 작성자(plan 스테이지)가 직접 실측 재검증**했다 — 리뷰어의 주장을 그대로 수용하지 않고 소스에서 확인한 뒤 반영했다.

---

## Blocker (4/4 반영)

### B1 — v2 hop이 `submit_broker`의 env 상속으로 전멸 · **반영**

**지적**: 계획 §2.3은 `resolve_live_instance`에서만 `AGENT_DISPATCH_BROKER_INSTANCE`를 제거했으나, `stage-dispatch-fallback.py:142-149` `submit_broker`의 `subprocess.run`에는 **`env=` 인자가 없어** 낡은 env를 상속한다. 그리고 `dispatch-broker.py:749` `meta = broker_status(...)`는 `serve` 분기 뒤 fall-through라 **`request` 서브커맨드에서도 실행**되어 `broker_status:160-162`가 낡은 env를 보고 `broker-instance-mismatch` → exit 76. SD-55 acceptance ① 달성 불가.

**작성자 실측 재검증** (수용 전 직접 확인):
```
738  if args.command == "serve": ... return server.serve()
749  meta = broker_status(root, jobs, args.stale_seconds)     ← fall-through 확인
750  if args.command == "request":
```
→ 지적이 **정확**하다. live 해석만 고쳐도 제출 단계에서 죽는다.

**반영**: §2.3을 "두 지점 모두"로 개정하고 공유 헬퍼 `broker_env(contract)`를 도입 — `resolve_live_instance`(§2.5a)와 `submit_broker`(§2.5e)가 공유. v1은 `dict(os.environ)` 그대로여서 회귀 0. §7 리스크 표에도 "한쪽만 하면 `:749` fall-through에서 죽는다"로 명시. checklist에 ★항목 2개 추가.

### B2 — `ensure`-fallback이 fail-closed 테스트를 파괴 (자기 모순) · **반영**

**지적**: §2.2가 "client는 broker를 기동하지 않고 조회만 한다"고 쓰면서 §2.5(a) 코드는 `for command in ("status", "ensure")`로 `ensure`를 부른다. `ensure`는 워커에서만 거부될 뿐(`:604`) **비-워커에서는 실제로 broker를 Popen한다**(`:665-673`). 구체적 파괴: `dispatch_broker.test.py:396` `test_missing_broker_fails_closed`는 존재하지 않는 broker root로 fail-closed를 단언하는데, v2 record + `TESTENV`(워커 env 제거) 조합에서 **ensure가 성공해 없어야 할 broker를 띄운다** → v12 AC3(§13.4.4-3)과 SD-55 acceptance ③ 동시 회귀.

**판단**: 지적이 정확하고, 리뷰어의 대안 논거가 원안보다 **강하다** — 계약상 호출자는 워커이므로 ensure-fallback은 실제 호출자에게 **아무 능력도 추가하지 않으면서** 금지된 컨텍스트에서만 부작용을 만든다. 순수한 손실이다.

**반영**: §2.2를 **status-only**로 개정(제목 포함). "ensure를 넣지 말 것" + 두 가지 이유를 명시. §2.5(a)를 status 단일 호출로 재작성하고 docstring에 근거를 남김. §7 리스크 표 + §8 이월 문구도 "status-first" → "status-only"로 정정. fixture ⑩에 "broker가 생기지 않았음(`broker.json` 부재)" 단언을 넣어 이 결정의 수호자로 삼음.

### B3 — terminal immutability 보존 주장이 거짓 (병렬화 신규 경합) · **반영** ★가장 중대

**지적**: §1.5 표의 "terminal immutability: `transition:417-418`이 terminal에서 예외"는 거짓이다. `transition:417`은 **인자로 받은 in-memory state**를 검사한다. v12는 전역 락이 "in-memory == on-disk"를 보장해 안전했으나 병렬화가 그 전제를 깬다:
1. Thread 1이 running으로 12분 target 실행 중(락 해제 상태)
2. Thread 2가 동일 request 재제출 → `:471` `registry_attempt`가 **row를 찾는다**(SD-52의 "spawn 전 registry row" 때문에 반드시)
3. → `recovered_response` → `transition(state,"done")` → **target이 도는데 request가 조기 종결**
4. Thread 1이 (D)에서 stale in-memory state로 terminal 전이 → `:417` 통과 → **on-disk terminal 덮어쓰기** = §13.4.2 위반

추가로 `:471` reconcile이 `:475` inflight보다 **먼저**라 SD-54가 §13.5.1에서 명시적으로 요구한 "claimed/running 재제출 = `broker-request-inflight` 거부"에 **도달 불가**. 계획 §1.3(e)의 "dedup 분기를 **로직 변경 없이** 이동한다"가 정확히 이 결함의 원인이다.

**작성자 실측 재검증**:
```
728  append_job(jobs, args)        ← registry row
768  subprocess.Popen(...)         ← spawn
```
→ row가 spawn보다 **앞**임을 확인. Thread 2는 반드시 row를 찾는다. 지적이 **정확하며 가장 중대**하다. reconcile-before-inflight 순서가 전역 락에 의존한 v12 산물이라는 진단도 옳다.

**반영**: §1.3(e)를 전면 재작성 — 4단계 시나리오 + `append_job:728`/`Popen:768` 실측 인용 + 올바른 순서의 코드 블록(inflight를 reconcile 앞으로, reconcile은 fenced recovery 전용) + (D)의 **on-disk 재독** 패턴. §1.5 표의 terminal immutability 행을 "in-memory 검사만으로는 불충분 — 세 가지 결합(per-request 락 + (D) 재독 + 갱신 스레드의 락 내 terminal 확인)"으로 정정. §7 리스크 표 최상단에 신규 행 추가. checklist에 ★항목 2개.

부수 효과: fixture ②의 단언도 함께 정정(아래 M-②).

### B4 — `AGENT_HOME` 무검증 해석이 marker 경로를 분열 · **반영**

**지적**: §3.2의 `Path(os.environ.get("AGENT_HOME", ROOT))`에서 `capability-route.py:7`의 `ROOT = parents[1]`은 **worktree**다. 저장소가 이미 겪고 고친 버그 패턴이며 `adapters/claude/bin/dispatch-headless.py:546-553` 주석이 그대로 경고한다("falling straight back to ROOT (=worktree) **split the registry**… SD-14b② registry gap"). writer(worktree의 conductor)와 reader(agent-home 기준 gate)가 갈리면 **모든 record-bound `--start`가 `completion-marker-missing`으로 fail-closed** → 전 fabric dispatch 중단 + worktree 산출물 금지(SD-25) 위반. 또한 gate를 `:607`에 넣는데 `agent_home`은 `:672`에서야 계산되어 scope에 없다.

**작성자 실측 재검증**: `sed -n '544,560p' adapters/claude/bin/dispatch-headless.py` — 주석 원문과 `resolve_agent_home`의 `core/CORE.md` 검증 선호 순서 확인. 지적이 **정확**하다.

**반영**: 신규 §3.2.1 추가 — 주석 실측 인용 + `utilities/dispatch_contract.py`에 검증형 `resolve_agent_home()` 공유 헬퍼를 두고 writer/reader가 **같은 헬퍼**를 쓰도록 규정. `completion_dir`을 공유 헬퍼 기반으로 변경. gate 시그니처를 `completion_marker_gate(route_file, route_node, action, agent_home)`로 바꿔 **agent_home을 명시 인자**로(함수 내 env 재독 금지). 호출부는 `main:615`에서 `args.agent_home = resolve_agent_home()`을 세팅하고 `:672`는 재사용하도록 정리. §7 리스크 표에 신규 행. checklist에 ★항목 2개.

---

## Major (4/4 반영)

| # | 지적 | 반영 |
|---|---|---|
| **M1** | `:404` `test_tampered_inherited_instance_fails_closed`가 §1.6에서 누락. v2 record가 되면 §2.3이 의도적으로 env를 무시해 이 방어가 무효화된다. **B1 수정 전엔 우연히 통과하고 B1을 고치는 순간 실패로 전환** — 최악의 진단 순서 | §1.6을 (a)/(b)로 분리하고 (b)에 이 테스트를 추가. **v1 record로 고정**하는 처방 + "타이밍이 위험하다"는 경고 명시. checklist ★항목 |
| **M2** | fixture ①이 회귀를 보장하지 못한다(거짓 음성). "`done-slow.marker` 부재 확인"은 A가 실행에 진입했음을 증명하지 않으므로, `fast`가 A의 accept보다 앞서면 **전역 락이 되살아나도 단언이 통과**한다 | §4.2①에 **배리어** 도입 — 가짜 adapter가 sleep **전에** `started-<slug>.marker`를 쓰고, `fast` 제출 전에 그것을 폴링. "배리어가 A의 락 보유를 보장하므로 회귀가 결정론적으로 잡힌다"로 논거 교체. checklist ★항목 3개 |
| **M3** | fixture ⑦의 spawn-0 주장은 참이나 단언 `reason`에 **도달하지 못한다**. `validate_nested_eligibility`가 `:652`에서 먼저 돌아 exit 69(`nested-eligibility-evidence-missing`). §4.2⑦ 예시 커맨드에 해당 인자가 없다. 또 gate가 `validate_route_record` 끝이라 `worker-route-guard.py:596-602`를 먼저 통과해야 함 | §4.2⑦ 커맨드에 `--parent-harness/--parent-transport/--parent-sandbox/--nested-eligibility/--eligibility-source/--launch-authority` 추가. §3.3 근거 블록에 **선행 게이트 2종의 순서**(eligibility → worker-route-guard → completion gate)를 명시. checklist ★항목 |
| **M4** | **SD-55 acceptance ③을 커버하는 fixture가 없다.** §2.7 표는 §2.5(a)로 매핑하지만 ①~⑨ 어디에도 v2 `broker-unavailable` 경로가 없다. `resolve_live_instance`가 `""`를 반환하는 경로는 전량 신규 코드이며 미검증 | **fixture ⑩ 신설** — §4.1 배치표 + §4.2에 상세 설계. v2 record + 없는/죽은 broker root → `reason=broker-unavailable` + `child_spawned=0` + row 0건 + **broker 미생성**. checklist ★항목 |

---

## Minor (5/5 반영)

| # | 지적 | 반영 |
|---|---|---|
| m1 | §2.5(b) "`--broker-root` 미지정 시" 판정이 구현 불가 — `:186-189`가 이미 기본값을 대입한 뒤. 또 `resolve_live_instance`가 루프 밖인데 `row["broker_root"]` 대조는 루프 안이라 순서가 뒤집힘 | §2.5를 (a)~(g)로 재구성. `p.parse_args()` 직후 `explicit_broker_root` 포착(b), v2 해석 전체를 **후보 루프 안**으로 이동(d) |
| m2 | SD-56 쓰기 의무의 부분 누락 — §13.5.3은 "conductor **또는 quick/inline의 capability owner**"인데 §3.5는 standard+ 파이프라인만 배선 | §8 이월 #2로 신설 — "의도된 축소이며 v14에서 quick/inline 문서 표면에 확장할 후보"로 정직하게 표기 |
| m3 | §2.2의 "행동상 동일"은 엄밀히 틀림 — `status`는 ping(`:731-737`)까지 하지만 `ensure`의 healthy 경로(`:607-608`)는 안 함 | §2.2 문구를 "관측 결과는 같고 `status`는 ping까지 더해 **더 보수적**(= fail-closed 방향이라 안전)"으로 정정 |
| m4 | renewer 스레드 수명 — `renewer.stop()`이 join을 포함하는지 불명 | §1.3(e)에 "daemon 스레드 + `stop_event.set()` 후 `join(timeout)`" 명시. checklist에도 반영 |
| m5 | §3.4 `dispatch-node.py` 관측 라인은 어떤 acceptance도 요구하지 않음 — spec이 파일을 스코프에 넣었을 뿐 | §3.4 도입부를 "어떤 acceptance도 요구하지 않는 **관측 편의**이며 §13.5.4가 파일을 목록에 넣었다는 이유만으로 정당화되지 않는다… 시간이 없으면 **생략 가능**"으로 정직하게 재작성. checklist에도 "생략 가능" 표기 |

---

## 리뷰어가 CORRECT로 확인한 항목 (커버리지)

**스코프 준수 4/4 통과** — broker 동시성 cap 없음(§1.4가 명시 금지, `sock.listen(16)`을 cap으로 오인하지 않음), `spec/` 미수정, `capabilities/topologies.json` 미수정, live broker 미접촉(모든 fixture가 `--root <tempdir>/broker`).

**코드 인용 전수 spot-check — 오류 0건.** `dispatch-broker.py`(`:444-523`, `:510`, `:385`, `:417-418`, `:426-442`, `:465-490`, `:475-476`, `:498`, `:70-79`, `:39`, `:33`, `:160-162`, `:235-248`, `:243`, `:285-290`, `:604`, `:633-638`, `:607-608`, `:573`, `:317-324`, `:29-31`, `:665-673`, `:731-737`), `capability-route.py`(`:18`, `:77-95`, `:84-89`, `:97-107`, `:103`, `:171`, `:191`, `:194-201`, `:233-240`, `:24-26`), `stage-dispatch-fallback.py`(`:190-191`, `:118-119`, `:68-81`, `:198`), `dispatch-headless.py`(`:587-607`, `:660`, `:669`, `:674`, `:682`, exit 65), `dispatch_broker.test.py`(`:43`, `:269`, `:278`, `:322`, `:356`, `:396`, `:404`), `dispatch-node.py`(`:12`, `:14`, `:3`), `core/ADAPTATION.md:16`, `dev-pipeline.md:24`, 3부 미러 md5 동일.

**설계 판단 타당 확인**: `dispatch_contract.py`가 3어댑터 gate의 올바른 공유 지점(3어댑터 동일 import 블록 실측) / write_once 충돌 해법 건전(이력=O_EXCL, canonical=atomic replace 역할 분리 + evidence sha256 비교로 타임스탬프 문제 흡수) / `_verify_fallback_chain` bool→version 3상태 진단(현행 `:191`이 v2에서 `False`를 넘겨 `:103` 단락 평가로 broker_root 검사까지 사라짐 — "좋은 발견") / `validate_route:243` 버전 분기 필요성 / route_hash 소급 회귀 0 논거 / request_locks GC 금지 논거("정확하고 미묘") / `renew_lease`가 `transition()`을 쓰지 않는 이유 / lease 만료 → 중복 launch 진단("이 계획의 최대 강점") / §0.1 워커 env 진단 및 "회귀로 오인 말 것" 경고 / `depends_on` 실측(`plan: []`, `execute: ['plan']`, …) / §6 실행 순서 근거.

---

## acceptance 커버리지 — 반영 후

| acceptance | fixture | 반영 후 판정 |
|---|---|---|
| §13.5.1 ① 느린 target 중 2nd request 독립 완주 | ① | ✔ 배리어 추가로 결정론화(M2) |
| §13.5.1 ② 동시·순차 재제출 = attempt/target 1개 | ② | ✔ B3 수정 + 정확한 `broker-request-inflight` 단언으로 조기-terminal defect 탐지 가능 |
| §13.5.1 ③ 병렬 하 fenced recovery 중복 launch 0 | ③ | ✔ |
| §13.5.2 ① rollover 후 v2 ordinal-1 성공·하강 0·hash 불변 | ④ | ✔ (B1 수정이 선행 조건). "hash 불변"이 record 파일 불변에서 자명해 동어반복이라는 지적은 수용 — 그래도 회귀 신호로서 유지 |
| §13.5.2 ② v1 record 회귀 0 | ⑤ + `:404`(v1 고정) | ✔ M1 반영 |
| §13.5.2 ③ `broker-unavailable` fail-closed | **⑩ (신설)** | ✔ M4 반영 — 초안 미커버 |
| §13.5.3 ① canonical marker 생성·필드 일치 | ⑥ | ✔ (B4 수정이 선행 조건) |
| §13.5.3 ② 선행 marker 부재 → spawn 0 + structured failure | ⑦ | ✔ M3 반영으로 reason 도달 가능 |
| §13.5.3 ③ marker 부재를 실패로 읽는 소비자 0 | ⑧ | ✔ ⑧(c) 정적 단언이 "무주장" 원칙의 수호자 |
| §13.5.3 ④ 재수확 이력 보존 + 최신 authoritative | ⑨ | ✔ |
| §13.5.3 ⑤ v1·record 미결합 gate 미적용 | ⑦⑧ | ✔ |

**미커버 0건.** 초안의 미커버 1건(SD-55 ③)과 증명 불충분 3건(SD-54 ①·②, SD-56 ②)이 모두 닫혔다.

---

## 최종 판정

**PASS-WITH-CHANGES → execute 착수 가능.**

리뷰가 계획의 세 가지 실질적 결함을 잡았다: (1) 병렬화가 도입하는 조기-terminal/덮어쓰기 경합(B3) — 계획이 "로직 변경 없이 이동"이라 쓴 바로 그 지점이 원인이었다. (2) env 정제 지점 누락(B1)과 `ensure` 부작용(B2) — SD-55의 두 축을 모두 무력화했을 것. (3) marker 경로의 registry-split 재발(B4). 어느 것도 execute 재량으로 처리할 수 없는 **설계 변경**이므로, 계획 단계에서 닫은 것이 맞다.

계획의 강점도 확인됐다 — 코드 인용 정확도 100%, lease 만료 진단, 워커 env 함정 경고는 유지된다.

**execute 유의**: B3의 `:471-476` 순서 변경과 B4의 공유 `resolve_agent_home()`은 **설계 결정**이지 구현 재량이 아니다. 계획 §1.3(e)·§3.2.1을 그대로 따르라.
