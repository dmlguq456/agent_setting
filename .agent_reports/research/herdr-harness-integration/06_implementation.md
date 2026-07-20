# 06 — Additive Implementation Plan

> 범위 원칙: 제거 없음. 의미론은 core first, Herdr는 optional integration.

## P0 — 호환성과 상태 안전

1. `preflight.sh herdr-info [--check]` 추가:
   - client/server version, protocol, socket, `api schema`
   - integration installed version
   - active hook entry와 script를 분리 판정
   - current pane/session binding
2. hook projection을 exact symlink 일치에서 **required hook set + 허용 external bridge** 검증으로 확장.
3. Codex/Claude/OpenCode용 worker-guarded Herdr bridge 작성.
4. 일반 registered headless dispatch에서 `HERDR_*` 제거. 새 `herdr-pty` transport가 명시 binding을 전달한 경우만 재주입.
5. 테스트: parent pane 오염, duplicate session report, missing socket, old protocol, hook coexistence.

## P1 — Fleet observer

1. `tools/fleet/collectors/herdr.py`를 optional collector로 추가.
2. `session.snapshot` 후 resource events 구독; reconnect 시 재-snapshot.
3. 모델에 `herdr_session/workspace/tab/pane/terminal`, `agent_session`, `status_source`를 보조 필드로 추가.
4. precedence:

```text
completion marker / exact attempt PID evidence
  > jobs.log route evidence
  > runtime transcript/DB
  > Herdr pane/agent state
```

5. attach/read action은 explicit user action. 자동 input/kill 없음.

## P2 — Discussion driver

artifact:

```text
.agent_reports/<owner>/<slug>/_internal/discussions/<discussion-id>/
  manifest.yaml
  rounds.jsonl
  synthesis.md
```

최소 계약:

- roles: maker, critic, fact-checker, synthesizer
- transport capability probe
- max rounds/timeout/retry
- `reply_to`/round correlation
- evidence refs 필수
- unresolved dissent 별도 보존
- final synthesis는 parent owner가 통합

이식 1차는 native Codex peer message, 2차는 Herdr read/send/wait adapter, 3차는 cross-harness discussion으로 확장한다.

## P3 — Optional Herdr PTY transport

기존 route compiler의 runtime surface에 `herdr-pty`를 추가하되 다음은 불변이다.

- `jobs.log` stable attempt registration
- depth≤2, parent, capability/mode/intensity/model role
- worktree와 artifact root
- permission/sandbox policy
- synchronous wait/harvest와 completion marker
- checked fallback: 기존 headless/native/inline 경로

## Spec gate

현재 `.agent_reports/spec/agent-fleet-dashboard/prd.md:359-364`는 “Herdr 채택 X”와 socket 후순위를 잠그고, `:488`은 attach/resume 비대상을 유지한다. 사용자 목표가 달라졌으므로 코드 전에 `autopilot-spec`에서 다음으로 개정한다.

> Herdr를 Fleet 대체재로 채택하지 않되, optional PTY/session transport와 secondary observability source로 통합한다. 현재 harness authority와 zero-injection 기본 경로는 유지한다.

## 성공 기준

- Herdr가 없어도 기존 테스트와 동작 100% 유지.
- interactive parent pane 상태를 headless child가 덮어쓰지 않음.
- discussion의 모든 round가 role, reply, evidence, timeout과 함께 재현 가능.
- Herdr 상태가 exact attempt terminal verdict를 바꾸지 않음.
- transport failure가 기존 checked fallback으로 수렴.
