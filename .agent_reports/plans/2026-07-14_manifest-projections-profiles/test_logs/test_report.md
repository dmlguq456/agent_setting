# Test report

Status: pass.

## Acceptance tests

- `tools/generated-projections.test.sh`: PASS
  - representative canonical change reaches Claude/Codex/OpenCode;
  - second generation is byte-stable;
  - manual generated edit fails `--check`.
- `tools/install/profile-activation.test.sh`: PASS
  - starter/builder/full across Claude/Codex/OpenCode;
  - capability, role, and Codex/Claude mode discovery is profile-filtered;
  - builder default, kernel surfaces, and `install --profile` alias;
  - activation-aware `harness verify`, profile-preserving duplicate remediation,
    and blocked project-scope dry-runs.
- `tools/install/runtime-activation.test.sh`: PASS, 19 Phase 1/profile-recovery scenarios.

## Regression gates

- `python3 tools/generate.py --check`: PASS, 8 groups.
- `bash tools/skill-conformance/check.sh`: PASS, 26 classifications.
- `bash tools/check-adaptation-boundary.sh`: PASS (documented reference warning only).
- `bash hooks/portable-guards.test.sh`: PASS=343, FAIL=0.
- `adapters/codex/bin/preflight.sh doctor`: PASS.
- Python compile smoke and `git diff --check`: PASS.

## Independent review

- OpenCode/profile review found activation-unaware legacy `verify` and missing
  executable bits on the two documented test scripts; both were fixed and
  covered by the profile E2E.
- Runtime/code review found unfiltered mode directories, a duplicate-remediation
  command that dropped the selected profile, and unsupported project scope
  bypassing validation during dry-run; all three were fixed and regression-tested.
  Its closure pass then found the nested mode journal allowlist lagging the new
  fan-out layout; crash recovery now accepts only the owned three-segment mode
  path and has a dedicated interrupted-transaction regression.
- No high-severity findings remain.

## Runtime-currentness evidence

- Codex official manual: local skills fit repo/personal workflows; plugins are
  distribution bundles and can add marketplace/MCP/app surfaces.
- Claude Code official docs: skills, agents, and hooks are native surfaces;
  session reload semantics remain distinct from file visibility.
- OpenCode official docs: plural global skills/agents paths are native; Phase 2
  activation continues to use those paths.

No drill was run because the repository policy prohibits automatic token-spending
runtime drills. The isolated offline golden-path fixture covers discovery and
activation without claiming public adoption or model-quality evidence.
