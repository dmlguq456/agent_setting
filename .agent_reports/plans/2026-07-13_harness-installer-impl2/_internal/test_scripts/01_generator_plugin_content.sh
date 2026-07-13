#!/bin/sh
# 01_generator_plugin_content.sh — code-test Phase 5 for Phase 1
# (adapters/claude/bin/sync-native-plugin.py).
#
# Hard isolation contract (INCIDENT_real_home_touched.md direct response,
# plan.md Phase 5 §1-3):
#   - ONE `sh` process, ONE Bash tool invocation. HOME/AGENT_HOME are exported
#     at the very top of THIS file and never carried across a tool-call
#     boundary.
#   - HOME is reassigned to a mktemp dir before anything else runs, defensively
#     (this generator never reads/writes HOME by construction — ROOT is
#     derived from `__file__`, not from any env var — but the isolation
#     contract is baked into every script regardless of whether a given test
#     happens to touch HOME).
#   - determinism guard: sha256 of real ~/.claude/settings.json,
#     ~/.codex/config.toml, ~/.config/opencode/opencode.json + a recursive
#     listing hash of real ~/.claude/plugins (if present) captured BEFORE
#     HOME is reassigned, re-checked in a EXIT trap.
#   - the generator itself only ever writes inside
#     adapters/claude/plugin-marketplace/ (repo-relative, ROOT = parents[3]
#     of the script file) — this script asserts that write-confinement via
#     `git status --porcelain`, since the generator has no target-root
#     argument to parameterize (Phase 5 §2's "confined temp checkout" OR
#     "write-set confinement assertion" branch — this script takes the
#     lighter-weight assertion branch, matching what code-execute already
#     did ad-hoc per dev_logs/step_01).
set -eu

REAL_REPO="/home/Uihyeop/agent_setting-wt/harness-installer-impl2"
PLAN_DIR="$REAL_REPO/.agent_reports/plans/2026-07-13_harness-installer-impl2"
LOGDIR="$PLAN_DIR/test_logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/01_generator_plugin_content.md"
WORKLOG=$(mktemp)

export PYTHONDONTWRITEBYTECODE=1

# ---------------------------------------------------------------------------
# Determinism guard — capture real-home file hashes BEFORE HOME is reassigned.
# ---------------------------------------------------------------------------
REAL_HOME_ORIG="$HOME"
GUARD_CLAUDE_SETTINGS="$REAL_HOME_ORIG/.claude/settings.json"
GUARD_CODEX_CONFIG="$REAL_HOME_ORIG/.codex/config.toml"
GUARD_OPENCODE_CONFIG="$REAL_HOME_ORIG/.config/opencode/opencode.json"
GUARD_CLAUDE_PLUGINS="$REAL_HOME_ORIG/.claude/plugins"

sha_or_absent() {
  if [ -f "$1" ]; then
    sha256sum "$1" | cut -d' ' -f1
  else
    echo "ABSENT"
  fi
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
    echo "# code-test — 01 generator plugin content (Phase 1) result"
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
      echo "~/.config/opencode/opencode.json, ~/.claude/plugins/ across the whole run"
      echo "(hashes captured before HOME was reassigned to a mktemp dir, re-checked"
      echo "at exit via trap)."
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

  rm -rf "${HOME:-}" 2>/dev/null || true
  if [ "$GUARD_OK" = "1" ]; then
    exit 99
  fi
  exit "$EXITCODE"
}
trap finalize EXIT

log "## Baseline"
log "- REAL_REPO=$REAL_REPO"
log "- determinism-guard baseline captured for real ~/.claude, ~/.codex, ~/.config/opencode, ~/.claude/plugins"
log ""

# ---------------------------------------------------------------------------
# Isolated env — single-shell export (defensive; this generator never touches
# HOME, but the isolation contract is baked in regardless).
# ---------------------------------------------------------------------------
export HOME
HOME="$(mktemp -d)"
export AGENT_HOME="$REAL_REPO"

log "## Isolated env"
log "- HOME(temp)=$HOME"
log "- AGENT_HOME=$AGENT_HOME"
log ""

GEN="$REAL_REPO/adapters/claude/bin/sync-native-plugin.py"
PLUGIN_ROOT="$REAL_REPO/adapters/claude/plugin-marketplace/plugins/agent-harness-claude"

# ---------------------------------------------------------------------------
# 0. Pre-condition — worktree clean/expected before mutating generator output.
# ---------------------------------------------------------------------------
log "## 0. Pre-condition — git status baseline"
cd "$REAL_REPO"
BASELINE_STATUS=$(git status --porcelain)
log '```'
log "$BASELINE_STATUS"
log '```'
# Everything outside the marketplace subtree + the generator script itself
# must be the *expected* cycle-2 diff (INSTALL_LAYOUT.md, drivers/claude.py) —
# not touched by this script. Confinement is checked precisely in step 4.
log ""

