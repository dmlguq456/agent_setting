# Depth-1 surface terminology remediation — autopilot-code owner

Complete the approved remediation in
`/home/Uihyeop/agent_setting-wt/depth1-surface-terminology-remediated`.
This is an `autopilot-code`, `dev/strong`, tracked standard+ cycle. Run the
route-declared `code-plan -> code-execute -> code-test -> code-report` stages
as separate registered depth-2 headless workers, sequentially, and keep all
durable artifacts under:

`/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_depth1-surface-terminology-remediation`

Authoritative inputs:

- Route:
  `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_depth1-surface-terminology-remediation/_internal/code-route.json`
- Current governing spec:
  `/home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch/prd.md`
  v20 §13.12 / SD-73–75.
- Audit:
  `/home/Uihyeop/agent_setting/.agent_reports/documents/2026-07-20_depth1-surface-terminology-audit.md`
- Approved source candidates: `7094c92b`, `c95ed391`.
- Rejected commit: `6b3a34bc`. Do not cherry-pick, reproduce, or otherwise
  introduce its co-primary/multi-capability composition contract.

The source worktree starts at current `origin/main`. The execute stage should
cherry-pick only `7094c92b` and `c95ed391`, resolve their intent against current
main, then amend and extend the result to satisfy v20. Preserve the original
`depth1-surface-terminology` branch unchanged.

Required implementation:

1. Replace current portable route/topology schema fields `depth`, `max_depth`,
   and `owner_depth` with `dispatch_depth`, `max_dispatch_depth`, and
   `owner_dispatch_depth` across authoritative source, validators, route
   records, completion/registry/Fleet consumers, tests, and generated sibling
   projections. Historical prose and explicitly version-tagged read-only
   legacy fixtures are the only exceptions. Codex `agents.max_depth` remains
   a distinct native setting.
2. Separate and validate the closed namespaces for wrapper `transport`,
   attempt `execution_surface`/`registered_worker`, and `fallback_hop`.
   Unknown values fail before route emission or registry/spawn.
3. For every `effective_intensity=quick` route, omitted transport derives to
   `headless`; explicit empty, `interactive`, `native-subagent`,
   `inline-fallback`, or arbitrary transport fails closed. Checked headless
   ineligibility emits `quick-headless-unavailable` with route/row/spawn count
   zero. Quick permits one capability-owner node at dispatch depth 1, no child,
   at most one live registered-headless attempt, serial registered-headless
   retries only, and terminal exhaustion
   `quick-registered-headless-exhausted`. No native or inline quick fallback.
4. Preserve direct main-inline behavior and the standard+ checked fallback
   chain exactly.
5. Correct terminology everywhere touched: Codex native subagent, Claude
   subagent, Claude agent-team teammate session, and registered headless
   worker session are four distinct surfaces. A team agent must not be called
   a runtime-native subagent.
6. Complete the missing derived-layer propagation identified by the audit,
   using repository generators/sync tools rather than hand-editing generated
   files where a source generator owns them. Add deterministic negative and
   preservation tests for the above invariants.

Self-hosting transition note:

- This implementation route was emitted by the pre-v20 compiler immediately
  after the v20 spec transaction, so its immutable bootstrap record still has
  legacy route field names. Treat it only as the one implementation bootstrap
  route and record that exact exception in `_internal/metrics.md`; do not claim
  its schema itself satisfies v20. After implementation, compile fresh
  direct/quick/standard+ routes with the new compiler and use those as
  acceptance evidence. No new or resumed legacy route may be emitted.

Verification must include at least:

- every-capability quick default compiles to one registered-headless-only node
  with qualified dispatch fields;
- all prohibited quick transport/surface cases fail with zero emitted route,
  row, and spawn;
- direct and standard+ preservation fixtures;
- topology, route, registry/completion/Fleet schema and legacy migration tests;
- terminology conformance across core, capabilities, portable skills, Claude,
  Codex, OpenCode, and plugin/generated projections;
- `python3 tools/generate.py --check`;
- `python3 tools/sync-entry-skill-layer.py --check`;
- `sh tools/check-adaptation-boundary.sh`;
- focused topology/route/dispatch/Fleet tests and the repository's applicable
  routing-contract/drill checks.

The test stage is the independent risk-focused review required by strong
intensity. It must inspect the actual diff, reject unsupported assertions, and
request a bounded execute fix loop if needed. Do not merge or push. Commit the
completed source branch only after PASS. Return the exact three-line worker
handoff required by `roles/worker-bootstrap.md`.
