# Fleet stable live ordering — final code-cycle record

## Final verdict: PASS

The approved Fleet PRD v13 behavior is implemented and independently verified. A
live curses run now owns one run-local `_LiveOrderState`: the first build and
stateless paths retain deterministic snapshot order; surviving visible project
groups and sessions retain relative order across redraws; newly visible rows
append in current snapshot order; disappeared rows are pruned; and a new live
run resets the anchors. Folded/empty groups remain available to the existing
folded-summary aggregation while their live anchors are pruned. Process view,
dispatch-job ordering, status classification, grouping, selection, scrolling,
and JSON/`--once` stateless behavior remain unchanged.

## Exact changed files

The final worktree contains exactly these four uncommitted changes:

- `tools/fleet/render.py` — canonical live-order state, identity and
  reconciliation logic, visibility-aware rendering, and `_loop`/`_draw`
  threading.
- `tools/fleet/tests/test_stable_live_order.py` — focused stable-order,
  prune/reveal, reset, stateless, and folded-summary regression coverage.
- `adapters/claude/tools/fleet/render.py` — byte-identical Claude mirror.
- `adapters/claude/tools/fleet/tests/test_stable_live_order.py` —
  byte-identical Claude mirror test.

No collector, model, control, route, specification, runtime-state, or
configuration file changed. `HEAD` is still
`781581bce0bac0ca51c70f676843457f68781ec7`.

## Stage history

1. The initial `code-execute` worker implemented the carried source/test diff,
   then hit model capacity after its write guards for `dev_logs/execute.md` and
   `checklist.md`. Dispatch closed that attempt as failed; no source rollback
   or completion marker was claimed.
2. The execute recovery inspected the carried diff, preserved the four-file
   scope, and recorded the focused implementation checks. It also corrected the
   folded-summary regression: only visible cards are reconciled, while folded
   and empty groups remain in snapshot order for the unchanged folded summary.
3. The first independent `code-test` pass failed on that folded-summary
   regression (`snapshot_has_folded=True`, `live_has_folded=False`) and also
   reported an import error from the prescribed discovery command run as
   `(cd tools && python3 -m unittest discover -s fleet/tests -p 'test_*.py' -v)`.
   The unchanged `test_v20_dispatch_contract` imports `tools.*`, so that
   working-directory failure was an environment/discovery-command issue; no
   source was changed for it.
4. The corrective execute pass added the folded-summary render regression and
   corrected the canonical discovery invocation to run from repository root.
5. The independent test retry passed the folded-summary/prune/reveal behavior
   and all required verification commands. The retry changed no source file.

## Verification evidence

All commands were run from
`/home/Uihyeop/agent_setting-wt/fleet-stable-session-order`, except the
discovery command, which intentionally ran from the repository root:

1. `python3 -m py_compile tools/fleet/render.py tools/fleet/tests/test_stable_live_order.py`
   — exit 0.
2. `(cd tools && python3 -m unittest fleet.tests.test_stable_live_order -v)`
   — exit 0; 5 tests passed in 0.019s.
3. `(cd tools && python3 -m unittest fleet.tests.test_scroll_regression fleet.tests.test_f27_control fleet.tests.test_f30_process_view -v)`
   — exit 0; 111 tests passed in 2.237s. The existing non-failing
   `ResourceWarning` at `test_f27_control.py:521` remains.
4. `(cd tools && python3 -m unittest fleet.tests.test_mirror_parity -v)`
   — exit 0; 1 test passed in 0.013s.
5. `python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py' -v`
   — exit 0; 738 tests passed in 19.115s. This is the corrected canonical
   root invocation; the earlier `cd tools` failure was not a source failure.
6. `git diff --check` — exit 0.
7. `cmp -s tools/fleet/render.py adapters/claude/tools/fleet/render.py` and
   the equivalent focused-test comparison — both exit 0. Retry SHA-256 values:

   ```text
   64fc2960eb9a92ddc10009c32b8b5dd292e76b2bca8e6685cbaee54e01afb36e  tools/fleet/render.py
   64fc2960eb9a92ddc10009c32b8b5dd292e76b2bca8e6685cbaee54e01afb36e  adapters/claude/tools/fleet/render.py
   2c15c0e7370af964ef336e905afcc54520f932c87aec00f743edd707a925d557  tools/fleet/tests/test_stable_live_order.py
   2c15c0e7370af964ef336e905afcc54520f932c87aec00f743edd707a925d557  adapters/claude/tools/fleet/tests/test_stable_live_order.py
   ```

Standard QA assurance was `plan-check:selected-independent-pass:final-verify`;
the selected independent retry supplied the final verification. Route spec
evidence was already wrapper-validated and `spec_update_evidence.md` records a
PASS within-spec PRD v13 alignment. The required Codex headless spec-read
marker could not be written because `/home/Uihyeop/agent_setting/.spec-grounding`
was read-only; this warning is preserved, and no spec edit was made.

## State and handoff

There are no staged changes and no commit. No merge, push, integration, or
worktree cleanup was performed. Uncommitted attribution is handed to the
dispatch-depth-0 owner for integration.

Residual risk is low: focused live rendering tests exercise `_build_lines`, not
a real end-to-end curses TTY; terminal redraw timing is covered structurally by
the single `_loop` owner plus existing draw/selection/scroll regressions.
Defensive identity collisions preserve all rows but use current snapshot order
within the collision bucket. The existing non-failing `ResourceWarning` remains
the only recorded test warning.
