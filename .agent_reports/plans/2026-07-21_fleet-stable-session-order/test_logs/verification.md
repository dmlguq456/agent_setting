# Fleet stable live ordering — code-test verification

## Verdict

FAIL. The selected independent verification pass found a user-visible folded-summary
regression in the live-state path, and the required canonical discovery command did
not exit successfully. No source file was changed or patched by this stage.

## Assignment and assurance

- Route / node / attempt: `rt-89280d33a6010a5a` / `test` /
  `att-acdd12dea0c1ebcb86ac006daf391ea03e66e01c3650b8b1`.
- Target: implementation diff against the approved `plan.md`, Fleet PRD v13,
  `checklist.md`, `dev_logs/execute.md`, and `spec_update_evidence.md`.
- QA policy: `standard` code; `plan-check:selected-independent-pass:final-verify`.
  Policy output named `1x-deep-reviewer+2x-fast-reviewers` as the upper bound for
  the selected pass, skipped the code-track fact checker and external adversary,
  and permitted an inline-review fallback only when an independent pass was
  unavailable. This registered dispatch-depth-2 `code-test` stage is the selected
  independent deep-reviewer pass; it did not dispatch further workers.
- Spec significance remains `within-spec`. The PRD and evidence were read-only.
- Preserved warning: the earlier `codex-headless` spec-read marker could not be
  written under the read-only `.spec-grounding` runtime path. The PRD v13 content
  was available and read; this is a marker warning, not missing spec evidence.

## Changed-file and mirror evidence

`git status --porcelain=v1` reported exactly the four planned surfaces:

```text
 M adapters/claude/tools/fleet/render.py
 M tools/fleet/render.py
?? adapters/claude/tools/fleet/tests/test_stable_live_order.py
?? tools/fleet/tests/test_stable_live_order.py
```

`git diff --cached --name-only` was empty. No collector, model, control, route,
spec, state/runtime, or configuration surface changed. `HEAD` was
`781581bce0bac0ca51c70f676843457f68781ec7`, exactly the approved source commit;
the corresponding merge-base ancestry check exited 0.

Exact canonical/mirror checks both exited 0:

```text
cmp -s tools/fleet/render.py adapters/claude/tools/fleet/render.py
cmp -s tools/fleet/tests/test_stable_live_order.py adapters/claude/tools/fleet/tests/test_stable_live_order.py
```

SHA-256 evidence:

```text
7d432b0bb64099794f7fd86a9c436b74254a6fd9395bd02a1cbdd5478bb36f03  tools/fleet/render.py
7d432b0bb64099794f7fd86a9c436b74254a6fd9395bd02a1cbdd5478bb36f03  adapters/claude/tools/fleet/render.py
f0bbb0517dbc2f5bf9f4d60a4712523cee6ddee25885eec5a8a9bf5f70f807d8  tools/fleet/tests/test_stable_live_order.py
f0bbb0517dbc2f5bf9f4d60a4712523cee6ddee25885eec5a8a9bf5f70f807d8  adapters/claude/tools/fleet/tests/test_stable_live_order.py
```

## Required command results

All commands ran from
`/home/Uihyeop/agent_setting-wt/fleet-stable-session-order` in the prescribed
order unless the command itself changes directory.

1. `python3 -m py_compile tools/fleet/render.py tools/fleet/tests/test_stable_live_order.py`
   - Exit 0; no output.
2. `(cd tools && python3 -m unittest fleet.tests.test_stable_live_order -v)`
   - Exit 0; 4 tests passed in 0.018s.
3. `(cd tools && python3 -m unittest fleet.tests.test_scroll_regression fleet.tests.test_f27_control fleet.tests.test_f30_process_view -v)`
   - Exit 0; 111 tests passed in 2.245s.
   - One non-failing, pre-existing `ResourceWarning` reported an unclosed read in
     `test_f27_control.py:521`.
4. `(cd tools && python3 -m unittest fleet.tests.test_mirror_parity -v)`
   - Exit 0; 1 test passed in 0.011s.
5. `(cd tools && python3 -m unittest discover -s fleet/tests -p 'test_*.py' -v)`
   - Exit 1; 730 tests ran in 18.873s with 1 import error.
   - Exact failing level: `test_v20_dispatch_contract` failed to import because
     `from tools.fleet.collectors import dispatch` raised
     `ModuleNotFoundError: No module named 'tools'` from the prescribed `tools/`
     working directory. The failing test file is unchanged by this diff, but the
     required completion command nevertheless did not pass and was not waived.
6. `git diff --check`
   - Exit 0; no output.

## Independent behavioral review

### Must-fix defect — live ordering removes the folded summary

`tools/fleet/render.py:2413-2428` replaces the complete snapshot group order with
only non-folded visible cards before the existing render loop runs. The existing
fold logic at `tools/fleet/render.py:2595-2603` can therefore no longer add a
stale-only group to `folded_groups` whenever `live_order` is supplied. That is
the normal live TUI path because `_loop()` always creates and threads a
`_LiveOrderState`.

