# Plan check — PASS

Refute-by-default questions:

1. Could a free-form note mint the new state? **No.** The classifier requires nested
   `state_evidence.attempt`, shared-observer source, exact rule/state, and matching
   attempt/route/node axes.
2. Could the UI claim success early? **No.** `reconciling` is excluded from done progress,
   carries no gate mark, and keeps successors pending.
3. Could a real failure be hidden? **No.** explicit killed/cancelled/fail-note evidence and
   parallel-group failure retain higher precedence; generic stale/dead remains failed.
4. Could an old retry override the current attempt? **No.** canonical priority and registry
   order select the current attempt; both ordering directions have regressions.
5. Is the dispatch observer contract changed? **No.** job liveness stays stale/reconcile-needed;
   only the route projection and its render vocabulary change.

Verdict: implementation may proceed.
