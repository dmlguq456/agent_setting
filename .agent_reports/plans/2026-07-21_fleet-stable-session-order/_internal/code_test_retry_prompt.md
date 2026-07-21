# Assigned code-test retry: Fleet stable live ordering

Work only as the registered dispatch-depth-2 `code-test` retry for route
`rt-89280d33a6010a5a`, node `test`, parent `fleet-stable-order-owner`.
Follow the supplied Portable Worker Kernel and stage contract. Do not dispatch,
commit, merge, push, clean, rewrite specs, or patch source.

File-only inputs:

- worktree `/home/Uihyeop/agent_setting-wt/fleet-stable-session-order`
- canonical cycle `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-21_fleet-stable-session-order/`
- `plan.md`, `checklist.md`, revised `dev_logs/execute.md`
- prior failing independent report `test_logs/verification.md`
- corrected uncommitted canonical/mirror source and focused tests

Independently confirm that the folded-summary regression is fixed and the new
live-state visibility/prune/reveal test is effective. Re-run:

```sh
python3 -m py_compile tools/fleet/render.py tools/fleet/tests/test_stable_live_order.py
(cd tools && python3 -m unittest fleet.tests.test_stable_live_order -v)
(cd tools && python3 -m unittest fleet.tests.test_scroll_regression fleet.tests.test_f27_control fleet.tests.test_f30_process_view -v)
(cd tools && python3 -m unittest fleet.tests.test_mirror_parity -v)
python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py' -v
git diff --check
```

The full discovery command intentionally runs from repository root because the
unchanged `test_v20_dispatch_contract.py` imports `tools.*`; the prior `cd tools`
variant was a verification-environment error, not a source defect. Verify exact
canonical/mirror bytes, exact four-file source change scope, bounded anchor
prune/reset, survivor/new-row rules, stateless snapshot behavior, folded summary,
process view, selection/scroll, and F-25 isolation.

Replace or append the durable `test_logs/verification.md` with complete retry
evidence, preserving the failed first-pass history, and update verification
checkboxes only after all gates pass. Run preflight write guards before artifact
edits. Preserve the read-only Codex spec-marker warning.

Completion gate: all commands exit 0, independent behavioral review passes, and
the durable report records exact counts plus residual risk.
