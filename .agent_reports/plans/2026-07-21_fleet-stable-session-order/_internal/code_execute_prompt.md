# Assigned code-execute stage: Fleet stable live ordering

Work only as the registered dispatch-depth-2 `code-execute` stage for route
`rt-89280d33a6010a5a`, node `execute`, parent `fleet-stable-order-owner`.
Follow the supplied Portable Worker Kernel and stage contract. Do not dispatch,
commit, merge, push, clean worktrees, or rewrite the already-complete spec.

File-only inputs:

- worktree: `/home/Uihyeop/agent_setting-wt/fleet-stable-session-order`
- source commit: `781581bce0bac0ca51c70f676843457f68781ec7`
- canonical artifact root: `/home/Uihyeop/agent_setting/.agent_reports`
- cycle root: `plans/2026-07-21_fleet-stable-session-order/`
- approved plan: `plans/2026-07-21_fleet-stable-session-order/plan.md`
- checklist: `plans/2026-07-21_fleet-stable-session-order/checklist.md`
- Fleet PRD v13: `spec/agent-fleet-dashboard/prd.md` under the canonical artifact root
- spec recovery evidence: `plans/2026-07-21_fleet-stable-session-order/spec_update_evidence.md`

Implement the approved minimal run-local stable-order design. Primary canonical
files are `tools/fleet/render.py` and a focused
`tools/fleet/tests/test_stable_live_order.py`, followed by the established exact
Claude adapter Fleet mirror sync if the repository contract requires it. Run
the preflight write guard before every edit. Preserve snapshot/`--once`/JSON
determinism and every non-order contract listed in the plan. The order state
must be bounded by currently visible identities, prune removals, and reset by
constructing a new live-run owner. Cover both project groups and session rows.

Run proportionate focused checks while implementing, but leave canonical final
verification to code-test. Record exact changed files, decisions, commands and
results in `dev_logs/`, and update the canonical checklist only with work truly
completed. Preserve the known warning that the Codex spec-read marker runtime
path is read-only even though the PRD was actually read and the route already
contains validated spec-read evidence.

Completion gate: minimal source diff and focused regression tests are present,
focused implementation checks pass, mirror files (if required) are exact, and
durable dev evidence is sufficient for code-test.
