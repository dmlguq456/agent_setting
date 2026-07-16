# Transfer metrics

- Retained F-25 items completed: exact attempt identity, exact PID/start,
  newest-attempt current view, diagnostic history, namespace-local heartbeat.
- Broker recovery items completed: `0` (withdrawn, invalid under v15).
- Full Fleet: 569 PASS.
- Fleet canonical/Claude mirror diff: PASS.
- Superseded-attempt liveness: PASS.
- Namespace-local fresh/terminal/stale heartbeat cases: PASS.
- Successor source merge: `5fbace3e` (with earlier source merges
  `7480c5bc`, `8d51304d`).
