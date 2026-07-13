#!/bin/sh
# 03_install_layout_and_regression.sh — code-test Phase 5 for Phase 4
# (INSTALL_LAYOUT.md reduction) + cross-cutting regression smoke (Phase 5 §6:
# confirm this cycle's changes didn't break cycle-1's driver/CLI behavior).
#
# Hard isolation contract (INCIDENT_real_home_touched.md, plan.md Phase 5):
#   - ONE `sh` process, ONE Bash tool invocation. HOME/AGENT_HOME exported at
#     the very top of THIS file, never carried across a tool-call boundary.
#   - determinism guard: sha256 of real ~/.claude/settings.json,
#     ~/.codex/config.toml, ~/.config/opencode/opencode.json + recursive hash
#     of real ~/.claude/plugins, captured before HOME is reassigned, re-checked
#     in an EXIT trap.
set -eu

REAL_REPO="/home/Uihyeop/agent_setting-wt/harness-installer-impl2"
PLAN_DIR="$REAL_REPO/.agent_reports/plans/2026-07-13_harness-installer-impl2"
LOGDIR="$PLAN_DIR/test_logs"
REVIEWDIR="$PLAN_DIR/_internal/test_reviews"
mkdir -p "$LOGDIR" "$REVIEWDIR"
LOG="$LOGDIR/03_install_layout_and_regression.md"
WORKLOG=$(mktemp)

export PYTHONDONTWRITEBYTECODE=1

REAL_HOME_ORIG="$HOME"
GUARD_CLAUDE_SETTINGS="$REAL_HOME_ORIG/.claude/settings.json"
GUARD_CODEX_CONFIG="$REAL_HOME_ORIG/.codex/config.toml"
GUARD_OPENCODE_CONFIG="$REAL_HOME_ORIG/.config/opencode/opencode.json"
GUARD_CLAUDE_PLUGINS="$REAL_HOME_ORIG/.claude/plugins"

sha_or_absent() {
  if [ -f "$1" ]; then sha256sum "$1" | cut -d' ' -f1; else echo "ABSENT"; fi
}
dir_sha_or_absent() {
  if [ -d "$1" ]; then
    find "$1" -type f -exec sha256sum {} \; 2>/dev/null | sort | sha256sum | cut -d' ' -f1
  else
    echo "ABSENT"
  fi
}

GUARD_SHA1_BEFORE=$(sha_or_absent "$GUARD_CLAUDE_SETTINGS")
GUARD_SHA2_BEFORE=$(sha_or_absent "$GUARD_CODEX_CONFIG")
GUARD_SHA3_BEFORE=$(sha_or_absent "$GUARD_OPENCODE_CONFIG")
GUARD_SHA4_BEFORE=$(dir_sha_or_absent "$GUARD_CLAUDE_PLUGINS")

PASS_COUNT=0
FAIL_COUNT=0
FAILED_IDS=""

log() { printf '%s\n' "$*" >> "$WORKLOG"; }
chk() {
  id="$1"; level="$2"; desc="$3"; ok="$4"
  if [ "$ok" = "0" ]; then
    log "- [PASS] $id — $desc"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    log "- [$level-FAIL] $id — $desc"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAILED_IDS="$FAILED_IDS $id"
  fi
}

