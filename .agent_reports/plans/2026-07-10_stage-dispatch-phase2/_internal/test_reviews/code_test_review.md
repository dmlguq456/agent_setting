# code-test review — stage-dispatch Phase 2

Full detail in `../../test_logs/test_report.md`. This note is the short internal
pointer for the conductor.

- Level reached: **3** (conformance) — Level 1/2/4 all clean; Level 3 full suite
  PASS=311 FAIL=12, of which **10 are pre-existing baseline (`8596e25`) environment
  FAILs** (reproduced identically in a clean baseline checkout) and **2 are new
  regressions**.
- New regressions root cause: code-execute added new files (`utilities/dispatch-wait*.sh`,
  2 new hooks, 8 profile files) and edited 9 `skills/**` reference docs without
  running `tools/build-manifest.py` or mirroring into `adapters/claude/{hooks,skills}/**`
  — breaks `tools/check-adaptation-boundary.sh` and `manifest.json --check`, which
  cascades into 2 `codex doctor --runtime[-strict]` conformance-test failures.
- Action: route back to code-execute for the manifest regen + adapter mirror sync
  before promoting plan status past "implemented" gate checks that run full
  conformance.
- Minor: drill handoff `assert.sh` fails strict `sh -n` (bashism) — flag to the
  loops-owning session, not blocking this plan.
