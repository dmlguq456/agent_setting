# code-test — 02 driver plugin wiring + verify (Phase 2+3) result

## [PASS] real-home determinism guard

No change detected in real ~/.claude/settings.json, ~/.codex/config.toml,
~/.config/opencode/opencode.json, ~/.claude/plugins/ across the whole run
(hashes captured before HOME/CLAUDE_CONFIG_DIR were reassigned, re-checked
at exit via trap).

---

## Summary

PASS=24 FAIL=0

---

## Baseline
- REAL_REPO=/home/Uihyeop/agent_setting-wt/harness-installer-impl2
- determinism-guard baseline captured for real ~/.claude, ~/.codex, ~/.config/opencode, ~/.claude/plugins

## Isolated env
- HOME(temp)=/tmp/tmp.ZBzuAeeHLp
- AGENT_HOME=/home/Uihyeop/agent_setting-wt/harness-installer-impl2
- CLAUDE_CONFIG_DIR(temp)=/tmp/tmp.JHfRv2yBHT

- claude CLI present on PATH: 1 (/home/Uihyeop/.local/bin/claude)

## 1. Syntax — py_compile
```
（출력 없음 — 정상）
```
- [PASS] syntax.py_compile — py_compile drivers/claude.py — exit=0

## 2. Import — drivers.claude
```
OK agent-harness agent-harness-claude@agent-harness
```
- [PASS] import.drivers_claude — drivers.claude imports, _plugin_action/install/checks callable — exit=0

## 3. Smoke — install(plugin=True, dry_run=True)
- [PASS] smoke.direct_install_dryrun_ran — claude_driver.install(plugin=True, dry_run=True) ran — exit=0
- [PASS] smoke.dryrun_both_commands_and_projection — plugin action status=planned with both CLI commands in detail; symlink/copy_once projection (10+ actions) also present in the same result; blocked=False
- [PASS] smoke.cli_install_dryrun_exit0 — harness install claude --plugin --dry-run --json — exit=0
- [PASS] smoke.cli_dryrun_prints_both_cmds_and_full_plan — harness CLI --json: claude.plugin.x present with both commands + full symlink/copy_once plan alongside it

## 4. CLI-absent SKIP — PATH without claude
- [PASS] skip.cli_absent_probe_ran — PATH-stripped probe ran (exit=0); PATH used: /usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
- [PASS] skip.plugin_action_skips_no_subprocess — _plugin_action(dry_run=False) returns status=skipped with SKIP(claude) detail when claude CLI unresolvable — no subprocess call attempted
- [PASS] skip.plugin_registered_check_skips — claude.plugin-registered check reports ok=true SKIP when claude CLI absent (never fails verify on CLI-absent boxes)

## 5. checks() — new Phase 3 IDs present
- [PASS] checks.enumeration_ran — claude_driver.checks() enumerated — exit=0
- [PASS] checks.count_23_and_three_new_ids — checks() returns 23 callables (was 20 pre-Phase-3) including claude.sync-native-plugin / claude.plugin-marketplace-source / claude.plugin-registered

## 6. CLI-gated integration — real claude plugin registration (mktemp CLAUDE_CONFIG_DIR)
- reusing CLAUDE_CONFIG_DIR(temp)=/tmp/tmp.JHfRv2yBHT set at script top (still empty/unregistered so far)
- [PASS] integration.pre_registration_probe_ran — claude.plugin-registered probed before registration — exit=0
- [PASS] integration.pre_registration_truthfully_false — claude.plugin-registered ok=False under a fresh mktemp CLAUDE_CONFIG_DIR (nothing registered yet) — not a SKIP, a truthful real-state read
- [PASS] integration.install_plugin_real_ran — claude_driver.install(plugin=True, dry_run=False) ran under mktemp CLAUDE_CONFIG_DIR — exit=0
- [PASS] integration.status_registered — plugin action status=registered after real marketplace add + plugin install under mktemp CLAUDE_CONFIG_DIR
- [PASS] integration.marketplace_list_exit0 — claude plugin marketplace list --json (CLAUDE_CONFIG_DIR=mktemp) — exit=0
- [PASS] integration.marketplace_agent_harness_present — 'agent-harness' marketplace appears in read-only marketplace list
- [PASS] integration.plugin_list_exit0 — claude plugin list --json (CLAUDE_CONFIG_DIR=mktemp) — exit=0
- [PASS] integration.plugin_installed_under_temp_config_not_real_home — agent-harness-claude@agent-harness enabled=true, installPath is NOT under the real ~/.claude/plugins
- [PASS] integration.post_registration_probe_ran — claude.plugin-registered probed after registration — exit=0
- [PASS] integration.post_registration_ok_true — claude.plugin-registered flips to ok=True after registration, detail names both marketplace + plugin
## 7. harness verify claude --json — full CLI path
- [PASS] integration.verify_exit_in_expected_set — harness verify claude --json exit is 0 or 2 (never a crash) — got 0
- [PASS] integration.verify_json_has_three_new_checks_ok — harness verify claude --json: claude.sync-native-plugin / claude.plugin-marketplace-source / claude.plugin-registered all present + ok=True (registration still live under CLAUDE_CONFIG_DIR)
- [PASS] integration.verify_read_only_on_config_dir — mktemp CLAUDE_CONFIG_DIR byte-identical immediately before/after a verify call (verify never installs/mutates during registration check)

## Done — Phase 2+3 graduated tests complete (CLI-gated integration ran), see Summary above.
