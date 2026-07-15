# Stage-dispatch v11 implementation

- Source branch: `stage-dispatch-v11`
- Source commit: `298bc043` (`feat(dispatch): implement v11 nested recovery`)
- Main merge: `7c293fd6` (`merge: stage-dispatch v11 nested recovery`)
- v10 worktree/cycle artifacts: read-only; no v10 artifact was modified.

## Implemented

- SD-48: route compilation now requires checked nested tuple evidence; the
  observed Codex conductor tuple remains hard `unsupported`, while an eligible
  ancestor broker can launch a logical depth-2 child.
- SD-49: all three wrappers share an immutable inherited global registry,
  stable `attempt_id`, pre-spawn writeability check, and idempotent legacy-row
  reconciliation.
- SD-50: route nodes carry the ordered fallback chain
  same-harness headless → cross-harness headless → native subagent → inline,
  with unchanged failed tuple retries suppressed.
- O1/SD-15: Codex start rows record `pid` and `pid_start`; shared liveness uses
  harness-aware PID validation and Codex `.codex.jsonl` fallback.

## Deferred by requirement

- O2 worker commit authority: no source change. v12 candidate; recommend the
  no-worker-commit contract with prepared commit message and main harvest.
- O3 self-modifying route completion stale digest: no source change. v12
  candidate; evaluate evidence-bearing orchestrator override versus compile-time
  digest pinning plus drift record.
