당신은 stage-dispatch v13 구현 사이클의 depth-2 **execute 스테이지 워커**다 (code-execute, intensity=standard, mode=dev, model role=fast implementer). 대화 컨텍스트는 없다 — 입력은 아래 산출물 파일뿐이다.

## 입력 (순서대로 읽어라 — plan이 규범)

1. `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_stage-dispatch-v13/plan/plan.md` — **이 스테이지의 규범**. 866줄. 계획이 확정한 설계 결정을 임의로 재해석하지 마라.
2. 같은 폴더 `plan/checklist.md` — 순차 체크할 실행 항목.
3. `_internal/plan_reviews/plan_check.md` — 계획에 이미 반영된 리뷰(맥락 파악용).
4. 규범 스코프 원본: `/home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch/prd.md` §13.5 (SD-54·SD-55·SD-56). plan과 spec이 충돌하면 spec이 우선이고, 그 충돌은 `_internal/carryover.md`에 기록하라.

## plan이 실측으로 확정한 함정 3가지 (계획 §0.1 — 반드시 먼저 흡수)

- **테스트가 워커 세션에서 전부 실패하는 것은 회귀가 아니다.** broker 테스트 10건이 setUp에서 exit 76으로 죽는 원인은 `utilities/dispatch-broker.py:604`의 "워커는 broker를 준비할 수 없다" 가드다. 워커 env를 걷어내면 10/10 통과가 확인됐다. **이것을 회귀로 오인해 코드를 고치지 마라.** 계획이 지정한 우회 절차를 따르라.
- **병렬화 자체가 새 버그를 만든다.** `append_job:728`가 `Popen:768`보다 먼저 registry row를 쓰므로, 기존 dedup 분기를 그대로 병렬 구조로 옮기면 둘째 제출이 그 row를 보고 target 실행 중에 request를 `done`으로 종결하고 원 스레드가 그 terminal을 덮어쓴다 = **terminal immutability 위반**. 계획이 확정한 "검사 순서 뒤집기 + 종결 시 디스크 상태 재독"을 그대로 구현하라.
- **`ensure` 문언은 그대로 구현하지 않는다.** 호출자인 conductor는 워커라 항상 거부당하고, 비-워커에선 fail-closed여야 할 자리에 broker를 생성해 기존 방어 테스트를 깬다. 계획대로 **`status`-only**로 구현하고, spec 문언 정정은 carryover 이월로만 남겨라(spec 수정 금지).

또한 계획이 **구현 재량이 아니라 설계 결정**으로 못박은 2건을 반드시 지켜라: ① broker 검사 순서 변경 ② marker 경로의 **공유 리졸버**(빠뜨리면 쓰는 쪽과 읽는 쪽이 다른 디렉터리를 봐서 전체 dispatch가 멈춘다 — 저장소가 이미 겪고 고친 패턴).

## 구현 대상 (plan의 단계 분해를 따르라)

- SD-54: `utilities/dispatch-broker.py` — 접수/검증/dedup/claim/transition = short critical section, target 실행 생애 = 전역 락 비보유. per-request lease/status로 동일 request_id 직렬화. v12 불변식 전부 유지(atomic transition, terminal immutability, fencing/lease, spawn 전 registry row, idempotency, fenced recovery). **broker에 동시성 cap 추가 금지**(SD-40 governor 소유).
- SD-55: `utilities/capability-route.py` + `utilities/stage-dispatch-fallback.py` — 신규 compile = `broker_contract_version: 2`(tuple은 `broker_root`+`launch_authority`만, `broker_instance` 미포함), `_fallback_chain`/`_verify_fallback_chain` 버전 분기, hop 시점 live instance 해석. v1 record 소급 변환 금지·회귀 0.
- SD-56: `utilities/capability-route.py`(canonical marker 경로 `<agent-home>/.dispatch/completion/<route_id>/<node_id>.json` + 재수확 이력 보존/최신 authoritative) + `adapters/{claude,codex,opencode}/bin/dispatch-headless.py` `--start` 선행 marker gate(부재 = spawn 0건 + structured `completion-marker-missing`) + `utilities/dispatch-node.py` + `skills/autopilot-code` 스테이지 reference 문서에 conductor 의무 명문화. 3어댑터 parity. v1 record·record 미결합 launch는 gate 미적용.

## 경계 (위반 금지)

- 소스 worktree: `/home/Uihyeop/agent_setting-wt/stage-dispatch-v13` (branch stage-dispatch-v13). 소스 수정은 여기에만.
- **`capabilities/topologies.json` 수정 금지** (자기수정 digest 경합 회피).
- **`spec/` 수정 금지** — drift는 `_internal/carryover.md`에 이월.
- **worktree에 산출물 쓰기 금지** (SD-25). 당신의 산출물 write scope:
  - `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_stage-dispatch-v13/dev_logs/**`
  - 같은 폴더 `plan/checklist.md`(체크 갱신), `_internal/dev_reviews/**`, `_internal/carryover.md`
- **live broker 절대 불가침**: `/home/Uihyeop/agent_setting/.dispatch/broker` (brk-d25176b21a134c10a6f6d1608ffc3af4) shutdown·restart·변조 금지. 이 브로커는 **지금 이 사이클을 실행 중**이다. fixture는 반드시 임시 `--root` 전용 broker만 스폰하라. 실제 claude/codex/opencode 세션 스폰·signal 금지.
- 커밋: branch에 커밋만 하라. merge/push 금지(main이 수확).

## 검증 (execute 단계의 self-check)

계획이 지정한 fixture 10종과 기존 portable guards 회귀 스위트를 실행해 자기 주장을 뒷받침하라. 단 **독립 재검증은 다음 test 스테이지의 몫**이므로, 당신은 통과/실패를 **정직하게** 기록하면 된다 — 실패를 숨기거나 테스트를 무력화하지 마라.

## 산출물 계약

- `dev_logs/`: 단계별 실행 로그(무엇을 왜 어떻게 바꿨는지, 실측 커맨드와 결과 포함). test 스테이지가 **대화 없이** 당신의 주장 전부를 재실행할 수 있도록 커맨드를 그대로 담아라 (§0.5 완결성 의무).
- `plan/checklist.md`: 완료 항목 갱신.
- 미해결·이월 사항은 `_internal/carryover.md`.

언어: 한국어. 코드 식별자는 원형 유지.
