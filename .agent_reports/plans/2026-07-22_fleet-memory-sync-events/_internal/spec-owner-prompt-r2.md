No asynchronous Monitor/wakeup/scheduling waits. Poll every registered child synchronously in this turn with `utilities/dispatch-wait.sh`, then harvest it. Do not return while a child is merely running.

Resume the approved `autopilot-spec update / standard` prerequisite after the first owner attempt was terminated before any writes because it passed its owner prompt to the research node, causing recursive self-wait. Do not repeat that prompt binding.

Immutable composed route: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/_internal/spec-route-composed.json` (`rt-4fb68fb6acaefc97`).
Worktree: `/home/Uihyeop/agent_setting-wt/fleet-memory-sync-events`.
Canonical artifact root: `/home/Uihyeop/agent_setting/.agent_reports`.
Cycle root: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events`.

Read `capabilities/autopilot-spec.md` completely and validate yourself against node `prd-transaction`. Dispatch exactly these dependency retries in order:

1. node `research`, slug `fleet-memory-sync-spec-research-r2`, mode `research/research-survey`, model role `deep maker`, prompt file `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/_internal/spec-research-prompt.md`;
2. after a PASS marker and harvest, node `review`, slug `fleet-memory-sync-spec-review-r2`, mode `research/plan-review`, model role `deep reviewer`, prompt file `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/_internal/spec-review-prompt.md`.

Never pass this owner prompt to a depth-2 child. Do not create any other child or dispatch depth 3.

After both exact markers PASS, re-read and mark both governing PRDs and run the declared git/spec guards. Under one `utilities/spec-transaction.py` transaction for node `prd-transaction`:

- snapshot the previous root PRD to the next version directory;
- snapshot the previous Fleet PRD under that same version directory preserving its `agent-fleet-dashboard/prd.md` relative path;
- clarify root D-37 and Fleet F-19/F-35f that a newly persisted migrate/sync absorption emits `action=add`, `actor=sync`, and the logical source project cwd;
- require repeat sync with no new persisted record to emit zero events;
- explicitly exclude historical journal backfill;
- update canonical `pipeline_state.yaml` and append the concise decision to `pipeline_summary.md`.

Do not edit source code, tests, core files, adapters, runtime-owned data, or Git history. Produce `_internal/spec-owner-report.md`, complete the exact `prd-transaction` marker/attempt, harvest your row, and end with the worker kernel's exact three-line handoff.
