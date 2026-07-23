# Orphan cascade / Codex–Claude parity 검증 보고서

## 결론

등록형 headless depth-1 owner가 사라질 때 exact-bound depth-2 child가 Fleet에
open 상태로 남는 경로를 닫았다. Codex와 Claude Code는 같은 parent-attempt 결합,
원자적 spawn/publication, foreground 회수, post-exit cascade, terminal precedence를
사용한다. 자동 재시작이나 successor 선택은 추가하지 않았으며, 검증 불가능한 live
process는 오살하지 않고 계속 표면화한다.

## 무엇이 달랐고 무엇을 고쳤나

기존 watcher는 owner 사망을 감지해 owner 행만 `dead-parent-orphaned`로 닫는
detection-only 계약이었다. child 연결도 재사용 가능한 slug 중심이어서 종료 권한을
주기에는 안전하지 않았다. 따라서 owner가 plan-refine child를 기다리다 종료된 실제
사건에서 child process/row가 독립적으로 남았다.

이번 변경은 다음 경계를 추가했다.

1. child는 같은 repo/worktree의 정확한 live `parent_attempt_id` 하나에만 결합한다.
2. 최종 parent 재확인, spawn, PID/start/PGID 게시를 jobs lock 안에서 한 번에 수행한다.
3. foreground supervisor가 parent 소실 시 child process group을 회수하고, detached
   owner watcher가 TERM→grace→KILL의 bounded cascade로 백스톱한다.
4. watcher는 같은 exact parent의 direct child만 다루며, marker/typed terminal을
   lock 아래에서 다시 분류해 cascade note보다 우선시한다.
5. PID 재사용은 replacement에 신호를 보내지 않고 원래 attempt만
   `dead-parent-exited`로 닫는다. route 충돌, non-group leader, outer identity 없는
   namespace-local, unverifiable legacy live row는 그대로 보이게 둔다.
6. Codex `turn.completed`와 Claude의 성공 `result`를 같은 terminal handoff로
   정규화했다. Claude `is_error=true` 또는 비-success result는 성공처럼 보이는
   payload가 있어도 terminal PASS로 승격하지 않는다.

## Parity 경계

| 구분 | Codex | Claude Code | 판정 |
|---|---|---|---|
| 공식 headless surface | `codex exec --json -` | `claude -p --output-format stream-json --verbose --no-session-persistence` | 각 런타임의 실제 CLI로 확인 |
| 최종 event | `turn.completed` | `result` | 공용 exact terminal parser로 동형 정규화 |
| parent/child lifecycle | exact attempt + process-group identity | exact attempt + process-group identity | 공용 lifecycle/contract primitive |
| post-exit recovery | exact direct-child cascade | exact direct-child cascade | 동일 closed-note vocabulary |
| liveness/harvest | 두 terminal source 모두 판독 | Codex 측 관측기에서도 Claude result 판독 | 교차-harness fixture 통과 |
| runtime-native agent | Codex native subagent | Claude subagent/agent team | 이번 parity 대상 아님 |

즉, 이번에 입증한 것은 repo가 소유하는 registered-headless process envelope의
parity다. 서로 다른 런타임의 native agent lifecycle이 동일하다는 주장은 아니다.

## 검증 증거

- 실제 런타임: Claude Code 2.1.218 `result`, Codex CLI 0.145.0
  `turn.completed`가 동일한 exact 3-line PASS로 정규화됨.
- Claude Code 독립 plan review: `CONDITIONAL PASS`; exact attempt binding,
  kill 후 lock 재분류, Claude terminal parser, 검증 가능한 process-group 범위,
  foreground/backstop 경계의 5개 must-fix를 모두 반영.
- 결정론 회귀: terminal parser 13, contract 24, lifecycle 6, registry 28,
  orphan watcher 2, adapter 10, harvest 7 및 양 wrapper SD-15/SD-45,
  liveness/concurrency/stage fallback suite 통과.
- 실제 child process를 둔 watcher 회귀에서 owner 종료 후 child group이 bounded
  시간 안에 사라지고 owner/child 행이 terminal로 수렴함.
- adaptation boundary와 generated manifest check 통과.
- portable umbrella guard는 352 PASS / 4 FAIL이었다. 4건은 변경 전 main에서도
  재현되거나 런타임 projection/미구성 OpenCode에 속하는 기존 baseline이며, 이번
  orphan/parity 경로의 scoped suite에는 실패가 없다.

## 남은 fail-closed 경계

기록된 group leader identity를 재검증할 수 없는 live process, group을 스스로
탈출한 descendant, watcher 자체가 재부팅으로 사라진 경우는 자동 kill 대상이 아니다.
이들은 liveness/Fleet/orphan scan에 남겨 depth-0가 의미적으로 판단한다. 자동 retry,
replacement owner 생성, route advance도 의도적으로 하지 않는다.

## 전달 및 정리

- spec v23 commit: `2dd0a9f0`
- lifecycle/parity source commit: `e2971940`
- integrated main verification: scoped regression, adaptation boundary,
  manifest, installed Codex runtime projection, `doctor --runtime` 모두 PASS
- push: `origin/main`이 `e2971940`까지 반영됨
- task attempt `att-baf2d7416526446aaed1fcaa3abf3f08`: registry `done`,
  recorded PID `dead`, task-scoped orphan scan 0
- guarded cleanup: active PID 0, stale registry row 0을 확인하고
  `/home/Uihyeop/agent_setting-wt/orphan-cascade-parity` worktree 제거. 복구용
  `orphan-cascade-parity` branch는 보존함.
