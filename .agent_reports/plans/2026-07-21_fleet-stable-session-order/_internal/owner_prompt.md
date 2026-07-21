# Assigned capability-owner task

You are the registered dispatch-depth-1 owner for an approved
`autopilot-code --mode debug --intensity standard` cycle.

User intent: Fleet's live dashboard currently moves active sessions around as
their status and recency refresh. Make live session positions stable so the
dashboard is calm and trackable.

Immutable context:

- worktree: `/home/Uihyeop/agent_setting-wt/fleet-stable-session-order`
- canonical artifact root: `/home/Uihyeop/agent_setting/.agent_reports`
- source commit: `781581bce0bac0ca51c70f676843457f68781ec7`
- cycle artifact: `plans/2026-07-21_fleet-stable-session-order/`
- primary capability: `autopilot-code`, mode `debug`, intensity `standard`
- route: `rt-89280d33a6010a5a`, source commit remains the immutable value above
- secondary `autopilot-spec` update is already complete as Fleet PRD v13;
  `spec_update_evidence.md` records its failed-worker recovery and locked PASS
- no runtime-native subagents; standard stages use only checked registered
  dispatch-depth-2 workers and never dispatch depth 3

The main checkout has unrelated pre-existing changes under
`.agent_reports/spec/stage-dispatch/**` and unrelated untracked artifacts.
Do not touch, overwrite, revert, or include them. The Fleet source and
`spec/agent-fleet-dashboard/**` were clean at intake.

Required diagnosis and contract:

- Fleet PRD v13 now requires deterministic initial snapshot order plus run-local
  stable survivor ordering for both groups and sessions.
- `tools/fleet/render.py` implements this through `_group_sort_key`,
  `_sort_group_sessions`, and `_build_lines`; `_loop` recollects and redraws
  every tick.
- This is now `spec-significance: within-spec` against PRD v13. Existing rows
  must retain their positions across refreshes even if liveness/mtime changes;
  newly visible sessions/groups append without moving survivors; disappeared
  rows are removed. A new Fleet process and stateless `--once`/JSON output
  remain deterministic from snapshot data.
- Preserve status classification, group membership, filtering/folding,
  selection identity, scrolling, process view, and all existing visual
  contracts unless the minimal stable-order implementation requires a shared
  helper. Do not conflate row ordering with F-25 state hysteresis.

Execution requirements:

1. Read `capabilities/autopilot-code.md`, the required worker bootstrap, the
   current Fleet PRD/state/summary, and only relevant Fleet source/tests.
2. Run all required Codex preflight read/write/capability guards. Re-read the
   recovered v13 Fleet PRD and `spec_update_evidence.md`; do not rewrite the
   already-completed spec transaction.
3. Materialize the standard code pipeline and use checked registered
   dispatch-depth-2 `code-plan -> code-execute -> code-test -> code-report`
   workers with file-only handoff, synchronous polling, harvest, and exact
   completion evidence. Do not end the owner turn while a stage is detached.
4. Implement a bounded live-order state keyed by stable row identity. Avoid an
   ever-growing cache; define and test reset/prune behavior. Keep one-shot
   output deterministic and preserve existing initial ordering semantics.
5. Add focused regression tests covering at least: liveness/recency swaps do
   not move surviving active sessions; a newly visible row does not move
   survivors; a removed row is pruned; a new live run resets anchors; stateless
   snapshot rendering remains deterministic. Test both session rows and project
   groups if both can move under current sort keys.
6. Run focused tests and the canonical Fleet test suite. Check canonical Fleet
   versus adapter mirror parity if the repository contract requires it. Record
   commands and results under the cycle artifact.
7. Do not merge, push, clean worktrees, or edit runtime-owned files. Under the
   Codex linked-worktree contract, leave source changes uncommitted for the
   dispatch-depth-0 main to attribute, review, integrate, commit, and push.

Completion gate: the worktree contains the minimal stable live-order
implementation and regression tests, all required verification passes, and
`pipeline_summary.md` gives exact evidence and any residual risk. Your final
output must follow the three-line worker handoff contract exactly.
