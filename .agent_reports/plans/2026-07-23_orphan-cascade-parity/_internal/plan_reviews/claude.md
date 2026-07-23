# Plan review — orphan-free registered headless parity (Claude 독립 리뷰)

- Date: 2026-07-23
- Plan: `plans/2026-07-23_orphan-cascade-parity/plan/plan.md`
- Task type: paper-driven code (infra) — 축: api-contracts / test-coverage 중심
- Reviewer: Claude Code (independent, read-only)
- 근거 실측: incident 로그 tail이 `item.completed`로 끝나고 `turn.completed` 부재 확인
  (`.dispatch/logs/codex-headless-context-parity-owner.codex.jsonl`) — 계획의 사건 기술과 일치.
  OPERATIONS.md:175 "no closing of a child" 및 PRD 13.10.3 detection-only 문구 확인 —
  "관측된 고아는 계약 준수"라는 계획의 전제도 정확.

## Verdict

**CONDITIONAL PASS** — 방향(부모-결합 계약 + 정확-attempt 계단식 reconcile + fail-closed)은
타당하고 기존 classifier/`close_attempt_row_if` 기반 위에 자연스럽게 얹힌다. 단, 아래
must-fix를 계획 텍스트에 반영하지 않으면 계단식 종료가 오살(誤殺) 또는 검증 불가능한
완료 주장으로 반증된다.

## Must-fix

1. **Cascade의 부모 결합 키가 slug면 안 된다.** 현재 자식 행의 부모 연결은
   `meta.parent == <owner slug>` + repo/worktree 일치다
   (`dispatch-registry.py:has_orphaned_dependents`, `resolve_owner_route`). slug는
   retry에서 재사용된다(직전 사이클이 attempt-id-specific 경로를 도입한 이유 자체가
   same-slug retry 오염이었다). 죽은 owner와 같은 slug의 **교체 owner가 이미 떠 있는**
   경우, slug 결합 cascade는 살아 있는 교체 owner의 자식을 TERM/KILL한다. 감지
   전용이던 기존 계약에서는 허용 가능한 약점이었지만 종료 권한이 생기는 순간
   치명적이다. 자식 종료 대상 선정은 attempt-유일 키(부모 attempt_id 또는
   parent_sid 정확 일치)로 해야 하며, plan §Contract change 3에 명시가 필요하다.
2. **자식 close도 lock 하의 재분류를 거쳐야 하며, kill→classify 순서를 명시하라.**
   owner close는 `close_attempt_row_if` + fresh `classify` 재검증(veto) 패턴을 쓴다.
   계획은 자식에 대해 "terminal evidence wins"만 말하고, ① 재검증이 registry lock
   아래 close 시점에 다시 일어나는지 ② process-group 종료 후 재분류해서 그 사이에
   생긴 completion marker(SD-70 linkage)나 terminal handoff가 이기는지의 순서를
   정하지 않았다. 자식이 marker를 쓰는 도중 watcher가 발화하는 race에서 순서 미정의는
   `dead-parent-terminated`가 `completed-marker`를 덮는 결과를 허용한다. 자식 close
   note enum(예: `dead-parent-terminated` vs owner의 `dead-parent-orphaned`)도 계획에
   닫힌 어휘로 명시해야 "same closed lifecycle vocabulary" 검증이 가능하다.
3. **Claude 터미널 envelope 파서가 실제 결손이다.** registry `classify`의 terminal
   precedence는 `codex_dispatch_terminal.inspect_terminal_log`에 의존하고, Claude
   wrapper의 foreground 경로(claude/bin/dispatch-headless.py:1111-1118)는 Codex와
   달리 wait 후 terminal-handoff close를 아예 수행하지 않는다. 즉 Claude 자식 행은
   오늘 terminal-evidence 우선순위를 누릴 수단이 없다. 계획의 wrapper-parity 항목이
   이걸 포함하는지 모호하다 — `claude -p --output-format stream-json`의 최종 `result`
   event를 파싱하는 Claude측 terminal inspection(또는 공용 envelope 추상화)을 명시적
   산출물로 승격해야 must-fix 2의 precedence가 Claude 행에서 성립한다.
4. **완료 게이트 문구 "no live exact child process"의 범위를 좁혀라.** ① group
   leader는 죽고 구성원만 남은 경우 pid/start 재검증이 구조적으로 불가능해 계획
   스스로 fail-closed를 요구하므로 live process가 남는다(옳은 선택이지만 게이트와
   모순). ② 자식이 내부에서 `setsid`로 그룹을 탈출한 손자는 killpg 범위 밖이다.
   게이트는 "기록된 process group 중 leader identity가 재검증 가능한 것"으로
   한정하고, 나머지는 fail-closed + 표면화가 정답임을 명시해야 검증 가능한 주장이
   된다. PID-reuse TOCTOU(재검증→killpg 사이) 역시 제거 불가능하므로 "killpg 직전
   1회 재판독"을 계약에 적고 잔여 위험으로 기록하라.
