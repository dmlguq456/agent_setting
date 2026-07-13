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
- [ ] Commit, merge, push, runtime installation, and worktree cleanup remain with the parent orchestrator.

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
- [ ] Utility projections/boundary checks updated (code-test stage).
- [x] Cross-runtime child/depth env markers + Codex/OpenCode procscan fix.
- [x] Code-only artifact/fuzzy stage inference.
- [x] SD-24 negative/positive fixtures.
- [x] Fleet supported Claude mirror synchronized.

## Code-test/report
- [ ] Helper, Fleet, portable guards, boundary, sync checks pass.
- [ ] Doctor/runtime/strict hook trust and diff-check recorded.
- [ ] Live exact/invalid probes run if permitted, else explicit fallback.
- [ ] Drill not auto-run.
- [ ] Final evidence/parity report; merge/cleanup left to orchestrator.
