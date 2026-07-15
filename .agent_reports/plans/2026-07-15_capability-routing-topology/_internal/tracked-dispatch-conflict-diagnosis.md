# 진단 — tracked 강제 구조와 분사(dispatch) 구조의 충돌면

- 날짜: 2026-07-15
- 작성: main 세션(Claude) — 본 세션 분석과 Codex 교차 진단을 통합. 두 진단의 인용 근거는 현재 소스에서 실측 검증했다.
- 대상 계약: `core/WORKFLOW.md §0/§1.1/§7`, `core/CONVENTIONS.md §1`, `core/OPERATIONS.md §5.8/§5.10`, `adapters/codex/bin/dispatch-headless.py`, `spec/stage-dispatch` PRD v9, `plans/2026-07-15_capability-routing-topology/plan.md`
- 용도: stage-dispatch PRD v10 결정과 capability-routing-topology plan 개정의 입력. 이 문서 자체는 spec을 변경하지 않는다.

## 1. 결론

tracked 강제와 분사 구조는 관할이 다른 직교 계약이다 — tracked는 **산출물 차원의 불변식**(무엇이 존재할 수 있고, 어떤 순서로, 누가 소유하는가), 분사는 **실행 차원의 토폴로지**(어느 세션이 어떤 write scope로 실행하는가). 본질적 상충은 없으나, 현재 구현에서 충돌이 나는 뿌리는 두 가지다.

1. **축 결합** (Codex 진단): tracked 여부가 intensity 선택에 직접 들어가고(`WORKFLOW.md:165` "Small localized *tracked* change → quick"), intensity 하나가 stage graph·plan 정책·dispatch·depth·assurance를 동시에 결정한다(`CONVENTIONS.md:26-33`). 그 결과 "추적할 작업인가"가 "분사할 규모인가"와 동일시된다.
2. **집행 장치의 세션 지역성** (본 세션 진단): tracked 불변식은 산출물 차원 계약인데 집행 수단은 세션 단위 메커니즘(hook, read marker, routing reminder)이다. 분사가 실행을 여러 세션으로 쪼갤 때마다 이 장치가 투영되지 않거나(marker 유실) 중복 발화한다(guard 재적용, 재라우팅).

수정 방향은 tracked 약화가 아니라 (a) 축 분리, (b) tracked 집행을 세션 스코프에서 route 스코프로 승격하는 것이다. 진행 중인 capability-routing-topology plan(4축 분리 + route record)이 이미 그 방향이며, 아래 §5의 delta 4건이 미반영 상태다.

## 2. 축 분리 프레임 (통합)

Codex의 4축과 plan.md §1의 4축을 합치면 5개 독립 축이 된다. Separability는 SD-17로, intensity/topology/worker_kind/transport 분리는 plan §1로 이미 존재하고, **Tracking을 독립 축으로 명시하는 것이 Codex 진단의 신규 기여**다.

| 축 | 결정하는 것 | 현재 상태 |
|---|---|---|
| Tracking | 산출물 필요 여부·순서·소유 capability·검증 계약 | intensity 선택에 결합됨 (`WORKFLOW.md:165`) |
| Intensity | 계획·검증에 투입할 effort/assurance | topology·dispatch까지 함께 결정 (`CONVENTIONS.md:26-33`) |
| Execution topology (+worker kind) | inline / depth-1 one-shot / conductor+depth-2 stages / worker 종류 | plan §1·§4.2에서 분리 착수 |
| Transport | headless / native subagent / detached process | plan §1에서 분리 착수 |
| Separability | 실제 독립 작업 단위 존재 여부 | SD-17로 존재, promotion signal과 통합 예정 |

## 3. 마찰면 통합 목록

각 항목에 출처(C=Codex 진단, S=본 세션 진단)와 현재 상태를 붙인다.

### F1. tracked가 dispatch 강도를 끌어올린다 (C1) — **미해소, 열린 결정**

tracked라는 사실만으로 작은 작업도 격리 worktree + depth-1 worker가 강제된다: `OPERATIONS.md:109` "Small tracked quick work → Depth-1 one-shot worker in an isolated worktree", `WORKFLOW.md:165`. 추적 필요성과 분사 규모가 동일시된다.

단, Codex 권고("명확한 독립 작업 패키지가 없으면 quick도 inline")를 그대로 채택하면 **사용자의 기존 결정과 충돌**한다 — plan §2 목표 "작은 tracked 작업은 quick depth-1 one-shot으로 메인 컨텍스트에서 분리한다", plan §4.1 "애매한 작업은 inline이 아니라 quick 쪽으로 기운다"(2026-07-13 사용자 결정, SD-18). 메인 컨텍스트 보호와 소규모 작업의 dispatch 오버헤드 절감이 quick 경계에서 맞선다. → §5 D1의 결정 사안.

