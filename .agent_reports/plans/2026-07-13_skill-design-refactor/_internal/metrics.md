# skill-design-c1 dispatch metrics

## Separability judgment

- C1 trial-flip은 pilot 한 파일의 flip → fresh Claude probe 3개 → 실패 시 즉시 양 트리 원복이 하나의 boundary-coupled 관측 단위였다. 이전 Claude conductor의 nested `claude -p` classifier 차단을 피하려는 비-nested Codex capability-owner 자리이기도 해서 inline 실행했다.
- 이 예외 근거를 gate 전에 본 파일에 기록했어야 하나, 최초 inline 실행 시 누락했다. 사용자가 분사 여부를 지적한 뒤 누락을 확인했고, 이후 분리 가능한 구현·검증·보고 단계는 depth-2 dispatch로 전환했다.

## Actual stage dispatch

| stage | slug | depth | result |
|---|---|---:|---|
| execute | `skill-design-c1-code-execute` | 2 | autopilot-ship 양 트리 dedupe 완료; parent diff review 후 `9d1abb2` commit |
| test | `skill-design-c1-code-test` | 2 | 14개 test artifact 수확; source gates green, sync/capability drift 분리 보고 |
| report | `skill-design-c1-code-report` | 2 | `pipeline_summary.md` 작성·수확 완료; source/state 무변경 확인 |

## Runtime observations

- 격리 Codex projection: `AGENT_HOME=<worktree>` + worktree 내부 `CODEX_HOME`; live `$CODEX_HOME` 인증만 재사용하고 main repo projection 혼입을 차단했다.
- depth-2 worker의 명령 실행·worktree write·file-only handoff는 정상 동작했다.
- `preflight.sh liveness`는 격리 projection의 실제 실행 프로세스와 JSONL 진행 중에도 `DEAD`를 반환했다. 실행 실패가 아니라 transcript/process discovery false negative로 관측했으며 정확한 하위 원인은 미확정이다.
- `workspace-write` child의 commit은 `/home/Uihyeop/agent_setting/.git/worktrees/skill-design-c1/index.lock`가 sandbox 밖이라 실패했다. parent가 수확·검토·commit하는 방식으로 닫았다.
- depth 3+는 계약상 사용하지 않았다.

## Invocation contract closure separability (2026-07-13)

- core의 분류 문장과 g7의 expected frontmatter는 같은 semantic anchor다. 한쪽만 독립 stage에서 바꾸면 변경 중간에 현재의 올바른 13개 `false` 상태를 잘못 FAIL시키거나, 반대로 낡은 규범을 계속 PASS시키므로 boundary-coupled로 판정했다.
- invocation contract → registry → checker → g7 fixture/assert를 한 브랜치에서 inline 결합 수정했다. 분리 가능한 검증은 syntax, live positive gate, synthetic negative/positive controls로 각각 독립 실행했다.
- dispatch 인프라 자체는 수정하지 않았다. full drill runner는 Codex `loop-info drill`의 manual-only 계약에 따라 실행하지 않고 0-turn static fixture/assert만 verification-runner로 직접 실행했다.
