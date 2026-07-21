# Assigned code-execute fix: preserve folded summary

Work only as a registered dispatch-depth-2 `code-execute` correction for route
`rt-89280d33a6010a5a`, node `execute`, parent `fleet-stable-order-owner`.
Follow the supplied Portable Worker Kernel and stage contract. Do not dispatch,
commit, merge, push, clean, rewrite specs, or modify runtime-owned state.

Required file-only inputs:

- approved cycle `plan.md` and `checklist.md`
- current uncommitted Fleet canonical/mirror diff
- prior execute evidence: `dev_logs/execute.md`
- failing independent review: `test_logs/verification.md`
- worktree `/home/Uihyeop/agent_setting-wt/fleet-stable-session-order`
- canonical cycle `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-21_fleet-stable-session-order/`

Fix the verified live-state regression: current `live_order` reconciliation
replaces the render-loop group order with visible cards only, so stale-only
groups never reach the unchanged `folded_groups` aggregation and the live TUI
drops `inactive +N folded <names>`. Preserve folded groups in the render input
while pruning them from live anchors. Add focused live-state render coverage
that fails on the current diff and proves folded summary parity plus prune/reveal
behavior; add any other small missing focused assertion needed for this exact
bug. Keep canonical and Claude mirror byte-identical.

Do not patch the unchanged `test_v20_dispatch_contract` import. The prior test
stage ran discovery after `cd tools`, but that test imports `tools.*`; the
canonical root invocation is `python3 -m unittest discover -s tools/fleet/tests
-p 'test_*.py' -v` and will be used by the retry verifier. Record this command
correction as a verification-environment correction, not a source fix.

Run preflight write guards before edits, focused stable-order and selected
regressions, mirror parity, and `git diff --check`. Update `dev_logs/execute.md`
with an appended fix section and truthfully update `checklist.md`. Do not run
the full suite; code-test retry owns final verification.

Completion gate: folded summaries remain unchanged in live rendering, focused
coverage proves it, all focused checks and mirror parity pass, and durable fix
evidence is complete.
