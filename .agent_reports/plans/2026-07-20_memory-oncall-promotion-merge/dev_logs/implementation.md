# Implementation log

## Selective port

- Ported only the incident-to-proposal bridge from `8ceb3cbd`; no file or
  behavior from `35a0c75d` was copied.
- Added D-43 after current D-40~42 instead of reusing the stale branch's D-41.
- Updated the dedicated self-improvement governance contract to v2 under the
  shared spec lock, with byte-exact v19/v1 snapshots.

## Hardening beyond the source branch

- Enforced a CLI-level `loop:*` ceiling: named collectors can target only
  `reproduced` or `proposed`.
- Rejected named-collector transitions after any prior human-owned proposal
  state, including a reviewed proposal later moved to deferred.
- Scoped current-context reproduction rebase to named collectors; manual actor
  behavior remains compatible with v1.
- Validated positive occurrence counters and bounded evidence/top-level history
  at 128 before copying recurrence evidence.
- Preserved the 2026-07-15 worklog approval parser contract: one promoted
  incident is one `## ` finding block.
- Synchronized Claude loop guidance and Codex/OpenCode manual `loop-info`
  metadata without claiming a native executable loop surface.

## Excluded commit

`35a0c75d` remains archive-only. It conflicts with D-42 by launching a daily
memory curator from an on-call worker, exceeds D-41 defaults, amplifies full
sync across repositories, and lacks safe cursor/journal/action transaction
semantics. No `daily-curator` path or hard-coded worker behavior is present in
the implementation diff.

## Verification completed before commit

- Proposal lifecycle and on-call contract: 24/24 PASS.
- Generated projection semantic verifier: 29/29 PASS.
- Portable guards: 355/355 PASS.
- Generation, adaptation boundary, Skill conformance, runtime activation,
  extension lifecycle, and managed release: PASS.
- Python/shell syntax and `git diff --check`: PASS.
- The first adaptation run overlapped the projection test's intentional
  temporary mutation and produced a false stale-file report; isolated rerun
  passed with no generated-file diff.
