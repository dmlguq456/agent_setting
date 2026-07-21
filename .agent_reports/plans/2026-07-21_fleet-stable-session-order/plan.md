# Fleet stable live ordering — implementation plan

## Route and classification

- Route: `rt-89280d33a6010a5a`, node `plan`, assigned contract `code-plan`.
- Source commit: `781581bce0bac0ca51c70f676843457f68781ec7` (confirmed at worktree `HEAD`).
- Capability / mode / QA: `autopilot-code` / `dev/refactor` / `standard`.
- `spec-significance: within-spec` — Fleet PRD v13 already locks the live-run anchor behavior. This cycle implements that contract without changing the PRD or state classification.
- Write scope for the implementation stage: canonical Fleet renderer and focused Fleet tests, followed by the required byte-for-byte Claude Fleet mirror sync. No collector, model, control, route, spec, or runtime configuration change is needed.

## Diagnosis

The reorder is entirely in the renderer:

- `tools/fleet/render.py:1693-1705` computes project-group order from current liveness, current session `mtime`, then name.
- `tools/fleet/render.py:1708-1714` computes session order from current liveness/detached rank and elapsed time.
- `_build_lines()` rebuilds groups and re-runs those sorts on every redraw (`tools/fleet/render.py:2264-2353`, with session emission at `2749-2802`). The curses loop redraws not only on a collection tick but also for blink, resize, selection, prompt, and input wakes (`3641-3655`, `3732-3807`). Consequently a liveness or recency change can move a surviving project card or session row during one live run.
- `render_once()` calls the same builder without any run context (`2919-2930`), while JSON bypasses the renderer (`tools/fleet/fleet.py:82-102,152-155`). The fix therefore must be opt-in state owned by the live curses run, not a module-global replacement for the existing snapshot sorts.

The existing snapshot sort functions are correct and remain the source of the initial order and the order among newly visible rows. Status classification, grouping, filtering/folding, dispatch-tree construction, and visual row construction are not the cause.

## Required invariants

1. On the first group-view build of a live run, groups and sessions use the existing deterministic snapshot sorts unchanged.
2. On later group-view builds, surviving visible groups retain their prior relative order. Surviving visible sessions retain their prior relative order within their existing group.
3. Rows first becoming visible append after survivors, in the existing snapshot-sort order for that refresh.
4. Rows no longer visible are immediately pruned from anchors. If later visible again, they are new rows and append after current survivors.
5. A fresh live run starts with empty anchors; no state survives `curses.wrapper` / `_loop` lifetime.
6. `--once` and JSON remain stateless. `--once` continues to call the existing snapshot builder with no live-order owner; JSON continues to bypass render state entirely.
7. Dispatch-job order remains `_sort_group_jobs()` order. Stable anchoring applies only to project groups and session rows, as specified.
8. The process view remains route-sorted and behaviorally unchanged. Group-view anchors are suspended while process view is shown and reconciled on the next group-view build.
9. No liveness/state classification, project grouping, section filtering, `a` filtering/folding, selection identity, scrolling, process-card folding, route resolution, title/subtitle, memory/governor, dispatch hierarchy, layout, tint, glyph, or width contract changes.

## Design

### 1. Add a small run-local reconciler in `render.py`

Add a private `_LiveOrderState` near the existing grouping sort helpers. It owns:

- one ordered list of currently anchored project-group identities;
- one ordered list of currently anchored session identities per visible project group.

Use one shared reconciliation rule: start from the already snapshot-sorted current items, keep anchored identities that are still current in their old relative order, discard missing identities, then append current identities not in the survivor set in snapshot order. The helper must never drop rows if a defensive identity collision occurs; preserve current snapshot order as the tie-breaker and keep all objects visible.

Stable identities:

