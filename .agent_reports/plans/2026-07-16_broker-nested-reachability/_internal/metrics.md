# Pipeline metrics and fallback record

- Selected graph: `autopilot-code debug/standard`.
- Inline exception (OPERATIONS §5.10 / SD-17 / STAGE_DISPATCH_INLINE_OK): 본 사이클의 수리 대상이 stage-dispatch broker 자체다. 수리 전 계약 경로(status)는 중첩 컨텍스트에서 본 결함으로 신뢰 불가하고, dispatch 인프라 자기수정은 orchestrator opt-out 대상이므로 plan·execute·test를 depth-0 세션이 인라인 수행한다. 선행 사이클 2건(stage-dispatch-v13, fleet-depth2-retry-liveness)의 동일 예외 기록과 같은 근거.
- Assurance compensation: spec v14 acceptance에 직접 앵커, 신규 fixture 4계열 + 기존 broker/fallback 스위트 전체 회귀 + 미러 parity + zsh/bash smoke + worker-유사 실전 acceptance를 분리 실행하고 test_logs에 전량 기록.
- Broker preflight at cycle start: 현행 live broker brk-9a6717359ce14394bb24ad6990ab3fd9 (pid 1057841) — depth-0에서 status check=ok. 구현 merge 후 implementation-digest mismatch로 계약 경로 롤오버 예정.
