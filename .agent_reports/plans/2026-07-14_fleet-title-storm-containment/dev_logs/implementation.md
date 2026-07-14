# Implementation log

- Stopped the old live Fleet process and removed all same-user processes carrying `FLEET_TITLE_REFRESH=1`; ordinary Claude/Codex sessions were not targeted.
- Added Fleet graph cuts for `mem_worker`, `is_child`, `app_server`, dead, and stale sessions.
- Added cross-process title worker leases, persistent rolling start records, multi-boundary kill-switch checks, stale recovery, and direct-provider enforcement.
- Added cheap Claude statusline kill-switch checks before Python spawn.
- Replaced distill `find/count` concurrency logic with atomic fixed-name `mkdir` slots and persistent fixed start leases.
- Synchronized `tools/fleet/` to the Claude mirror and the Claude distill hook to its physical runtime copy.