5. **Foreground 감독이 결합하는 "exact parent identity"의 출처와 SIGKILL 잔여 경로를
   명시하라.** 계획 §Contract change 2는 어떤 pid/start를 관찰하는지(depth-1 owner
   attempt 행의 pid/pid_start), 그리고 wrapper 자신이 SIGKILL당해 감독이 소멸하는
   경로의 처분(→ owner post-exit watcher cascade가 백스톱, foreground-scoped depth-1
   등 watcher가 없는 경로는 문서화된 잔여 위험으로 depth-0 소관)을 정해야 한다.
   현재 watcher는 `dispatch_depth==1 ∧ worker_type==owner ∧ DETACHED`에서만 뜬다.

## Accepted design points

- **부모-결합 계약 자체(§1)와 detection-only 계약의 명시적 폐기**: 사건이 계약 준수
  하에 발생했다는 진단이 정확하고, OPERATIONS §post-exit reconcile + PRD 13.10.3을
  스코프에 포함해 스펙과 구현을 동시에 바꾸는 구성이 옳다.
- **fail-closed 집합(§4)**: route conflict / identity 결손 / PID reuse /
  non-group-leader에서 닫지 않고 depth-0에 남기는 선택은 기존
  `resolve_owner_route`·`classify`의 fail-closed 관행과 정합.
- **namespace-local 행은 kill 없이 증거 기반 close만(§3)**: host pid 번호가 무의미한
  행에 killpg를 시도하지 않는 것이 유일하게 안전한 처분. `pid_scope=namespace-local`
  주석이 이미 wrapper에 기록되므로 판별 가능.
- **자동 교체/재개 금지 유지(§5)**: SD-64 ②의 depth-0 재개 권한과 충돌 없음.
- **per-owner 비상주 watcher 유지**: 상주 데몬 재도입 없이 기존
  `dispatch-orphan-watch.py` 확장으로 충분하다는 판단에 동의.
- **런타임별 차등 처리 최소화**: 두 wrapper는 spawn(`start_new_session`)·
  `wait_foreground`·watcher 배선이 이미 대칭이므로, 실질 차이는 터미널 envelope
  파싱(must-fix 3)뿐이라는 계획의 암묵 전제는 맞다. 실 CLI probe를 "registry 소유
  주장 없이" 수행하는 검증 항목도 적절.
- **TERM→KILL 순서**: 진행 중 자식이 artifact를 flush할 유예를 주는 grace 순서가
  이미 `wait_foreground`에 존재하며 cascade에도 동일 적용하는 것이 옳다.

## Minimal executable test matrix

| # | Fixture (결정론, fake sleeper/로그) | 기대 |
|---|---|---|
| T1 | owner pid+start 사망, open 자식 행, 자식 그룹 live(leader==pgid, start 일치) | 그룹 TERM→KILL, owner+자식 행 모두 terminal, sibling byte-identical |
| T2 | 자식 행 pid를 무관 프로세스가 재사용(start ticks 불일치) | kill 0회, 부모-사망 증거로만 close, 무관 프로세스 생존 |
| T3 | `pid_scope=namespace-local` 자식 행 | host killpg 시도 0회, 증거 기반 close |
| T4 | 기록 pid 생존이나 `getpgid(pid) != pid` | fail-closed, 행 open 유지 + 표면화 |
| T5 | 자식 로그에 최종 FAIL/BLOCKED handoff — Codex `turn.completed`와 Claude `result` 각각 | typed terminal note가 `dead-parent-terminated`에 우선 |
| T6 | kill 전후로 completion marker+SD-70 linkage 존재 | `completed-marker` close, cascade note 미적용 |
| T7 | 죽은 owner와 same-slug의 live 교체 owner + 그 자식 | 교체 owner의 자식 무접촉 (attempt-유일 결합 입증) |
| T8 | watcher/`orphan-status --apply` 2회 연속 실행 | 2회차 no-op, registry byte-identical |
| T9 | 살아 있는 owner / 전 노드 marker 완료 route | 고아 판정 0 (오탐 0) |
| T10 | foreground 감독 중 부모 SIGKILL | 감독자가 자식 그룹 종료 + typed close (양 wrapper) |
| T11 | leader만 사망, 그룹 구성원 생존 | fail-closed + 표면화 (완료 게이트 문구와 정합 확인) |
| T12 | cascade와 depth-0 `reconcile --apply` 동시 실행 | lock 하 단일 close, note 분기 없음 |
| T13 | 동일 fixture를 Codex/Claude wrapper 양쪽에 | lifecycle 어휘 필드 동일 (parity) |

## Uncertainty

- `codex_dispatch_terminal.inspect_terminal_log`가 Claude stream-json을 어느 범위까지
  수용하는지는 소스 정밀 판독 없이 이름·배선 기준으로 판단했다 — must-fix 3 착수 시
  실측으로 확정할 것.
- 재부팅으로 watcher 자체가 소멸하는 경로는 테스트 불가 잔여 위험이며
  `orphan-scan`/preflight 표면이 백스톱이라는 전제만 확인했다.
