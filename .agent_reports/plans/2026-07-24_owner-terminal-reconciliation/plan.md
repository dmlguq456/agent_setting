# Owner terminal reconciliation and dispatch model policy

## Goal

종료된 registered owner가 `open`으로 남아 parent park/harvest가 반복되는 결함을
구조적으로 닫는다. 동시에 Claude 모델 정책을 다음처럼 고정한다.

- `deep` 역할의 Claude 실현은 Opus다.
- Fable은 대화형 depth-0 메인 세션에서만 허용한다.
- registered headless owner/stage, native 분사, inherited dispatch 및 capacity
  fallback 후보에서 Fable을 제외한다.

## Spec significance

`SPEC-SIGNIFICANT`: SD-59의 capacity failover 자격, SD-77/78의 supervisor 수명주기,
SD-79/83의 liveness 소비 경계를 함께 바꾼다. stage-dispatch PRD v29에서 먼저
SD-85~87을 확정한 뒤 구현한다.

## Implementation plan

1. v29 spec transaction으로 모델 자격·supervisor terminal reconcile·canonical repo
   identity 및 공통 liveness 판정을 명문화한다.
2. supervisor 최종 envelope와 process exit를 exact attempt terminal state로 원자
   reconcile하고 capacity를 typed `dead-capacity`로 보존한다.
3. parent attempt 해석은 primary/linked worktree를 같은 canonical repository로
   인식하되 exact worktree/attempt 생존 조건은 유지한다.
4. Fleet, park, wait, fallback이 같은 observed-liveness classifier를 소비하게 하고,
   read-only Fleet는 mutation 없이 stale-open/reconcile-needed를 정직하게 표시한다.
5. Claude dispatch 모델 정책을 surface-aware하게 강제하고 deep role/capacity cascade를
   Opus 중심으로 갱신한다.
6. deterministic fixture, adapter parity, live-safe smoke, integrated main 검증 후
   commit/merge/push/guarded worktree cleanup을 수행한다.

## Safety boundaries

- runtime-owned jobs/log/config/credential은 수정하지 않는다.
- exact attempt 외 row를 slug/cwd로 breadth-close하지 않는다.
- unrelated primary worktree 변경과 기존 open job은 보존한다.
- Fable 관측용 statusline/Fleet 표시는 유지하고 실행 자격만 제한한다.
