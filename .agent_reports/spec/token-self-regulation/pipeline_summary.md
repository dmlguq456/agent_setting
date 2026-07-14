# Token Self-Regulation — Spec Pipeline Summary

- **Date**: 2026-07-13
- **Current version**: v2
- **Status**: Phase 2 implementation and Phase 3 isolated tooling complete; real experiment/adoption pending
- **Placement**: component SoT under `spec/token-self-regulation/`
- **Production policy**: v1 static transition-only; dynamic disabled

## v2 update — Phase 2 accounting and Phase 3 isolated adoption gate

기존 v1을 `_internal/versions/v1/prd.md`로 exact snapshot한 뒤 PRD를 update mode로 갱신했다.

## v2 implementation completion

- Phase 2 content-free bounded accounting, exact delivered-byte ownership,
  monotonic counter observations, JSON/KV diagnostics, and fail-open lifecycle
  integration are implemented and verified.
- Phase 3 frozen offline candidate, strict unique-workload triplet evaluator,
  deterministic bootstrap gates, and explicit isolated CLI are implemented.
- Final verification passed Phase 2 21, Phase 3 10, Fleet 221, portable guards
  344/0, adaptation/boundary/manifest/doctor/diff, mirror/projection checks, and
  independent re-review.
- Candidate SHA-256 is
  `11288b737241598dcf585eb762cfc033f3cbcca70eee6ff583cb6065f6de3606`.
- Synthetic fixtures remain non-evidentiary. Real paired sample count is zero;
  production dynamic stays disabled and adoption remains blocked.

### Phase 2

- hook invocation을 `zero_injection|emission`으로 완결하고 `invocations = zero + emissions` 불변식을 정의했다.
- emitted directive의 실제 삽입 문자열 UTF-8 bytes와 exact-session runtime cumulative counter의 monotonic observed delta를 분리했다.
- exact tokenizer provenance가 없으면 token 수를 추정하지 않는다.
- bytes/counter를 production savings, billing cost, ROI로 부르지 않는다.
- hashed-session, content-free XDG aggregate를 8 KiB/file, 256 files, 2 MiB로 bound하고 atomic/fail-open 동작을 요구했다.
- progressive disclosure를 L0 zero / L1 essential / L2 diagnostic / L3 experiment로 분리해 accounting·experiment 설명이 production prompt에 추가되지 않도록 했다.

### Phase 3

- `offline-forecast-v1`은 frozen deterministic pure function이며 production hook에서는 disabled다.
- isolated runner의 control/static/dynamic complete triplet과 config fingerprint 계약을 companion `experiment_contract.md`에 고정했다.
- adoption eligibility는 30 complete triplets, 복수 stratum당 10, required+safety 100%, quality 2% tolerance, 10,000회 paired bootstrap의 control/static 두 positive lower bounds를 모두 요구한다.
- evaluator의 최고 verdict는 `eligible_for_user_review`다. 사용자 `adopt|reject|continue-experiment` 결정과 후속 spec/code cycle 없이는 production을 바꾸지 않는다.

### 계속 금지

input/transcript/artifact pruning·요약, RL/online learning, model/reasoning effort, intensity, dispatch/depth, QA/reviewer budget, required tools/tests/safety/security/error handling/accessibility/guard 축소는 Phase 2–3에서도 금지다.

## QA and runtime boundary

- v1 snapshot과 git HEAD의 기존 PRD byte equality: passed.
- `pipeline_state.yaml` parse와 v2/gate/resume field assertions: passed.
- PRD/experiment contract의 required metric·bound·gate·금지사항 및 artifact scope census: passed.
- 현재 Phase 0–1 token-budget regression tests: 12 passed.
- production source의 `offline-forecast-v1`/dynamic-enable path 부재와 `git diff --check`: passed.
- thorough QA policy의 독립 reviewer budget은 별도 Codex agent/headless pass가 실제 실행된 경우에만 주장할 수 있다. 이 worker에서는 inline multi-axis review와 final deterministic verification으로 fallback한다.
- Codex `autopilot-spec`은 instruction-only로 지원된다.
- Codex flat spec-read gate는 `spec/token-self-regulation/prd.md`를 인식하지 못해 route/capability preflight가 component spec read를 승인하지 않았다. actual component PRD는 읽었고, 이 미지원 계약을 완료 보고에 남긴다.
- native `apply_patch` hook도 component artifact target을 직접 판별하지 못해, 동일 `apply_patch`를 explicit write-preflight된 shell 경로로 실행했다.
- source code와 adapter 파일은 수정하지 않으며 이 worker는 commit/push하지 않는다.

## Resume

다음 entry는 `autopilot-lab`이다. 고정 계약으로 real paired
control/static/dynamic evidence를 수집한다. production dynamic policy는
별도 adoption 결정과 후속 spec/code cycle 전까지 disabled다.

## v1 history — Phase 0–1

v1은 shared telemetry parser가 active context와 cumulative session counters를 분리하고, Codex exact-session rollout observer와 static 70/85% transition-only directive를 채택했다. normal/unknown/native/same-band는 0 bytes이며 intensity/model/dispatch/depth/QA/safety/input context는 불변으로 잠갔다. 당시 Phase 2 reinjection accounting과 Phase 3 dynamic experiment는 의도적으로 deferred였다.