finalize() {
  EXITCODE=$?
  GUARD_SHA1_AFTER=$(sha_or_absent "$GUARD_CLAUDE_SETTINGS")
  GUARD_SHA2_AFTER=$(sha_or_absent "$GUARD_CODEX_CONFIG")
  GUARD_SHA3_AFTER=$(sha_or_absent "$GUARD_OPENCODE_CONFIG")
  GUARD_SHA4_AFTER=$(dir_sha_or_absent "$GUARD_CLAUDE_PLUGINS")

  GUARD_OK=0
  if [ "$GUARD_SHA1_BEFORE" != "$GUARD_SHA1_AFTER" ] || [ "$GUARD_SHA2_BEFORE" != "$GUARD_SHA2_AFTER" ] || \
     [ "$GUARD_SHA3_BEFORE" != "$GUARD_SHA3_AFTER" ] || [ "$GUARD_SHA4_BEFORE" != "$GUARD_SHA4_AFTER" ]; then
    GUARD_OK=1
  fi

  {
    echo "# code-test — 03 INSTALL_LAYOUT.md + regression (Phase 4 + cross-cutting) result"
    echo
    if [ "$GUARD_OK" = "1" ]; then
      echo "## [CRITICAL] real-home determinism guard FAILED"
      echo
      echo "STOP — a real runtime-home file changed during this run. Do not"
      echo "attempt further remediation from this script; report immediately."
      echo
      echo "- claude settings.json: before=$GUARD_SHA1_BEFORE after=$GUARD_SHA1_AFTER"
      echo "- codex config.toml:    before=$GUARD_SHA2_BEFORE after=$GUARD_SHA2_AFTER"
      echo "- opencode config.json: before=$GUARD_SHA3_BEFORE after=$GUARD_SHA3_AFTER"
      echo "- claude/plugins dir:   before=$GUARD_SHA4_BEFORE after=$GUARD_SHA4_AFTER"
      echo
    else
      echo "## [PASS] real-home determinism guard"
      echo
      echo "No change detected in real ~/.claude/settings.json, ~/.codex/config.toml,"
      echo "~/.config/opencode/opencode.json, ~/.claude/plugins/ across the whole run."
      echo
    fi
    echo "---"
    echo
    echo "## Summary"
    echo
    echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
    if [ -n "$FAILED_IDS" ]; then
      echo
      echo "Failed check ids:$FAILED_IDS"
    fi
    echo
    echo "---"
    echo
    cat "$WORKLOG"
  } > "$LOG"
  rm -f "$WORKLOG"

  if [ -d "${ART:-}" ]; then
    rm -rf "$REVIEWDIR/03_artifacts"
    cp -r "$ART" "$REVIEWDIR/03_artifacts" 2>/dev/null || true
  fi

  rm -rf "${HOME:-}" 2>/dev/null || true
  if [ "$GUARD_OK" = "1" ]; then
    exit 99
  fi
  exit "$EXITCODE"
}
trap finalize EXIT

log "## Baseline"
log "- REAL_REPO=$REAL_REPO"
log ""

export HOME
HOME="$(mktemp -d)"
export AGENT_HOME="$REAL_REPO"
ART="$HOME/artifacts"
mkdir -p "$ART"

HARNESS_SH="$REAL_REPO/tools/install/harness.sh"
harness() { sh "$HARNESS_SH" "$@"; }

log "## Isolated env"
log "- HOME(temp)=$HOME"
log "- AGENT_HOME=$AGENT_HOME"
log ""

LAYOUT_MD="$REAL_REPO/INSTALL_LAYOUT.md"

# ---------------------------------------------------------------------------
# 1. INSTALL_LAYOUT.md — no copy-pasteable per-runtime ln -sfn recipe lists,
#    no manual Migration Order battery, contract facts retained.
# ---------------------------------------------------------------------------
log "## 1. INSTALL_LAYOUT.md — reduction contract (Phase 4)"

LINE_COUNT=$(wc -l < "$LAYOUT_MD" | tr -d ' ')
log "- wc -l: $LINE_COUNT (pre-Phase-4 baseline: 514)"
okval=$([ "$LINE_COUNT" -lt 300 ] && echo 0 || echo 1)
chk "layout.line_count_reduced" HIGH "INSTALL_LAYOUT.md line count ($LINE_COUNT) well under the pre-reduction 514 (substantive reduction, not cosmetic)" "$okval"

LN_SFN_COUNT=$(grep -c "ln -sfn" "$LAYOUT_MD" || true)
okval=$([ "$LN_SFN_COUNT" -le 3 ] && echo 0 || echo 1)
chk "layout.no_per_runtime_ln_sfn_enumeration" HIGH "'ln -sfn' occurrences ($LN_SFN_COUNT) at or below the 3 expected (Windows-prose mention + kept fleet-launcher one-liner + retrospective-prose mention) — no per-runtime recipe enumeration block remains" "$okval"

