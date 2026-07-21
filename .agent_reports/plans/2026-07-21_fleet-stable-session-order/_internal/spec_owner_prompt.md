# Assigned spec transaction

You are the registered dispatch-depth-1 one-shot owner for an approved
`autopilot-spec --mode update --intensity quick` secondary step inside the
Fleet stable-session-order fix.

User intent is already confirmed: Fleet's live dashboard must stop moving
surviving active session rows and project groups around on every refresh.

Immutable scope:

- worktree: `/home/Uihyeop/agent_setting-wt/fleet-stable-session-order`
- canonical artifact root: `/home/Uihyeop/agent_setting/.agent_reports`
- target spec: `spec/agent-fleet-dashboard/{prd.md,pipeline_state.yaml,pipeline_summary.md}`
- write scope: only that Fleet spec transaction and its next version snapshot
- source files are read-only in this step

Read the `autopilot-spec` contract, current Fleet PRD/state/summary, and the
relevant current implementation around `_group_sort_key`,
`_sort_group_sessions`, `_build_lines`, and `_loop` only as grounding. Run the
required Codex guards and the 3–4 question quick plan-check-lite.

Record this contract without broadening the feature:

- Initial ordering in a newly launched live TUI and stateless `--once`/JSON
  output stays deterministic from the existing snapshot rules.
- During one live TUI run, groups and session rows that remain visible retain
  their relative positions even when liveness or mtime changes.
- Newly visible groups/sessions append after survivors; disappeared rows are
  pruned from the anchor so the state stays bounded; a new Fleet run resets it.
- Status classification, filtering/folding, selection identity, scroll,
  process view, dispatch ordering, and visual layout are otherwise unchanged.

Use the shared spec transaction/lock. Snapshot the old PRD to the next version,
update the exact ordering language in the PRD, refresh pipeline state metadata,
and append a concise decision/update entry to pipeline summary atomically.
Do not touch the unrelated dirty `spec/stage-dispatch/**` files or any runtime
state. Do not edit source, merge, push, or clean the worktree.

Completion gate: the Fleet spec transaction is atomic, internally consistent,
and sufficient for the subsequent implementation stage. Write exact evidence
under `plans/2026-07-21_fleet-stable-session-order/` and end with the required
three-line worker handoff only.
