# dispatch-routing-policy-v7 checklist

## Final verification
- [x] Canonical Fleet full suite: 165/165 PASS; mirror parity PASS.
- [x] Live dispatch-routing tree 2 → 1; two legitimate interactive Codex sessions remain and no headless/detached top-level row remains.
- [x] dispatch-route.test and usage-check.test PASS; exact mapping probes PASS.
- [x] Codex/OpenCode projection checks and git diff --check PASS.
- [x] Adaptation-boundary has exactly 18 pre-existing missing Claude mirror paths; new memory-scout and dispatch-route/model-map checks PASS.
- [x] Portable-guards is not claimed green: existing liveness shell/doctor block remains flaky/pre-existing; focused new role/memory/Fleet/model checks PASS.
- [x] Drill not run; code-test-r2 stopped after duplicate-tree reproduction, then fixed and verified by a focused quick Fleet worker.

## Handoff
- [x] Report artifacts finalized.
- [x] Implementation committed, rebased onto concurrent installer work, and merged to main.
- [x] Installed Codex projection and installed `fleet` target verified from main.
- [x] Main pushed; worktree intentionally retained for the rollback window.

## Code-plan
- [x] Bootstrap, all core docs, code-plan contract, QA mode, PRD v7 read.
- [x] Status/prompt-signal/mode/route/capability/mode-info/QA policy run.
- [x] Official docs and local runtime/projection checked.
- [x] Usage, mappings, projections, Fleet collectors/tests inspected.
- [x] Plan/checklist/inline review written; no source edits.

## Code-execute
- [x] Core-first SD-21/22 contract and deep/balanced orchestrator separation.
- [x] Read-only route helper/tests using usage-check.
- [x] Claude/Codex exact role maps (Sol/Terra/Luna; balanced env knob); OpenCode honest unknown.
- [x] Wrappers consume shared adapter mappings.
- [x] Utility projections/boundary checks updated; boundary retains 18 unrelated pre-existing mirror gaps.
- [x] Cross-runtime child/depth env markers + Codex/OpenCode procscan fix.
- [x] Code-only artifact/fuzzy stage inference.
- [x] SD-24 negative/positive fixtures.
- [x] Fleet supported Claude mirror synchronized.

## Code-test/report
- [x] Helper, Fleet, focused guards, boundary, and sync checks recorded; full portable-guards is explicitly not claimed green.
- [x] Doctor/runtime/strict hook trust and diff-check recorded, including worktree projection caveats.
- [x] Live exact-model probes and fallback behavior recorded.
- [x] Drill not auto-run.
- [x] Final evidence/parity report written; merge/cleanup left to orchestrator.
