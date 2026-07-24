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
