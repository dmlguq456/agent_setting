# code-test — 03 INSTALL_LAYOUT.md + regression (Phase 4 + cross-cutting) result

## [PASS] real-home determinism guard

No change detected in real ~/.claude/settings.json, ~/.codex/config.toml,
~/.config/opencode/opencode.json, ~/.claude/plugins/ across the whole run.

---

## Summary

PASS=14 FAIL=0

---

## Baseline
- REAL_REPO=/home/Uihyeop/agent_setting-wt/harness-installer-impl2

## Isolated env
- HOME(temp)=/tmp/tmp.xv9P5Ehr4l
- AGENT_HOME=/home/Uihyeop/agent_setting-wt/harness-installer-impl2

## 1. INSTALL_LAYOUT.md — reduction contract (Phase 4)
- wc -l: 225 (pre-Phase-4 baseline: 514)
- [PASS] layout.line_count_reduced — INSTALL_LAYOUT.md line count (225) well under the pre-reduction 514 (substantive reduction, not cosmetic)
- [PASS] layout.no_per_runtime_ln_sfn_enumeration — 'ln -sfn' occurrences (3) at or below the 3 expected (Windows-prose mention + kept fleet-launcher one-liner + retrospective-prose mention) — no per-runtime recipe enumeration block remains
- [PASS] layout.no_manual_verification_battery — no '^rg ' manual Migration Order verification lines remain (count=0)
- [PASS] layout.contract_facts_retained — all 7 required contract-fact phrases present in the rewritten doc (missing:)
- [PASS] layout.plugin_self_contained_fact_present — Claude plugin self-contained cache model + sync-native-plugin.py generator-binding fact present (dev_logs/step_04's own deviation note — the doc states the *contract*, not the ${CLAUDE_PLUGIN_ROOT} implementation-level env var literal)
```
 INSTALL_LAYOUT.md | 507 ++++++++++++------------------------------------------
 1 file changed, 109 insertions(+), 398 deletions(-)
```
- [PASS] layout.git_diff_readable — git diff --stat INSTALL_LAYOUT.md ran cleanly (working-tree diff inspectable) — exit=0

## 2. Regression subset
```
（출력 없음 — 정상）
```
- [PASS] regression.full_syntax — py_compile all tools/install/*.py + drivers/*.py + sync-native-plugin.py — exit=0
```
manifest up-to-date; delta baselines bound
```
- [PASS] regression.build_manifest_check — python3 tools/build-manifest.py --check — exit=0
- [PASS] regression.install_all_dryrun_exit0 — harness install --dry-run --json (all runtimes) — exit=0
- [PASS] regression.install_all_covers_three_runtimes_no_source_absent — checks[] covers claude/codex/opencode; no unexpected 'source absent' skips in this worktree
- [PASS] regression.verify_all_exit_in_expected_set — harness verify --json (all runtimes) exit is 0 or 2 (never crash) — got 2
- [PASS] regression.verify_all_includes_new_claude_checks — harness verify --json (all runtimes) includes the 3 new claude plugin check ids alongside the pre-existing claude/codex/opencode checks
- [PASS] regression.codex_plugin_dryrun_exit0 — harness install codex --plugin --dry-run --json (untouched cycle-1 channel) — exit=0
- [PASS] regression.codex_plugin_dryrun_unaffected — codex.plugin.x still plans 'marketplace add' + 'plugin add' unchanged (this cycle's claude-only edits did not regress the codex driver)

## Note — full cycle-1 51-test suite re-run scope

Not re-executed in full here (out of this stage's scope per plan Phase 5 §6
'최소 관련 스모크 재확인'); the representative subset above (full syntax,
build-manifest --check, install --dry-run all-runtimes, verify --json
all-runtimes, codex plugin dry-run) covers the surfaces this cycle's diff
(drivers/claude.py, INSTALL_LAYOUT.md, new generator + generated content)
could plausibly have regressed. cycle-1's own e2e_lifecycle.sh remains the
durable full-suite artifact at
`.agent_reports/plans/2026-07-13_harness-installer-impl/_internal/test_scripts/e2e_lifecycle.sh`
and was not re-run wholesale here to avoid duplicating ~15 minutes of
already-passing (51/51) coverage this cycle's diff does not touch.

## Done — Phase 4 + regression checks complete, see Summary above.