### F2. worker가 main처럼 재라우팅하고 세션 스코프 게이트를 재적용한다 (C2 + S1) — **부분 반영**

Codex headless worker의 required bootstrap이 `status → prompt-signal → mode → route`를 전부 재실행한다(`dispatch-headless.py:279-282`). main이 이미 결정한 capability/intensity를 worker가 재해석할 여지, 중복 온보딩 비용, tracked gate 반복 적용이 발생한다. 세션 스코프 read marker도 같은 뿌리다: prd.md read gate는 "현재 세션" 단위인데(`WORKFLOW.md §7.0`) 분사는 세션을 조각내며, PRD v9 process log에 "Codex root/core read-marker persistence was unavailable under worker sandbox, so instruction-only fallback used"가 실측으로 남아 있다.

plan §6.2의 immutable route record가 main 측 컴파일은 도입하지만, **worker 측 소비 계약**(capability 재선택 금지, gate 통과 증거의 record 탑재)은 아직 명시되지 않았다. → D2.

### F3. artifact-guard가 worker 레벨에서 뒤늦게 발화한다 (S2) — **봉합됨, 구조 원인은 잔존**

라우팅 판단은 main에서 끝났는데 생성 순서 게이트는 파일을 만드는 worker에서 발화한다. SD-13 실측(spec-less repo에서 stage worker가 artifact-guard에 차단)이 그 사례다. conductor의 spec 전제 선보장으로 봉합했으나, 판단 시점(main)과 집행 시점(worker)의 분리라는 구조 원인은 route record에 gate 증거를 실어야 닫힌다. → D2에 흡수.

### F4. 이중 enforcement 레이어의 정합성 검사가 없다 (S3) — **미반영**

plan Phase 1의 `capabilities/topologies.json` validator는 stage별 `write_scope`를 fail-closed로 검사하지만, artifact-guard의 생성 순서 규칙과는 별개 레이어다. registry가 어떤 stage에 `spec/**` write를 허용해도 guard는 research 부재로 막을 수 있다 — 충돌이 validation 시점이 아니라 runtime에 드러난다. plan §6.1 validator 검사 목록에 guard↔write_scope 정합성 항목이 없다. → D3.

### F5. 격리된 source worktree가 전역 tracked 표면에서 다시 합류한다 (C3 + S4) — **미반영**

v8(SD-25~27)이 worker worktree를 source-only로 만들고 모든 artifact write를 primary checkout의 canonical root로 보냈다(`OPERATIONS.md:119-125`). `plans/<slug>/`는 경로 분리로 무경합이지만 `spec/`, `pipeline_state.yaml`, `pipeline_summary.md`는 공유 표면이고, §5.8 lock은 artifact write만 보호하며 merge/rebase·dirty 상태·동일 branch는 감지하지 않는다(`OPERATIONS.md:57`). `_internal/versions/v{N}` 버전 체인은 본질적으로 직렬화 지점이라, 병렬 분사가 spec에 닿는 순간 병목이 된다. 현재는 사람이 중재하는 직렬화(plan §10 "parity merge 후 rebase 전에는 수정하지 않는다")로 회피 중이다. → D4.

### F6. depth-2 모델이 code 파이프라인 중심이다 (C4) — **이미 반영됨**

명확한 stage contract는 `code-plan → code-execute → code-test → code-report`뿐이고(`OPERATIONS.md:129-131`), wrapper 레벨에서도 execution contract가 `autopilot-code`에만 주입된다(`dispatch-headless.py:257` — 본 진단에서 추가 확인한 증거). 다만 이는 plan이 정확히 고치는 대상이다: 비목표 "모든 entry capability를 네 칸에 억지로 맞추지 않는다", §5 capability별 topology 표, SD-36~38. 추가 조치 불요, wrapper의 capability별 contract 주입은 Phase 2~3 구현 범위로 확인만 하면 된다.

### F7. 트랜잭션 중심 capability의 back-jump (S5) — **이미 반영됨**

sole-update-path 때문에 stage worker가 spec drift를 스스로 고칠 수 없고 conductor→main→`autopilot-spec`으로 되올라간다. plan §5의 의도적 비대칭("spec/refine/note/ship은 reviewer/map worker만, 가짜 four-stage 금지")과 SD-36~38 single-writer transaction이 이미 답이다. 추가 조치 불요.

## 4. 이미 흡수된 선례 (참고)

