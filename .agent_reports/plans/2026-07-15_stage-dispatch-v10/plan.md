# Stage-dispatch PRD v10 implementation plan

## Verdict

`spec-significance: within-spec`. Implement SD-44–47 without modifying the canonical PRD and preserve report-only rollout for legacy low-level dispatch.

## Plan

1. Update core-first contracts: separate tracking from escalation language in `core/WORKFLOW.md` and `core/OPERATIONS.md`; strengthen §5.8 to cover the complete spec transaction/version chain and wait/re-read/next-version behavior.
2. Extend `capabilities/topologies.json` and `tools/capability_topology.py` with tracking/guard schema, report-only rollout metadata, and fail-closed spec write-scope ownership/precondition validation.
3. Extend `utilities/capability-route.py` with independent `tracking`, selection/escalation basis, four tracked-gate evidence fields, and `spec_touch`; preserve direct/ambiguous→quick/promotion→standard+ behavior.
4. Add a shared worker route validator and wire Claude/Codex/OpenCode dispatch wrappers to validate route hash, assigned node/scope, tracked evidence, absolute cwd, canonical artifact root, and git state without rerouting. Keep legacy no-route dispatch as the report-only compatibility path.
5. Add structured artifact-guard failures tied to route id/file and a spec-transaction helper that serializes version reservation, emits BLOCKED/wait/acquired evidence, re-reads latest version under lock, and rejects missing spec-touch.
6. Generate projections from sources, add independent adapter fixtures plus route/topology/guard/concurrency negative fixtures, and run all v10 acceptance and required regression gates.
7. Record implementation/test/report artifacts and commit the branch with the required co-author trailer; do not merge or push.

## Risk focus

The independent strong review targets SD-45’s reduced bootstrap and three-adapter homomorphism, especially accidental capability/intensity rerouting or one adapter’s fixture acting as a proxy for siblings.