The read-only reproduction used one stale-only `alpha` session with `_SHOW_ALL`
false and called `_build_lines()` once without state and once with a fresh state.
Its exact result was:

```text
snapshot_has_folded= True
live_has_folded= False
snapshot_inactive_lines= ['· inactive  +1 folded   alpha']
live_inactive_lines= []
outputs_equal= False
```

This violates the approved plan's “folded-group summary unchanged” invariant and
the PRD v13 baseline requiring `inactive +N folded <names>`. The anchor should be
pruned for a folded group without removing that group from the separate input
used to build the folded aggregate.

### Test adequacy gap

`test_stable_live_order.py` contains four tests. Three exercise the state/helper
directly and one checks only stateless snapshot sorting. It has no live-state
render assertion for filtering/folding, no `_draw(..., live_order=...)`
interaction smoke, and no direct `render_once`/JSON or process-view parity
assertion. The selected legacy regressions give useful isolation evidence, but
they do not pass a `live_order` object through the group render path. This gap is
why the folded-summary regression passed the focused suite. Add the planned
visibility-boundary render test before re-verification.

### Reviewed invariants that remain sound

- Boundedness: reconciliation stores one group anchor list plus one session list
  per currently visible group; group pruning also drops its session-anchor entry.
- Identity: session ID, harness, and row kind are stable; sidless process rows use
  harness/PID/process-start, with cwd/slug only as the final fallback. Volatile
  liveness, mtime, elapsed, title, summary, model, effort, and screen position are
  excluded.
- Initial/new-row order: existing `_group_sort_key()` and
  `_sort_group_sessions()` still produce snapshot order before reconciliation;
  survivor order is retained and newcomers append in that snapshot order.
- Reset: state is created inside `_loop()` and is not module-global.
- Stateless paths: `render_once()` calls `_build_lines()` without `live_order`;
  `_snapshot_json()` remains in `fleet.py` and constructs no render state.
- Process view: its early return precedes reconciliation and does not mutate
  group anchors; the 20 process-view regression tests included in the selected
  111-test command passed.
- Dispatch-job ordering remains `_sort_group_jobs()` and is not included in live
  anchors.
- Selection/scroll: no identity, cursor, offset, click-map, or viewport policy was
  changed; the selected 10 scroll tests and 81 F-27 control tests passed.
- F-25 state behavior: the diff does not touch collectors, classification,
  liveness vocabulary, or state mutation/control code.

## Residual risk and handoff

The source cannot advance to `code-report` as PASS. Correct the folded-summary
regression, add a focused render test that fails on the current code, then rerun
all six required commands. Separately, the canonical discovery invocation's
unchanged `test_v20_dispatch_contract` import assumption must be resolved or the
approved command/environment corrected by an authorized implementation/refine
stage; this test stage does not waive or patch either failure.

One-line stage verdict: FAIL — live folded-summary regression plus one required
full-discovery import error.

---

# Retry verification — corrected folded summary and root discovery

## Verdict

PASS. The corrected live-state path preserves the folded summary while pruning
its anchors, the focused regression proves reveal/re-prune/re-reveal behavior,
and every required command now exits 0. This retry changed no source file.

## Retry assignment and assurance

- Route / node / attempt: `rt-89280d33a6010a5a` / `test` /
  `att-0d57a51e1a4e40ae89835669d799fe20`.
- Target: the revised `dev_logs/execute.md`, the corrected four-file source/test
  scope, and the failed first-pass report preserved above.
- QA policy: `standard` code, with assurance scope
  `plan-check:selected-independent-pass:final-verify`. The policy reported
  `1x-deep-reviewer+2x-fast-reviewers` as the upper bound for a selected pass,
  skipped the code-track fact checker and external adversary, and requires a
  separate Codex agent/headless/external pass before claiming independence.
  This registered dispatch-depth-2 retry is separate from `code-execute` and is
  the selected independent verification pass; it did not dispatch further work.
- Preserved warning: the earlier `codex-headless` spec-read marker could not be
  written under the read-only `.spec-grounding` runtime path. No spec was edited,
  and this retry does not claim that marker succeeded.

## Exact changed-file and mirror evidence

`git status --porcelain=v1` reported exactly four planned surfaces, with no
staged changes:

```text
 M adapters/claude/tools/fleet/render.py
 M tools/fleet/render.py
?? adapters/claude/tools/fleet/tests/test_stable_live_order.py
?? tools/fleet/tests/test_stable_live_order.py
```

There is no collector, model, control, route, spec, runtime-state, or
configuration change; F-25 classification and state paths are isolated from the
diff. `HEAD` remains `781581bce0bac0ca51c70f676843457f68781ec7`.

Both exact byte comparisons exited 0. Retry SHA-256 evidence is:

