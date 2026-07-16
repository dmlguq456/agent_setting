# Direct Headless Resilience — checklist

## Contract and transfer

- [x] Read v14 §13.6.2–13.6.4 and v15 §13.7.4.
- [x] Preserve F-25 exact-attempt/newest-attempt work.
- [x] Withdraw broker recovery and add no broker-like replacement.

## SD-58

- [x] Reuse one F-25 exact-attempt classifier.
- [x] Add bounded atomic heartbeat/watchdog state and real stage phases.
- [x] Implement warning, exact revalidation, interrupt, closure, and checked continuation.
- [x] Fail native-subagent routing closed without child proof.
- [x] Handle depth-2 namespace-local PID visibility with exact heartbeat evidence.

## SD-59

- [x] Add anchored capacity detection and exact closure to all wrappers.
- [x] Keep replacement selection in the conductor.
- [x] Enforce allowed/different model, cooldown, stable identity, and one retry.
- [x] Cover success, second-capacity fallback, prose false-positive, and same-model rejection.

## SD-60

- [x] Add current filters and newest-attempt current view.
- [x] Add dry-run/apply reconciliation with locked revalidation.
- [x] Reuse SD-29 merge/worktree safety and preserve unsafe/unrelated rows.
- [x] Expose current/reconcile through preflight and liveness paths.
- [x] Cover mixed rows, idempotency, concurrency, and namespace-local terminal reconciliation.

## Verification and delivery

- [x] Focused SD-58/59/60 and existing dispatch suites pass.
- [x] Claude/Codex/OpenCode wrapper suites pass.
- [x] Full Fleet suite passes (569 tests).
- [x] Fleet canonical/Claude byte parity passes.
- [x] Portable guards and adaptation boundary pass with no bytecode caches.
- [x] Real recursive Codex headless smoke passes with zero broker path use.
- [x] Independent verifier reports PASS with all five repros closed.
- [x] Source commits merged to `main` and runtime projections refreshed.
- [ ] Final artifact commit, push, and eligible worktree cleanup (owner closeout).
