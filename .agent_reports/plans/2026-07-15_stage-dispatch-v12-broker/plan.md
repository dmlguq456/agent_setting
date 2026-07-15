# stage-dispatch v12 broker — Implementation Plan

## Objective

Implement SD-51~53 so logical depth-2 Claude/Codex workers are launched by one deterministic depth-0 broker protocol, independent of the depth-1 conductor harness. Preserve route/registry/file-only handoff semantics and leave O2/O3 unchanged.

## Baseline and significance

- Base: `origin/main` at `edb29709` (v12 spec commit).
- Worktree: `/home/Uihyeop/agent_setting-wt/stage-dispatch-v12-broker`.
- Canonical artifacts: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-15_stage-dispatch-v12-broker/`.
- spec-significance: within-spec after PRD v12; implementation is bounded by SD-51~53 acceptance.
- Existing gap: `stage-dispatch-fallback.py` invokes the target wrapper in the conductor process even for `ancestor-broker`; eligibility checks root readiness only.

## Design

1. Add a vendor-neutral deterministic broker utility with a versioned declarative request envelope, canonical runtime root/jobs binding, atomic JSON state, idempotent request identity, broker PID/start-tick/instance/heartbeat metadata, lease/fencing checks, and structured failure output.
2. Keep the broker non-model. The broker builds only allowlisted adapter wrapper argv from request fields and invokes without a shell. A test-only allowlisted adapter map supplies inert fixtures; arbitrary argv/env are rejected.
3. Make `stage-dispatch-fallback.py` a broker client for all supported headless hops. The route layer still chooses same/cross harness and fallback ordinal; the broker executes exactly one chosen target and never reroutes.
4. Expose broker lifecycle/status through Codex and OpenCode preflight, plus a shared Claude-facing utility surface. Root dispatch prepares the broker endpoint; descendant dispatch only requests/status/waits and cannot replace endpoint/jobs.
5. Update nested eligibility to require a live, identity-checked broker for `ancestor-broker`; direct conductor tuples remain separately probed and do not imply portable recursion.
6. Add focused protocol and four-placement fixtures, then run existing fallback/route/adapter/liveness/boundary/manifest suites.

## File ownership

- Shared protocol/client/server: `utilities/dispatch-broker.py` (new), `utilities/dispatch_contract.py`, `utilities/stage-dispatch-fallback.py`, `utilities/nested-dispatch-eligibility.py`.
- Route/adapter surface: `utilities/capability-route.py`, `adapters/{codex,opencode}/bin/preflight.sh`, adapter documentation/projections only where the command contract changes.
- Tests: new `utilities/dispatch_broker.test.py`; updates to focused v11 fallback/adapter fixtures.
- Portable contract wording: core first if implementation requires command-surface documentation changes; no unrelated topology or O2/O3 logic.

## Verification gates

1. Unit: request schema, endpoint/jobs binding, atomic lifecycle, duplicate request id, missing/stale broker, no arbitrary executable.
2. Placement matrix: Claude→Claude, Claude→Codex, Codex→Claude, Codex→Codex; broker authority distinct from conductor, logical parent/depth preserved.
3. Fallback: route chooses next harness in order, separate request/attempt evidence, broker never reroutes.
4. Regression: capability route, dispatch contract, v11 sibling adapter, fallback, liveness/wait, adaptation boundary, generated manifest/projection checks.
5. Integration: merge branch to main, rerun focused suite on integrated tree, push, guarded worktree cleanup.

## Explicit exclusions

- O2 worker commit ownership and O3 self-modification stale-digest handling are v13 candidates only.
- No claim that native Claude/Codex subagents or direct recursive CLI spawning are equivalent to registered headless dispatch.
- No runtime-owned credentials, config, session DB, or cache edits.
