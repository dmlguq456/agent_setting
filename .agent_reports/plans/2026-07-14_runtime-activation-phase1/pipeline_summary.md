# Runtime activation Phase 1 pipeline summary

Status: complete.

Branch: `runtime-activation-phase1`.

## Outcome

- Added `harness runtime activate|status|refresh|doctor` for Claude Code,
  Codex, and OpenCode.
- `linked` projects one explicit local source; `packaged` builds a
  checksum-pinned local bundle and exposes it through the same native runtime
  discovery paths.
- Plugin marketplace/install/package-manager calls are absent from both modes.
  Existing exact harness registry entries are disabled and harness-owned cache
  is quarantined so it cannot shadow the selected source.
- Activation state records source/active revision, digest, discovery paths,
  duplicate sources, freshness, external dependencies, and session action.
- Single-runtime and multi-runtime operations use bounded snapshots plus a
  durable transaction journal. Runtime credentials, sessions, logs, DBs, and
  foreign cache remain outside the write set.
- Phase 1 runtime activation is global-only. Project scope is explicitly
  rejected for every runtime without falling through to global; the legacy
  project installer remains a separate compatibility path.

## Runtime-specific realization

- Claude merges only harness hooks into user `settings.json`, projects the
  referenced tools/utilities, and preserves other user keys.
- Codex uses native skills, custom agents, modes, and hooks in both modes;
  marketplace/plugin installation is not part of activation.
- OpenCode uses plural `skills/agents/commands/plugins`, preserves foreign JSON
  config, supports string and option-tuple plugin entries, and safely blocks
  harness entries in JSONC instead of rewriting comments.

## Verification

- Cross-runtime isolated-HOME E2E: PASS (offline linked, packaged immutability,
  bundle tamper, duplicate cleanup, JSON/JSONC, rollback, journal ownership,
  source symlink, removed discovery, and external-command sentinels).
- Canonical portable guards: `PASS=343 FAIL=0`.
- Manifest check, adaptation boundary, skill conformance, legacy installer
  dry-run, Python compile, and `git diff --check`: PASS.
- Independent code review: PASS, no remaining HIGH/MEDIUM findings.
- Independent OpenCode projection review: PASS.

## Remaining runtime boundary

File freshness does not mean a running conversation has reloaded instructions.
The status schema therefore reports runtime-specific `session_action`
(`reinvoke`, `new-session`, or `restart-required`) separately.

The implementation and this report are committed together on the branch above
and pushed to its upstream branch.
