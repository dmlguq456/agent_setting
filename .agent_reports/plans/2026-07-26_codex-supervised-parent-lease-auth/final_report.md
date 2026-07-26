# Final report

## Outcome

The recurring Codex depth-1→depth-2 failure is fixed, verified, and
fast-forwarded into `main` on 2026-07-27.

- Supervised Codex owners now hold a nonce-bound, exact-attempt `flock-v1`
  lease. PID/start evidence stays primary; the lease is accepted only for the
  exact `process-namespace-unverifiable` case and grants no launch, completion,
  fence, or signal authority.
- Parent identity is revalidated before spawn, before fence release, and for
  the full foreground child wait. Lease loss closes the fence or tears down the
  exact child.
- Codex auth status is parsed line by line while retaining the exit-zero gate,
  so warning-prefixed valid login output no longer becomes `auth-unavailable`.
- Supervisor and orphan cleanup remove only the exact declared lease; stale,
  free, foreign, nonce-mismatched, symlinked, and PID-reuse cases fail closed.
- Codex start receipts now expose the exact `child_spawned=1|0` result.

## Acceptance evidence

Live owner `att-3fedfb87bf9942c7a8c2c701c02509af` started depth-2
`code-plan` child `att-ac2d63c649184f38a812b684771a8932` with
`child_spawned=1`, `parent_liveness_source=supervisor-lease`, and nested
eligibility `supported`. Exact completion delivery, parent/child liveness,
harvest, lease/state cleanup, and process quiescence all passed. Detailed live
evidence is under `_internal/live-smoke/evidence.md`.

After rebasing onto current `origin/main`, all focused and dispatch integration
suites passed, as did shell liveness, adaptation-boundary, and generated-
projection tests. `tools/generate.py --check` still reports unrelated baseline
`post-it` projection drift in paths untouched by this branch.

## Delivery

- `379164fe` — implementation and regressions
- `78b79561` — portable lease contract
- remote branch: `origin/fix/codex-supervised-parent-lease-auth`
- `main` was fast-forwarded through `78b79561`; this integration also records
  the scoped v31 stage-dispatch specification and curated verification evidence.
- unrelated primary artifact changes and raw live-smoke session logs were not
  staged or modified by the integration.
