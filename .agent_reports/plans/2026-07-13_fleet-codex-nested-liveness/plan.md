# Fleet Codex nested liveness hotfix

## Goal

다른 Codex 세션이 worktree-local `CODEX_HOME`에서 실행한 depth-1/depth-2 dispatch를 Fleet과 `preflight.sh liveness`가 활성 작업으로 표시한다.

## Implementation

1. 비-profile Codex job은 `<worktree>/.dispatch/codex-home/sessions`와 기본 session store를 함께 탐색한다.
2. profile job은 기존 격리 경로만 사용해 profile isolation을 유지한다.
3. Fleet collector와 Codex liveness helper에 같은 경로 규칙과 회귀 테스트를 둔다.
4. 현재 열린 `skill-design-c1` nested dispatch로 실제 회귀를 확인한다.

## Scope

- `spec-significance: within-spec`
- UI 렌더링과 dead-row folding 정책은 변경하지 않는다.
- registry schema 및 dispatch launch contract는 변경하지 않는다.
