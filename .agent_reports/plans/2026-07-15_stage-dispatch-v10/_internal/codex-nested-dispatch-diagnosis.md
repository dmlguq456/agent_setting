# 진단 — Codex conductor의 중첩 depth-2 headless 분사 실패

- 날짜: 2026-07-15
- 관측 사이클: `plans/2026-07-15_stage-dispatch-v10/` (stage-dispatch PRD v10 SD-44~47 구현, depth-1 Codex conductor `gpt-5.6-sol`, intensity=strong, route `rt-fda0402b695fb63c`)
- 용도: **별도 세션의 해결 입력.** 이 문서는 spec을 변경하지 않는다. 반영은 진단 검증 → 필요 시 `autopilot-spec` update(stage-dispatch v11 후보) → 구현 순.
- 관련 계약: SD-34(inline enum), SD-19(fallback 사슬), SD-16(상호보완 크로스 하네스), SD-14b(worktree-local registry 갭), SD-22(hard eligibility), SD-38(adapter runtime 경계), SD-43(sibling 독립 검증)

## 1. 사실 (실측, 2026-07-15)

1. depth-1 Codex conductor는 code-plan stage를 **depth-2 headless로 총 6회 시도**했다(최초 `stage-dispatch-v10-code-plan` + 재시도 `-r2`~`-r6`). route_id/hash/node/write_scope/completion_gate 메타데이터는 전부 정확했다.
2. **6회 전부 실패**: `codex-headless-network-operation-not-permitted` — conductor 자신이 `codex exec` workspace sandbox 안에서 돌 때, 중첩 `codex exec` 자식의 network가 `Operation not permitted`로 차단된다. 초기에는 runtime home read-only, isolated runtime으로 thread 기동까지는 성공했으나 headless response websocket/API에서 차단.
3. conductor는 **계약된 fallback을 정확히 밟았다**: SD-34 inline enum `runtime-unavailable` + evidence를 `_internal/metrics.md`에 기록, structured failure JSON(`failed-code-plan-{network,runtime}.json`)에 route 참조 보존, 이후 inline capability-owner로 계속. 무단 inline("예외 차용" 위반 패턴)이 아니다.

## 2. 이슈 3건 (해결 대상)

### I1. Codex 중첩 spawn 불가가 eligibility에 반영되지 않음 — 구조 한계

- `preflight.sh headless --check`는 **main 세션에서** ok였으나, 같은 check가 통과한 환경이라도 **conductor 세션 내부(중첩 sandbox)에서는 spawn이 막힌다**. check가 "중첩 컨텍스트에서의 자식 launch 가능성"을 검사하지 않는 갭.
- 결과: Codex conductor를 선택하면 standard+ stage-dispatch가 사실상 항상 inline fallback으로 하강한다. v9 구현 사이클(`capability-routing-topology-impl`, 동일 codex conductor)도 전역 jobs.log에 depth-2 row가 없어 같은 경로였을 것으로 추정 — **재발 2회째**.
- 수정 방향 후보: SD-22 우선순위 2단계(hard eligibility)에 "nested child-spawn capability"를 probe 항목으로 추가 — standard+ conductor 후보 선정 시 자식 launch 가능 여부가 하네스 선택을 결정해야 함. main(depth-0)이 conductor 하네스를 고를 때 이 신호를 소비.

### I2. 실패 시도 row가 전역 registry에 없음 — Fleet 불가시 (원인 확정)

- 6회 시도 row가 전역 `.dispatch/jobs.log`가 아니라 cycle `_internal/jobs.log`에 기록됐다. Fleet에는 스테이지 시도·실패가 전혀 보이지 않았고, 전역 registry에는 depth-1 `stage-dispatch-v10` conductor row만 존재한다.
- **판정 = 의도적 `--jobs` 로컬 지정.** transcript에서 최초 dry-run부터 실제 start, `dispatch-wait`, `harvest`, `-r2`~`-r6` 재시도까지 모두 `--jobs /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-15_stage-dispatch-v10/_internal/jobs.log`를 명시했다. 명시 `--jobs`가 registry 선택 우선순위 1위라 전역 기본값은 한 번도 선택되지 않았다.
- **sandbox 쓰기 불가가 직접 원인이라는 증거는 없다.** 전역 registry 쓰기를 시도했다가 실패한 기록이나 permission error가 없고, 최초 dry-run 이전부터 로컬 경로를 선택했다. 따라서 “전역 쓰기 실패 후 우회”로 판정할 수 없다. 전역 경로가 중첩 sandbox에서 실제 writable인지 여부는 I1 probe의 별도 검증 항목이다.
- **SD-14b와의 관계**: 과거 SD-14b의 `AGENT_HOME` fallback/parent-child registry 발견 불일치가 재발한 것은 아니다. 이번 cycle 경로는 worktree snapshot이 아니라 main canonical artifact root 아래이며 parent의 wait/harvest도 같은 명시 경로를 일관되게 사용했다. 다만 explicit override가 Fleet의 authoritative 전역 registry를 우회할 수 있다는 더 일반적인 **registry authority 갭**이 드러났다.
- **확정 수정 방향**: 등록형 model dispatch의 모든 launch attempt(실패 포함)는 canonical global registry에 반드시 먼저 기록한다. cycle-local registry는 선택적 audit mirror일 수 있으나 단독 authoritative sink가 될 수 없다. noncanonical `--jobs`는 global dual-write/동일 attempt identity를 강제하거나 launch 전 fail-closed하고, legacy local row는 harvest에서 idempotent하게 global로 reconcile한다.

### I3. fallback 사슬에 cross-harness 자식 단계가 없음

- conductor는 codex 자식 5회 실패 후 **claude harness 자식을 시도하지 않고** 바로 inline으로 내려갔다.
- SD-19(quick fallback: headless→native subagent→inline)와 SD-16(사용량·특성 상호보완 크로스 하네스)의 취지대로면 standard+ stage fallback에도 "타 하네스 headless 자식" 단계가 있어야 자연스럽다. 현행 계약에는 이 단계가 명시돼 있지 않다(계약 갭이지 위반 아님).
- 수정 방향 후보: standard+ stage 분사 fallback 사슬을 `same-harness headless → cross-harness headless(SD-16 eligibility 통과 시) → native subagent(가능 시) → inline(enum+기록)`으로 명문화.

## 3. 즉시 함의 (해결 전 운영 지침)

- standard+ full stage-dispatch가 필요한 사이클은 **conductor를 Claude로** 선택하거나, main이 conductor 분사 전에 중첩 spawn 가능성을 확인한다.
- Codex conductor는 당분간 "inline fallback을 감수하는 deep-orchestration 단일 세션"으로 간주 — assurance 손실은 main 측 독립 검증(family 다양성)으로 보완.

## 4. 증거 경로

- `plans/2026-07-15_stage-dispatch-v10/_internal/metrics.md` — inline exception `runtime-unavailable` + evidence
- `plans/2026-07-15_stage-dispatch-v10/_internal/failed-code-plan-{network,runtime}.json` — structured failure + route 참조
- `plans/2026-07-15_stage-dispatch-v10/_internal/jobs.log` — depth-2 시도 6 row (최초 1 + 재시도 5, route 메타 포함)
- `.dispatch/logs/stage-dispatch-v10.codex.jsonl` — 최초 dry-run부터 `-r6`까지 동일 cycle-local `--jobs`를 명시한 conductor transcript
- `.dispatch/jobs.log` — 전역 registry에는 depth-1 conductor row만 존재
