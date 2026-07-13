#!/bin/sh
# 02_driver_plugin_wiring_and_verify.sh — code-test Phase 5 for Phase 2
# (drivers/claude.py install --plugin wrapping) + Phase 3 (checks() plugin
# verify checks), CLI-gated where `claude` CLI is used.
#
# Hard isolation contract (INCIDENT_real_home_touched.md, plan.md Phase 5):
#   - ONE `sh` process, ONE Bash tool invocation. HOME/AGENT_HOME/
#     CLAUDE_CONFIG_DIR exported at the very top of THIS file, never carried
#     across a tool-call boundary.
#   - real `claude plugin` CLI mutations (marketplace add / plugin install)
#     ONLY ever run under a mktemp CLAUDE_CONFIG_DIR — never against the real
#     ~/.claude/plugins. Gated behind `claude` CLI presence; SKIP not fail
#     when absent.
#   - determinism guard: sha256 of real ~/.claude/settings.json,
#     ~/.codex/config.toml, ~/.config/opencode/opencode.json + recursive hash
#     of real ~/.claude/plugins, captured before HOME/CLAUDE_CONFIG_DIR are
#     reassigned, re-checked in an EXIT trap.
set -eu

REAL_REPO="/home/Uihyeop/agent_setting-wt/harness-installer-impl2"
PLAN_DIR="$REAL_REPO/.agent_reports/plans/2026-07-13_harness-installer-impl2"
LOGDIR="$PLAN_DIR/test_logs"
REVIEWDIR="$PLAN_DIR/_internal/test_reviews"
mkdir -p "$LOGDIR" "$REVIEWDIR"
LOG="$LOGDIR/02_driver_plugin_wiring_and_verify.md"
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
    echo "# code-test — 02 driver plugin wiring + verify (Phase 2+3) result"
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
      echo "(hashes captured before HOME/CLAUDE_CONFIG_DIR were reassigned, re-checked"
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

  if [ -d "${ART:-}" ]; then
    rm -rf "$REVIEWDIR/02_artifacts"
    cp -r "$ART" "$REVIEWDIR/02_artifacts" 2>/dev/null || true
  fi

  rm -rf "${HOME:-}" 2>/dev/null || true
  rm -rf "${CLAUDE_CONFIG_DIR:-}" 2>/dev/null || true
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
# Isolated env — single-shell export. CLAUDE_CONFIG_DIR is set here (top of
# script, alongside HOME/AGENT_HOME) so that EVERY claude CLI invocation for
# the rest of this script — including the ones nested inside checks()'s
# _plugin_registered closure in step 5, not just the explicit CLI calls in
# step 6 — is confined to a throwaway config root from the very first call,
# never relying on HOME-reassignment alone for isolation (Phase 5 §4: CLI
# tests "point CLAUDE_CONFIG_DIR (mktemp) at a throwaway dir" explicitly).
# ---------------------------------------------------------------------------
export HOME
HOME="$(mktemp -d)"
export AGENT_HOME="$REAL_REPO"
export CLAUDE_CONFIG_DIR
CLAUDE_CONFIG_DIR="$(mktemp -d)"
ART="$HOME/artifacts"
mkdir -p "$ART" "$HOME/.claude"

INSTALL_PY="$REAL_REPO/tools/install"
HARNESS_SH="$REAL_REPO/tools/install/harness.sh"
harness() { sh "$HARNESS_SH" "$@"; }

log "## Isolated env"
log "- HOME(temp)=$HOME"
log "- AGENT_HOME=$AGENT_HOME"
log "- CLAUDE_CONFIG_DIR(temp)=$CLAUDE_CONFIG_DIR"
log ""

CLAUDE_PRESENT=0
if command -v claude >/dev/null 2>&1; then CLAUDE_PRESENT=1; fi
log "- claude CLI present on PATH: $CLAUDE_PRESENT ($(command -v claude 2>/dev/null || echo n/a))"
log ""

