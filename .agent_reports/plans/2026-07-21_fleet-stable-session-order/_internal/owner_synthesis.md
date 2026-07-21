# Fleet stable session order — owner synthesis

## Verdict

PASS. Route `rt-89280d33a6010a5a` completed the registered depth-2
`code-plan -> code-execute -> code-test -> code-report` pipeline, including one
verification-driven execute correction and a passing independent test retry.
The public cycle record is `../pipeline_summary.md`.

## Completion evidence

- Source base/HEAD: `781581bce0bac0ca51c70f676843457f68781ec7`.
- Spec significance: `within-spec` against recovered Fleet PRD v13; the spec
  transaction remained read-only during code work.
- Final source scope: exactly canonical/mirror `render.py` plus canonical/mirror
  `test_stable_live_order.py`; no staged changes and no commit.
- Plan marker: route node `plan`, schema v2, sequence 1.
- Execute marker: route node `execute`, schema v2, sequence 2, evidence
  `dev_logs/execute.md`.
- Test marker: route node `test`, schema v2, sequence 1, evidence
  `test_logs/verification.md`.
- Report marker: route node `report`, schema v2, sequence 1, evidence
  `pipeline_summary.md`.
- Final verification: 5 focused stable-order tests, 111 selected
  scroll/control/process-view regressions, explicit mirror parity, and 738-test
  canonical root discovery all passed; `git diff --check` and both byte mirrors
  passed.

## Implemented contract

One `_LiveOrderState` is constructed per curses `_loop`. Existing deterministic
snapshot sorts seed the first live ordering and order newcomers; survivor group
and session identities retain their relative positions; removals prune bounded
anchors; reappearing rows append; a new loop resets state. Stateless
`render_once`/JSON, process view, dispatch order, selection, scroll, grouping,
folded summaries, and F-25 classification remain unchanged.

## Recovery history and warnings

- The initial execute worker produced the source/test diff and focused PASS
  evidence, then failed on model capacity before durable handoff. A registered
  cooled-model recovery completed the execute artifact.
- The first independent test pass correctly found that the live path dropped
  folded summaries. A registered execute correction preserved folded aggregate
  input while pruning only card anchors, added live prune/reveal coverage, and a
  second independent test pass verified the fix.
- The first full discovery command used the wrong working directory; the retry
  used canonical root invocation `python3 -m unittest discover -s
  tools/fleet/tests -p 'test_*.py' -v` and passed 738 tests. No source change was
  made for the environment error.
- Codex could read Fleet PRD v13, but its headless marker write under the
  read-only `.spec-grounding` runtime path failed. The route already carried
  validated spec-read evidence and `spec_update_evidence.md` records the locked
  recovered spec PASS; no spec claim depends on a successful new marker.
- The branch is two commits behind the current upstream snapshot. Integration,
  attribution, commit, push, and cleanup remain dispatch-depth-0 responsibilities.

Residual risk is low: live behavior is exercised at the render-builder and
interaction-regression layers rather than by an end-to-end real curses TTY.
