# Token Self-Regulation — Spec Pipeline Summary

- **Date**: 2026-07-13
- **Status**: Phase 0–1 implemented and repository-verified
- **Scope**: Phase 0–1 only
- **Placement**: independent component spec under `spec/token-self-regulation/`

## Outcome

Research의 Ponytail 방향을 현재 Codex runtime에 맞춰 구현했다. 정적 bootstrap 계측기인 `context-footprint.py`를 세션 parser로 늘리지 않고, shared telemetry parser가 active context와 cumulative session counters를 분리한다. Codex는 exact session rollout을 읽고 Claude/OpenCode는 이번 cycle에서 unsupported auto-hook을 추측하지 않는다.

## Locked decisions

- Codex native `rollout_budget`는 feature/probe를 통과한 명시 opt-in에서만 harness directive를 억제한다.
- native 기능을 켜기 위해 `$CODEX_HOME/config.toml`을 수정하지 않는다.
- fallback policy는 context 70%/85%에서 tight/critical로 바뀐다.
- normal/unknown/native/동일 band에서는 주입 0 byte, tight/critical 신규 진입에서만 240 bytes 이하 1줄이다.
- budget은 출력 간결성과 명시되지 않은 선택적 범위만 조절한다.
- intensity, model/role, dispatch/depth, plan/review/test, safety/security/error handling/a11y, input context는 불변이다.
- 조사 초안의 “budget tight → 분사 억제”는 폐기한다.

## Runtime boundary

Official Codex docs expose native status/context surfaces and an under-development rollout-budget config. Local Codex 0.144.1 reports the features disabled and rejects the documented config shape, so the default is rollout JSON observer fallback rather than a second native-budget implementation.

## Verification

- focused token-budget tests: 12 passed
- full Fleet tests: 202 passed
- portable guards: 343 passed, 0 failed
- adaptation boundary, manifest, native projections, mirror parity, diff check, repository doctor: passed
- two independent implementation reviews: findings corrected, no remaining P0/P1

## Runtime boundary and next

The feature was fast-forwarded to main and pushed. The installed `$CODEX_HOME`
projection was refreshed with native skill discovery; strict projection and hook
trust checks pass. No runtime-owned `config.toml`, credential, transcript, or
session store was mutated.

Phase 2 reinjection cost accounting and Phase 3 dynamic-policy experiments remain intentionally deferred.
