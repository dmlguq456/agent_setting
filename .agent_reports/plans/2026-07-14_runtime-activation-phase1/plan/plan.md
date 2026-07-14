---
status: completed
created: 2026-07-14
spec: .agent_reports/spec/harness-productization/prd.md
intensity: standard
qa: standard
---

# Cross-Runtime Source Activation — Phase 1

## Goal

Make the active harness source explicit and testable for Codex, Claude Code, and
OpenCode. Maintainer installs use one offline `linked` source; reproducible
installs use one immutable local `packaged` bundle. Both modes use only native
runtime discovery; plugin registry/cache state must not shadow either source.

## Decisions

- Extend the existing `tools/install/harness.sh` → `installer.py` CLI with a
  `runtime` command family; do not create a second installer.
- Store activation truth in each runtime's harness-owned
  `<runtime-home>/.harness/activation.json`.
- Use native linked projections for all runtimes. OpenCode uses current plural
  `skills/`, `agents/`, `commands/`, and `plugins/` discovery paths.
- Build packaged mode as an immutable local bundle. Codex, Claude, and OpenCode
  expose the bundle through the same native discovery paths as linked mode.
- Remove plugin/marketplace/package-manager state from Phase 1 activation.
  Exact existing harness registry entries are disabled and harness-owned cache
  is quarantined without touching foreign runtime state.
- Apply a preflighted operation journal and restore it in reverse order on any
  failure. Runtime-owned credentials, sessions, databases, logs, and foreign
  cache entries are outside the write set.
- Status computes the live source revision and projection digest. It reports
  session freshness separately from file freshness.

## Implementation

1. Add `tools/install/runtime_activation.py`: source identity/digest, runtime
   mappings, activation state, transactional apply/rollback, duplicate
   discovery, status, refresh, and doctor.
2. Add `harness runtime {status,activate,refresh,doctor}` parsing and stable JSON
   output in `tools/install/installer.py`.
3. Add isolated-HOME E2E coverage for offline linked activation, packaged
   immutability, duplicates, source identity, session actions, rollback, and
   OpenCode projection.
4. Synchronize `README.md` and `INSTALL_LAYOUT.md` with the activation contract.

## Verification

- `python3 -m py_compile tools/install/*.py tools/install/drivers/*.py`
- `sh tools/install/runtime-activation.test.sh`
- `python3 tools/build-manifest.py --check`
- `sh tools/check-adaptation-boundary.sh`

All mutating tests run in one shell with throwaway `HOME`, `XDG_CONFIG_HOME`,
and `XDG_DATA_HOME`. Runtime CLIs and network/package commands are fail sentinels.

## Risks

- A real file at a harness discovery name is a collision, not permission to
  overwrite; activation fails and rolls back.
- Session-bound instructions cannot be hot-reloaded reliably; status must say
  `new-session` or `restart-required` instead of claiming freshness.
- Packaged mode cannot depend on marketplace state or downloads. It uses only a
  bundle copied from the explicitly supplied local source.
