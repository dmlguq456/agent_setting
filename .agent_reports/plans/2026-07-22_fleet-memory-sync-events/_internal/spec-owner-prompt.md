No asynchronous Monitor/wakeup/scheduling waits. Poll every registered stage synchronously in this turn with `utilities/dispatch-wait.sh`, then harvest it. Do not return while a child is merely running.

Own the approved `autopilot-spec update / standard` prerequisite for the Fleet memory-sync attribution fix. The immutable composed route is:

`/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/_internal/spec-route-composed.json` (`rt-4fb68fb6acaefc97`).

Worktree: `/home/Uihyeop/agent_setting-wt/fleet-memory-sync-events`.
Canonical artifact root: `/home/Uihyeop/agent_setting/.agent_reports`.
Cycle root: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events`.

Read `capabilities/autopilot-spec.md` completely. Consume the route as `prd-transaction`, dispatch and close the checked registered `research` and `review` nodes in dependency order, and keep their artifacts beneath this cycle root using their declared route scopes. The diagnosis is already evidence-backed; no internet research is needed.

Approved specification decision:

- `tools/memory/mem.py migrate/sync` absorption is a memory mutation and must emit the same durable write-event journal contract that Fleet F-19 consumes.
- Attribute an absorbed auto-memory/post-it record to the logical source project cwd, never the sync process cwd.
- Use the existing `action=add` vocabulary with an explicit sync actor (recommended `actor=sync`) instead of inventing a second Fleet action family.
- Emit only after a record is newly persisted; idempotent repeat sync must emit zero duplicates.
- Do not backfill or rewrite historical user journal rows.
- Update both `/home/Uihyeop/agent_setting/.agent_reports/spec/prd.md` (D-37) and `/home/Uihyeop/agent_setting/.agent_reports/spec/agent-fleet-dashboard/prd.md` (F-19/F-35f) plus the canonical pipeline state/summary in one locked transaction.

Before writes, re-read and mark both governing PRDs, run the declared git/spec guards, and use `utilities/spec-transaction.py` for the complete multi-PRD transaction. Preserve the previous root PRD in the next version snapshot and also preserve the previous Fleet PRD under the same version snapshot with its relative component path. Do not edit source code, tests, core files, adapters, runtime state, or Git history. Produce a concise owner report at `_internal/spec-owner-report.md`, complete the exact `prd-transaction` attempt marker/row, and end with the worker kernel's exact three-line handoff.
