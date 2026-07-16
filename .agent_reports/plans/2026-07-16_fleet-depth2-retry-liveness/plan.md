# Fleet depth-2 retry liveness — transfer disposition

status: completed-and-transferred
successor: `plans/2026-07-16_direct-headless-resilience`

## Retained and completed

1. Preserve `attempt_id`, `pid`, and `pid_start` from canonical registry rows.
2. Feed exact process identity to the single F-25 classifier before transcript
   heuristics so another retry's cwd activity cannot revive an exited attempt.
3. Select the newest canonical attempt per `(route_id, route_node)` for current
   Fleet/conductor presentation while retaining older diagnostic history.
4. Record depth-2 namespace-local PIDs explicitly and use a matching exact
   heartbeat at root, avoiding false death and duplicate retry/session display.

These items are implemented and verified in the direct-headless resilience
cycle, including full Fleet (569 tests), mirror parity, superseded-attempt
liveness, and recursive Codex headless smoke.

## Withdrawn

The former fenced broker stop/ensure recovery and broker fixture are invalid
under spec v15 §13.7.4. They were not implemented. No broker repair is required
for F-25 attempt identity, newest-attempt presentation, or direct depth-2
liveness.
