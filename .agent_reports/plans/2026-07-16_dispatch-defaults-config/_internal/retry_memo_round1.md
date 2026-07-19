# Retry memo — round 1 (code-test FAIL → bounded retry)

- Cycle: 2026-07-16_dispatch-defaults-config (route rt-20f4481665281810)
- code-test verdict: FAIL — `test_logs/verification.md` (codex, independent verifier)
- Retry authority: dev-pipeline Step 4, one bounded retry. Route is immutable and has
  no `refine` node, so the plan revision is folded into the `execute` redispatch
  (resume boundary `execute`), not a new node.
- Baseline to fix forward from: `7697c3b6` (tree clean, no safety-restore needed —
  the two commits are sound; the gaps are additive).

## Findings triaged

### F1 — adapter projection regression (MATERIAL, caused by this cycle) → FIX
`tools/check-adaptation-boundary.sh:1278` requires every top-level `utilities/*` file to be
classified `UTILITY_PROJECTED` or `UTILITY_DEFERRED`. New `utilities/dispatch-defaults.py`
is in neither → guard fails loud. Worse: `utilities/dispatch-route.sh` IS projected
(symlinked into `adapters/{claude,codex,opencode}/utilities/`), and it resolves the new
helper relative to the invocation path, so all three adapter-projected selectors die:

```
CASE adapter-projected-{claude,codex,opencode}-selector
exit=64  python3: can't open file '.../adapters/<h>/utilities/dispatch-defaults.py'
```

Decision: the helper is a runtime dependency of a projected selector, so it must be
projected the same way (symlink `../../../utilities/dispatch-defaults.py` in all three
adapters + add `dispatch-defaults.py` to `UTILITY_PROJECTED` and to the per-adapter
`find ... ! \( -name ... \)` allowlists). Resolving the helper from the symlink's real root
is the alternative, but projection matches the existing `dispatch-route.sh` pattern and
keeps each adapter surface self-contained.

### F2 — fixture isolation incomplete (REAL) → FIX
`utilities/dispatch-route.test.sh` runs its first `route()` block BEFORE
`export DISPATCH_DEFAULTS_CONFIG="$cfg"`, so that block still consumes the shipped
`profiles/dispatch-defaults.yaml`. The plan requires the suite to be isolated from the
repo default. Export the fixture before ANY `route()` call.

### F3 — live probe `unsupported` inside the child (ENVIRONMENT ARTIFACT) → DO NOT "FIX"
The verifier's probe returned `failure_class=auth-unavailable, probe_source=direct-auth-check,
status=unsupported`. This is NOT a regression from this cycle: the probe ran inside the
nested codex sandbox (`codex exec --sandbox workspace-write`), which cannot see the host's
codex auth state. Conductor-level probes on the same worktree returned `status=supported`
three times this cycle (12:38:01Z, 12:48:56Z probe for claude, 13:50:11Z), and every
cross-harness dispatch in this pipeline launched successfully on that evidence.
The stderr-acceptance regression test itself PASSES (4 tests OK).
Action: none in source. Record the sandbox limitation as the item-(D) finding.

### F4 — plan's unittest command is wrong (MINOR) → FIX in dev log/plan note only
`python3 -m unittest utilities/nested_dispatch_eligibility.test.py` →
`ModuleNotFoundError`; direct file execution passes. Use direct execution.

## Out of retry scope (pre-existing, NOT caused by this cycle)
- `check-adaptation-boundary.sh`: `adapters/{codex,opencode}/tools/memory/mem.py` referencing
  `CLAUDE_HOME` — fails on baseline too, untouched by these commits.
- `hooks/portable-guards.test.sh`: "codex dispatch wrapper should not trust invalid AGENT_HOME"
  — unrelated, unchanged assertion.
- PRD `exec`/`review` vs topology `plan/execute/test/report`: the canonical-node mapping is
  sound (verifier concurred); a distinct `review` coordinate needs a later spec/topology
  convergence. Carry as follow-up, do not widen this cycle.

## Retry gate
Redispatch `execute` (fix F1, F2, F4) → redispatch `test`. A second FAIL means rollback,
failed `pipeline_summary.md`, and stop before `report`.
