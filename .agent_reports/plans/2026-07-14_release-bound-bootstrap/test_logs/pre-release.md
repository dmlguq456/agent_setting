# Pre-release verification

- `tools/install/release-lifecycle.test.sh`: PASS, including deterministic four
  assets, embedded exact repository/tag, override rejection, all-runtime packaged
  activation, update no-op, and legacy redirect.
- `tools/install/runtime-activation.test.sh`: PASS.
- `tools/install/profile-activation.test.sh`: PASS.
- `tools/install/extension-lifecycle.test.sh`: PASS.
- `python3 tools/generate.py --check`: PASS.
- `tools/generated-projections.test.sh`: PASS.
- `tools/skill-conformance/check.sh`: PASS.
- `tools/check-adaptation-boundary.sh`: PASS.
- `adapters/codex/bin/preflight.sh doctor`: PASS.
- Python compile, POSIX shell syntax, YAML/asset census, public URL/raw-main
  absence, and `git diff --check`: PASS.
- Committed implementation release build ×2: all four assets byte-identical;
  both sidecars verify; installer shell parses; embedded distribution bytes equal
  `git show HEAD:tools/install/distribution.py`; archive marker is `v1.0.1` and
  report roots are excluded.

Independent delegation was unavailable under the active no-subagent instruction;
the required adversarial fallback was an inline failure-mode review. It found and
closed pipeline-status masking and repository-override risks.