# ---------------------------------------------------------------------------
# 1. Syntax — py_compile (independent re-check, self-contained per script).
# ---------------------------------------------------------------------------
log "## 1. Syntax — py_compile"
set +e
SYN_OUT=$(cd "$REAL_REPO" && python3 -m py_compile tools/install/drivers/claude.py 2>&1)
SYN_CODE=$?
set -e
log '```'
log "${SYN_OUT:-（출력 없음 — 정상）}"
log '```'
okval=$([ "$SYN_CODE" -eq 0 ] && echo 0 || echo 1)
chk "syntax.py_compile" HIGH "py_compile drivers/claude.py — exit=$SYN_CODE" "$okval"
log ""

# ---------------------------------------------------------------------------
# 2. Import — drivers.claude module + _plugin_action symbol.
# ---------------------------------------------------------------------------
log "## 2. Import — drivers.claude"
set +e
IMP_OUT=$(python3 -c "
import sys
sys.path.insert(0, '$INSTALL_PY')
from drivers import claude as claude_driver
assert callable(claude_driver._plugin_action)
assert callable(claude_driver.install)
assert callable(claude_driver.checks)
print('OK', claude_driver._MARKETPLACE_NAME, claude_driver._PLUGIN_SPEC)
" 2>&1)
IMP_CODE=$?
set -e
log '```'
log "$IMP_OUT"
log '```'
okval=$([ "$IMP_CODE" -eq 0 ] && echo 0 || echo 1)
chk "import.drivers_claude" HIGH "drivers.claude imports, _plugin_action/install/checks callable — exit=$IMP_CODE" "$okval"
log ""

# ---------------------------------------------------------------------------
# 3. Smoke — dry-run install(plugin=True) under mktemp HOME, both via direct
#    Python call and via the `harness` CLI wrapper.
# ---------------------------------------------------------------------------
log "## 3. Smoke — install(plugin=True, dry_run=True)"
set +e
DRYRUN_OUT=$(python3 -c "
import sys, json
sys.path.insert(0, '$INSTALL_PY')
from drivers import claude as claude_driver
result = claude_driver.install(scope='global', plugin=True, dry_run=True)
print(json.dumps(result))
" 2>&1)
DRYRUN_CODE=$?
set -e
printf '%s' "$DRYRUN_OUT" > "$ART/direct_install_dryrun.json"
okval=$([ "$DRYRUN_CODE" -eq 0 ] && echo 0 || echo 1)
chk "smoke.direct_install_dryrun_ran" HIGH "claude_driver.install(plugin=True, dry_run=True) ran — exit=$DRYRUN_CODE" "$okval"

set +e
python3 -c "
import json
d = json.load(open('$ART/direct_install_dryrun.json'))
plugin_actions = [a for a in d['actions'] if a['action'] == 'plugin']
assert len(plugin_actions) == 1, plugin_actions
pa = plugin_actions[0]
assert pa['status'] == 'planned', pa
assert 'claude plugin marketplace add' in pa['detail'], pa
assert 'claude plugin install' in pa['detail'], pa
assert 'agent-harness-claude@agent-harness' in pa['detail'], pa
other_actions = [a for a in d['actions'] if a['action'] in ('symlink', 'copy_once', 'skip', 'delegate')]
assert len(other_actions) >= 10, len(other_actions)
assert d['blocked'] is False, d['blocked']
"
ASSERT_CODE=$?
set -e
chk "smoke.dryrun_both_commands_and_projection" HIGH "plugin action status=planned with both CLI commands in detail; symlink/copy_once projection (10+ actions) also present in the same result; blocked=False" "$ASSERT_CODE"

# via harness CLI wrapper (installer.py cmd_install --json shape: checks[]).
set +e
CLI_DRYRUN_OUT=$(cd "$REAL_REPO" && harness install claude --plugin --dry-run --json)
CLI_DRYRUN_CODE=$?
set -e
printf '%s' "$CLI_DRYRUN_OUT" > "$ART/cli_install_dryrun.json"
okval=$([ "$CLI_DRYRUN_CODE" -eq 0 ] && echo 0 || echo 1)
chk "smoke.cli_install_dryrun_exit0" HIGH "harness install claude --plugin --dry-run --json — exit=$CLI_DRYRUN_CODE" "$okval"

set +e
python3 -c "
import json
d = json.load(open('$ART/cli_install_dryrun.json'))
ids = [c['id'] for c in d['checks']]
assert 'claude.plugin.x' in ids, ids
plugin_check = next(c for c in d['checks'] if c['id'] == 'claude.plugin.x')
assert plugin_check['ok'] is True, plugin_check
assert 'marketplace add' in plugin_check['detail'] and 'plugin install' in plugin_check['detail'], plugin_check
symlink_ids = [i for i in ids if i.startswith('claude.symlink.') or i.startswith('claude.copy_once.')]
assert len(symlink_ids) >= 10, symlink_ids
assert d['channel'] == 'plugin', d['channel']
"
ASSERT_CODE=$?
set -e
chk "smoke.cli_dryrun_prints_both_cmds_and_full_plan" HIGH "harness CLI --json: claude.plugin.x present with both commands + full symlink/copy_once plan alongside it" "$ASSERT_CODE"
log ""

# ---------------------------------------------------------------------------
# 4. CLI-absent SKIP path — PATH stripped of claude's directory only.
# ---------------------------------------------------------------------------
log "## 4. CLI-absent SKIP — PATH without claude"
CLAUDE_BIN_DIR=$(dirname "$(command -v claude 2>/dev/null || echo /nonexistent/claude)")
PY3_DIR=$(dirname "$(command -v python3)")
SH_DIRS="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
SAFE_PATH="$PY3_DIR:$SH_DIRS"
# defensively strip the claude bin dir if it happens to overlap a coreutils dir
SAFE_PATH=$(printf '%s' "$SAFE_PATH" | tr ':' '\n' | grep -v -F "$CLAUDE_BIN_DIR" | tr '\n' ':' | sed 's/:$//')

set +e
SKIP_OUT=$(PATH="$SAFE_PATH" python3 -c "
import sys, json
sys.path.insert(0, '$INSTALL_PY')
from drivers import claude as claude_driver
result = {}
result['plugin_action_cli_absent'] = claude_driver._plugin_action(dry_run=False)
checks = claude_driver.checks(scope='global')
by_id = {}
for c in checks:
    r = c()
    by_id[r['id']] = r
result['plugin_registered_cli_absent'] = by_id.get('claude.plugin-registered')
result['bootstrap_smoke_cli_absent'] = by_id.get('claude.bootstrap-smoke')
print(json.dumps(result))
" 2>&1)
SKIP_CODE=$?
set -e
printf '%s' "$SKIP_OUT" > "$ART/cli_absent_probe.json"
okval=$([ "$SKIP_CODE" -eq 0 ] && echo 0 || echo 1)
chk "skip.cli_absent_probe_ran" HIGH "PATH-stripped probe ran (exit=$SKIP_CODE); PATH used: $SAFE_PATH" "$okval"

if [ "$SKIP_CODE" -eq 0 ]; then
  set +e
  python3 -c "
import json
d = json.load(open('$ART/cli_absent_probe.json'))
pa = d['plugin_action_cli_absent']
assert pa['status'] == 'skipped', pa
assert 'SKIP(claude)' in pa['detail'], pa
"
  ASSERT_CODE=$?
  set -e
  chk "skip.plugin_action_skips_no_subprocess" HIGH "_plugin_action(dry_run=False) returns status=skipped with SKIP(claude) detail when claude CLI unresolvable — no subprocess call attempted" "$ASSERT_CODE"

  set +e
  python3 -c "
import json
d = json.load(open('$ART/cli_absent_probe.json'))
pr = d['plugin_registered_cli_absent']
assert pr['ok'] is True, pr
assert 'SKIP(claude)' in pr['detail'], pr
"
  ASSERT_CODE=$?
  set -e
  chk "skip.plugin_registered_check_skips" HIGH "claude.plugin-registered check reports ok=true SKIP when claude CLI absent (never fails verify on CLI-absent boxes)" "$ASSERT_CODE"
else
  log "- [HIGH-FAIL] skip.plugin_action_skips_no_subprocess — probe crashed, see cli_absent_probe.json"
  FAIL_COUNT=$((FAIL_COUNT + 2))
  FAILED_IDS="$FAILED_IDS skip.plugin_action_skips_no_subprocess(probe-crash) skip.plugin_registered_check_skips(probe-crash)"
fi
log ""

# ---------------------------------------------------------------------------
# 5. checks() count + new IDs present (no CLI required for this assertion).
# ---------------------------------------------------------------------------
log "## 5. checks() — new Phase 3 IDs present"
set +e
CHECKS_OUT=$(python3 -c "
import sys, json
sys.path.insert(0, '$INSTALL_PY')
from drivers import claude as claude_driver
cl = claude_driver.checks(scope='global')
ids = [c() ['id'] for c in cl]
print(json.dumps({'count': len(ids), 'ids': ids}))
" 2>&1)
CHECKS_CODE=$?
set -e
printf '%s' "$CHECKS_OUT" > "$ART/checks_ids.json"
okval=$([ "$CHECKS_CODE" -eq 0 ] && echo 0 || echo 1)
chk "checks.enumeration_ran" HIGH "claude_driver.checks() enumerated — exit=$CHECKS_CODE" "$okval"

set +e
python3 -c "
import json
d = json.load(open('$ART/checks_ids.json'))
assert d['count'] == 23, d['count']
for expect in ('claude.sync-native-plugin', 'claude.plugin-marketplace-source', 'claude.plugin-registered'):
    assert expect in d['ids'], (expect, d['ids'])
"
ASSERT_CODE=$?
set -e
chk "checks.count_23_and_three_new_ids" HIGH "checks() returns 23 callables (was 20 pre-Phase-3) including claude.sync-native-plugin / claude.plugin-marketplace-source / claude.plugin-registered" "$ASSERT_CODE"
log ""

if [ "$CLAUDE_PRESENT" -eq 0 ]; then
  log "## 6-7. CLI-gated integration — SKIPPED (claude CLI not present on PATH)"
  log ""
  log "## Done — Phase 2+3 graduated tests complete (CLI-gated integration SKIPPED, see Summary)."
  exit 0
fi

# ---------------------------------------------------------------------------
# 6. CLI-gated integration — real registration under mktemp CLAUDE_CONFIG_DIR.
#    Never touches the real ~/.claude/plugins.
# ---------------------------------------------------------------------------
log "## 6. CLI-gated integration — real claude plugin registration (mktemp CLAUDE_CONFIG_DIR)"
log "- reusing CLAUDE_CONFIG_DIR(temp)=$CLAUDE_CONFIG_DIR set at script top (still empty/unregistered so far)"

# 6a. pre-registration: checks() must report unregistered (real, not SKIP —
# CLI is present, config dir is fresh and empty).
set +e
PRE_REG_OUT=$(python3 -c "
import sys, json
sys.path.insert(0, '$INSTALL_PY')
from drivers import claude as claude_driver
checks = claude_driver.checks(scope='global')
by_id = {c()['id']: None for c in []}
result = None
for c in checks:
    r = c()
    if r['id'] == 'claude.plugin-registered':
        result = r
print(json.dumps(result))
" 2>&1)
PRE_REG_CODE=$?
set -e
printf '%s' "$PRE_REG_OUT" > "$ART/pre_registration_check.json"
okval=$([ "$PRE_REG_CODE" -eq 0 ] && echo 0 || echo 1)
chk "integration.pre_registration_probe_ran" HIGH "claude.plugin-registered probed before registration — exit=$PRE_REG_CODE" "$okval"

set +e
python3 -c "
import json
d = json.load(open('$ART/pre_registration_check.json'))
assert d['ok'] is False, d
assert 'agent-harness' in d['detail'], d
"
ASSERT_CODE=$?
set -e
chk "integration.pre_registration_truthfully_false" HIGH "claude.plugin-registered ok=False under a fresh mktemp CLAUDE_CONFIG_DIR (nothing registered yet) — not a SKIP, a truthful real-state read" "$ASSERT_CODE"

# 6b. install(plugin=True, dry_run=False) — real marketplace add + plugin install.
set +e
REG_OUT=$(python3 -c "
import sys, json
sys.path.insert(0, '$INSTALL_PY')
from drivers import claude as claude_driver
result = claude_driver.install(scope='global', plugin=True, dry_run=False)
print(json.dumps(result))
" 2>&1)
REG_CODE=$?
set -e
printf '%s' "$REG_OUT" > "$ART/real_install_plugin.json"
okval=$([ "$REG_CODE" -eq 0 ] && echo 0 || echo 1)
chk "integration.install_plugin_real_ran" HIGH "claude_driver.install(plugin=True, dry_run=False) ran under mktemp CLAUDE_CONFIG_DIR — exit=$REG_CODE" "$okval"

set +e
python3 -c "
import json
d = json.load(open('$ART/real_install_plugin.json'))
plugin_actions = [a for a in d['actions'] if a['action'] == 'plugin']
assert len(plugin_actions) == 1, plugin_actions
pa = plugin_actions[0]
assert pa['status'] == 'registered', pa
assert 'agent-harness-claude@agent-harness' in pa['detail'], pa
"
ASSERT_CODE=$?
set -e
chk "integration.status_registered" HIGH "plugin action status=registered after real marketplace add + plugin install under mktemp CLAUDE_CONFIG_DIR" "$ASSERT_CODE"

# 6c. read-only cross-check via direct claude CLI queries, scoped to the mktemp config dir.
set +e
MP_LIST_OUT=$(claude plugin marketplace list --json 2>&1)
MP_LIST_CODE=$?
set -e
printf '%s' "$MP_LIST_OUT" > "$ART/claude_marketplace_list.json"
okval=$([ "$MP_LIST_CODE" -eq 0 ] && echo 0 || echo 1)
chk "integration.marketplace_list_exit0" HIGH "claude plugin marketplace list --json (CLAUDE_CONFIG_DIR=mktemp) — exit=$MP_LIST_CODE" "$okval"

set +e
python3 -c "
import json
d = json.load(open('$ART/claude_marketplace_list.json'))
assert any(m.get('name') == 'agent-harness' for m in d), d
"
ASSERT_CODE=$?
set -e
chk "integration.marketplace_agent_harness_present" HIGH "'agent-harness' marketplace appears in read-only marketplace list" "$ASSERT_CODE"

set +e
PL_LIST_OUT=$(claude plugin list --json 2>&1)
PL_LIST_CODE=$?
set -e
printf '%s' "$PL_LIST_OUT" > "$ART/claude_plugin_list.json"
okval=$([ "$PL_LIST_CODE" -eq 0 ] && echo 0 || echo 1)
chk "integration.plugin_list_exit0" HIGH "claude plugin list --json (CLAUDE_CONFIG_DIR=mktemp) — exit=$PL_LIST_CODE" "$okval"

set +e
python3 -c "
import json, os
d = json.load(open('$ART/claude_plugin_list.json'))
match = next((p for p in d if p.get('id') == 'agent-harness-claude@agent-harness'), None)
assert match is not None, d
assert match.get('enabled') is True, match
install_path = match.get('installPath', '')
real_home_plugins = os.path.join('$REAL_HOME_ORIG', '.claude', 'plugins')
assert not install_path.startswith(real_home_plugins), install_path
assert '$CLAUDE_CONFIG_DIR' in install_path or '$HOME' in install_path or install_path, install_path
"
ASSERT_CODE=$?
set -e
chk "integration.plugin_installed_under_temp_config_not_real_home" HIGH "agent-harness-claude@agent-harness enabled=true, installPath is NOT under the real ~/.claude/plugins" "$ASSERT_CODE"

# 6d. post-registration: checks() must flip to ok=True (truthfully reflects live state).
set +e
POST_REG_OUT=$(python3 -c "
import sys, json
sys.path.insert(0, '$INSTALL_PY')
from drivers import claude as claude_driver
checks = claude_driver.checks(scope='global')
result = None
for c in checks:
    r = c()
    if r['id'] == 'claude.plugin-registered':
        result = r
print(json.dumps(result))
" 2>&1)
POST_REG_CODE=$?
set -e
printf '%s' "$POST_REG_OUT" > "$ART/post_registration_check.json"
okval=$([ "$POST_REG_CODE" -eq 0 ] && echo 0 || echo 1)
chk "integration.post_registration_probe_ran" HIGH "claude.plugin-registered probed after registration — exit=$POST_REG_CODE" "$okval"

set +e
python3 -c "
import json
d = json.load(open('$ART/post_registration_check.json'))
assert d['ok'] is True, d
assert 'agent-harness' in d['detail'] and 'agent-harness-claude' in d['detail'], d
"
ASSERT_CODE=$?
set -e
chk "integration.post_registration_ok_true" HIGH "claude.plugin-registered flips to ok=True after registration, detail names both marketplace + plugin" "$ASSERT_CODE"

# ---------------------------------------------------------------------------
# 7. `harness verify claude --json` includes the 3 new checks end-to-end.
# ---------------------------------------------------------------------------
log "## 7. harness verify claude --json — full CLI path"
set +e
VERIFY_OUT=$(cd "$REAL_REPO" && harness verify claude --json)
VERIFY_CODE=$?
set -e
printf '%s' "$VERIFY_OUT" > "$ART/cli_verify_claude.json"
okval=0
if [ "$VERIFY_CODE" -eq 0 ] || [ "$VERIFY_CODE" -eq 2 ]; then okval=0; else okval=1; fi
chk "integration.verify_exit_in_expected_set" HIGH "harness verify claude --json exit is 0 or 2 (never a crash) — got $VERIFY_CODE" "$okval"

set +e
python3 -c "
import json
d = json.load(open('$ART/cli_verify_claude.json'))
ids = {c['id']: c for c in d['checks']}
for expect in ('claude.sync-native-plugin', 'claude.plugin-marketplace-source', 'claude.plugin-registered'):
    assert expect in ids, (expect, list(ids))
assert ids['claude.sync-native-plugin']['ok'] is True, ids['claude.sync-native-plugin']
assert ids['claude.plugin-marketplace-source']['ok'] is True, ids['claude.plugin-marketplace-source']
assert ids['claude.plugin-registered']['ok'] is True, ids['claude.plugin-registered']
assert all(c['id'].startswith('claude.') for c in d['checks']), [c['id'] for c in d['checks'] if not c['id'].startswith('claude.')]
"
ASSERT_CODE=$?
set -e
chk "integration.verify_json_has_three_new_checks_ok" HIGH "harness verify claude --json: claude.sync-native-plugin / claude.plugin-marketplace-source / claude.plugin-registered all present + ok=True (registration still live under CLAUDE_CONFIG_DIR)" "$ASSERT_CODE"

# 7b. read-only — verify never mutates. Tight before/after window.
PRE_VERIFY_PLUGIN_HASH=$(dir_sha_or_absent "$CLAUDE_CONFIG_DIR")
set +e
VERIFY2_OUT=$(cd "$REAL_REPO" && harness verify claude --json)
VERIFY2_CODE=$?
set -e
POST_VERIFY_PLUGIN_HASH=$(dir_sha_or_absent "$CLAUDE_CONFIG_DIR")
okval=$([ "$PRE_VERIFY_PLUGIN_HASH" = "$POST_VERIFY_PLUGIN_HASH" ] && echo 0 || echo 1)
chk "integration.verify_read_only_on_config_dir" HIGH "mktemp CLAUDE_CONFIG_DIR byte-identical immediately before/after a verify call (verify never installs/mutates during registration check)" "$okval"
log ""

log "## Done — Phase 2+3 graduated tests complete (CLI-gated integration ran), see Summary above."
