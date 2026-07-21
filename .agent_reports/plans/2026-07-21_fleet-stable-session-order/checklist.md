# Fleet stable live ordering — execution checklist

## Gate 0 — immutable inputs and safety

- [x] Confirm worktree `HEAD` is still based on `781581bce0bac0ca51c70f676843457f68781ec7`; stop for overlapping renderer/test edits rather than overwrite them.
- [x] Treat Fleet PRD v13 and `spec_update_evidence.md` as read-only; record `spec-significance: within-spec`.
- [x] Run the required write preflight before every canonical or mirror file edit.
- [x] Preserve the planning warning that the `codex-headless` spec-read marker path was read-only; do not claim the marker succeeded.

## Step 1 — add the run-local order model

- [x] In `tools/fleet/render.py`, add `_LiveOrderState` and a single reconciliation helper beside the existing group/session snapshot-sort helpers.
- [x] Implement group identity as the existing project group key.
- [x] Implement session identity priority: harness+session ID+row-kind; otherwise harness+PID+process start time; final defensive harness+cwd+slug fallback.
- [x] Exclude volatile liveness, mtime, elapsed, title, summary, model, effort, and screen position from identity.
- [x] Ensure reconciliation keeps survivors, prunes missing identities, appends new identities in current snapshot order, and never drops collision rows.

Completion gate: pure helper tests demonstrate swap stability, append, prune/reappearance, and fresh-state reset for groups and sessions.

## Step 2 — apply anchors after visibility/folding

- [x] Add optional `live_order=None` to `_build_lines()` without changing existing callers' snapshot behavior.
- [x] Preserve `_PROCESS_VIEW`'s current route-card branch and ordering.
- [x] Prepare group visibility once using the existing section, dead-job, `_SHOW_ALL`, and fold predicates.
- [x] Reconcile only visible project cards; prune session anchors for groups no longer visible.
- [x] Feed snapshot-sorted visible sessions through the per-group anchor.
- [x] Leave child/orphan/loop dispatch ordering on `_sort_group_jobs()`.
- [x] Keep folded-group summary output and empty-group suppression unchanged.
  Recovery execute keeps non-card groups in snapshot order for the unchanged folded
  aggregation while reconciling and pruning only visible card/session anchors.

Completion gate: render integration tests cover group/session liveness and recency swaps plus hide/fold prune and reveal append.

## Step 3 — bind state to one curses run

- [x] Instantiate exactly one `_LiveOrderState` inside `_loop()` before its initial draw.
- [x] Thread the object through every `_draw()` call and into `_build_lines()` by keyword.
- [x] Do not create a module-global anchor, a public reset API, or state in `fleet.py`.
- [x] Confirm `render_once()` supplies no live state and JSON still bypasses render state.

Completion gate: one state persists across redraw/tick paths; a newly constructed state restores current deterministic snapshot order.

## Step 4 — focused regression coverage

- [x] Add `tools/fleet/tests/test_stable_live_order.py`.
- [x] Cover session liveness/recency swap.
- [x] Cover project-group liveness/recency swap.
- [x] Cover single and multiple new-row append.
- [x] Cover prune and reappearance-as-append.
- [x] Cover new-run reset.
- [x] Cover `_SHOW_ALL`/fold visibility pruning with a render assertion that the
  folded summary remains visible while its live anchor is pruned, then reappears as
  an appended card when revealed.
- [x] Cover permuted-input stateless snapshot determinism with fixed time. (Focused stateless sort assertion plus existing deterministic snapshot sorts.)
- [x] Cover `--once` and JSON isolation from live state. (Call-path inspection confirms both remain state-free.)
- [x] Cover process-view output parity with/without supplied order state. (Early-return inspection plus `test_f30_process_view` regression pass.)
- [x] Cover selectable/click-map identity and scroll-offset smoke through the existing fake-screen pattern. (`test_scroll_regression`, `test_f27_control`, and process-view mouse regressions pass.)

Completion gate:

```sh
python3 -m py_compile tools/fleet/render.py tools/fleet/tests/test_stable_live_order.py
(cd tools && python3 -m unittest fleet.tests.test_stable_live_order -v)
(cd tools && python3 -m unittest fleet.tests.test_scroll_regression fleet.tests.test_f27_control fleet.tests.test_f30_process_view -v)
```

All commands must exit 0; record command, exit code, and output summary in the code-test artifact.

## Step 5 — mirror and canonical Fleet verification

- [x] Sync the full canonical Fleet tree to the Claude adapter mirror only after canonical focused tests pass:

```sh
rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/
```

- [x] Run the explicit parity gate:

```sh
(cd tools && python3 -m unittest fleet.tests.test_mirror_parity -v)
```

- [x] Run the canonical Fleet suite from the repository root (retry verifier owns this gate):

```sh
python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py' -v
```

  The prior `(cd tools && ...)` invocation was a verification-environment error:
  unchanged `test_v20_dispatch_contract` imports `tools.*` and therefore requires
  the repository root on `sys.path`. No source patch was made for that import.

- [x] Run `git diff --check`.
- [x] Inspect the final diff and confirm only the planned canonical renderer/test files and their exact mirror copies changed.
- [x] Confirm no collector/model/control/route/spec/runtime file changed and no status vocabulary, grouping, dispatch order, process cards, selection, scrolling, or visual contract was altered.

Completion gate: focused tests, interaction regressions, explicit mirror parity, canonical Fleet suite, and diff checks all pass with exact evidence. Any failure returns to `code-refine`; do not waive or silently reduce the gate.

## QA record

- [x] Record standard code QA policy: `plan-check:selected-independent-pass:final-verify`.
- [x] Do not claim independent review unless a genuinely separate permitted pass ran.
- [x] Planning-stage fallback used: inline review only, because this dispatch-depth-2 worker was forbidden to dispatch.
- [x] Final implementation report distinguishes test evidence from unverified assumptions and repeats the read-only spec-marker warning.
- [x] Selected independent `code-test` pass executed; durable evidence is in
  `test_logs/verification.md`.
- [x] Final verification PASS. Recovery `code-execute` is PASS: focused folded-summary,
  prune/reveal, selected regressions, mirror parity, and diff hygiene pass. The retry
  `code-test` stage still owns the corrected root-level full discovery gate.
