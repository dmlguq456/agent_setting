# Fleet post-unit migration — execution log

- Source commit: `a4f7f040` (`feat(fleet): project portable unit metadata`)
- Integrated branch: `codex/fleet-post-units`, rebased onto `4c7e4dab` and fast-forwarded into `main`.
- Added optional `unit` transport to Claude, Codex, and OpenCode dispatch wrappers through both jobs.log and `AGENT_DISPATCH_UNIT`.
- Added `DispatchJob.unit` and collector ingestion for process-environment and registry rows.
- Preserved `unit_catalog_digest`, `composed`, `nodes[].unit`, and `nodes[].unit_choices` through route views and JSON summaries.
- Kept `assigned_contract`, `unit`, `worker_type`, `model_role`, and legacy-only `worker_role` as separate axes.
- Updated compact Fleet projection, memory-journal `cwd` documentation, focused fixtures, and the canonical↔Claude Fleet mirror.
- Per user direction, the existing stage ordering/layout was not redesigned in this cycle.

No runtime-owned configuration, credentials, sessions, logs, caches, or user-owned stage-dispatch artifacts were modified.
