# Assigned code-test stage: Fleet stable live ordering

Work only as the registered dispatch-depth-2 `code-test` stage for route
`rt-89280d33a6010a5a`, node `test`, parent `fleet-stable-order-owner`.
Follow the supplied Portable Worker Kernel and stage contract. Do not dispatch,
commit, merge, push, clean worktrees, rewrite specs, or modify runtime-owned
state. This is the selected final independent verification pass required by
standard code QA.

File-only inputs:

- worktree: `/home/Uihyeop/agent_setting-wt/fleet-stable-session-order`
- canonical cycle: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-21_fleet-stable-session-order/`
- `plan.md`, `checklist.md`, and `dev_logs/execute.md` in that cycle
- implementation diff in the worktree (canonical and exact Claude mirror)
- Fleet PRD v13 and `spec_update_evidence.md` are read-only context

Independently inspect the diff against the approved plan and PRD v13. Run and
record exact results for at least:

```sh
python3 -m py_compile tools/fleet/render.py tools/fleet/tests/test_stable_live_order.py
(cd tools && python3 -m unittest fleet.tests.test_stable_live_order -v)
(cd tools && python3 -m unittest fleet.tests.test_scroll_regression fleet.tests.test_f27_control fleet.tests.test_f30_process_view -v)
(cd tools && python3 -m unittest fleet.tests.test_mirror_parity -v)
(cd tools && python3 -m unittest discover -s fleet/tests -p 'test_*.py' -v)
git diff --check
```

Also verify exact canonical/mirror bytes and that the changed-file set contains
only planned Fleet renderer/test surfaces. Review boundedness, prune/reset,
session/group stable identity, initial/new-row snapshot ordering, stateless
`--once`/JSON behavior, process-view isolation, selection/scroll preservation,
and absence of F-25 state changes. Preserve the known read-only Codex spec-read
marker warning without treating it as missing spec evidence.

Write durable evidence under `test_logs/` and update only verification fields in
`checklist.md`, running preflight write guards first. If a test or review gate
fails, return FAIL with precise evidence; do not waive it or silently patch
source in this verification stage.

Completion gate: all required verification passes and the durable test report
contains exact commands, counts, review findings, and residual risk.
