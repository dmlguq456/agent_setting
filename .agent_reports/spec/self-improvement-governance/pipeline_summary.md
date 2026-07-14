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
