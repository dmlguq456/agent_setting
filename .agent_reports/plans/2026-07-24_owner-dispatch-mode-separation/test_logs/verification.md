# Verification log

## Final gates

- `preflight.sh verification-runner --timeout 900 -- hooks/portable-guards.test.sh`
  — `PASS=358 FAIL=0`, including installed projection and strict runtime doctor
  fixtures.
- `python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py'`
  — `Ran 871 tests`, `OK`.
- `python3 tools/generate.py --check` — all generated projection groups current.
- `tools/check-adaptation-boundary.sh` — passed; only the documented portable
  reference warning remained.
- Installed `check-runtime-projection.sh` — hook trust, bootstrap, plugin, native
  skills/agents and active builder profile all `status=ok`.
- `preflight.sh doctor --runtime` — generated projections, native subagents, hooks,
  token budget, adaptation boundary, and runtime projection all `status=ok`.

## Focused regression

Shared mode-contract tests, cross-adapter mode-axis tests, all three SD-45 suites,
all SD-15 suites, dispatch-node, stage-fallback, route, prompt, artifact-root,
parent-context, completion-marker, and the actual depth-2 start drill passed before
the final full gates.

The final rebase exposed four fixture-only failures after the harness root resolver
was tightened on `main`. Explicit source-worktree `AGENT_HOME` fixtures and the
canonical-root fallback expectation were corrected; the complete portable suite
then passed with no product-code regression.
