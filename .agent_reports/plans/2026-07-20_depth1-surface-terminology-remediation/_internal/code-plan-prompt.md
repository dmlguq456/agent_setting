# Code-plan stage assignment

Create the durable implementation plan and checklist for the approved depth-1
surface terminology remediation. This is the `code-plan` stage of route node
`plan`; do not edit source.

Use these authoritative inputs:

- route: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_depth1-surface-terminology-remediation/_internal/code-route.json`
- governing spec: `/home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch/prd.md` v20 §13.12 / SD-73–75
- audit: `/home/Uihyeop/agent_setting/.agent_reports/documents/2026-07-20_depth1-surface-terminology-audit.md`
- approved source candidates: commits `7094c92b` and `c95ed391`
- rejected commit: `6b3a34bc`; its co-primary/multi-capability composition contract must not be introduced
- worktree: `/home/Uihyeop/agent_setting-wt/depth1-surface-terminology-remediated`, currently based on `origin/main`
- artifact directory: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_depth1-surface-terminology-remediation`

The plan must cover all six required implementation areas from the owner
assignment: qualified dispatch-depth field names; closed transport,
execution-surface/registered-worker, and fallback-hop namespaces; strict quick
headless-only semantics and zero-emission failures; direct and standard+
preservation; four-surface terminology; generator-owned derived propagation;
and deterministic negative/preservation tests.

Plan the execute stage to cherry-pick only `7094c92b` and `c95ed391`, resolve
their intent against current main, amend/extend to v20, and leave the original
branch untouched. Explicitly include the self-hosting legacy bootstrap-route
exception in `_internal/metrics.md`, fresh post-change direct/quick/standard+
route acceptance evidence, all required verification commands, independent
risk-focused diff review, a bounded execute-fix loop if requested, and commit
only after PASS. Record the standard QA policy assurance:
`plan-check:selected-independent-pass:final-verify` with one deep and up to two
fast reviewers; do not claim independent delegation unless a separate worker
actually ran.

Write `plan.md` and `checklist.md` under the artifact directory. The handoff
must be sufficient for the execute stage without conversation history. End
with the worker kernel's exact three-line handoff.
