# pipeline_summary — dispatch-routing-policy-v7

## Final evidence

- Canonical Fleet full suite: **165/165 PASS**; mirror parity **PASS**.
- Live dispatch-routing tree **2 → 1**; two legitimate interactive Codex sessions remain, with no headless/detached top-level row.
- `dispatch-route.test`, `usage-check.test`, exact mapping probes, Codex/OpenCode projection checks, and `git diff --check`: **PASS**.
- Deep: Codex `gpt-5.6-sol/high`, Claude `opus/high`; balanced: Codex `gpt-5.6-terra/medium`, Claude `sonnet/medium`; fast implementer=Terra; fast reviewer/tool=Luna; memory-scout=Luna low/read-only. OpenCode deep/balanced are config-driven; concrete model unknown.
- Adaptation-boundary still has exactly 18 pre-existing missing Claude mirror paths; new memory-scout and dispatch-route/model-map checks pass.
- Portable-guards is not claimed green because the existing liveness shell/doctor block is flaky/pre-existing; focused new role/memory/Fleet/model checks pass. Drill was not run.
- `code-test-r2` stopped after live duplicate-tree reproduction; a focused quick Fleet worker fixed and verified it.

F1/F2/F3 are resolved: maker-family consumed, portable role normalization restored, selector coverage expanded, and Sol/Terra/Luna split complete.

## Handoff

Commit, merge, push, runtime installation, and worktree cleanup remain with the parent orchestrator.
