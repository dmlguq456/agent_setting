# Direct Headless Resilience — implementation log

status: complete
worktree: `/home/Uihyeop/agent_setting-wt/direct-headless-resilience`

## SD-58

- Added the shared exact-attempt/progress classifier and bounded progress
  fingerprint in `tools/fleet/model.py`.
- Added atomic per-attempt heartbeat/watchdog state in
  `utilities/dispatch-progress.py` and synchronous observation/continuation in
  `utilities/stage-dispatch-fallback.py`.
- Added real stage heartbeat calls to generated prompts and launch heartbeat
  seeding in all direct wrappers.
- Added exact process-group interruption, locked `dead-no-progress` closure,
  native-child proof, and deterministic write/artifact/test evidence.
- Final smoke hardening records depth-2 launch PIDs as
  `pid_scope=namespace-local`. Fleet, portable registry, and runtime liveness
  use a fresh exact heartbeat instead of root `/proc`; terminal heartbeat is
  `done`, and stale evidence falls back without a false host-PID death.

## SD-59

- Centralized strict anchored capacity parsing in `dispatch_contract.py`.
- Added exact `dead-capacity` closure and model/profile evidence to Claude,
  Codex, and OpenCode wrappers without giving wrappers model-selection power.
- Added allowlisted adapter-paired alternative selection, cooldown evidence,
  stable retry identity, one-retry authority, and ordinary fallback descent.
- Made per-attempt logs unique so an older capacity line cannot poison a newer
  attempt.

## SD-60 and Fleet

- Added selected current views and guarded reconciliation in
  `utilities/dispatch-registry.py`, including exact-dead, SD-29 merged,
  stale-terminal, namespace-terminal, unsafe veto, dry-run, apply,
  idempotency, and concurrent locked revalidation.
- Projected current/reconcile/heartbeat through Codex preflight and all relevant
  liveness paths.
- Preserved exact `pid + pid_start + attempt_id` and deterministic newest
  attempt presentation. Synchronized `tools/fleet/` and the Claude mirror
  byte-for-byte.

## Commits and integration

- `821405f3 feat(dispatch): add direct-headless watchdog failover reconciliation`
- `3b9622a2 fix(dispatch): close resilience edge cases`
- `f59163e8 fix(dispatch): classify namespace-local depth2 attempts`
- Merged to main as `7480c5bc`, `8d51304d`, and `5fbace3e`.
- Linked runtime projections for Claude, Codex, and OpenCode were refreshed and
  reported `fresh`, with no duplicate sources.

No broker, spool, socket authority, resident watcher, lease, or supervisor was
introduced. Historical broker compatibility code is outside the active call
graph and remains retired.
