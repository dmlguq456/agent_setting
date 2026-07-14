# Implementation log

Status: complete.

## Canonical product contract

- Added strict stdlib validation and resolution for `harness-manifest.json`.
- Root `manifest.json` remains a generated compatibility view.
- Capability and role catalogs plus capability Contract blocks are generated.

## Runtime projections

- Refactored Claude metadata, Codex skills/agents/modes, and OpenCode
  skills/commands/agents to consume canonical metadata.
- Claude compatibility skill metadata is generated with the native copy so the
  historical byte-equivalence invariant remains true.
- Core generation and checks use `tools/generate.py`; marketplace bundle
  generators are not called by this path.

## Activation profiles

- Added starter/builder/full resolution to activate, refresh, status, doctor,
  and the linked `install --profile` alias.
- Filtered runtime-native capabilities and roles while leaving bootstrap,
  instructions, hooks/config bridges, guards, and memory-scout active.
- New activation defaults to builder. Phase 1 states without a profile retain
  full discovery semantics.

## Product surface

- Rewrote the root README around profile quickstart, differentiated value,
  manifest architecture, runtime truthfulness, and native-first distribution.
- Removed marketplace registration and plugin projection freshness from core
  doctor/verify/adaptation gates. Explicit legacy plugin installation remains
  optional and cannot be combined with native discovery.
- Advanced the productization spec to v4 and recorded Phase 2 complete.
