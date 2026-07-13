# code-test — 01 generator plugin content (Phase 1) result

## [PASS] real-home determinism guard

No change detected in real ~/.claude/settings.json, ~/.codex/config.toml,
~/.config/opencode/opencode.json, ~/.claude/plugins/ across the whole run
(hashes captured before HOME was reassigned to a mktemp dir, re-checked
at exit via trap).

---

## Summary

PASS=15 FAIL=0

---

## Baseline
- REAL_REPO=/home/Uihyeop/agent_setting-wt/harness-installer-impl2
- determinism-guard baseline captured for real ~/.claude, ~/.codex, ~/.config/opencode, ~/.claude/plugins

## Isolated env
- HOME(temp)=/tmp/tmp.BnQY5HRedh
- AGENT_HOME=/home/Uihyeop/agent_setting-wt/harness-installer-impl2

## 0. Pre-condition — git status baseline
```
 M INSTALL_LAYOUT.md
 M tools/install/drivers/claude.py
?? .agent_reports/plans/2026-07-13_harness-installer-impl2/
?? adapters/claude/bin/sync-native-plugin.py
?? adapters/claude/plugin-marketplace/plugins/agent-harness-claude/agents/
?? adapters/claude/plugin-marketplace/plugins/agent-harness-claude/hooks/
?? adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/
```

## 1. Syntax — py_compile
```
（출력 없음 — 정상）
```
- [PASS] syntax.py_compile — py_compile sync-native-plugin.py + drivers/claude.py — exit=0

## 2. Import — sync-native-plugin.py module load
```
OK /home/Uihyeop/agent_setting-wt/harness-installer-impl2/adapters/claude/plugin-marketplace/plugins/agent-harness-claude
```
- [PASS] import.sync_native_plugin_module — module loads, sync/check/plugin_json/marketplace_json/hooks_json callable — exit=0

## 3. Smoke — --check on clean tree
```

```
- [PASS] smoke.check_clean_exit0 — sync-native-plugin.py --check on clean tree — exit=0 (expect 0)

## 4. Functional — sync() idempotency / drift detection / confinement
```
generated Claude native plugin projection at adapters/claude/plugin-marketplace/plugins/agent-harness-claude
```
- [PASS] functional.sync_reruns_ok — sync() re-run — exit=0
- [PASS] functional.sync_idempotent_no_diff — git status --porcelain unchanged after a re-run of sync() (byte-identical output)
- [PASS] functional.check_clean_after_resync — --check exit=0 after idempotent re-sync (expect 0)
### 4b. drift-probe --check output
```
Claude native plugin projection is stale:
  adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/audit/SKILL.md
```
- [PASS] functional.check_detects_touch — --check exit=1 after touching a generated file (expect 1)
- [PASS] functional.check_names_touched_file — stale[] output names the exact touched file
### 4c. excess-file --check output
```
Claude native plugin projection is stale:
  adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/audit/SKILL.md
  adapters/claude/plugin-marketplace/plugins/agent-harness-claude/agents/__stray_probe.md
```
- [PASS] functional.check_detects_excess_file — --check exit=1 with an extra untracked file under agents/ (expect 1)
- [PASS] functional.check_names_stray_file — stale[] output names the stray excess file
- [PASS] functional.regen_after_drift_ok — sync() regenerates after drift+stray — exit=0
- [PASS] functional.check_clean_after_regen — --check exit=0 after regeneration (expect 0, clean again)
- [PASS] functional.stray_file_removed_by_regen — stray excess file removed by rmtree-then-copytree regen
- [PASS] functional.final_state_matches_baseline — git status --porcelain after touch->stray->regen cycle matches the pre-test baseline exactly (deterministic round-trip)

## 5. Write-set confinement
```
 M INSTALL_LAYOUT.md
 M tools/install/drivers/claude.py
?? .agent_reports/plans/2026-07-13_harness-installer-impl2/
```
- [PASS] confinement.no_writes_outside_marketplace — git status outside adapters/claude/plugin-marketplace/ + the generator script is unchanged from baseline (generator wrote nowhere else)

## Done — Phase 1 generator graduated tests complete, see Summary above.
