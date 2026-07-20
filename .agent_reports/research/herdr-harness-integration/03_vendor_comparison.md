# 03 — Herdr vs Current Harness

| 항목 | Herdr stable | 현재 하네스 | 결합 원칙 |
|---|---|---|---|
| 세션 구조 | server/workspace/tab/pane/terminal | main/native/headless/route node | Herdr ID를 attempt 보조 provenance로 |
| 지속성 | detach 시 live PTY 유지; server restart 시 프로세스 소실 | registry/artifact 기반 재개 | live continuity는 Herdr, semantic resume는 harness |
| 상태 | screen manifest 또는 integration, rollup | PID/start-time/transcript/completion evidence | exact attempt는 harness 우선 |
| 조작 | focus/read/send/start/attach/wait/events | dispatch/follow-up/wait/harvest | harness가 정책, Herdr가 transport |
| 토론 | read/send/wait 조합 가능 | 역할·QA·artifact와 native peer message | rounds/consensus는 harness |
| worktree | create/open/remove API | guarded creation, branch, artifact root, cleanup | 초기에는 Herdr mutation 금지 |
| 원격 | SSH UI/direct terminal attach | 별도 runtime/headless 중심 | P4에서 선택적으로 채택 |
| plugin | 사용자 코드로 확장 | Skills/hooks/adapters | Herdr plugin은 unsandboxed 신뢰 코드로 취급 |

## 판정

- **맞음**: 여러 agent terminal을 동시에 운영하고, 상태를 모아 보고, agent/script가 다른 pane을 읽고 입력하고 기다리는 기능은 잘 되어 있다.
- **과장**: Herdr가 agent들 사이에 structured mailbox, shared context, role graph, debate/consensus protocol을 제공한다는 해석.
- **우리에게 유리한 점**: 과장된 부분이 바로 현재 하네스의 강점이므로, 중복 제거가 아니라 결합 가치가 크다.

세부 카드: [cards/herdr.md](cards/herdr.md) · [cards/current-harness.md](cards/current-harness.md)
