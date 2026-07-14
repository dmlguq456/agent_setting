# Self-Improvement Governance — Pipeline Summary

## 2026-07-14 — v1 specification

- Chose proposal-gated improvement instead of active self-edit.
- Split portable proposal adoption from version-bound runtime realization.
- Assigned the evidence inbox to XDG state outside runtime discovery and repo source.
- Limited the first implementation to an inactive local CLI and deterministic tests.
- Explicitly excluded hooks, cron, plugin installation, runtime config mutation, and automatic adoption.

## 2026-07-14 — v1 implementation

- Added the offline XDG proposal inbox and dual proposal/realization state machines.
- Added exact context-fingerprint freshness gates and explicit approval provenance.
- Added bounded evidence copies, path isolation, locking, and atomic records.
- Added core/loop ownership contracts and Claude collapsed projection; Codex and OpenCode native projection is explicitly deferred.
- Passed lifecycle, adaptation, generation, runtime activation, extension, and managed release regressions without changing runtime-owned state.

## 2026-07-14 — v2 on-call promotion specification

- Allowed the scheduled on-call agent to use recent memory mutations as discovery signals.
- Required full-body memory reads and current source/log/test/runtime corroboration before promotion.
- Chose agent-authored exact incident keys; deterministic code only deduplicates exact matches.
- Limited unattended promotion to `observed`, `reproduced`, or `proposed`; review, adoption, and activation remain human-owned.
- Required recurrences to append evidence without reopening or changing reviewed/terminal proposal state.

## 2026-07-14 — v2 implementation

- Connected on-call memory discovery to the offline proposal inbox without adding an apply or activation path.
- Added exact incident-key recurrence under the existing inbox lock, including concurrent collector coverage and ambiguous-key fail-closed behavior.
- Preserved proposal state and base context on ingest; only a fresh context-bound reproduction can rebase a stale pre-review proposal.
- Added a 128-item evidence/history ceiling and kept incoming recurrence context as a fingerprint rather than another full context copy.
- Synchronized the concrete Claude loop projection; Codex and OpenCode continue to consume the canonical loop contract through their existing runners.
- Passed proposal, generation, projection, adaptation, skill, runtime activation, extension, and release regressions.
