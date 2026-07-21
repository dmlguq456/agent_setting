# Fleet stable live ordering — execute handoff

## Stage result

- Route / node / attempt: `rt-89280d33a6010a5a` / `execute` / `att-c3b9dd692ea8453ca249449dfe18809f`.
- Verdict: PASS for the `code-execute` gate. The carried source/test diff was inspected and required no recovery correction.
- Spec significance: `within-spec`. Fleet PRD v13 and `spec_update_evidence.md` remained read-only.
- Commit state: no commit, merge, push, cleanup, or integration was performed.

## Changed files present in the worktree

- `tools/fleet/render.py`
  - Adds run-local `_LiveOrderState`, stable session identities, and collision-safe reconciliation.
  - Reconciles only visible project groups and their snapshot-sorted visible sessions.
  - Threads one order owner through every live `_loop` redraw while leaving `render_once` and process view stateless.
- `tools/fleet/tests/test_stable_live_order.py`
  - Covers survivor ordering, append, prune/reappearance, reset, row-kind/PID-start identity, and stateless snapshot sorting.
- `adapters/claude/tools/fleet/render.py`
- `adapters/claude/tools/fleet/tests/test_stable_live_order.py`
  - Exact byte mirrors of the two canonical files.

No collector, model, control, route, spec, or runtime configuration file changed. The diff remains limited to the planned canonical renderer/test and exact mirror copies.

## Implementation review

- Existing `_group_sort_key()` and `_sort_group_sessions()` remain the initial/new-row ordering oracle.
- Stable identities exclude volatile liveness, recency, elapsed time, display text, model/effort, and screen position.
- Reconciliation retains all current objects across defensive identity collisions, prunes absent identities, preserves surviving relative order, and appends newcomers in current snapshot order.
- The process-view early return still occurs before group/session reconciliation, so process cards remain route-sorted and do not mutate the group anchors.
- Folded/section-hidden groups are excluded before group reconciliation; per-group session anchors are discarded when their group is pruned.
- `_LiveOrderState` is instantiated inside `_loop`, so anchors cannot leak across live runs. `render_once()` still invokes `_build_lines()` without a live-order owner; JSON remains outside renderer state.
- No independent review is claimed. This immutable dispatch-depth-2 stage could not dispatch; the standard-QA fallback is an inline implementation review.

## Verification evidence

All commands ran from `/home/Uihyeop/agent_setting-wt/fleet-stable-session-order` and exited 0.

1. `python3 -m py_compile tools/fleet/render.py tools/fleet/tests/test_stable_live_order.py`
   - Result: PASS.
2. `(cd tools && python3 -m unittest fleet.tests.test_stable_live_order -v)`
   - Result: PASS, 4 tests.
3. `(cd tools && python3 -m unittest fleet.tests.test_scroll_regression fleet.tests.test_f27_control fleet.tests.test_f30_process_view -v)`
   - Result: PASS, 111 tests.
   - One pre-existing `ResourceWarning` reports an unclosed read in `test_f27_control.py`; it does not fail the suite.
4. `(cd tools && python3 -m unittest fleet.tests.test_mirror_parity -v)`
   - Result: PASS, 1 test.
5. `git diff --check`
   - Result: PASS.
6. `cmp -s` for canonical/mirror renderer and focused test pairs
   - Result: PASS for both pairs.
7. `git merge-base --is-ancestor 781581bce0bac0ca51c70f676843457f68781ec7 HEAD` and `git rev-parse HEAD`
   - Result: PASS; `HEAD` is exactly `781581bce0bac0ca51c70f676843457f68781ec7`.

The full canonical Fleet discovery suite was deliberately not run in this stage because the recovery assignment reserves final verification for `code-test`.

## Required QA and warnings

