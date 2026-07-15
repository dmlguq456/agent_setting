# Capability routing topology — checklist

## Preparation

- [x] Separate worktree created: `/home/Uihyeop/agent_setting-wt/capability-routing-topology`
- [x] Base started at `origin/main@68d90996` and rebased onto `origin/main@e7a43a65`
- [x] Core routing/intensity/depth contracts reviewed
- [x] Stage-dispatch, QA-intensity, dispatch-profile component specs reviewed
- [x] All autopilot entry capability portable contracts inventoried
- [x] Current Codex capability-info/headless behavior probed
- [x] Current official Codex hook/subagent/non-interactive contracts checked
- [x] Active parity worktree overlap census recorded
- [x] Capability-specific topology matrix drafted
- [x] Implementation phases and acceptance matrix drafted
- [x] Plan self-check recorded

## Before implementation

- [x] Approved v9 component and root specs read
- [x] Worktree base confirmed against current `origin/main`
- [x] Re-run overlap census; preserve landed parity/lightweight work
- [x] Re-check official Codex runtime documentation currentness
- [x] Confirm topology registry/schema and exact 10-capability/22-recipe domain

## Implementation

- [x] Phase 1 — registry and validator
- [x] Phase 2 — route compiler and transport readiness
- [x] Phase 3 — capability rollout and sibling projections
- [x] Phase 4 — detached lifecycle, smoke, report contract
- [x] Phase 5 — global governor, cwd, spec-sync parser
- [x] Phase 6 — hash-bound completion/report-only enforcement

## Final gates

- [x] Registry coverage and negative tests green
- [x] Linked-worktree headless preflight green; nested runtime launch unavailable in sandbox
- [x] Route-based code node dry-run and row identity pilot complete
- [x] Lab setup/eval route recipes exact-coverage validated
- [x] Design, draft, and research standard+ DAGs exact-coverage validated
- [x] Detached process survival/stop test green
- [x] Smoke hash fail-closed test green
- [x] HTML/media report contract test green
- [x] Global spawn cap 50-attempt stress test green
- [x] Projection/adaptation/Fleet regression green
- [x] Main orchestrator rebased, amended, and pushed commit `26497cd0` to `origin/capability-routing-topology`
- [x] User-authorized integration merged into `main` as `cdf24f27`; integrated portable and focused regression suites green
