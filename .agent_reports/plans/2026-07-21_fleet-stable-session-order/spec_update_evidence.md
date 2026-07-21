# Fleet stable-order spec update evidence

- Verdict: PASS after dispatch-depth-0 recovery of a failed quick owner handoff.
- Route: `rt-6632bf58fbc5ce94`, attempt
  `att-6fb222b8681a47b0bf91e87fb37f17c5`.
- The owner wrote the v13 PRD/state/summary change and an exact pre-change
  `spec/agent-fleet-dashboard/_internal/versions/v12/prd.md` snapshot, then
  returned FAIL because its evidence write and completion marker were blocked
  by a Codex headless session-id/spec-read-marker mismatch.
- The failed attempt was closed deterministically as `dead-worker-fail` from
  its exact `turn.completed:FAIL` evidence; it is not claimed as a successful
  quick route.
- Main re-read the canonical Fleet spec and ran a shared-lock recovery
  validation through `utilities/spec-transaction.py`. The transaction acquired
  the canonical lock, reported `next_version=13`, verified that the v12
  snapshot hash exactly matches the pre-change `HEAD` PRD, verified all three
  v13 surfaces, and released with result 0.
- Recovery log: `spec_recovery_transaction.jsonl`.

Final contract:

- Initial live order and stateless `--once`/`--json` order remain the existing
  deterministic snapshot order.
- During one live run, visible survivor groups and sessions keep their relative
  positions; new rows append; disappeared rows are pruned; a new run resets the
  anchors.
- Status classification and all non-order Fleet behavior remain unchanged.
