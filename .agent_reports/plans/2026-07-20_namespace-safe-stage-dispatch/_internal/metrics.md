# Pipeline metrics and exceptions

- Route: `autopilot-code · dev/refactor · strong · standard QA · depth 1 owner`.
- Self-hosting exception: `STAGE_DISPATCH_INLINE_OK=dispatch-infra-self-modification`.
- Checked stage probe count: 1 invocation.
- Probe result: exit 79, `selected_hop=inline`, `reason=runtime-unavailable`, `fleet_visibility=none`.
- Same-harness attempt: exit 77, `nested-sandbox-lifetime`, attempt `att-413cd2d51f3708c71f80cf765c04331120ad94ee59bbed43`.
- Cross-harness attempt: exit 77, `nested-sandbox-lifetime`, attempt `att-5cc0847b9fb89916c6b402bc98041bed2204c5920597a158`.
- Child sessions spawned: 0 (both wrappers failed before spawn).
- Independent plan/execute/test/report stages: did not run; bounded work continued inline under the approved dispatch-infrastructure self-modification exception.
- Spec-read marker warning: `preflight.sh read` could not write the primary checkout's `.spec-grounding` marker because that path was read-only in this worker sandbox. The dispatch wrapper had already validated the tracked gate; the PRD read and warning are retained here.
- QA fallback: independent reviewer transport unavailable through the same defective nested lifecycle; inline review plus deterministic conformance verification used and disclosed.

## Post-fix live and integration evidence

- Claude depth-2: `att-liveclaude…0001`, foreground-scoped, PASS artifact,
  exact completion marker, terminal row, harvested.
- Codex depth-2: `att-livecodex…0002`, foreground-scoped, PASS artifact,
  66 focused tests, exact completion marker, terminal row, harvested.
- Fleet: live unmatched-parent depth-2 row rendered as a visible orphan; corrected
  dispatch-chain parent identity now defaults from `AGENT_DISPATCH_SELF_SLUG`.
- Integrated deterministic verification: 9 adapter tests, 5+5 lifecycle projection
  tests, 10 fallback, 6 capacity, 16 registry, 10 progress, 9 marker, 4 eligibility,
  13 route-guard, 110 Fleet tests, liveness/wait/route/concurrency suites, and
  adaptation boundary PASS.
- Secondary spec route: `rt-94ed270212e80967`; stage-dispatch PRD v19 transaction
  completed with component snapshot `_internal/versions/v18/prd.md`.
