# Verification Log

All commands below were run through the Codex verification-runner unless noted.

- `python3 -m unittest discover -s tools/fleet/tests` -> exit 0, 165 tests passed.
- `bash utilities/usage-check.test.sh` -> exit 0, conformance PASS.
- `bash -n loops/runtime-watch.sh loops/runtime-watch.test.sh adapters/claude/loops/runtime-watch.sh adapters/claude/loops/runtime-watch.test.sh ...` -> exit 0.
- `bash loops/runtime-watch.test.sh` -> exit 0; first run writes a report and a stable second run returns `status=unchanged` without rewriting it.
- `bash loops/runtime-watch.sh --probe` -> exit 0; Codex pricing/changelog and Claude plan/changelog fingerprints succeeded. Two OpenAI Help Center pages remained `fetch-failed` and are reported as unavailable rather than treated as current.
- Live branch Fleet snapshot -> Codex rendered as `7d 20%`, not `5h`, from `limit_window_seconds=604800`.
- `python3 tools/build-manifest.py --check` -> exit 0, manifest up-to-date and delta baselines bound.
- `adapters/codex/bin/sync-native-skills.py --check` -> exit 0.
- `adapters/codex/bin/sync-native-plugin.py --check` -> exit 0.
- `adapters/codex/bin/sync-native-agents.py --check` -> exit 0.
- `adapters/codex/bin/sync-native-modes.py --check` -> exit 0.
- `bash tools/check-adaptation-boundary.sh` -> exit 0, boundary checks passed; warning only for existing documented Claude/model references.
- `adapters/codex/bin/preflight.sh doctor` -> exit 0; runtime projection check skipped by non-runtime doctor.
- `git diff --check` -> exit 0.

`preflight.sh loop-info drill` reports `manual-only`. Drill would be useful for the changed dispatch action rule, but was not run because it can launch headless runtime sessions and spend tokens.
