# Assigned code-execute recovery: finish durable Fleet handoff

Work only as a registered dispatch-depth-2 `code-execute` recovery for route
`rt-89280d33a6010a5a`, node `execute`, parent `fleet-stable-order-owner`.
Follow the supplied Portable Worker Kernel and stage contract. Do not dispatch,
commit, merge, push, clean, or alter the complete spec.

Required file-only inputs:

- worktree: `/home/Uihyeop/agent_setting-wt/fleet-stable-session-order`
- canonical cycle: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-21_fleet-stable-session-order/`
- approved `plan.md` and `checklist.md` in that cycle
- prior attempt log: `/home/Uihyeop/agent_setting/.dispatch/logs/fleet-stable-order-code-execute.att-53282a652f2720754cbb3b79cadb5ed8c6fb3851d2cc0af4.codex.jsonl`

Recovery context: the prior worker implemented the canonical and exact Claude
mirror changes in `render.py` plus `test_stable_live_order.py`. Its focused new
tests passed (4), the selected scroll/control/process regressions passed (107),
mirror parity passed (1), and `git diff --check` passed. It then hit model
capacity after its write guards for `dev_logs/execute.md` and `checklist.md`, so
the registry correctly closed that attempt as failed and no execute completion
marker exists.

Inspect the existing uncommitted diff and tests. Correct anything necessary to
meet the approved plan, run focused implementation checks sufficient to verify
the carried diff, then write the missing durable `dev_logs/execute.md` and
truthfully update `checklist.md`. Preserve the read-only Codex spec-marker
warning. Do not run the full canonical Fleet suite; code-test owns final
verification. Run every required preflight write guard before edits.

Completion gate: minimal correct source/test diff remains present, canonical and
mirror copies match, focused checks pass, and durable execute evidence plus
checklist handoff are complete.
