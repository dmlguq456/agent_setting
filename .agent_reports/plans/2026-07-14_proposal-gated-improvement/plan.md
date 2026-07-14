# Proposal-Gated Improvement Foundation — Implementation Plan

## Context

- Spec: `.agent_reports/spec/self-improvement-governance/prd.md`
- Starting HEAD: `cdc29038b86e58ac6e0cc4986a7f51fc0697550e`
- Worktree: `proposal-gated-loop`
- Intensity: standard

## Spec significance

`SPEC-SIGNIFICANT`: this introduces a new governance state model and local CLI.
The component PRD was created before implementation.

## Scope

1. Add an offline proposal lifecycle library/CLI under `tools/improvement/`.
2. Store records under XDG state, outside repo and runtime discovery paths.
3. Enforce proposal transitions, realization transitions, approval references,
   context freshness, bounded evidence copies, locking, and atomic writes.
4. Add focused documentation to core/loop contracts without duplicating the PRD.
5. Add isolated tests that prove runtime homes and plugin/config surfaces remain unchanged.

## Explicit exclusions

- No hook, cron, session lifecycle, plugin, or runtime config wiring.
- No source diff application, commit automation, activation, or release command.
- No network or runtime CLI call from the proposal tool.
- No generated adapter edits.

## Steps

1. Implement `tools/improvement/proposals.py` with `observe`, `transition`,
   `realization`, `check`, `show`, and `list`.
2. Add `tools/improvement/README.md` and `loops/improvement.md`; link the loop
   contract from existing core/loop docs.
3. Add Python functional tests using temporary HOME/XDG state and negative path tests.
4. Run syntax, functional, manifest, adaptation, generation, and installer/runtime
   activation regressions through the Codex verification runner.
5. Record results, update spec state, commit, and push the isolated branch.

## Verification

- `python3 -m py_compile tools/improvement/proposals.py`
- `bash tools/improvement/proposals.test.sh`
- `python3 tools/generate.py --check`
- `tools/check-adaptation-boundary.sh`
- `tools/generated-projections.test.sh`
- `tools/install/runtime-activation.test.sh`
- `tools/install/extension-lifecycle.test.sh`
- Diff audit proving no runtime config, plugin cache, generated adapter, or activation wiring changed.

## Rollback

The feature is inactive and additive. Revert its source/spec/doc commit. Local
proposal state, if manually created later, remains outside the repo and is not
loaded by any runtime.

## Plan check

- Ownership: source contract and local evidence plane are separate; yes.
- Activation leakage: no hook/plugin/config integration is in scope.
- Stale approval: exact canonical context fingerprint gates review/adoption/active realization.
- Real-home safety: tests replace HOME/XDG and compare real config/plugin hashes before/after.
- Instruction growth: one core principle and one operational guide; detailed semantics remain in the component PRD.
