# Analysis Summary

## 1. 주장 판정

**“Herdr는 여러 세션을 동시에 조율한다” — 사실.** 실제 PTY pane, workspace/tab rollup, detach/attach, agent/pane read-send-wait, events와 SSH 접근을 제공한다.

**“Herdr가 에이전트끼리 논의하게 한다” — transport 수준에서는 사실, semantic protocol 수준에서는 과장.** coordinator가 pane 출력을 읽어 다른 agent에 입력하고 다시 기다릴 수 있다. 하지만 role/round/reply/evidence/consensus를 표현하는 내장 계약은 확인되지 않았다.

## 2. 상보성

- Herdr의 결손: portable role, QA, route DAG, exact attempt, artifact ownership, worktree guard, consensus ledger.
- 현재 하네스의 결손: 지속 interactive PTY, 한눈에 보는 pane UI, 직접 attach, SSH/mobile 접근, cross-session terminal transport.
- 결론: 기존 기능을 빼지 않고 양쪽의 결손만 메운다.

## 3. 검증된 현실

이 조사 자체에서 두 native Codex subagent를 병렬로 실행하고 sibling message로 서로의 주장에 반론하게 했다. 이는 같은 thread 내 논의 transport가 이미 있다는 증거다. 반면 cross-harness headless는 현재 `core/OPERATIONS.md:123`대로 file handoff와 parent conductor가 중심이다. Herdr는 이 구간에 persistent terminal transport를 추가할 수 있다.

## 4. 가장 큰 통합 위험

hook composition과 ambient pane identity다. 현재 harness projection은 Herdr hook config를 active path에서 대체하고, headless launcher는 `HERDR_*`를 상속한다. 단순히 Herdr hook을 다시 켜면 잘못된 pane/session 보고가 생길 수 있다. 그러므로 기능 추가보다 P0 guard가 먼저다.

## 5. 최종 아키텍처 결정

```text
Herdr = persistent terminal/session plane
Harness = semantic execution/assurance plane
Fleet = merged observability plane
```

Herdr는 optional이며 없을 때 기존 동작이 완전히 유지돼야 한다. Herdr 상태는 secondary evidence이고 exact attempt ledger는 계속 현재 하네스가 소유한다.
