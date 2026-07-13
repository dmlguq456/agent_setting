# Implementation Log

- Updated `.agent_reports/spec/agent-fleet-dashboard/prd.md` to v4/F-20 and snapshotted the prior PRD at `.agent_reports/spec/agent-fleet-dashboard/_internal/versions/v3/prd.md`.
- Generalized Codex fleet usage parsing to prefer `limit_window_seconds`, keep legacy `primary=5h`/`secondary=7d` fallback only when duration is absent, and render dynamic windows ahead of legacy slots.
- Updated `utilities/usage-check.sh` so known future reset times remain authoritative beyond the old 300-minute marker age, unknown-reset stays bounded, and default bias is neutral `auto` unless `HARNESS_CAPACITY_BIAS` is set.
- Added `loops/runtime-watch.md` and `loops/runtime-watch.sh` as a report/proposal loop that separates official runtime support, local projection, parity gaps, and fallback; it does not edit policy automatically.
- Synced loop/fleet/tool projections required by the repository boundary: Claude loop concrete projection, Claude fleet concrete mirror, shared tool symlink collapse, Codex/OpenCode loop-info, README/manifest/install layout.

Inline QA note: no independent QA delegation was claimed; standard QA was handled through deterministic tests and adapter boundary/doctor checks.
