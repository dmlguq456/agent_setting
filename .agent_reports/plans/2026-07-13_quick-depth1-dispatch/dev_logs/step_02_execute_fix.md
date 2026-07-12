# Execute Fix Pass

## Spec Significance

spec-significance: SPEC-SIGNIFICANT.

Reason: this branch is still enforcing the portable autopilot dispatch topology and adapter boundary contracts. The fixes here affect capability metadata, boundary validation, and compatibility-reference parity.

## Changes

- Synced the changed compatibility reference files under `skills/` back to byte-equal parity with `adapters/claude/skills/` for the 6 drifted files found by `diff -qr`.
- Updated `tools/check-adaptation-boundary.sh` so the autopilot-code plan-policy checks expect the current quick contract (`depth1-one-shot-micro-plan+plan-check-lite`) instead of the stale inline-only wording.
- Added `tools/install` to the boundary script's deferred projection list so the top-level tools domain now has an explicit projection decision.
- Updated `adapters/codex/README.md` to describe the current autopilot-code quick policy using the same depth-1 one-shot wording as the capability map.

## Verification

Passed:

- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 tools/fleet/tests/test_dispatch.py`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 tools/fleet/tests/test_mirror_parity.py`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 adapters/codex/bin/sync-native-skills.py --check`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 adapters/opencode/bin/sync-native-skills.py --check`
- `git diff --check`
- `diff -qr skills adapters/claude/skills` now reports only `Only in skills: .sync_state.json`

Boundary check result:

- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- bash tools/check-adaptation-boundary.sh`
- The targeted failures were cleared.
- Remaining failures are existing unrelated Claude/projected-surface debt, including missing `adapters/claude/loops/drill/cases_growing/g_stage_dispatch`, `adapters/claude/tools/install`, and `adapters/claude/tools/memory/mem_cluster_j.test.sh`.
- Final status: `FAIL: ...` with `WARN: 58 concrete Claude/model references remain in portable areas.`

## Notes

- I did not attempt unrelated liveness/drill debt or full Claude wrapper parity cleanup.
- Merge and worktree cleanup remain for the main orchestrator.
