# Direct Headless Resilience — final report

overall verdict: **PASS**
scope: stage-dispatch v14 SD-58, SD-59, SD-60 retained by v15 §13.7.4
architecture: broker-retired direct headless

## Outcome

SD-58 progress watchdog, SD-59 capacity failover, and SD-60 registry current
view/reconciliation are implemented end to end on the direct-headless path.
The implementation preserves F-25 exact attempt identity and newest-attempt
presentation and adds no broker-like authority.

## Delivered behavior

- Progress is attempt-scoped, bounded, atomic, and based on deterministic stage
  evidence. Two consecutive quiet windows trigger an exact revalidation and
  targeted interruption before checked fallback continuation.
- Capacity failures are anchored and recorded by each wrapper; the conductor
  alone selects one allowed different model, persists cooldown/retry identity,
  and never launches a same-model or third retry.
- Current views filter selected work before totals and fold older logical
  retries. Reconciliation is dry-run by default and exact/locked/atomic on
  apply, with SD-29 safety gates and bounded reasons.
- Depth-2 PID namespace differences are explicit. A root process never treats
  a namespace-local numeric PID as host identity; exact heartbeat evidence
  supplies live/terminal state and stale evidence falls back safely.
- Fleet canonical and Claude mirror trees are byte-identical.

## Evidence

- Focused suites: SD-58 10, SD-59 6, SD-60 8, fallback 7, contract 10,
  nested 4, prompt 2, adapters 6 — all PASS.
- Full Fleet: 569 PASS.
- Three wrapper SD-15/capacity suites and portable liveness: PASS.
- Mirror parity/tree diff, portable guards (`368/0`), adaptation boundary,
  syntax/compile, and diff check: PASS.
- Independent verifier: PASS, no blocker, five repros closed.
- Real Codex headless recursion: PASS through `same-harness-headless`,
  `launch_authority=conductor`, `broker_lifecycle=retired`.

## Integration

Source commits `821405f3`, `3b9622a2`, and `f59163e8` were merged into `main`
as `7480c5bc`, `8d51304d`, and `5fbace3e`. Claude, Codex, and OpenCode linked
runtime projections were refreshed and reported fresh with no duplicate
sources. Final artifact commit, push, and eligible worktree cleanup complete
the owner closeout after this report is staged.

No runtime-owned credentials, sessions, databases, or user configuration were
edited.
