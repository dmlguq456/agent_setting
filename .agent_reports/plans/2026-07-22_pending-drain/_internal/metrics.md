# Conductor Metrics — 2026-07-22_pending-drain (rt-04b88e3110f2c2f0)

## Dispatch 경로 기록 (계약 이탈 아님 — sanctioned fallback runner 사용 근거)

- 지시된 1차 디스패처 `utilities/dispatch-node.py`는 모든 depth-2 노드에서
  `dispatch-evidence-parent-runtime-mismatch`
  (`parent_sandbox: record=workspace-write, actual=adapter-default`)로 fail-closed(exit 65).
- 원인(실측): 봉인 route의 증거 튜플은 `parent_sandbox=workspace-write`(codex 어휘)로
  컴파일됐으나, claude wrapper(`adapters/claude/bin/dispatch-headless.py:1023`)는 자식에게
  `AGENT_DISPATCH_CURRENT_SANDBOX="adapter-default"`를 하드코딩으로 내보낸다.
  → claude wrapper로 기동된 depth-1 conductor는 이 route로는 dispatch-node 검증을
  구조적으로 통과할 수 없음(어휘 드리프트, route 재컴파일은 봉인으로 금지).
- 처분: 환경변수 위조·route 재컴파일 없이, 계약이 지정한 checked fallback runner
  `utilities/stage-dispatch-fallback.py`(CLAUDE.md·route evidence의 fallback_runner 표면)로
  전 노드 dispatch. 전 노드 hop 1(same-harness-headless, registered)로 정상 기동 —
  fleet 가시성·attempt row·완료 트랜잭션 모두 유지, 저하(hop 3/4) 불사용.
- 후속 권고(main 세션 소관): route 컴파일러의 parent_sandbox 어휘를 wrapper export와
  일치시키거나 dispatch-node 검증에 어휘 매핑 추가. dispatch-liveness 곱집합 하네스에
  claude-parent×sealed-route 셀 추가 검토.

## 관측 사항

- dispatch-wait: 자식 handoff 후에도 터미널 heartbeat 미착륙 시 장시간 ALIVE 표시
  (plan-check에서 handoff 후 ~20분). pid_scope=namespace-local이라 conductor ps로는
  직접 판정 불가 → artifact+handoff+프로세스 실측(governor/sh/claude 트리오 부재)으로
  터미널 판정 후 완료 발행.
- stage-dispatch-fallback --start는 detached 스폰 후 외부 프로세스가 오래 붙잡혀
  100s timeout으로 끊음(자식은 무사, row 정상 등록). 6/6 노드 이 패턴.

## Attempt 대장

| node | attempt_id | verdict | evidence |
|---|---|---|---|
| plan | att-e260210ec088559037e6c14e74c2e9b72c0096a743c3271a | PASS | plan.md |
| plan-check | att-cdfbd74a816294dea5eb91202d12ad1c82e4e0632e6c35f5 | PASS / memo CLEAN | _internal/plan_reviews/round_1.md |
| execute | att-4ab8a04e9e587b8cd0899c29bc28864c9130dc5fbd2663fc | PASS / plan status done / commit eae36aad | dev_logs/execute.md |
| impl-review | att-4a0fed159d747f6930618eb171d955551d995c5e265455e8 | PASS / memo CLEAN | _internal/dev_reviews/phase_review.md |
| test | att-883367eb6af99e61cf5b1d51da16683683d4250c5e2d98ac | PASS (신규 23, 기존 33+40+22) | test_logs/test_report.md |
| report | att-0a9b4ccfc894477d8116ef9a19f91e05cd39371fed6045ae | PASS | final_report.md |