- Project group: the existing canonical group key returned by `_group_key_session()` / `_group_key_job()` (`project_of(...)`, including `loops` and `drill:<case>` special groups). This is already the grouping identity.
- Session: `(sid, harness, session_id, row-kind)` when `session_id` exists. `row-kind` distinguishes ordinary/app-server/memory-worker variants without using volatile display fields. For a sidless process-backed row, use `(proc, harness, pid, proc_start)` so PID reuse is distinguished when start-time evidence is present. Retain a final defensive `(fallback, harness, cwd, slug)` identity only for a row lacking both session ID and PID. Never include liveness, `mtime`, elapsed time, title, summary, model, effort, or selection position.

Keep this state as an ordinary object, not module global. That makes reset semantics structural and prevents test or sequential-run leakage.

### 2. Reconcile only after visibility decisions

In `_build_lines()`:

- Add an optional `live_order=None` parameter; all existing callers preserve snapshot behavior by default.
- Keep `_PROCESS_VIEW`'s early return before group-order reconciliation so process cards and their route/fold state are untouched.
- Continue computing the snapshot group order with `_group_sort_key()`.
- Prepare each group using the current section filter, dead-job filter, live-session fold decision, and `_SHOW_ALL` session filter before anchoring. Folded/empty groups are not visible group cards and therefore are pruned from the live group anchor; their existing single folded summary remains deterministic and unchanged.
- Pass the visible, snapshot-sorted group list through `_LiveOrderState` when supplied.
- For each visible group, pass `_sort_group_sessions(shown)` through that group's session anchor when state is supplied. Keep all dispatch child/orphan/loop calls to `_sort_group_jobs()` unchanged.
- When a group is pruned, discard its per-group session anchor too. Reappearance therefore starts from its current snapshot session order and appends as a new visible group.

This preparation may be a small private helper or a compact local structure, but it must centralize the existing visibility/fold predicates rather than duplicate them with divergent logic.

### 3. Make `_loop` the live-run owner

Instantiate one `_LiveOrderState` inside `_loop()` before the first collection/draw. Thread it through every `_draw()` call and from `_draw()` to `_build_lines()` via an optional keyword. This covers the initial tick, timed refresh, forced `r`, resize, blink, selection, prompt, and mouse redraws with the same anchors.

Do not add a public reset function or put anchors in `fleet.py`: entering a new `_loop()` constructs a new owner, which is the exact PRD definition of a new live run. `render_once()` does not pass a state object. The JSON branch does not import or construct one.

### 4. Preserve interaction and visual contracts by construction

Only the order of the already-prepared group/session objects changes. Existing row emitters, `_SELECTABLE` generation, PID/start-time cursor identity, `_OFFSET` clamping, click/fold maps, process view, dispatch nesting and sorting, status/tint calculation, layout allocation, and footer/legend code remain in place. Removal can necessarily shorten content, but no scroll key or viewport policy is changed.

## Exact implementation files

Primary edits:

- `tools/fleet/render.py` — private live-order state, visible-group preparation/reconciliation, optional state threading through `_build_lines`, `_draw`, and `_loop`.
- `tools/fleet/tests/test_stable_live_order.py` — focused hermetic state and render-path coverage.

Required projection sync after canonical edits:

- `adapters/claude/tools/fleet/render.py`
- `adapters/claude/tools/fleet/tests/test_stable_live_order.py`

The projection must be produced by the repository's established mirror command, not independently implemented. `tools/fleet/fleet.py` is deliberately unchanged: its JSON path is already separate from renderer state, and adding live anchors there would violate the stateless contract.

## Focused test plan

Create `test_stable_live_order.py` using in-memory `Session` instances and fixed time where rendered text is compared:

