# code-test — T0~T6 spec-pipeline DATA-rebase (Phase 4) result

## [PASS] real-home determinism guard

No change detected in real ~/.claude/settings.json, ~/.codex/config.toml,
~/.config/opencode/opencode.json, ~/.claude/plugins/ across the whole run
(hashes captured before HOME was reassigned to a mktemp dir, re-checked
at exit via trap).

---

## Summary

PASS=29 FAIL=0

---

## Baseline
- REAL_REPO=/home/Uihyeop/agent_setting-wt/harness-installer-hooks
- determinism-guard baseline captured for real ~/.claude, ~/.codex, ~/.config/opencode, ~/.claude/plugins

## Isolated env
- HOME(temp)=/tmp/tmp.X2UYJ34wXQ
- AGENT_HOME=/home/Uihyeop/agent_setting-wt/harness-installer-hooks
- CLAUDE_CONFIG_DIR(temp)=/tmp/tmp.usAzUTmRZV

## 0. Pre-condition — git status baseline
```
 M .agent_reports/plans/2026-07-13_harness-installer-impl2/_internal/hooks_inventory.md
 M adapters/claude/bin/sync-native-plugin.py
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/hooks/hooks.json
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/analyze-project/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/analyze-user/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/audit/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-apply/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-code/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-code/references/arguments-and-decisions.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-design/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-draft/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-lab/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-note/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-refine/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-research/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-ship/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-spec/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-execute/README.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-execute/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-plan/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-refine/README.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-refine/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-report/README.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-report/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-test/README.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-test/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/design-components/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/design-review/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/design-tokens/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/draft-refine/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/draft-strategy/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/post-it/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/sync-skills/SKILL.md
 M adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/sync-skills/references/finalize-and-hooks.md
?? .agent_reports/plans/2026-07-13_harness-installer-hooks/
?? adapters/claude/plugin-marketplace/plugins/agent-harness-claude/hooks/spec-read-marker.sh
?? adapters/claude/plugin-marketplace/plugins/agent-harness-claude/hooks/spec-skill-gate.sh
?? adapters/claude/plugin-marketplace/plugins/agent-harness-claude/hooks/spec-sync-nudge.sh
?? adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-design/references/
?? adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/autopilot-ship/references/
?? adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/design-tokens/references/
?? adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/draft-refine/references/
?? adapters/claude/plugin-marketplace/plugins/agent-harness-claude/utilities/
```

## T0 — static / generator basics
- [PASS] T0.py_compile — py_compile sync-native-plugin.py — exit=0
- [PASS] T0.check_clean_exit0 — --check on already-generated tree — exit=0 (expect 0)
- [PASS] T0.check_dirty_after_content_mutation — --check exit=1 after appending a byte to hooks.json (expect 1)
- [PASS] T0.regen_restores_clean — sync() regen (exit=0) then --check exit=0 (expect 0/0)
- [PASS] T0.idempotent_round_trip_no_diff — git status --porcelain identical to baseline after touch+regen round-trip
- [PASS] T0.hooks_json_event_counts — PreToolUse=3 (expect 3) / PostToolUse=2 (expect 2)
```
OK
```
- [PASS] T0.hooks_json_command_shape — existing 2 hooks unprefixed (regression-free) + spec 3 hooks carry DATA-prefix + PLUGIN_ROOT path
- [PASS] T0.utilities_bundle_exec — utilities/agent-home.sh exists + exec bit
- [PASS] T0.hooks_dir_five_sh_exec — hooks/ has 5 .sh files (expect 5), 0 missing exec bit (expect 0)

## Fixture
- FIXTURE=/tmp/tmp.MCPbPeIcRL
- FIXTURE_KEY=_tmp_tmp.MCPbPeIcRL

## T1 — marker rebasing
- [PASS] T1.marker_created_under_mktemp_data — marker at $DATA/.spec-grounding/... exists
- [PASS] T1.no_marker_under_temp_home — no .spec-grounding leaked into the script's own $HOME
- [PASS] T1.gate_passes_with_marker — gate exit=0, stdout empty (no deny) when marker present
- [PASS] T1.gate_denies_without_marker — gate emits deny JSON when marker absent (out: {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"spec-backed cwd인데 prd.md를 이번 세션에 Rea)
- [PASS] T1.gate_denies_on_reverse_drift — gate emits deny JSON after prd.md mtime advances past marker (out: {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"prd.md가 마지막 Read 이후 갱신됨(역방향 )

## T2 — dual-firing safety
- [PASS] T2.markers_created_in_own_dirs — marker present under both $A and $B independently
- [PASS] T2.no_cross_contamination — $A/.spec-grounding has 1 file(s), $B/.spec-grounding has 1 file(s) (expect 1/1, no leakage)
- [PASS] T2.both_gates_pass_with_own_marker — gate($A) and gate($B) both pass on first firing
- [PASS] T2.gate_idempotent_side_effect_zero — 2nd firing of both gates still passes, marker file counts unchanged ($A=1 $B=1)
- [PASS] T2.asymmetric_deny_wins_failsafe — $B marker removed -> $A still passes, $B denies (conservative re-Read forced, no side effect since gate is read-only)

## T3 — fail-open / non-plugin regression
- [PASS] T3.unset_agent_home_falls_back_no_crash — AGENT_HOME unset -> agent-home.sh fallback resolves ($HOME/.claude, no $HOME/agent_setting present), marker written there, exit=0, no crash
- [PASS] T3.empty_agent_home_degrades_no_crash — AGENT_HOME="" (empty) -> ':-' fallback still resolves (not just unset), no crash, exit=0
- [PASS] T3.canonical_hooks_unmodified — git diff --stat -- hooks/ empty (canonical hook bodies untouched, invariant)

## T4 — self-contained path confinement
- [PASS] T4.hooks_json_no_relative_escape — hooks.json command strings contain no '../' (all ${CLAUDE_PLUGIN_ROOT}/${CLAUDE_PLUGIN_DATA}-relative)
- [PASS] T4.hook_bodies_only_utilities_escape — spec trio bodies reference only '../utilities/agent-home.sh' (found: ../utilities/agent-home.sh)
- [PASS] T4.utilities_relpath_stays_inside_plugin_root — hooks/../utilities resolves to /home/Uihyeop/agent_setting-wt/harness-installer-hooks/adapters/claude/plugin-marketplace/plugins/agent-harness-claude/utilities == PLUGIN_ROOT/utilities (/home/Uihyeop/agent_setting-wt/harness-installer-hooks/adapters/claude/plugin-marketplace/plugins/agent-harness-claude/utilities) — no escape outside PLUGIN_ROOT

## T5 — real-home determinism guard
- structural: see trap-based guard in the report header (whole-script coverage).
- [PASS] T5.guard_scaffolding_present — sha256 baseline captured pre-HOME-reassignment + EXIT trap re-check wired (see report header)

## T6 — integration smoke
- [PASS] T6.build_manifest_up_to_date — build-manifest.py --check exit=0, output: manifest up-to-date; delta baselines bound
- [PASS] T6.harness_verify_sync_native_plugin_ok — harness verify claude --json (exit=2) -> claude.sync-native-plugin: FOUND True OK: python3 adapters/claude/bin/sync-native-plugin.py --check

## Write-set confinement (post-run)
- [PASS] confinement.git_status_matches_baseline — repo git status --porcelain unchanged by this entire test run (T0's own touch+regen round-trip already restored clean; T1-T6 write only to mktemp dirs)
