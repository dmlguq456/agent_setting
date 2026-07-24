# Owner dispatch mode-axis separation

## Outcome

등록형 depth-1 capability owner가 capability 실행 모드와 depth-2 worker persona를
하나의 `--mode`에 함께 싣지 못하게 한다. 새 writer는 `capability_mode`와
`worker_mode`를 분리하고, owner는 `_kernel/owner`만 사용하며 stage/review worker의
`worker_mode`는 sealed route의 non-reserved `unit`과 정확히 일치해야 한다.

## Evidence and root cause

같은 owner tuple에서 `--mode dev`는 형식 오류로 거부되지만
`--mode plan/plan-author`는 통과한다. 그 값은 registry, Fleet, generated task와
native-mode bootstrap 문구에 재사용된다. 원인은 capability mode와 worker persona를
단일 adapter 필드로 표현한 축 중복 및 owner 모순 검증 누락이다.

## Contract

1. `--capability-mode`는 capability catalog 및 sealed route와 일치한다.
2. `--worker-mode`는 non-owner unit의 호환 projection이며 exact unit과 일치한다.
3. owner는 `_kernel/owner`, assigned capability contract, worker mode 부재다.
4. legacy `--mode`는 scalar/capability와 slash/worker 형태로만 분류한다.
5. jobs.log/env/Fleet는 두 mode 축을 별도 보존한다.

## Implementation order

1. stage-dispatch, dispatch-profiles, Fleet PRD transaction.
2. core-first portable bootstrap contract.
3. shared validator, three wrappers, route/fallback writer.
4. Fleet collector/model/render and Claude mirror.
5. focused/full regression, projection/boundary verification.

## Rollback

spec와 source commit을 별도로 유지하고 기존 jobs rows는 legacy read-only로 보존한다.

## Completion

- shared mode contract가 canonical `capability_mode`와 optional `worker_mode`를
  분리하고 세 adapter wrapper에 동일하게 적용됐다.
- owner는 `worker_type=owner`, `unit=_kernel/owner`, worker mode 부재만 허용하며,
  owner와 slash/stage mode 또는 non-owner와 `_kernel/owner` 조합은 row/prompt/spawn
  전에 거부한다.
- Fleet는 두 축을 따로 수집·표시하고 legacy owner slash-mode 오염을 `mode!`로
  드러내며, 정상 owner에는 capability mode만 표시한다.
- 구현 커밋 `89b59d72`를 `main`에 fast-forward 통합·푸시했고 격리 worktree는
  checked cleanup으로 제거했다.
