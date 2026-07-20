# 00 — Executive Briefing

> **결론**: “Herdr가 여러 세션을 동시에 조율하고 서로 논의하게 할 수 있다”는 말은 **절반은 맞다**. 다중 PTY·세션 유지·상태 집계·read/send/wait·원격 attach는 잘 되어 있다. 반면 토론 라운드, 메시지 상관관계, 증거·반론·합의 규칙은 Herdr의 내장 의미론이 아니다. 이 부분은 현재 하네스가 맡고 Herdr를 하위/병렬 런타임 계층으로 붙이는 것이 맞다.

## 핵심 발견

1. Herdr는 각 에이전트를 실제 터미널 pane에서 실행하고, workspace/tab/pane 상태를 집계하며, CLI/socket으로 pane·agent를 읽고 입력하고 기다릴 수 있다. detach 후에도 프로세스가 유지되고 SSH/직접 attach가 가능하다. [Agents](https://herdr.dev/docs/agents/) · [Socket API](https://herdr.dev/docs/socket-api/) · [Persistence](https://herdr.dev/docs/persistence-remote/)
2. Herdr의 `agent.send`는 대상 terminal에 입력을 보내는 transport다. planner, task DAG, mailbox, debate engine, consensus engine은 확인되지 않았다. 따라서 “A 출력 읽기 → B에게 전달 → B 응답 대기 → A에게 반론 전달”은 구현 가능하지만, 라운드와 판정은 외부 coordinator가 소유해야 한다.
3. 현재 하네스에는 이미 두 조율면이 있다.
   - 같은 Codex thread의 native subagent: 병렬 실행과 sibling message가 가능하며, 이번 조사에서 실제 교차 메시지를 검증했다.
   - registered headless/cross-harness: route, depth≤2, exact attempt, worktree, artifact, liveness/harvest가 강하지만 worker 간 실시간 대화보다는 부모 conductor와 파일 handoff가 중심이다.
4. Herdr와 현재 하네스는 경쟁재가 아니라 상보재다.

| 축 | Herdr 우세 | 현재 하네스 우세 |
|---|---|---|
| 지속 실행/사람 개입 | PTY, detach/attach, SSH, pane UI | 완료 전달·harvest 규칙 |
| 조율 의미론 | terminal read/send/wait | 역할, route DAG, QA, rounds, artifacts |
| 격리/정확성 | workspace/worktree 편의 | exact attempt, depth, worktree guard, completion evidence |
| 관찰 | agent/pane 상태와 화면 | Fleet 전역 job/session 및 권위 원장 |

## 현 설치 실측

- Herdr client/server: `0.6.6`, protocol `12`, named session `notes`에서 실행 중.
- 설치 integration: Claude v4, Codex v4.
- stable 공식 최신 릴리스: v0.7.4. [release](https://github.com/ogulcancelik/herdr/releases/tag/v0.7.4)
- 공식 최신 restore 요구치는 Claude v6, Codex v5이므로 현 integration은 full restart 뒤 native conversation resume 요건에 못 미친다. [Session restore](https://herdr.dev/docs/session-state/)
- Codex `multi_agent`: stable/enabled.

## 바로 가져올 순서

1. **P0 안전/호환** — version·protocol·schema·hook 활성 preflight, hook composition, 일반 headless worker의 `HERDR_*` 상속 차단.
2. **P1 관찰** — Fleet에 Herdr snapshot/events collector 추가. `jobs.log` exact attempt가 계속 권위 원장.
3. **P2 토론 driver** — 하네스가 role/round/timeout/evidence/dissent/consensus/ledger를 소유하고, transport만 native peer message 또는 Herdr read/send/wait로 선택.
4. **P3 선택적 Herdr PTY dispatch** — 장기 interactive owner/worker만 pane에 올리되 기존 route·QA·worktree·completion 계약 유지.
5. **P4 remote/mobile/plugin** — 신뢰 경계와 AGPL/상용 라이선스 검토 후 확장.

현재 Fleet PRD의 “Herdr 채택 X, socket 후순위, attach/resume 비대상” 결정은 사용자 의도와 달라졌다. 구현 전에 `autopilot-spec`으로 **“대체하지 않는 optional runtime/transport integration”**을 명시해야 한다. 코드는 아직 변경하지 않았다.

세부 근거: [03_vendor_comparison.md](03_vendor_comparison.md) · [04_technical_deep_dive.md](04_technical_deep_dive.md) · [06_implementation.md](06_implementation.md)
