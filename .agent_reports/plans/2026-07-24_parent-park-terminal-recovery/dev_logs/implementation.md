# Implementation log

## Root cause

`pretooluse-write-guard.py` selected `done && process_quiescence != quiescent`
for every parent session. That state is correct for successor readiness and for a
registered owner whose supervisor or explicit poll fallback still owns completion
delivery, but it is not recoverable through the ordinary interactive hook's
wait/harvest allowlist. A terminal-unverifiable row therefore became a permanent
session-wide tool lock.

## Change

- Added an explicit internal strict set: `supervised` and wrapper-projected `poll`.
- Exact latest `open|running` rows park every matching parent as before.
- Terminal non-quiescent rows park only the two registered completion-delivery modes.
- Ordinary interactive sessions can use unrelated local tools while the terminal row
  remains unchanged and visible; readiness/join/wait/fallback/cleanup stay fail-closed.
- Updated core first, then Codex README/ADAPTATION and the adapter hook.
- Native Codex subagent code and registered runtime state were not modified.

## Recovery discipline

The operator-provided `AGENT_PARENT_PARK_BYPASS=1` was used only to reach this
self-repair path. No jobs row was closed, deleted, rewritten, or inferred dead.
