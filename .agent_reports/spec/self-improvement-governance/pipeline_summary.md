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

## 2026-07-20 — v2 on-call promotion specification

- Allowed the scheduled on-call agent to use recent memory mutations as discovery leads only.
- Required full-body memory reads and current source/log/test/runtime corroboration before promotion.
- Chose agent-authored exact incident keys; deterministic code only deduplicates exact matches.
- Limited named collectors to `reproduced` and `proposed`, with no transition after a prior human decision.
- Preserved the worklog approval parser contract by reporting each promoted incident as one `## ` finding block.

## 2026-07-20 — v2 implementation

- Connected on-call discovery to the offline proposal inbox without adding an apply, memory lifecycle, nested-model, or activation path.
- Added exact-key recurrence under the existing inbox lock, including concurrent collector coverage, ambiguous-key fail-closed behavior, and a 128-item evidence/history ceiling.
- Preserved proposal state and base context on ingest; only a current-context-bound collector reproduction may rebase a never-reviewed proposal, while manual actor behavior remains compatible.
- Synchronized Claude loop projection and Codex/OpenCode manual loop metadata with the canonical contract.
- Passed proposal, generation, projection, adaptation, skill, portable-guard, runtime activation, extension, and release regressions without changing runtime-owned state.