1. Session liveness/recency swap: initial `A,B`; a later snapshot sort prefers `B,A`; the same live state still renders `A,B`.
2. Project-group liveness/recency swap: initial group `alpha,beta`; swapped activity/mtime would sort `beta,alpha`; survivors remain `alpha,beta`.
3. Append: a newly working/recent session and project group would normally sort first, but each appends after survivors; multiple new rows append in their deterministic snapshot order.
4. Prune: remove a session and a group, confirm their anchor entries disappear immediately; reintroduce them and confirm they append as new visible rows.
5. Reset: construct a second `_LiveOrderState` and confirm its first build follows the current snapshot sort rather than the previous run's anchors.
6. Visibility boundary: hide a stale session with `_SHOW_ALL=False` (or fold an inactive group), confirm pruning, then reveal it and confirm append-after-survivors. Restore global render toggles in teardown.
7. Stateless determinism: permute input object order for the same snapshot and call `_build_lines()` without live state; fixed-time outputs/order must match the existing `_group_sort_key()` / `_sort_group_sessions()` result. A second fresh state must do the same on its first call.
8. `--once`/JSON isolation: assert `render_once()` invokes the builder without a live-order object and that `_snapshot_json()` remains deterministic for the same collector-defined snapshot without constructing renderer state.
9. Process-view preservation: with `_PROCESS_VIEW=True`, outputs with and without a supplied live-order object are identical and route ordering/folding remain unchanged.
10. Interaction smoke: use the existing fake-screen pattern to ensure `_draw(..., live_order=state)` still builds selectable/click rows in display order without changing cursor identity or `_OFFSET` policy.

Focused command (from repository root):

```sh
(cd tools && python3 -m unittest fleet.tests.test_stable_live_order -v)
```

## Verification and projection commands

Run in this order after implementation:

```sh
python3 -m py_compile tools/fleet/render.py tools/fleet/tests/test_stable_live_order.py
(cd tools && python3 -m unittest fleet.tests.test_stable_live_order -v)
(cd tools && python3 -m unittest fleet.tests.test_scroll_regression fleet.tests.test_f27_control fleet.tests.test_f30_process_view -v)
rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/
(cd tools && python3 -m unittest fleet.tests.test_mirror_parity -v)
(cd tools && python3 -m unittest discover -s fleet/tests -p 'test_*.py' -v)
git diff --check
```

The full Fleet discovery command is the canonical regression suite. The explicit mirror test is retained even though discovery also includes it, because byte parity is a required completion gate and its result must be separately recorded.

## Standard QA assurance and plan check

`preflight.sh qa-policy standard code` reported:

- reviewers: `1x-deep-reviewer+2x-fast-reviewers` upper bound for the selected pass;
- assurance scope: `plan-check:selected-independent-pass:final-verify`;
- independent delegation may be claimed only if a separate Codex agent/headless/external pass actually ran;
- fallback: report inline review when an independent agent is unavailable.

This immutable dispatch-depth-2 stage explicitly forbids further dispatch, so no independent reviewer is claimed. Inline plan check result: PASS for stage handoff. The design is bounded to renderer order, uses the existing sorts as the initial/new-row oracle, makes reset a lifetime property, and leaves snapshot/process/interaction paths state-free or unchanged. The implementation stage must still record focused and full-suite evidence; any failure in ordering, process view, control/scroll regressions, or mirror parity returns the cycle to code refinement.

## Evidence, warnings, and unsupported runtime detail

- Read Fleet PRD v13 and `spec_update_evidence.md`; the spec recovery transaction is complete and read-only.
- Read the assigned code-plan contract, Codex `dev/refactor` mode projection, current renderer sort/build/live-loop paths, and relevant Fleet ordering/scroll/process/mirror tests.
- No source edits, tests, commits, merges, pushes, cleanup, or spec writes were performed in this stage.
- The required `preflight.sh read <prd> codex-headless` marker attempt could not write under `/home/Uihyeop/agent_setting/.spec-grounding` because that runtime path is mounted read-only. This is an unsupported marker-write detail, not a missing spec read: the PRD was read, the wrapper had already validated the route/spec transaction, and this plan makes no spec edit. The implementation owner should preserve this warning in cycle evidence rather than claim a successful marker write.