충돌이 생길 때마다 어느 한쪽을 없애는 대신 경계를 다듬어 온 이력: worker worktree tracked snapshot ↔ canonical root 충돌 → v8 source-only worktree; 소규모 작업의 durable plan 강제 마찰 → quick depth-1 one-shot(SD-18); main-only hook lifecycle ↔ worker 분리 → §5.10 bootstrap boundary. 이번 delta들도 같은 패턴(경계 재정의)으로 처리한다.

## 5. 미반영 delta — PRD v10 반영 후보

### D1. Tracking 축을 dispatch escalation에서 분리 (F1) — **사용자 결정 필요**

tracked 여부는 산출물 계약(순서·소유·검증)만 결정하고, 분사 여부는 route record의 promotion/separability 신호가 결정하도록 축을 나눈다. 단 quick 경계는 두 방향이 맞선다:

- **(a) 현행 유지**: 애매하면 quick depth-1 (메인 컨텍스트 보호 우선, 2026-07-13 사용자 결정과 정합)
- **(b) Codex 권고**: 명확한 독립 작업 패키지가 있을 때만 depth-1 one-shot, 아니면 inline (dispatch 오버헤드 절감 우선)

어느 쪽이든 "tracked = 자동 escalation"은 제거하고, 선택 근거를 route record에 남긴다. 이 선택은 기존 SD-18을 개정하므로 spec update에서 옵션으로 제시하고 확정한다.

### D2. worker manifest-consumer 계약 (F2 + F3)

- worker는 capability/intensity/topology를 재선택하지 않는다. route record hash를 검증하고, 배정된 node scope만 실행하며, 증거와 결과를 반환한다.
- tracked gate 통과 증거(spec-read 여부, drift verdict, tracked/untracked mode, artifact-guard 전제 충족)를 route record 필수 필드로 운반한다. worker 측 read marker 재취득을 대체하되, worker가 실제로 prd.md를 새로 읽은 경우의 marker 기록은 유지한다.
- worker 부트스트랩의 `status/prompt-signal/mode/route` 재실행을 "재라우팅"에서 "record 검증 + 안전 확인" 전용으로 축소한다(`dispatch-headless.py` 3어댑터 동형).

### D3. guard ↔ topology 정합성 validator (F4)

`topologies.json`의 stage `write_scope`가 artifact-guard 생성 순서 규칙과 모순되지 않는지 Phase 1 validator에 fail-closed 항목으로 추가한다(예: `spec/**` write를 선언한 node는 그 capability가 spec의 sole-update-path 소유자이거나 conductor 선보장 gate를 선언해야 함). runtime에서 guard가 route-승인된 write를 차단하면 조용한 실패가 아니라 structured failure + route record 참조를 낸다.

### D4. 공유 tracked 표면의 병렬 계약 (F5)

`spec/`, `pipeline_state.yaml`, `pipeline_summary.md` 등 공유 표면의 mutation 직렬화를 명시한다 — §5.8 lock의 보호 범위 확장 또는 spec-transaction 단일 대기열. `_internal/versions/v{N}` 버전 체인의 동시 갱신 경합 규칙(선점 실패 시 재시도가 아니라 대기)을 포함한다. "소스는 격리됐지만 추적 상태는 충돌"하는 경로를 계약으로 닫는다.

## 6. 권장 라우팅 (Codex 제안, D1 결정 반영 전 기준)

- `direct`: main inline (atomic 조건 전부 충족 시)
- `quick`: depth-1 one-shot — inline 경계는 D1 결정에 따름
- `standard+`: depth-1 capability owner 분사 원칙
- depth-2: 해당 capability가 topology registry에 명시적 stage graph를 선언했고 SD-17 separable일 때만
- spec처럼 분절 파이프가 없는 capability: depth-1 owner + read-only reviewer (기존 SD-36~38)
- code: 기존 4단계 depth-2 파이프 / lab: setup·run·eval·report 고유 파이프 / note·refine: 대량 배치·독립 파일군일 때만 map/reviewer 분사

main → worker 계약: main이 의도 복원·capability/intensity/topology 결정·route record 발행을 소유하고, worker는 record 검증 → 배정 scope 실행 → 증거 반환만 한다.

## 7. 반영 경로

1. **spec update** (sole-update-path 준수): `autopilot-spec` update로 `spec/stage-dispatch/prd.md` v10 — D1(옵션 제시 후 확정), D2, D3, D4를 SD로 등재하고 acceptance criteria에 연결. v9 snapshot을 `_internal/versions/v9/`로 보존.
2. **plan 개정**: capability-routing-topology plan의 Phase 1 validator 목록(D3), route record 필수 필드(D2), 검증 matrix(D4 동시성 케이스)를 v10 결정에 맞춰 amend.
3. 소스 구현은 기존 plan Phase 순서를 따르며 이 문서는 입력으로만 쓴다. parity 선행 merge/rebase 전제는 plan §10 그대로 유지.