RG_BATTERY_COUNT=$(grep -c "^rg " "$LAYOUT_MD" || true)
okval=$([ "$RG_BATTERY_COUNT" -eq 0 ] && echo 0 || echo 1)
chk "layout.no_manual_verification_battery" HIGH "no '^rg ' manual Migration Order verification lines remain (count=$RG_BATTERY_COUNT)" "$okval"

# contract facts that must survive the rewrite (plan Step 4.1/4.2 "Keep" list).
MISSING_FACTS=""
for phrase in \
  "harness install" \
  "harness verify" \
  "copy-once" \
  "INST-OPEN-4" \
  "install-windows.sh" \
  "local/bin" \
  "Exit code"
do
  if ! grep -q -F "$phrase" "$LAYOUT_MD"; then
    MISSING_FACTS="$MISSING_FACTS [$phrase]"
  fi
done
okval=$([ -z "$MISSING_FACTS" ] && echo 0 || echo 1)
chk "layout.contract_facts_retained" HIGH "all 7 required contract-fact phrases present in the rewritten doc (missing:$MISSING_FACTS)" "$okval"

if grep -q -F "self-contained" "$LAYOUT_MD" && grep -q -F "sync-native-plugin.py" "$LAYOUT_MD"; then
  okval=0
else
  okval=1
fi
chk "layout.plugin_self_contained_fact_present" MEDIUM "Claude plugin self-contained cache model + sync-native-plugin.py generator-binding fact present (dev_logs/step_04's own deviation note — the doc states the *contract*, not the \${CLAUDE_PLUGIN_ROOT} implementation-level env var literal)" "$okval"

set +e
DIFFSTAT=$(cd "$REAL_REPO" && git diff --stat INSTALL_LAYOUT.md 2>&1)
DIFFSTAT_CODE=$?
set -e
log '```'
log "$DIFFSTAT"
log '```'
okval=$([ "$DIFFSTAT_CODE" -eq 0 ] && echo 0 || echo 1)
chk "layout.git_diff_readable" HIGH "git diff --stat INSTALL_LAYOUT.md ran cleanly (working-tree diff inspectable) — exit=$DIFFSTAT_CODE" "$okval"
log ""

# ---------------------------------------------------------------------------
# 2. Regression subset — cross-cutting sanity that this cycle's changes did
#    not break cycle-1 driver/CLI behavior. Full 51-test cycle-1 re-run is
#    out of scope for this stage (dev_logs/step_01-04 already re-derived the
#    relevant slices); this is a representative smoke subset, not exhaustive.
# ---------------------------------------------------------------------------
log "## 2. Regression subset"