# ---------------------------------------------------------------------------
# 1. Syntax — py_compile.
# ---------------------------------------------------------------------------
log "## 1. Syntax — py_compile"
set +e
SYN_OUT=$(cd "$REAL_REPO" && python3 -m py_compile adapters/claude/bin/sync-native-plugin.py tools/install/drivers/claude.py 2>&1)
SYN_CODE=$?
set -e
log '```'
log "${SYN_OUT:-（출력 없음 — 정상）}"
log '```'
okval=$([ "$SYN_CODE" -eq 0 ] && echo 0 || echo 1)
chk "syntax.py_compile" HIGH "py_compile sync-native-plugin.py + drivers/claude.py — exit=$SYN_CODE" "$okval"
log ""

# ---------------------------------------------------------------------------
# 2. Import — load sync-native-plugin.py as a module without executing main().
# ---------------------------------------------------------------------------
log "## 2. Import — sync-native-plugin.py module load"
set +e
IMPORT_OUT=$(python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('sync_native_plugin', '$GEN')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
assert callable(mod.sync)
assert callable(mod.check)
assert callable(mod.plugin_json)
assert callable(mod.marketplace_json)
assert callable(mod.hooks_json)
print('OK', mod.PLUGIN_ROOT)
" 2>&1)
IMPORT_CODE=$?
set -e
log '```'
log "$IMPORT_OUT"
log '```'
okval=$([ "$IMPORT_CODE" -eq 0 ] && echo 0 || echo 1)
chk "import.sync_native_plugin_module" HIGH "module loads, sync/check/plugin_json/marketplace_json/hooks_json callable — exit=$IMPORT_CODE" "$okval"
log ""

# ---------------------------------------------------------------------------
# 3. Smoke — --check on the currently-clean generated tree.
# ---------------------------------------------------------------------------
log "## 3. Smoke — --check on clean tree"
set +e
CHECK1_OUT=$(cd "$REAL_REPO" && python3 adapters/claude/bin/sync-native-plugin.py --check 2>&1)
CHECK1_CODE=$?
set -e
log '```'
log "$CHECK1_OUT"
log '```'
okval=$([ "$CHECK1_CODE" -eq 0 ] && echo 0 || echo 1)
chk "smoke.check_clean_exit0" HIGH "sync-native-plugin.py --check on clean tree — exit=$CHECK1_CODE (expect 0)" "$okval"
log ""

# ---------------------------------------------------------------------------
# 4. Functional — sync() idempotency, drift detection (touch + excess-file),
#    regeneration, and write-set confinement.
# ---------------------------------------------------------------------------
log "## 4. Functional — sync() idempotency / drift detection / confinement"

# 4a. re-run sync(): must be byte-identical (no git diff) to the already
#     committed-untracked baseline generated tree.
set +e
SYNC1_OUT=$(cd "$REAL_REPO" && python3 adapters/claude/bin/sync-native-plugin.py 2>&1)
SYNC1_CODE=$?
set -e
log '```'
log "$SYNC1_OUT"
log '```'
okval=$([ "$SYNC1_CODE" -eq 0 ] && echo 0 || echo 1)
chk "functional.sync_reruns_ok" HIGH "sync() re-run — exit=$SYNC1_CODE" "$okval"

AFTER_SYNC_STATUS=$(git status --porcelain)
okval=$([ "$AFTER_SYNC_STATUS" = "$BASELINE_STATUS" ] && echo 0 || echo 1)
chk "functional.sync_idempotent_no_diff" HIGH "git status --porcelain unchanged after a re-run of sync() (byte-identical output)" "$okval"

set +e
CHECK2_OUT=$(cd "$REAL_REPO" && python3 adapters/claude/bin/sync-native-plugin.py --check 2>&1)
CHECK2_CODE=$?
set -e
okval=$([ "$CHECK2_CODE" -eq 0 ] && echo 0 || echo 1)
chk "functional.check_clean_after_resync" HIGH "--check exit=$CHECK2_CODE after idempotent re-sync (expect 0)" "$okval"

# 4b. drift detection — touch a generated file, --check must fail and name it.
TOUCHED_FILE="$PLUGIN_ROOT/skills/audit/SKILL.md"
printf '\n<!-- drift-probe -->\n' >> "$TOUCHED_FILE"
set +e
CHECK3_OUT=$(cd "$REAL_REPO" && python3 adapters/claude/bin/sync-native-plugin.py --check 2>&1)
CHECK3_CODE=$?
set -e
log "### 4b. drift-probe --check output"
log '```'
log "$CHECK3_OUT"
log '```'
okval=$([ "$CHECK3_CODE" -eq 1 ] && echo 0 || echo 1)
chk "functional.check_detects_touch" HIGH "--check exit=$CHECK3_CODE after touching a generated file (expect 1)" "$okval"
case "$CHECK3_OUT" in
  *"skills/audit/SKILL.md"*) okval=0 ;;
  *) okval=1 ;;
