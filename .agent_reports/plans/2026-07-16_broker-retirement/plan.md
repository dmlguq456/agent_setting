# Broker Retirement — Implementation Plan

status: approved
spec-significance: SPEC-SIGNIFICANT — stage-dispatch PRD v15 committed as `b50e4524`
worktree: `/home/Uihyeop/agent_setting-wt/broker-retirement`

## Goal

Remove the launch broker from every newly compiled and newly started stage-dispatch path. Replace it with checked direct adapter launches, an owner-only network-enabled Codex conductor profile, one stable attempt identity, and Fleet exact process evidence. Preserve v1/v2 records only as read-only migration input.

## Implementation

1. Core/runtime contract: retire broker-first wording and expose direct nested headless as the standard v3 path.
2. Route compiler: emit `dispatch_contract_version: 3`, accept only conductor direct candidates, and remove broker fields/requirements from new records while still verifying historical v1/v2 records.
3. Dispatch chain: call the selected adapter wrapper once in the caller process; do not create a daemon, socket, spool, heartbeat, request lease, or broker request identity.
4. Wrappers: stop auto-ensuring/projecting the broker; make attempt claim atomic and idempotent; enable network only for Codex depth-1 standard+ owners.
5. Eligibility: replace the fixed 2026-07-15 unsupported verdict with current command/worktree/network evidence.
6. Fleet: preserve attempt/process identity, reject cwd-wide transcript freshness when exact PID identity says exited, and deterministically select the newest active retry.
7. Compatibility: keep broker CLI/source for one release as explicit diagnostic/stop-only legacy surface, marked retired; no production path may call ensure/request.

## Verification

- Route v3 compile/verify and broker-field absence.
- Direct same/cross-harness chain with fake adapter; zero broker files/processes.
- Concurrent duplicate start produces one registry attempt and one child.
- Codex owner-only network configuration; depth-2 unchanged.
- Historical v1/v2 verification and Fleet fixture compatibility.
- Full dispatch contract, route, wrapper, Fleet, portable guard, adaptation-boundary suites.
- Independent verifier review focused on hidden daemon replacement, idempotency races, and fallback honesty.

## Integration

Commit source on `broker-retirement`, merge latest main, rerun integrated checks, merge to main, push, then run guarded worktree cleanup only if all gates pass.
