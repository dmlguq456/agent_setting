당신은 stage-dispatch v13 구현 사이클의 depth-2 **plan 스테이지 워커**다 (code-plan, intensity=standard, mode=dev, model role=deep maker). conductor와의 소통은 산출물 파일뿐이다 — 대화 컨텍스트는 없다.

## 먼저 읽을 것 (spec-read 게이트)

1. `/home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch/prd.md` **§13.5 (v13, SD-54·SD-55·SD-56)** = 이번 사이클의 유일한 규범 스코프. `§13.4`(v12 broker 계약)와 `§14`(의미↔규칙 경계, v13 추가분) 함께.
2. route record: `/home/Uihyeop/agent_setting/.dispatch/logs/stage-dispatch-v13.route.json` (rt-5fd84b9bcf8a799c).
3. 근거 실측: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-15_fleet-v10-process-view/final_report.md` §5 + 같은 폴더 `_internal/carryover.md` §1.

## 소스·산출물 경계

- 소스 worktree: `/home/Uihyeop/agent_setting-wt/stage-dispatch-v13` (branch stage-dispatch-v13, main 98308ec4 기점). **읽기만 하라** — plan 스테이지는 소스를 수정하지 않는다.
- 당신의 write scope는 정확히 두 곳이다 (route record 노드 `plan`의 write_scope):
  - `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_stage-dispatch-v13/plan/**` → `plan.md`, `checklist.md`
  - `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_stage-dispatch-v13/_internal/plan_reviews/**` → plan-check 결과
- worktree에 산출물 쓰기 금지 (SD-25). `spec/` 수정 금지 — drift 발견 시 `_internal/carryover.md`에 이월만.
- `capabilities/topologies.json` 수정 계획 금지 (자기수정 digest 경합 회피).

## 계획할 구현 스코프

### SD-54 — broker HOL blocking 해소 (`utilities/dispatch-broker.py`)
`process_request`가 `request_guard`를 쥔 채 `subprocess.run`(대략 line 510)하는 구조를 분리한다. 접수·schema/route 검증·dedup·claim·state transition = short critical section, target adapter process의 **실행 생애는 전역 락 비보유**. 동일 request_id 직렬화는 per-request state(lease/status)로 — claimed/running 재제출은 `broker-request-inflight` 거부(현행 lease 기반 로직 재사용 가능), terminal 재제출은 기존 상태 반환.
- v12 불변식 전부 유지: atomic transition, terminal immutability, PID/start-ticks+heartbeat/lease+fencing, spawn 전 canonical registry row, idempotency(AC4), fenced recovery(AC5).
- **broker에 동시성 cap 추가 금지** — cap은 SD-40 governor 소유(이중 상한 금지).

### SD-55 — record↔broker-identity 결합 해제 (`utilities/capability-route.py`, `utilities/stage-dispatch-fallback.py`)
- 신규 compile = `broker_contract_version: 2`: dispatch_evidence tuple은 `broker_root`(+`launch_authority=ancestor-broker`)만 필수이고 `broker_instance`를 **포함하지 않는다**. `_fallback_chain`/`_verify_fallback_chain`의 instance 요구를 버전 분기하라.
- hop 시점 해석: `stage-dispatch-fallback.py`가 request 제출 직전 record의 `broker_root`에 `dispatch-broker.py ensure`를 idempotent 실행해 live instance를 확보하고 envelope에 넣는다. broker의 envelope↔현재 instance 대조는 불변.
- v1 record는 소급 변환 없이 기존 검증·열화 거동 그대로(회귀 0). ensure 실패 시 v12 계약대로 structured `broker-unavailable` fail-closed.

### SD-56 — completion 통과 marker 배선 (`utilities/capability-route.py`, `adapters/{claude,codex,opencode}/bin/dispatch-headless.py`, `utilities/dispatch-node.py`, `skills/autopilot-code` 스테이지 reference 문서)
- `complete` 서브커맨드의 canonical 출력 경로: `<agent-home>/.dispatch/completion/<route_id>/<node_id>.json`. 현행 구현은 `<evidence>.completion.json`에 `write_once`로 쓴다(carryover §1 실측) — 재수확 시 이전 marker **이력 보존 + 최신 authoritative**가 되도록 write_once 충돌 해법을 설계하라.
- marker 필드: route_id/route_hash/registry_digest/node_id/completion_gate/evidence sha256.
- wrapper 3종 `--start`: route-file 결합 시 해당 노드 `depends_on` 전 노드의 marker 존재 검사 → 부재 시 **spawn 0건 + structured `completion-marker-missing` failure**. v1 record·record 미결합 launch는 gate 미적용(소급 강제 금지). 3어댑터 parity.
- conductor 의무(스테이지 수확 판정 직후 `complete` 호출)를 `skills/autopilot-code`의 해당 reference 문서에 명문화.

## 계획에 반드시 포함할 검증 설계

deterministic fixture 9종 — 각각 어느 테스트 파일에 어떤 형태로 들어갈지 지정하라:
① slow-target 병렬(둘째 request가 첫 target 생애와 독립 완주) ② request_id 동시·순차 idempotency(attempt/target 정확히 1) ③ claim 직후·spawn 직후 crash fenced recovery(중복 launch 0) ④ broker rollover 후 v2 record ordinal-1 hop 성공(fallback 하강 0, record hash 불변) ⑤ v1 record 기존 거동 회귀 0 ⑥ marker 생성·필드가 record와 일치 ⑦ 선행 marker 부재 시 gate fail-closed ⑧ marker 부재를 실패로 읽는 소비자 0(negative) ⑨ 재수확 이력 보존 + 최신 authoritative.

기존 portable guards 스위트 전체 회귀도 계획에 포함(v12 기준 359 통과 — 실행 방법·위치를 repo에서 직접 탐색해 확정하라; `utilities/*.test.py`·`*.test.sh` 인접 및 tests/ 후보).

**fixture 전용 broker만 스폰**(임시 `--root`). live broker(`/home/Uihyeop/agent_setting/.dispatch/broker`, brk-d25176b21a134c10a6f6d1608ffc3af4)의 shutdown·restart·변조 절대 금지 — 롤오버는 merge 후 depth-0 main이 수행. 실제 claude/codex/opencode 세션 스폰·signal 금지.

## 산출물 계약

- `plan/plan.md`: SD-54/55/56 각각의 단계 분해(파일·함수 단위 착수점 명시, 현행 코드 실측 인용 — 줄 번호 포함), 불변식 보존 논거, fixture 9종 설계, 회귀 스위트 실행 커맨드, 리스크·롤백. 다음 스테이지(execute)가 **대화 없이** 완주 가능하도록 컨텍스트를 완전히 담아라 (§0.5 완결성 의무).
- `plan/checklist.md`: execute가 순차 체크할 실행 항목.
- `_internal/plan_reviews/plan_check.md`: **독립 리뷰**(plan-check) — 계획을 작성한 관점과 분리된 검토를 수행해 스코프 이탈·불변식 위반·검증 공백을 지적하고, 반영 결과를 기록하라. standard intensity 기준.

언어: 한국어. 코드 식별자는 원형 유지.
