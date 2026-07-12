# Verification

## Passed

- `adapters/codex/bin/preflight.sh verification-runner --timeout 180 -- python3 tools/fleet/tests/test_dispatch.py`
- `python3 tools/fleet/tests/test_mirror_parity.py`
- `python3 adapters/codex/bin/sync-native-skills.py --check`
- `python3 adapters/codex/bin/sync-native-plugin.py --check`
- `python3 adapters/opencode/bin/sync-native-skills.py --check`
- `python3 adapters/opencode/bin/sync-native-commands.py --check`
- `git diff --check`
- Manual quick-depth probes:
  - `python3 adapters/codex/bin/dispatch-headless.py --register ... --intensity quick --depth 1`
  - `python3 adapters/opencode/bin/dispatch-headless.py --register ... --intensity quick --depth 1`
  - `python3 adapters/codex/bin/dispatch-headless.py --dry-run ... --intensity quick --depth 2 --parent ...` returned `reason=invalid-depth-two-intensity`
  - `python3 adapters/opencode/bin/dispatch-headless.py --dry-run ... --intensity quick --depth 2 --parent ...` returned `reason=invalid-depth-two-intensity`

## Mixed / Existing Failures

- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- bash hooks/portable-guards.test.sh`
- The portable guards suite still reports several unrelated BADs in existing registry/liveness/doctor paths outside the quick depth1/2 contract being implemented here.

## Codex Headless Code-Test Run

Date: 2026-07-13
Worker: codex headless `code-test`

### Passed

- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 tools/fleet/tests/test_dispatch.py`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 tools/fleet/tests/test_mirror_parity.py`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 adapters/codex/bin/sync-native-skills.py --check`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 adapters/codex/bin/sync-native-plugin.py --check`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 adapters/opencode/bin/sync-native-skills.py --check`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 adapters/opencode/bin/sync-native-commands.py --check`
- `git diff --check`
- `adapters/opencode/bin/preflight.sh headless --check .`

### Failed or Existing Debt

- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- bash hooks/portable-guards.test.sh`
  - First actionable BADs observed in this run:
    - `claude dispatch wrapper should record cross-harness ownership metadata`
    - `dispatch-liveness.sh should report fresh transcript ALIVE`
    - `dispatch-liveness.sh should report ~10m transcript ALIVE under default STALE_MIN=15`
    - `dispatch-liveness.sh should report ~20m transcript SUSPECT under default STALE_MIN=15`
  - Later BADs were existing compatibility/projected-surface debt:
    - `adapters/claude/loops/drill/cases_growing/g_stage_dispatch` missing
    - `adapters/claude/tools/install` missing
    - `skills/` compatibility refs differ from `adapters/claude/skills/`
    - 58 concrete Claude/model references remain in portable areas
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- bash tools/check-adaptation-boundary.sh`
  - `FAIL: Codex autopilot-code capability-info must expose the portable pipeline/artifact/role/dispatch contracts`
  - `FAIL: no projection decision for tools/install (must be classified projected or deferred)`
  - `status=failed`
- `adapters/codex/bin/preflight.sh doctor --runtime`
  - `check=bootstrap:failed reason=codex-debug-failed exit=1`
  - `status=failed fails=1`
- `adapters/codex/bin/preflight.sh runtime-projection`
  - `check=runtime-projection:skipped`
  - `runtime_projection_hint=adapters/codex/bin/preflight.sh doctor --runtime`
  - `status=failed`
- `adapters/opencode/bin/preflight.sh doctor`
  - `check=adaptation-boundary:failed`
  - `status=failed`

### Notes

- No source, core, adapter, Fleet, or test implementation files were edited in this stage.
- Existing dirty worktree content pre-dated this verification pass; only this artifact file was updated here.

## Verification-Runner Reruns

These wrapper-based reruns were executed to satisfy the concrete verification-command contract:

- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- adapters/codex/bin/preflight.sh doctor`
  - `status=failed`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- adapters/codex/bin/preflight.sh doctor --runtime`
  - `check=bootstrap:failed reason=codex-debug-failed exit=1`
  - `status=failed`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- adapters/codex/bin/preflight.sh runtime-projection`
  - `check=runtime-projection:skipped`
  - `status=failed`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- adapters/opencode/bin/preflight.sh headless --check .`
  - `runtime_projection=ok`
  - `status=ok`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- adapters/opencode/bin/preflight.sh doctor`
  - `check=adaptation-boundary:failed`
  - `status=failed`


## 2026-07-13 codex headless rerun

- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- git diff --check` passed.
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 tools/fleet/tests/test_dispatch.py` passed.
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 tools/fleet/tests/test_mirror_parity.py` passed.
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 adapters/codex/bin/sync-native-skills.py --check` passed.
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 adapters/codex/bin/sync-native-plugin.py --check` passed.
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 adapters/opencode/bin/sync-native-skills.py --check` passed.
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 adapters/opencode/bin/sync-native-commands.py --check` passed.
- `adapters/codex/bin/preflight.sh capability-info autopilot-code` confirms `quick=depth1-one-shot-micro-plan+plan-check-lite`.
- `diff -qr skills adapters/claude/skills` still reports only `Only in skills: .sync_state.json`.
- `tools/check-adaptation-boundary.sh`, `adapters/codex/bin/preflight.sh doctor`, `adapters/codex/bin/preflight.sh doctor --runtime`, `adapters/codex/bin/preflight.sh runtime-projection`, and `adapters/opencode/bin/preflight.sh doctor` still fail on existing Claude adapter boundary/runtime debt.