- `preflight.sh qa-policy standard code` reported `plan-check:selected-independent-pass:final-verify`, with `1x-deep-reviewer+2x-fast-reviewers` as an upper bound for a selected independent pass and inline-review fallback when independent delegation is unavailable.
- Assurance supplied here: approved-plan inspection, inline implementation review, focused compile/tests, selected scroll/control/process regressions, exact mirror parity, and diff hygiene. Final full-suite verification remains for `code-test`.
- Preserve the planning-stage runtime warning: the required `codex-headless` spec-read marker could not be written under `/home/Uihyeop/agent_setting/.spec-grounding` because that runtime path was read-only. The PRD was read in planning and the route/spec transaction was wrapper-validated; do not claim that marker succeeded.

## Next-stage handoff

`code-test` should run the canonical full Fleet discovery command from the approved plan, retain the explicit mirror-parity and diff checks in final evidence, and verify the four-file scope before integration.

## Recovery fix — preserve folded summaries in live rendering

### Assignment and result

- Route / node / attempt: `rt-89280d33a6010a5a` / `execute` /
  `att-a508842d2c4b47ae8ae381f124d40600`.
- Result: PASS for the bounded recovery `code-execute` gate. No commit, merge,
  push, cleanup, spec edit, or full-suite run was performed.
- Standard code QA policy remained
  `plan-check:selected-independent-pass:final-verify`; this stage supplies the
  focused implementation assurance, while the retry `code-test` stage owns the
  independent final verification.

### Source correction

- `tools/fleet/render.py`: live reconciliation now separates anchored visible
  project cards from non-card groups. Only visible cards enter
  `_LiveOrderState.reconcile_groups`; folded/empty groups remain in snapshot order
  in the render-loop input, so the unchanged `folded_groups` aggregation still
  emits `inactive +N folded <names>`. A folded group is absent from group/session
  anchors and appends after surviving cards when it becomes visible again.
- `tools/fleet/tests/test_stable_live_order.py`: added a live-state render regression
  that compares snapshot/live folded-summary output, asserts folded anchor pruning,
  reveals the previously folded group ahead of the snapshot sort but after the
  surviving live anchor, refolds it, and proves the second reveal appends again.
- `adapters/claude/tools/fleet/render.py` and
  `adapters/claude/tools/fleet/tests/test_stable_live_order.py` contain the exact
  byte-identical mirror correction and coverage.

### Verification evidence

All commands ran from
`/home/Uihyeop/agent_setting-wt/fleet-stable-session-order` and exited 0:

1. `python3 -m py_compile tools/fleet/render.py tools/fleet/tests/test_stable_live_order.py`
   — PASS.
2. `(cd tools && python3 -m unittest fleet.tests.test_stable_live_order -v)`
   — PASS, 5 tests including folded-summary parity and prune/reveal.
3. `(cd tools && python3 -m unittest fleet.tests.test_scroll_regression fleet.tests.test_f27_control fleet.tests.test_f30_process_view -v)`
   — PASS, 111 tests. The existing non-failing `ResourceWarning` at
   `test_f27_control.py:521` remains.
4. `(cd tools && python3 -m unittest fleet.tests.test_mirror_parity -v)`
   — PASS, 1 test.
5. Canonical/mirror `cmp -s` checks for renderer and focused test pairs — PASS.
6. `git diff --check` — PASS.

The full suite was deliberately not run because this recovery assignment reserves
it for the retry verifier. Its canonical invocation is corrected to run from the
repository root:

```sh
python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py' -v
```

The prior `(cd tools && ...)` discovery attempt was a verification-environment
error: unchanged `test_v20_dispatch_contract` imports `tools.*`, which requires the
repository root on `sys.path`. No source fix was made to that unchanged test.

### Scope and warnings

- Worktree source changes remain the planned canonical renderer/test and their
  exact Claude mirrors; no collector, model, control, route, spec, or runtime file
  changed.
- Preserve the planning warning: the earlier `codex-headless` spec-read marker
  could not be written beneath the read-only `.spec-grounding` runtime path. This
  stage made no spec change and does not claim that marker succeeded.