esac
chk "functional.check_names_touched_file" HIGH "stale[] output names the exact touched file" "$okval"

# 4c. excess-file detection — stray file inside a generated subtree not from SoT.
STRAY_FILE="$PLUGIN_ROOT/agents/__stray_probe.md"
printf 'stray\n' > "$STRAY_FILE"
set +e
CHECK4_OUT=$(cd "$REAL_REPO" && python3 adapters/claude/bin/sync-native-plugin.py --check 2>&1)
CHECK4_CODE=$?
set -e
log "### 4c. excess-file --check output"
log '```'
log "$CHECK4_OUT"
log '```'
okval=$([ "$CHECK4_CODE" -eq 1 ] && echo 0 || echo 1)
chk "functional.check_detects_excess_file" HIGH "--check exit=$CHECK4_CODE with an extra untracked file under agents/ (expect 1)" "$okval"
case "$CHECK4_OUT" in
  *"__stray_probe.md"*) okval=0 ;;
  *) okval=1 ;;
esac
chk "functional.check_names_stray_file" HIGH "stale[] output names the stray excess file" "$okval"

# 4d. regenerate — sync() must erase both the touch and the stray file (rmtree-then-copytree).
set +e
SYNC2_OUT=$(cd "$REAL_REPO" && python3 adapters/claude/bin/sync-native-plugin.py 2>&1)
SYNC2_CODE=$?
set -e
okval=$([ "$SYNC2_CODE" -eq 0 ] && echo 0 || echo 1)
chk "functional.regen_after_drift_ok" HIGH "sync() regenerates after drift+stray — exit=$SYNC2_CODE" "$okval"

set +e
CHECK5_OUT=$(cd "$REAL_REPO" && python3 adapters/claude/bin/sync-native-plugin.py --check 2>&1)
CHECK5_CODE=$?
set -e
okval=$([ "$CHECK5_CODE" -eq 0 ] && echo 0 || echo 1)
chk "functional.check_clean_after_regen" HIGH "--check exit=$CHECK5_CODE after regeneration (expect 0, clean again)" "$okval"

if [ -f "$STRAY_FILE" ]; then okval=1; else okval=0; fi
chk "functional.stray_file_removed_by_regen" HIGH "stray excess file removed by rmtree-then-copytree regen" "$okval"

FINAL_STATUS=$(git status --porcelain)
okval=$([ "$FINAL_STATUS" = "$BASELINE_STATUS" ] && echo 0 || echo 1)
chk "functional.final_state_matches_baseline" HIGH "git status --porcelain after touch->stray->regen cycle matches the pre-test baseline exactly (deterministic round-trip)" "$okval"
log ""

# ---------------------------------------------------------------------------
# 5. Write-set confinement — nothing outside adapters/claude/plugin-marketplace/
#    (plus the already-tracked generator script itself, unchanged) was ever
#    touched by this script's generator invocations.
# ---------------------------------------------------------------------------
log "## 5. Write-set confinement"
OUTSIDE_DIFF=$(git status --porcelain -- . \
  ':!adapters/claude/plugin-marketplace' \
  ':!adapters/claude/bin/sync-native-plugin.py')
# The cycle's own already-in-progress edits (INSTALL_LAYOUT.md, drivers/claude.py,
# .agent_reports/**) are expected baseline noise from *other* phases, not from
# this script's generator calls — confinement means this set is IDENTICAL
# before and after, which functional.final_state_matches_baseline (step 4)
# already proved for the full status; this step isolates the claim to the
# non-marketplace, non-generator-script portion specifically.
BASELINE_OUTSIDE=$(printf '%s\n' "$BASELINE_STATUS" | grep -v -E '(^\?\? adapters/claude/plugin-marketplace/|^\?\? adapters/claude/bin/sync-native-plugin\.py$)' || true)
log '```'
log "$OUTSIDE_DIFF"
log '```'
okval=$([ "$OUTSIDE_DIFF" = "$BASELINE_OUTSIDE" ] && echo 0 || echo 1)
chk "confinement.no_writes_outside_marketplace" HIGH "git status outside adapters/claude/plugin-marketplace/ + the generator script is unchanged from baseline (generator wrote nowhere else)" "$okval"
log ""

log "## Done — Phase 1 generator graduated tests complete, see Summary above."
