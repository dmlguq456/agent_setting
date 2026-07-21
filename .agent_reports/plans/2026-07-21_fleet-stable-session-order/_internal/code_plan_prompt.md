# Assigned code-plan stage: Fleet stable live ordering

Work only as the registered dispatch-depth-2 `code-plan` stage for route
`rt-89280d33a6010a5a`, node `plan`, parent `fleet-stable-order-owner`.
Follow the supplied Portable Worker Kernel and stage contract. Do not dispatch.

Immutable inputs:

- worktree: `/home/Uihyeop/agent_setting-wt/fleet-stable-session-order`
- canonical artifact root: `/home/Uihyeop/agent_setting/.agent_reports`
- source commit: `781581bce0bac0ca51c70f676843457f68781ec7`
- cycle: `plans/2026-07-21_fleet-stable-session-order/`
- spec: `/home/Uihyeop/agent_setting/.agent_reports/spec/agent-fleet-dashboard/prd.md` (v13)
- spec recovery evidence: `plans/2026-07-21_fleet-stable-session-order/spec_update_evidence.md`
- task: diagnose and plan the minimal bounded live-order state for Fleet so survivor session and project-group positions stay stable across live refreshes, new visible rows append, removed rows prune, a new live run resets anchors, and stateless `--once`/JSON remain deterministically snapshot-sorted.

Read only the stage contract, required inputs above, relevant `tools/fleet/render.py`
code, and relevant Fleet tests. The spec transaction is complete and read-only.
Classify `spec-significance: within-spec` against Fleet PRD v13.

Write a durable `plan.md` and multi-step `checklist.md` in the canonical cycle
root. The plan must identify stable row identities, the live-run state owner and
reset/prune behavior, exact source/test files, and verification commands. Cover
both sessions and project groups where current sort keys can move them; preserve
status classification, grouping, filtering/folding, selection, scrolling,
process view, dispatch order, and all visual contracts. Include focused tests
for liveness/recency swaps, append, prune, reset, deterministic stateless
rendering, and the canonical Fleet suite plus required mirror parity check.

No source edits, tests, commits, merges, pushes, cleanup, or spec rewrites.
