# Parent-park terminal recovery plan

## 목표

Codex의 registered-child 보호를 completion-delivery 표면별로 분리한다. supervised와 명시적 poll fallback의 exact-batch 안전성은 유지하되, interactive depth-0 세션이 이미 terminal인 `process-unverifiable` 과거 행 때문에 전역적으로 영구 정지되는 회귀를 제거한다.

## 근거와 판정

- `b645a145`는 one-shot polling 보조책으로 일반 parent park를 도입했다.
- `d4d926fb`는 registered standard+ owner에 runtime-owned supervised join을 추가했다.
- `8f78d361`는 ordinary hook의 후보를 `done && process != quiescent`까지 넓혔지만, 허용된 wait/harvest는 terminal-unverifiable 행을 닫을 수 없어 recovery-free self-deadlock을 만들었다.
- 공식 Codex native subagent/wait 표면과 registered-headless supervisor는 별개다. 본 수정은 native subagent 정책을 변경하지 않는다.

spec-significance: SPEC-SIGNIFICANT — SD-79의 shared quiescence 분류를 readiness와 PreToolUse admission에 동일 적용한 문구를 completion-delivery mode별로 분리한다.

## 상태별 계약

| 호출 표면 | open/running | terminal+live | terminal+unverifiable | terminal+quiescent |
|---|---|---|---|---|
| supervised owner | phase park | phase park | phase park | release/harvest state |
| explicit poll-fallback owner | park | park | park; bounded wait may return typed unresolved | release |
| interactive depth-0 parent | park | global park 해제; successor/readiness 별도 차단 | global park 해제; exact readiness는 fail-closed 유지 | release |

## 구현

1. stage-dispatch PRD와 core hook/operations 계약을 먼저 갱신한다.
2. Codex hook에서 completion mode를 명시적으로 분류한다. `supervised|poll`만 terminal non-quiescent를 park 후보에 포함하고, mode가 없는 interactive parent는 registry open/running 행만 park한다.
3. supervised phase classifier, dispatch join, dispatch wait, successor readiness는 변경하지 않는다.
4. adapter 문서에서 ordinary interactive guard가 readiness oracle이 아님을 명시한다.
5. terminal-unverifiable self-deadlock, poll/supervised strictness, open-row blocking, terminal quiescent release 회귀를 테스트한다.

## 검증

- `utilities/codex-parent-park.test.py`
- `utilities/dispatch_completion_join.test.py`
- `utilities/dispatch-wait.test.sh`
- `utilities/worktree-cleanup.test.py`
- portable guard/adaptation boundary 중 관련 스위트
- `py_compile`, `git diff --check`, 통합 브랜치 재검증

## 비범위

- shared quiescence classifier 자체 완화
- successor launch, completion join, polling wait의 fail-closed 완화
- native subagent lifecycle 변경
- registry 행 수동 변조 또는 process 부재 추정
