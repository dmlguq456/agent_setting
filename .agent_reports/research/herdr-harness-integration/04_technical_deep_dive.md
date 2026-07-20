# 04 — Technical Deep Dive

## 1. Herdr control surface

Herdr socket은 local newline-delimited JSON이며 schema introspection을 제공한다. workspace/tab/pane CRUD, pane read/send/wait, agent list/read/send/start, state report, event subscription, worktree helper를 노출한다. [Socket API](https://herdr.dev/docs/socket-api/)

stable v0.7.4 소스의 `AgentSendRequest`는 `target`과 `text`를 받고, 구현은 해석된 terminal target에 텍스트 입력을 전달한다. 즉 이는 semantic agent message bus가 아니라 PTY transport다.

- [schema source](https://github.com/ogulcancelik/herdr/blob/v0.7.4/src/api/schema/agents.rs)
- [implementation source](https://github.com/ogulcancelik/herdr/blob/v0.7.4/src/app/api/agents.rs)

## 2. 현재 하네스 control surface

Codex native multi-agent는 같은 thread 내부 병렬 delegate와 peer message를 제공한다. 공식 문서는 main agent가 subagent를 spawn하고 follow-up/wait로 조율한다고 설명한다. [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)

registered headless는 별도 process를 stable attempt identity로 등록하고 route/depth/worktree/artifact/liveness/harvest를 강제한다. `core/OPERATIONS.md:98`, `:123`, `:131-142`가 이 의미론을 정의한다.

## 3. 발견된 통합 충돌

현재 projection installer는 real `$CODEX_HOME/hooks.json`이 있으면 `.pre-harness`로 한 번 백업한 뒤 하네스 symlink로 교체한다(`adapters/codex/bin/install-runtime-projection.sh:78-96,121`). 로컬에는 Herdr Codex hook script와 백업된 Herdr hook config가 있지만 active `hooks.json`은 하네스 전용이다. 그래서 Herdr가 “current v4”라고 보고해도 실제 Codex hook entry가 활성이라는 뜻은 아니다.

더 중요한 위험은 `dispatch-headless.py:1235-1258`이 broker 변수 외의 부모 환경을 거의 모두 복사한다는 점이다. Herdr pane에서 dispatch하면 `HERDR_ENV`, `HERDR_SOCKET_PATH`, `HERDR_PANE_ID`, `HERDR_SESSION`이 자식에게 들어간다. guard 없는 Herdr hook을 단순 복구하면 headless worker가 부모 pane 상태/session identity를 잘못 보고할 수 있다.

repo의 `hooks/herdr-agent-state.sh:10-20`에는 worker 억제 guard가 있지만 설치된 Codex integration과 active hook composition은 별개다. P0는 다음 두 조건을 동시에 만족해야 한다.

```text
active_hooks = required_harness_hooks + guarded_herdr_session_hook
normal_headless_env = parent_env - HERDR_*
herdr_bound_env = explicit(session, socket, terminal/pane identity)
```

## 4. 토론 driver

```text
coordinator
  ├─ create discussion + roles + max_rounds + deadline
  ├─ send claim to critic
  ├─ wait/read response
  ├─ route response to maker
  ├─ require evidence refs and explicit dissent
  └─ synthesize + persist ledger
```

transport 선택:

- same Codex thread → native peer message
- persistent/cross-session/cross-harness → Herdr agent/pane read-send-wait
- transport unavailable → 현재 file handoff + parent conductor

이 구조에서는 Herdr의 장점을 즉시 얻으면서 논의 품질·추적성·timeout은 현재 하네스가 보장한다.
