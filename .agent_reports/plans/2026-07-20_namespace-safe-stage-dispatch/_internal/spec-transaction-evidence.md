# Stage-dispatch PRD transaction handoff

- Target: `/home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch/prd.md`.
- Patch: `_internal/spec-transaction.patch` in this cycle.
- Proposed decision: `SD-72 — namespace-safe automatic lifecycle selection`.
- Ownership status: applied by the root integration boundary through secondary
  `autopilot-spec` route `rt-94ed270212e80967` (`spec_touch=true`).
- Transaction: `utilities/spec-transaction.py run --spec-root
  .../spec/stage-dispatch --require-snapshot`; acquired the shared lock without
  waiting, reread latest, created component snapshot
  `stage-dispatch/_internal/versions/v18/prd.md`, and released with result 0.
- Current artifacts: PRD/pipeline state/summary are v19 and include SD-72,
  parent/Fleet visibility, scoped Codex inner sandbox behavior, and the narrow
  Claude `session-env` runtime scratch projection.
- Events: `_internal/spec-transaction-events.jsonl`; route:
  `_internal/spec-route.json`; research/review/transaction completion markers
  are bound to the two live PASS reviews and final PRD.
- Source order evidence: portable runtime contract was changed first in `core/OPERATIONS.md`; shared utility and Codex/Claude adapter realizations followed.
