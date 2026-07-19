# Cycle metrics & dispatch-degradation evidence — spec-gate-multi-spec

route: `rt-603bfc57313d9266` (dispatch_contract_version 2, compile 시점 source_commit=4272eba8)

## Conductor attempts

| attempt | 결과 | 비고 |
|---|---|---|
| r1 (`spec-gate-multi-spec`, opus, 07:02Z) | preflight·spec-significance·plan 분사까지 정상 후 **SD-14 위반 사망** — dispatch-wait를 배경 대기로 걸고 턴 종료(`claude -p` = 턴 종료 시 프로세스 종료). plan 워커는 고아 생존 | depth-0가 pid 감시로 감지, 행 `done,note=dead-turn-ended-before-harvest` 수동 마감. 프롬프트에 one-shot 폴링 지시가 있었음 → 지침-단독 재발 방지 불충분의 실증. SD-64 등재 근거 |
| r2 (`spec-gate-multi-spec-r2`, opus, 07:13Z) | SD-14 완주(전경 폴링) — plan 수확·marker, execute 분사·수확·marker 후 **BLOCKED 반환** | blocker = worker-route-guard `route-source-commit-mismatch` |

## Stage transport / fallback 기록 (SD-50)

- `plan` 노드: same-harness headless (hop 1, ancestor-broker) — 정상. 단 r1이 dispatch-node.py의 eligibility 증거 미전달로 첫 시도 `nested-eligibility-evidence-missing` fail-closed, record 기록 증거를 passthrough 인자로 수동 전달해 해소(도구 갭 — v15 구현 흡수 등재).
- `execute` 노드: same-harness headless — 정상 (커밋 395a797c, 8496bf90).
- `test` 노드 fallback chain:
  1. same-harness headless (claude): **failed** — `route-source-commit-mismatch` (guard가 HEAD==source_commit 정확 일치 강제 vs execute의 계약상 커밋. 구조 모순, SD-65 등재 근거)
  2. cross-harness headless (codex): **failed** — 동일 failure class (어댑터 무관 확인)
  3. **native-subagent (claude Agent tool, 품질관리팀/test): 채택** — Fleet 가시성 열화(등록 행 없음, 이 문서가 대체 기록). depth-0이 직접 발주(대체 conductor 재분사도 동일 가드에 막히므로).
  4. inline: 미사용.
- `report` 노드: headless 후보 동일 사유 fail-closed 예상 → transport 목록상 다음 후보인 **inline-fallback** 사용 예정, inline reason = runtime-unavailable(가드 fail-closed) — 본 문서가 기록 의무 이행.

## 파생 조치

- stage-dispatch PRD v15 minor #1 (`a53813cd`): SD-64(conductor 고아 감지·재개), SD-65(post-execute source_commit 계보 검증), dispatch-node 증거 전달 갭 — 본 사이클 실측을 근거로 등재.
- fleet PRD v10 minor #4 (`1468076f`): F-31 분사 세션 rolling 요약 관측 — 본 사이클의 관측 공백 경험(턴 중간 로그 불가시)이 배경 근거 중 하나.
- broker 정비: 분사 전 ensure가 구현-해시 불일치 broker(다른 worktree 소스에서 기동) + 2세대 전 고아 요청(`req-8741ad…`, running-고착)에 막혀 있었음 → 활성 요청 0 확인 후 SIGTERM graceful rotation(brk-e1ca7129). 고아 요청 파일은 보존(v15 broker retirement 마이그레이션에서 audit history로 처리 예정).
