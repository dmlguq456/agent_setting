# Phase 3 implementation log

## Product surface

- Added `tools/install/extensions.py` as the stdlib-only local extension
  lifecycle and wired `extension inspect|add|update|remove` through the existing
  installer CLI.
- Added XDG/runtime root resolution in `paths.py`, reserved the external physical
  namespace in the built-in manifest validator, and made built-in native-source
  detection require exact harness targets.
- Added collapsed Claude adapter projections for the shared lifecycle code,
  test, and fixtures; portable code remains canonical under `tools/`.

## Safety and ownership

- Source census uses root directory fds and `O_NOFOLLOW`; manifest identity and
  checksum come from the same captured bytes and are rechecked after staging.
- Snapshots contain Markdown only, have versioned source/projection digests, and
  are traversed and deleted from the trusted XDG data root without following
  parent symlinks.
- Registry entries store canonical identity and resolved runtime roots. Mutation
  destinations are recomputed, current links must match exact ownership, and
  runtime-root drift blocks update/remove.
- Transactions preserve raw registry bytes and before/after CAS hashes and
  generations. Crash recovery restores only a recognized before/after state and
  refuses foreign registry content.
- Packages block mutation; scripts/hooks/MCP/connectors/plugins stay inactive and
  are reported as parity loss. Secret values are never printed or persisted.

## Compatibility

- The extension registry is separate from `harness-manifest.json` and built-in
  activation state.
- Core verify/runtime doctor do not depend on external extension health.
- Runtime paths honor Codex, Claude Code, and OpenCode native overrides without
  copying another runtime's plugin/config format.
