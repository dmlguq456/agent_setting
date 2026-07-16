# Direct Headless Resilience Owner Task

Implement stage-dispatch spec v14 §13.6.2–13.6.4 in this worktree, on top of merged v15 broker retirement. Work in strict priority order: SD-58 progress watchdog, then SD-59 capacity failover, then SD-60 registry reconciliation/current filter. This is an `autopilot-code`, `debug/standard` cycle and must run the full `code-plan -> code-execute -> code-test -> code-report` sequence, using direct registered headless stage workers where separable.

Authoritative context:

- `.agent_reports/spec/stage-dispatch/prd.md` §13.6.2–13.6.4 and §13.7.4.
- `.agent_reports/plans/2026-07-16_fleet-depth2-retry-liveness/`: retain F-25 exact attempt identity/newest-attempt work; mark broker stop/ensure recovery work withdrawn/invalid.
- `.agent_reports/plans/2026-07-16_broker-nested-reachability/_internal/withdrawal.md`: preserve and extend the transfer record if needed.
- v15 direct launch is already merged. Do not recreate a broker, spool, resident watcher, socket, heartbeat daemon, lease, or supervisor.

Required behavior:

1. SD-58: deterministic progress signals only (file writes/artifacts, tool/registry transition, stage heartbeat). Speech-only progress is never ALIVE. Warn on the first no-progress deadline; after two consecutive windows interrupt the exact attempt and advance through the checked fallback chain. Native-subagent fallback must prove child creation via row/PID/artifact or fail closed. Expose heartbeat through the same F-25 classifier source, with no second classifier.
2. SD-59: wrappers detect capacity death and close `dead-capacity`; route/orchestrator selects one different allowed model or explicit inheritance profile for exactly one automatic retry, preserving prompt/artifact ownership/route node. The capacity model is in per-node cooldown. A second capacity failure descends through SD-50; never select the same model again. Keep selection out of wrappers.
3. SD-60: one shared F-25 classification source drives exact-dead PID, merged branch, and stale terminal reconciliation. Add a preflight surface for current session/route/job filtering and guarded reconciliation. Reuse SD-29 safety gates and SD-49 attempt identity; only safe rows close with `cleanup-merged|dead-*`.

Acceptance and verification:

- Deterministic fixtures for warning -> interrupt -> fallback; speech-only not alive; heartbeat/classifier single source.
- Capacity retry-success and retry-failure->fallback, with exactly one alternative and same-model count zero.
- Mixed registry fixture: active + exact-dead + merged + stale; current view only shows the selected work and reconciliation closes only safety-approved rows.
- Canonical Fleet and Claude Fleet mirror remain byte-equivalent where required.
- Run focused suites, full Fleet tests, portable guards, adaptation boundary, compile/syntax, and direct-headless smoke. Do not run tests in parallel with adaptation/doctor checks because ignored `__pycache__` is intentionally rejected.
- Maintain durable plan/checklist/dev/test/final artifacts under `.agent_reports/plans/2026-07-16_direct-headless-resilience/`.
- Commit the source branch. Do not merge or push; root will verify and integrate.

Return exactly the typed worker handoff required by `roles/worker-bootstrap.md`.