set +e
FULL_SYN_OUT=$(cd "$REAL_REPO" && python3 -m py_compile tools/install/*.py tools/install/drivers/*.py adapters/claude/bin/sync-native-plugin.py 2>&1)
FULL_SYN_CODE=$?
set -e
log '```'
log "${FULL_SYN_OUT:-（출력 없음 — 정상）}"
log '```'
okval=$([ "$FULL_SYN_CODE" -eq 0 ] && echo 0 || echo 1)
chk "regression.full_syntax" HIGH "py_compile all tools/install/*.py + drivers/*.py + sync-native-plugin.py — exit=$FULL_SYN_CODE" "$okval"

set +e
BM_OUT=$(cd "$REAL_REPO" && python3 tools/build-manifest.py --check 2>&1)
BM_CODE=$?
set -e
log '```'
log "$BM_OUT"
log '```'
okval=$([ "$BM_CODE" -eq 0 ] && echo 0 || echo 1)
chk "regression.build_manifest_check" HIGH "python3 tools/build-manifest.py --check — exit=$BM_CODE" "$okval"

set +e
ALL_DRYRUN_OUT=$(cd "$REAL_REPO" && harness install --dry-run --json)
ALL_DRYRUN_CODE=$?
set -e
printf '%s' "$ALL_DRYRUN_OUT" > "$ART/regression_install_all_dryrun.json"
okval=$([ "$ALL_DRYRUN_CODE" -eq 0 ] && echo 0 || echo 1)
chk "regression.install_all_dryrun_exit0" HIGH "harness install --dry-run --json (all runtimes) — exit=$ALL_DRYRUN_CODE" "$okval"

set +e
python3 -c "
import json
d = json.load(open('$ART/regression_install_all_dryrun.json'))
for rt in ('claude', 'codex', 'opencode'):
    assert any(c['id'].startswith(rt + '.') for c in d['checks']), rt
assert not any('source absent' in c.get('detail', '') for c in d['checks']), [c for c in d['checks'] if 'source absent' in c.get('detail','')]
"
ASSERT_CODE=$?
set -e
chk "regression.install_all_covers_three_runtimes_no_source_absent" HIGH "checks[] covers claude/codex/opencode; no unexpected 'source absent' skips in this worktree" "$ASSERT_CODE"

set +e
VERIFY_ALL_OUT=$(cd "$REAL_REPO" && harness verify --json)
VERIFY_ALL_CODE=$?
set -e
printf '%s' "$VERIFY_ALL_OUT" > "$ART/regression_verify_all.json"
okval=0
if [ "$VERIFY_ALL_CODE" -eq 0 ] || [ "$VERIFY_ALL_CODE" -eq 2 ]; then okval=0; else okval=1; fi
chk "regression.verify_all_exit_in_expected_set" HIGH "harness verify --json (all runtimes) exit is 0 or 2 (never crash) — got $VERIFY_ALL_CODE" "$okval"

set +e
python3 -c "
import json
d = json.load(open('$ART/regression_verify_all.json'))
ids = [c['id'] for c in d['checks']]
for expect in ('claude.sync-native-plugin', 'claude.plugin-marketplace-source', 'claude.plugin-registered'):
    assert expect in ids, (expect, ids)
"
ASSERT_CODE=$?
set -e
chk "regression.verify_all_includes_new_claude_checks" HIGH "harness verify --json (all runtimes) includes the 3 new claude plugin check ids alongside the pre-existing claude/codex/opencode checks" "$ASSERT_CODE"

# codex plugin channel (cycle-1, out of this cycle's scope) must remain unaffected.
set +e
CODEX_PLUGIN_OUT=$(cd "$REAL_REPO" && harness install codex --plugin --dry-run --json)
CODEX_PLUGIN_CODE=$?
set -e
printf '%s' "$CODEX_PLUGIN_OUT" > "$ART/regression_codex_plugin_dryrun.json"
okval=$([ "$CODEX_PLUGIN_CODE" -eq 0 ] && echo 0 || echo 1)
chk "regression.codex_plugin_dryrun_exit0" HIGH "harness install codex --plugin --dry-run --json (untouched cycle-1 channel) — exit=$CODEX_PLUGIN_CODE" "$okval"

set +e
python3 -c "
import json
d = json.load(open('$ART/regression_codex_plugin_dryrun.json'))
assert any(c['id'] == 'codex.plugin.x' and 'marketplace add' in c['detail'] and 'plugin add' in c['detail'] for c in d['checks']), d['checks']
"
ASSERT_CODE=$?
set -e
chk "regression.codex_plugin_dryrun_unaffected" HIGH "codex.plugin.x still plans 'marketplace add' + 'plugin add' unchanged (this cycle's claude-only edits did not regress the codex driver)" "$ASSERT_CODE"
log ""

log "## Note — full cycle-1 51-test suite re-run scope"
log ""
log "Not re-executed in full here (out of this stage's scope per plan Phase 5 §6"
log "'최소 관련 스모크 재확인'); the representative subset above (full syntax,"
log "build-manifest --check, install --dry-run all-runtimes, verify --json"
log "all-runtimes, codex plugin dry-run) covers the surfaces this cycle's diff"
log "(drivers/claude.py, INSTALL_LAYOUT.md, new generator + generated content)"
log "could plausibly have regressed. cycle-1's own e2e_lifecycle.sh remains the"
log "durable full-suite artifact at"
log "\`.agent_reports/plans/2026-07-13_harness-installer-impl/_internal/test_scripts/e2e_lifecycle.sh\`"
log "and was not re-run wholesale here to avoid duplicating ~15 minutes of"
log "already-passing (51/51) coverage this cycle's diff does not touch."
log ""

log "## Done — Phase 4 + regression checks complete, see Summary above."
