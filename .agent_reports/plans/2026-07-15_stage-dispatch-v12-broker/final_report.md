# stage-dispatch v12 broker — Final report

## Outcome

Claude Code와 Codex의 runtime-native 재귀 방식 차이를 topology 계약에서 제거했다. 이제 standard+의 모든 logical depth-2 headless hop은 parent/child harness 조합과 무관하게 하나의 depth-0 deterministic broker protocol을 사용한다.

| Parent conductor | Child stage | Result |
|---|---|---|
| Claude | Claude | PASS |
| Claude | Codex | PASS |
| Codex | Claude | PASS |
| Codex | Codex | PASS |

Conductor는 target CLI/wrapper를 직접 재귀 실행하지 않는다. Route layer가 same/cross-harness 후보와 fallback ordinal을 선택하고, broker는 선택된 target 하나만 allowlisted argv로 실행한다. Fleet/global registry의 logical `depth=2,parent=<conductor>`는 OS ancestry와 분리되어 그대로 유지된다.

## Reliability and safety

- Versioned declarative envelope only; arbitrary shell, argv, and environment injection are rejected.
- Canonical broker root, instance, jobs registry, worktree, artifact root, route hash/node/scope are identity-checked and mismatches fail with zero local fallback launches.
- Request state is atomic and idempotent. Concurrent and sequential duplicate requests create one attempt.
- PID/start ticks, heartbeat, lease, predecessor fencing, and global attempt reconciliation cover stale/missing brokers and both claim-time/post-registry crash recovery.
- Every target attempt is registered before wrapper spawn and carries request id, attempt id, route node, target harness, and logical parent.

## O1/O2/O3 disposition

- O1 liveness false-DEAD: existing v11 within-spec implementation is retained and verified. Codex rows carry PID/start ticks and PID-less legacy rows use the harness-aware transcript fallback.
- O2 worker commit failure: linked-worktree worker sandbox cannot create the Git common-dir `index.lock`. v12 does not change commit ownership. v13 should evaluate `worker no-commit + prepared commit/evidence → depth-0 harvest/commit`.
- O3 route-completion stale digest: self-modifying dispatch code can invalidate the compiler-input digest used by its own completion check. v12 does not add an override. v13 should compare an evidence-bearing orchestrator override against compile-time digest pinning plus an explicit drift record.

## Evidence

- Source commit: `8897bf76`; main integration: `70bac6ef`.
- Report/spec state commit and main push: `d24e0af8`; guarded source worktree cleanup completed with the branch preserved.
- Broker protocol tests: 10/10.
- Portable guards: 359/359.
- Adaptation boundary, manifest, dispatch concurrency/liveness/wait, and installed Codex runtime projection: PASS.

Detailed commands and stage evidence are in `dev_logs/implementation.md` and `test_logs/verification.md`.