```text
64fc2960eb9a92ddc10009c32b8b5dd292e76b2bca8e6685cbaee54e01afb36e  tools/fleet/render.py
64fc2960eb9a92ddc10009c32b8b5dd292e76b2bca8e6685cbaee54e01afb36e  adapters/claude/tools/fleet/render.py
2c15c0e7370af964ef336e905afcc54520f932c87aec00f743edd707a925d557  tools/fleet/tests/test_stable_live_order.py
2c15c0e7370af964ef336e905afcc54520f932c87aec00f743edd707a925d557  adapters/claude/tools/fleet/tests/test_stable_live_order.py
```

## Required command results

All commands ran from the assigned worktree in the prescribed order. The full
discovery command ran from repository root as corrected by the retry assignment.

1. `python3 -m py_compile tools/fleet/render.py tools/fleet/tests/test_stable_live_order.py`
   - Exit 0; no output.
2. `(cd tools && python3 -m unittest fleet.tests.test_stable_live_order -v)`
   - Exit 0; **5 tests** passed in **0.019s**.
   - Includes the new live folded-summary equality, immediate anchor prune,
     reveal-after-survivor, re-prune, and second reveal regression.
3. `(cd tools && python3 -m unittest fleet.tests.test_scroll_regression fleet.tests.test_f27_control fleet.tests.test_f30_process_view -v)`
   - Exit 0; **111 tests** passed in **2.237s**.
   - The existing non-failing `ResourceWarning` at
     `test_f27_control.py:521` remains.
4. `(cd tools && python3 -m unittest fleet.tests.test_mirror_parity -v)`
   - Exit 0; **1 test** passed in **0.013s**.
5. `python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py' -v`
   - Exit 0; **738 tests** passed in **19.115s**.
   - The unchanged `test_v20_dispatch_contract` imports succeeded from repository
     root, confirming the first pass's failure was only its `cd tools` environment.
6. `git diff --check`
   - Exit 0; no output.

## Independent behavioral review

No must-fix issue remains in the corrected diff.

- Folded summary: live ordering now reconciles only visible card names, then
  retains non-card groups in snapshot order for the existing folded aggregate.
  The focused test proves byte-equivalent `· inactive  +1 folded   alpha`
  output with and without fresh live state, while `alpha` is absent from both
  group and per-group session anchors.
- Survivor and newcomer rules: an additional in-memory review drove the real
  `_group_sort_key()` and `_sort_group_sessions()` outputs through the
  reconciler. Snapshot swaps to `beta,alpha` and `b,a` remained live as
  `alpha,beta` and `a,b`; snapshot-first newcomers appended; pruned rows
  reappeared after survivors; a new `_LiveOrderState` followed current snapshot
  order. The corrected probe exited 0.
- Bounded prune/reset: group reconciliation drops missing group anchors and
  their session maps; session reconciliation replaces each visible group's
  anchor list with only current rows. State is constructed once inside `_loop`
  and is not module-global. A collision probe retained both rows sharing one
  defensive identity rather than dropping either.
- Stateless behavior: `_build_lines(..., live_order=None)` keeps the existing
  snapshot sorts; `render_once()` does not pass state; `_snapshot_json()` remains
  renderer-independent. The focused stateless regression and full suite pass.
- Process view: `_PROCESS_VIEW` returns before group reconciliation. A direct
  parity probe showed identical output with/without supplied state and no anchor
  mutation; all **18** `test_f30_process_view` tests within the 111-test set pass.
- Selection/scroll: state threading changes no cursor identity, click map,
  `_OFFSET`, or viewport policy. All **10** scroll regression tests and the full
  F-27 control suite pass. Dispatch children/orphans/loops still use
  `_sort_group_jobs()` and are outside the anchor model.
- F-25 isolation: the exact four-file scope contains only renderer logic and its
  canonical/mirror focused tests; the full suite passed without any collector or
  liveness-classification change.

One auxiliary review probe initially exited 1 because it incorrectly assumed a
new working group must sort ahead of an already-working alphabetically earlier
group. The corrected probe made the newcomer the sole working group, exercised
the intended snapshot-first condition, and exited 0; this was probe setup, not a
source failure.

The first post-write progress heartbeat was rejected as a phase regression
(`test->file-write`) because required tests had already advanced the registry.
The subsequent durable-artifact heartbeat used phase/kind `artifact` and was
accepted at sequence 6. This is a progress-reporting correction, not missing
artifact or verification evidence.

## Residual risk and handoff

Residual risk is low. The new focused coverage exercises `_build_lines` rather
than a real interactive curses collection tick, so terminal-specific redraw
timing is covered structurally by the single `_loop` owner and by existing
draw/selection/scroll regressions, not by an end-to-end TTY test. Defensive
identity collisions preserve all rows but necessarily use current snapshot order
inside the collision bucket. Neither risk blocks the approved contract.

One-line stage verdict: PASS — all six required commands exit 0, 738-test root
discovery passes, folded-summary/prune/reveal behavior is covered, and exact
canonical/mirror parity plus four-file scope are verified.
