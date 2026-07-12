#!/bin/sh
# e2e_lifecycle.sh — code-test standard-tier verification for tools/install/ (harness CLI).
#
# Hard isolation contract (INCIDENT_real_home_touched.md direct response):
#   - runs entirely inside ONE `sh` process (this file), so HOME/AGENT_HOME/MEM_STORE
#     exported here stay exported for every command below — never split across
#     separate Bash tool calls (that env-loss is the incident's documented root cause).
#   - HOME is reassigned to a mktemp dir before the first `harness` invocation.
#   - the only references to the real HOME are the sha256 snapshots used by the
#     determinism guard (captured from $HOME as inherited at process start, before
#     reassignment) — no real-home path is ever a literal in this file.
set -eu

REAL_REPO="/home/Uihyeop/agent_setting-wt/harness-installer-impl"
PLAN_DIR="$REAL_REPO/.agent_reports/plans/2026-07-13_harness-installer-impl"
LOGDIR="$PLAN_DIR/test_logs"
REVIEWDIR="$PLAN_DIR/_internal/test_reviews"
ASSERT_PY="$PLAN_DIR/_internal/test_scripts/_json_assert.py"
mkdir -p "$LOGDIR" "$REVIEWDIR"
LOG="$LOGDIR/e2e_lifecycle.md"
WORKLOG=$(mktemp)

export PYTHONDONTWRITEBYTECODE=1

# ---------------------------------------------------------------------------
# Determinism guard — capture real-home file hashes BEFORE HOME is ever reassigned.
# ---------------------------------------------------------------------------
REAL_HOME_ORIG="$HOME"
GUARD_CLAUDE_SETTINGS="$REAL_HOME_ORIG/.claude/settings.json"
GUARD_CODEX_CONFIG="$REAL_HOME_ORIG/.codex/config.toml"
GUARD_OPENCODE_CONFIG="$REAL_HOME_ORIG/.config/opencode/opencode.json"

sha_or_absent() {
  if [ -f "$1" ]; then
    sha256sum "$1" | cut -d' ' -f1
  else
    echo "ABSENT"
  fi
}

GUARD_SHA1_BEFORE=$(sha_or_absent "$GUARD_CLAUDE_SETTINGS")
GUARD_SHA2_BEFORE=$(sha_or_absent "$GUARD_CODEX_CONFIG")
GUARD_SHA3_BEFORE=$(sha_or_absent "$GUARD_OPENCODE_CONFIG")

PASS_COUNT=0
FAIL_COUNT=0
FAILED_IDS=""

log() { printf '%s\n' "$*" >> "$WORKLOG"; }

chk() {
  # $1=id  $2=level(HIGH|MEDIUM|LOW)  $3=description  $4=0(pass)/nonzero(fail)
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

  GUARD_OK=0
  if [ "$GUARD_SHA1_BEFORE" != "$GUARD_SHA1_AFTER" ] || [ "$GUARD_SHA2_BEFORE" != "$GUARD_SHA2_AFTER" ] || [ "$GUARD_SHA3_BEFORE" != "$GUARD_SHA3_AFTER" ]; then
    GUARD_OK=1
  fi

  {
    echo "# code-test — harness-installer e2e lifecycle result"
    echo
    if [ "$GUARD_OK" = "1" ]; then
      echo "## [CRITICAL] real-home determinism guard FAILED"
      echo
      echo "A real runtime-home config file changed during this test run. STOP —"
      echo "do not attempt further remediation from this script; report immediately"
      echo "to the user/orchestrator before taking any other action."
      echo
      echo "- claude settings.json: before=$GUARD_SHA1_BEFORE after=$GUARD_SHA1_AFTER"
      echo "- codex config.toml:    before=$GUARD_SHA2_BEFORE after=$GUARD_SHA2_AFTER"
      echo "- opencode config.json: before=$GUARD_SHA3_BEFORE after=$GUARD_SHA3_AFTER"
      echo
    else
      echo "## [PASS] real-home determinism guard"
      echo
      echo "No change detected in real ~/.claude/settings.json, ~/.codex/config.toml,"
      echo "~/.config/opencode/opencode.json across the whole run (hashes captured"
      echo "before HOME was reassigned to a mktemp dir, re-checked at exit via trap)."
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

  # preserve raw JSON artifacts for post-hoc inspection (outside the temp HOME,
  # which we remove next) — allowed write scope (_internal/test_reviews/).
  if [ -d "${ART:-}" ]; then
    rm -rf "$REVIEWDIR/e2e_artifacts"
    cp -r "$ART" "$REVIEWDIR/e2e_artifacts" 2>/dev/null || true
  fi

  if [ "$GUARD_OK" = "1" ]; then
    rm -rf "${HOME:-}" 2>/dev/null || true
    exit 99
  fi

  rm -rf "${HOME:-}" 2>/dev/null || true
  exit "$EXITCODE"
}
trap finalize EXIT

log "## Baseline"
log "- REAL_REPO=$REAL_REPO"
log "- determinism-guard baseline captured for real ~/.claude, ~/.codex, ~/.config/opencode (hashes not printed here, compared at exit)"
log ""

# ---------------------------------------------------------------------------
# Isolated env — single-shell export, per the incident's process fix.
# ---------------------------------------------------------------------------
export HOME
HOME="$(mktemp -d)"
export AGENT_HOME="$REAL_REPO"
export MEM_STORE="$HOME/mem"
mkdir -p "$MEM_STORE"
ART="$HOME/artifacts"
mkdir -p "$ART"

harness() { sh "$REAL_REPO/tools/install/harness.sh" "$@"; }

log "## Isolated env"
log "- HOME(temp)=$HOME"
log "- AGENT_HOME=$AGENT_HOME"
log "- MEM_STORE=$MEM_STORE"
log ""

# ---------------------------------------------------------------------------
# 1. Syntax — py_compile all installer modules.
# ---------------------------------------------------------------------------
log "## 1. Syntax — py_compile"
set +e
SYN_OUT=$(cd "$REAL_REPO" && python3 -m py_compile tools/install/*.py tools/install/drivers/*.py 2>&1)
SYN_CODE=$?
set -e
log '```'
log "${SYN_OUT:-（출력 없음 — 정상）}"
log '```'
okval=$([ "$SYN_CODE" -eq 0 ] && echo 0 || echo 1)
chk "syntax.py_compile" HIGH "python3 -m py_compile tools/install/*.py tools/install/drivers/*.py — exit=$SYN_CODE" "$okval"
log ""

# ---------------------------------------------------------------------------
# 2. Import — paths.agent_home() / paths.runtime_home('claude','global').
# ---------------------------------------------------------------------------
log "## 2. Import — paths.py"
set +e
P0_OUT=$(python3 -c "
import sys
sys.path.insert(0, '$REAL_REPO/tools/install')
import paths
print(paths.agent_home())
print(paths.runtime_home('claude', 'global'))
" 2>&1)
P0_CODE=$?
set -e
log '```'
log "$P0_OUT"
log '```'
P0_LINE1=$(printf '%s\n' "$P0_OUT" | sed -n '1p')
P0_LINE2=$(printf '%s\n' "$P0_OUT" | sed -n '2p')
if [ "$P0_CODE" -eq 0 ] && [ "$P0_LINE1" = "$REAL_REPO" ] && [ "$P0_LINE2" = "$HOME/.claude" ]; then
  okval=0
else
  okval=1
fi
chk "import.paths" HIGH "agent_home()==$REAL_REPO, runtime_home(claude,global)==\$HOME/.claude (temp) — got [$P0_LINE1] [$P0_LINE2] exit=$P0_CODE" "$okval"
log ""

# ---------------------------------------------------------------------------
# 3. Smoke — install --dry-run --json (all runtimes), no real writes.
# ---------------------------------------------------------------------------
log "## 3. Smoke — install --dry-run --json (all runtimes)"
set +e
SMOKE_OUT=$(harness install --dry-run --json)
SMOKE_CODE=$?
set -e
printf '%s' "$SMOKE_OUT" > "$ART/phase1_install_dryrun.json"
okval=$([ "$SMOKE_CODE" -eq 0 ] && echo 0 || echo 1)
chk "smoke.install_dryrun.exit0" HIGH "exit=$SMOKE_CODE (expect 0)" "$okval"

set +e
python3 "$ASSERT_PY" "$ART/phase1_install_dryrun.json" 'all(any(c["id"].startswith(rt + ".") for c in d["checks"]) for rt in ("claude", "codex", "opencode"))'
ASSERT_CODE=$?
set -e
chk "smoke.install_dryrun.all_three_runtimes" HIGH "checks[] covers claude/codex/opencode ids" "$ASSERT_CODE"

set +e
python3 "$ASSERT_PY" "$ART/phase1_install_dryrun.json" 'not any("source absent" in c.get("detail", "") for c in d["checks"])'
ASSERT_CODE=$?
set -e
chk "smoke.install_dryrun.no_source_absent_skips" HIGH "no skip:source-absent entries — {claude,codex,opencode}_setting/ all exist in this worktree" "$ASSERT_CODE"
log ""

# ---------------------------------------------------------------------------
# 4. Functional E2E — claude lifecycle (temp HOME only).
# ---------------------------------------------------------------------------
log "## 4. Functional — claude install / manifest / drift / reapply"
mkdir -p "$HOME/.claude"

set +e
P2_INSTALL_OUT=$(harness install claude --json)
P2_INSTALL_CODE=$?
set -e
printf '%s' "$P2_INSTALL_OUT" > "$ART/phase2_install_claude.json"
okval=$([ "$P2_INSTALL_CODE" -eq 0 ] && echo 0 || echo 1)
chk "e2e.install_claude.exit0" HIGH "harness install claude --json — exit=$P2_INSTALL_CODE" "$okval"

if [ -f "$HOME/.claude/.harness/manifest.json" ]; then okval=0; else okval=1; fi
chk "e2e.manifest_created" HIGH "\$HOME/.claude/.harness/manifest.json exists" "$okval"

if [ -L "$HOME/.claude/core" ] && [ -L "$HOME/.claude/skills" ]; then okval=0; else okval=1; fi
chk "e2e.symlinks_created" HIGH "projection symlinks created for representative claude entries (core, skills)" "$okval"

set +e
python3 "$ASSERT_PY" "$HOME/.claude/.harness/manifest.json" 'set(d.get("files", {}).keys()) >= {"settings.json", "keybindings.json"}'
ASSERT_CODE=$?
set -e
chk "e2e.manifest_hash_recorded" HIGH "manifest.files includes settings.json+keybindings.json hash entries" "$ASSERT_CODE"

# install codex + opencode for real too (still temp HOME only) so the verify
# calls below exercise all three runtimes instead of flagging codex/opencode
# as "not installed yet" (that would be a test-ordering artifact, not a real
# installer defect — codex/opencode driver install() never touches anything
# outside runtime_home(rt, scope), which resolves under our temp HOME).
set +e
CODEX_REAL_OUT=$(harness install codex --json)
CODEX_REAL_CODE=$?
set -e
printf '%s' "$CODEX_REAL_OUT" > "$ART/phase4_install_codex.json"
okval=$([ "$CODEX_REAL_CODE" -eq 0 ] && echo 0 || echo 1)
chk "e2e.install_codex.exit0" HIGH "harness install codex --json — exit=$CODEX_REAL_CODE" "$okval"

set +e
OPENCODE_REAL_OUT=$(harness install opencode --json)
OPENCODE_REAL_CODE=$?
set -e
printf '%s' "$OPENCODE_REAL_OUT" > "$ART/phase4_install_opencode.json"
okval=$([ "$OPENCODE_REAL_CODE" -eq 0 ] && echo 0 || echo 1)
chk "e2e.install_opencode.exit0" HIGH "harness install opencode --json — exit=$OPENCODE_REAL_CODE" "$okval"

set +e
VERIFY1_OUT=$(harness verify --json)
VERIFY1_CODE=$?
set -e
printf '%s' "$VERIFY1_OUT" > "$ART/phase34_verify_after_install.json"
if [ "$VERIFY1_CODE" -eq 0 ]; then
  okval=0
else
  okval=1
fi
chk "e2e.verify_after_install.exit0" HIGH "harness verify --json right after install (claude+codex+opencode all installed) — expect all pass, exit=$VERIFY1_CODE" "$okval"

# drift injection — path built from the script's own temp-HOME variable, never hardcoded.
SETTINGS_PATH="$HOME/.claude/settings.json"
printf '\n// user edit\n' >> "$SETTINGS_PATH"

set +e
P2_UPDATE_OUT=$(harness update --json)
P2_UPDATE_CODE=$?
set -e
printf '%s' "$P2_UPDATE_OUT" > "$ART/phase2_update_drift.json"
okval=$([ "$P2_UPDATE_CODE" -eq 4 ] && echo 0 || echo 1)
chk "e2e.drift_detected.exit4" HIGH "harness update --json after hand-edit — expect exit=4 (EXIT_DRIFT), got $P2_UPDATE_CODE" "$okval"

set +e
python3 "$ASSERT_PY" "$ART/phase2_update_drift.json" 'len(d.get("drift", [])) > 0 and any(dr["path"] == "settings.json" for dr in d["drift"])'
ASSERT_CODE=$?
set -e
chk "e2e.drift_nonempty" HIGH "drift[] non-empty and names settings.json" "$ASSERT_CODE"

set +e
P2_REAPPLY_OUT=$(harness update --reapply --json)
P2_REAPPLY_CODE=$?
set -e
printf '%s' "$P2_REAPPLY_OUT" > "$ART/phase2_reapply.json"
okval=$([ "$P2_REAPPLY_CODE" -eq 0 ] && echo 0 || echo 1)
chk "e2e.reapply.exit0" HIGH "harness update --reapply --json — exit=$P2_REAPPLY_CODE" "$okval"

set +e
python3 "$ASSERT_PY" "$ART/phase2_reapply.json" 'any(c["id"] == "update.reapplied" and c["detail"] == "1개 재적용" for c in d["checks"]) and any(c["id"] == "update.conflicts" and c["ok"] for c in d["checks"])'
ASSERT_CODE=$?
set -e
chk "e2e.reapply_reapplied_no_conflicts" HIGH "1 file reapplied via git merge-file 3-way, 0 conflicts" "$ASSERT_CODE"

if grep -q 'user edit' "$SETTINGS_PATH"; then okval=0; else okval=1; fi
chk "e2e.reapply_preserved_user_edit" HIGH "merged settings.json still contains '// user edit' after reapply" "$okval"
log ""
log "(note: canonical source file itself was NOT mutated for this reapply pass — doing so"
log " would require editing a git-tracked repo file outside this stage's write scope;"
log " the drift -> reapply -> user-edit-preserved invariant is still fully exercised"
log " against the unchanged canonical source. Deliberate scope narrowing, not a gap.)"
log ""

# ---------------------------------------------------------------------------
# 5. Verify (read-only) — full set + per-runtime subsets, confirm no disk mutation.
# ---------------------------------------------------------------------------
log "## 5. Verify (read-only) — full + subsets"

# tight before/after window around ONE verify call only — must not span any
# other (legitimately mutating) command, or this proves nothing about verify.
PRE_VERIFY_HASH=$(sha256sum "$HOME/.claude/.harness/manifest.json" "$SETTINGS_PATH" 2>/dev/null | sha256sum | cut -d' ' -f1)
set +e
V_ALL_OUT=$(harness verify --json)
V_ALL_CODE=$?
set -e
POST_VERIFY_HASH=$(sha256sum "$HOME/.claude/.harness/manifest.json" "$SETTINGS_PATH" 2>/dev/null | sha256sum | cut -d' ' -f1)
printf '%s' "$V_ALL_OUT" > "$ART/phase34_verify_all.json"

okval=$([ "$PRE_VERIFY_HASH" = "$POST_VERIFY_HASH" ] && echo 0 || echo 1)
chk "verify.read_only" HIGH "manifest.json + settings.json byte-identical immediately before/after this one verify call (verify never mutates disk)" "$okval"

if [ "$V_ALL_CODE" -eq 0 ] || [ "$V_ALL_CODE" -eq 2 ]; then okval=0; else okval=1; fi
chk "verify.exit_in_expected_set" HIGH "harness verify --json exit is 0(all pass) or 2(1+ check failed) — never a crash exit, got $V_ALL_CODE" "$okval"

if [ "$V_ALL_CODE" -eq 0 ]; then
  log "- [PASS] verify.all_checks_pass — every registered check() returned ok=true"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  FAILING=$(python3 -c "
import json
d = json.load(open('$ART/phase34_verify_all.json'))
bad = [c['id'] + ': ' + c['detail'] for c in d['checks'] if not c['ok']]
print('; '.join(bad) if bad else '(none)')
")
  log "- [MEDIUM-FAIL] verify.all_checks_pass — 1+ check() returned ok=false (may reflect this sandbox's CLI/auth state rather than an installer defect): $FAILING"
  FAIL_COUNT=$((FAIL_COUNT + 1))
  FAILED_IDS="$FAILED_IDS verify.all_checks_pass"
fi

set +e
V_CODEX_OUT=$(harness verify codex --json)
V_CODEX_CODE=$?
set -e
printf '%s' "$V_CODEX_OUT" > "$ART/phase34_verify_codex.json"
set +e
python3 "$ASSERT_PY" "$ART/phase34_verify_codex.json" 'len(d["checks"]) > 0 and all(c["id"].startswith("codex.") for c in d["checks"])'
ASSERT_CODE=$?
set -e
chk "verify.codex_subset_only" HIGH "harness verify codex --json returns only codex.* checks (nonempty)" "$ASSERT_CODE"

set +e
V_OPENCODE_OUT=$(harness verify opencode --json)
V_OPENCODE_CODE=$?
set -e
printf '%s' "$V_OPENCODE_OUT" > "$ART/phase34_verify_opencode.json"
set +e
python3 "$ASSERT_PY" "$ART/phase34_verify_opencode.json" 'len(d["checks"]) > 0 and all(c["id"].startswith("opencode.") for c in d["checks"])'
ASSERT_CODE=$?
set -e
chk "verify.opencode_subset_only" HIGH "harness verify opencode --json returns only opencode.* checks (nonempty)" "$ASSERT_CODE"

set +e
STATUS_OUT=$(harness status --json)
STATUS_CODE=$?
set -e
printf '%s' "$STATUS_OUT" > "$ART/phase34_status.json"
okval=$([ "$STATUS_CODE" -eq 0 ] && echo 0 || echo 1)
chk "verify.status_exit0" HIGH "harness status --json — exit=$STATUS_CODE" "$okval"
set +e
python3 "$ASSERT_PY" "$ART/phase34_status.json" 'all("NotImplementedError" not in c.get("detail", "") for c in d["checks"])'
ASSERT_CODE=$?
set -e
chk "verify.status_no_notimplemented" HIGH "no NotImplementedError leaks into status checks[].detail" "$ASSERT_CODE"
log ""

# ---------------------------------------------------------------------------
# 6. Codex / OpenCode driver coverage — single-runtime install --dry-run.
# ---------------------------------------------------------------------------
log "## 6. Codex / OpenCode driver coverage (install --dry-run)"

set +e
CODEX_DRY_OUT=$(harness install codex --dry-run --json)
CODEX_DRY_CODE=$?
set -e
printf '%s' "$CODEX_DRY_OUT" > "$ART/phase6_codex_install_dryrun.json"
okval=$([ "$CODEX_DRY_CODE" -eq 0 ] && echo 0 || echo 1)
chk "driver.codex_install_dryrun.exit0" HIGH "harness install codex --dry-run --json — exit=$CODEX_DRY_CODE" "$okval"

set +e
OPENCODE_DRY_OUT=$(harness install opencode --dry-run --json)
OPENCODE_DRY_CODE=$?
set -e
printf '%s' "$OPENCODE_DRY_OUT" > "$ART/phase6_opencode_install_dryrun.json"
okval=$([ "$OPENCODE_DRY_CODE" -eq 0 ] && echo 0 || echo 1)
chk "driver.opencode_install_dryrun.exit0" HIGH "harness install opencode --dry-run --json — exit=$OPENCODE_DRY_CODE" "$okval"
log ""

# ---------------------------------------------------------------------------
# 6b. CLI-absent SKIP behaviour — simulate via a PATH stripped of the
#     user-local bin dirs where codex/opencode/claude actually live on this
#     box (all three CLIs happen to be installed here, so this is the only
#     way to exercise the "CLI absent -> SKIP, not a crash" branches).
# ---------------------------------------------------------------------------
log "## 6b. CLI-absent SKIP simulation (codex plugin-wrap, bootstrap-smoke x3)"

PY3_DIR=$(dirname "$(command -v python3)")
SAFE_PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
case ":$SAFE_PATH:" in
  *":$PY3_DIR:"*) : ;;
  *) SAFE_PATH="$PY3_DIR:$SAFE_PATH" ;;
esac

set +e
CLI_ABSENT_OUT=$(PATH="$SAFE_PATH" python3 -c "
import sys, json
sys.path.insert(0, '$REAL_REPO/tools/install')
from drivers import claude as claude_driver
from drivers import codex as codex_driver
from drivers import opencode as opencode_driver

result = {}
result['codex_plugin_cli_absent'] = codex_driver._plugin_action(dry_run=False)
result['codex_bootstrap_smoke_cli_absent'] = codex_driver.checks(scope='global')[-1]()
result['opencode_bootstrap_smoke_cli_absent'] = opencode_driver.checks(scope='global')[-1]()
result['claude_bootstrap_smoke_cli_absent'] = claude_driver.checks(scope='global')[-1]()
print(json.dumps(result))
" 2>&1)
CLI_ABSENT_CODE=$?
set -e
printf '%s' "$CLI_ABSENT_OUT" > "$ART/phase6b_cli_absent.json"
okval=$([ "$CLI_ABSENT_CODE" -eq 0 ] && echo 0 || echo 1)
chk "driver.cli_absent_probe_ran" HIGH "PATH-stripped probe ran (exit=$CLI_ABSENT_CODE); PATH used: $SAFE_PATH" "$okval"

if [ "$CLI_ABSENT_CODE" -eq 0 ]; then
  set +e
  python3 "$ASSERT_PY" "$ART/phase6b_cli_absent.json" 'd["codex_plugin_cli_absent"]["status"] == "skipped" and "codex CLI" in d["codex_plugin_cli_absent"]["detail"]'
  ASSERT_CODE=$?
  set -e
  chk "driver.codex_plugin_skip_on_cli_absent" HIGH "codex plugin-wrap SKIPs (no subprocess call) when codex CLI unresolvable via PATH" "$ASSERT_CODE"

  set +e
  python3 "$ASSERT_PY" "$ART/phase6b_cli_absent.json" 'd["codex_bootstrap_smoke_cli_absent"]["ok"] is True and "SKIP" in d["codex_bootstrap_smoke_cli_absent"]["detail"]'
  ASSERT_CODE=$?
  set -e
  chk "driver.codex_bootstrap_smoke_skip" HIGH "codex.bootstrap-smoke reports ok=true SKIP when codex CLI absent" "$ASSERT_CODE"

  set +e
  python3 "$ASSERT_PY" "$ART/phase6b_cli_absent.json" 'd["opencode_bootstrap_smoke_cli_absent"]["ok"] is True and "SKIP" in d["opencode_bootstrap_smoke_cli_absent"]["detail"]'
  ASSERT_CODE=$?
  set -e
  chk "driver.opencode_bootstrap_smoke_skip" HIGH "opencode.bootstrap-smoke reports ok=true SKIP when opencode CLI absent" "$ASSERT_CODE"

  set +e
  python3 "$ASSERT_PY" "$ART/phase6b_cli_absent.json" 'd["claude_bootstrap_smoke_cli_absent"]["ok"] is True and "SKIP" in d["claude_bootstrap_smoke_cli_absent"]["detail"]'
  ASSERT_CODE=$?
  set -e
  chk "driver.claude_bootstrap_smoke_skip" MEDIUM "claude.bootstrap-smoke reports ok=true SKIP when claude CLI absent" "$ASSERT_CODE"
else
  log "- [HIGH-FAIL] driver.codex_plugin_skip_on_cli_absent — probe crashed, see phase6b_cli_absent.json"
  FAIL_COUNT=$((FAIL_COUNT + 3))
  FAILED_IDS="$FAILED_IDS driver.codex_plugin_skip_on_cli_absent(probe-crash) driver.codex_bootstrap_smoke_skip(probe-crash) driver.opencode_bootstrap_smoke_skip(probe-crash)"
fi
log ""

# ---------------------------------------------------------------------------
# 7. Full lifecycle continuation — idempotent reinstall, clean update, uninstall.
# ---------------------------------------------------------------------------
log "## 7. Full lifecycle — idempotent reinstall / clean update / uninstall"

set +e
P5_DRYALL_OUT=$(harness install all --dry-run --json)
P5_DRYALL_CODE=$?
set -e
printf '%s' "$P5_DRYALL_OUT" > "$ART/phase5_install_all_dryrun.json"
okval=$([ "$P5_DRYALL_CODE" -eq 0 ] && echo 0 || echo 1)
chk "lifecycle.install_all_dryrun.exit0" HIGH "harness install all --dry-run --json — exit=$P5_DRYALL_CODE" "$okval"

set +e
P5_REINSTALL_OUT=$(harness install claude --json)
P5_REINSTALL_CODE=$?
set -e
printf '%s' "$P5_REINSTALL_OUT" > "$ART/phase5_reinstall_claude.json"
okval=$([ "$P5_REINSTALL_CODE" -eq 0 ] && echo 0 || echo 1)
chk "lifecycle.idempotent_reinstall.exit0" HIGH "harness install claude --json (second run, all-unchanged expected) — exit=$P5_REINSTALL_CODE" "$okval"
set +e
python3 "$ASSERT_PY" "$ART/phase5_reinstall_claude.json" 'all(c["ok"] for c in d["checks"] if c["id"].startswith("claude."))'
ASSERT_CODE=$?
set -e
chk "lifecycle.idempotent_reinstall.no_blocked" HIGH "no blocked actions on idempotent re-install" "$ASSERT_CODE"

set +e
P5_UPDATE_OUT=$(harness update --json)
P5_UPDATE_CODE=$?
set -e
printf '%s' "$P5_UPDATE_OUT" > "$ART/phase5_update_clean.json"
okval=$([ "$P5_UPDATE_CODE" -eq 0 ] && echo 0 || echo 1)
chk "lifecycle.update_clean_after_reapply.exit0" HIGH "update after the earlier reapply resolved drift — expect exit=0, got $P5_UPDATE_CODE" "$okval"

set +e
P5_UNINSTALL_DRY_OUT=$(harness uninstall claude --dry-run --json)
P5_UNINSTALL_DRY_CODE=$?
set -e
printf '%s' "$P5_UNINSTALL_DRY_OUT" > "$ART/phase5_uninstall_dryrun.json"
okval=$([ "$P5_UNINSTALL_DRY_CODE" -eq 0 ] && echo 0 || echo 1)
chk "lifecycle.uninstall_dryrun.exit0" HIGH "harness uninstall claude --dry-run --json — exit=$P5_UNINSTALL_DRY_CODE" "$okval"

PROBE_FILE="$HOME/.claude/PROBE_NOT_IN_MANIFEST.txt"
printf 'probe — not tracked by any manifest entry\n' > "$PROBE_FILE"

set +e
P5_UNINSTALL_OUT=$(harness uninstall claude --json)
P5_UNINSTALL_CODE=$?
set -e
printf '%s' "$P5_UNINSTALL_OUT" > "$ART/phase5_uninstall.json"
okval=$([ "$P5_UNINSTALL_CODE" -eq 0 ] && echo 0 || echo 1)
chk "lifecycle.uninstall.exit0" HIGH "harness uninstall claude --json — exit=$P5_UNINSTALL_CODE" "$okval"

if [ -f "$HOME/.claude/.harness/manifest.json" ]; then okval=1; else okval=0; fi
chk "lifecycle.manifest_removed" HIGH "manifest.json removed after uninstall" "$okval"

if [ -L "$HOME/.claude/core" ] || [ -L "$HOME/.claude/skills" ]; then okval=1; else okval=0; fi
chk "lifecycle.symlinks_removed" HIGH "manifest-scoped projection symlinks (core, skills) removed after uninstall" "$okval"

if [ -f "$PROBE_FILE" ]; then okval=0; else okval=1; fi
chk "lifecycle.non_manifest_file_preserved" HIGH "file never enumerated by the manifest survives uninstall untouched" "$okval"
log ""

# ---------------------------------------------------------------------------
# 8. mem import + PATH launchers + collision guard (Phase 6, PRD P0.5).
# ---------------------------------------------------------------------------
log "## 8. mem import + ~/.local/bin launchers + PATH-collision guard"

printf '{"id":"t1","type":"note","body":"probe","tags":[],"links":[]}\n' > "$MEM_STORE/dump.jsonl"

set +e
P6_INSTALL_OUT=$(harness install claude --json)
P6_INSTALL_CODE=$?
set -e
printf '%s' "$P6_INSTALL_OUT" > "$ART/phase8_install_claude.json"
okval=$([ "$P6_INSTALL_CODE" -eq 0 ] && echo 0 || echo 1)
chk "bootstrap.reinstall_after_uninstall.exit0" HIGH "fresh install claude --json (post-uninstall) — exit=$P6_INSTALL_CODE" "$okval"

if [ -f "$MEM_STORE/memory.db" ]; then okval=0; else okval=1; fi
chk "bootstrap.memory_db_created" HIGH "\$MEM_STORE/memory.db created from dump.jsonl on install" "$okval"

if [ -L "$HOME/.local/bin/harness" ] && [ -L "$HOME/.local/bin/fleet" ]; then okval=0; else okval=1; fi
chk "bootstrap.launchers_created" HIGH "\$HOME/.local/bin/{harness,fleet} symlinks created (temp HOME)" "$okval"

COLLISION_HOME="$HOME/collision-test-home"
mkdir -p "$COLLISION_HOME/.local/bin"
printf '#!/bin/sh\necho foreign-harness\n' > "$COLLISION_HOME/.local/bin/harness"
chmod +x "$COLLISION_HOME/.local/bin/harness"

set +e
COLLISION_OUT=$(python3 -c "
import sys, json
sys.path.insert(0, '$REAL_REPO/tools/install')
import bootstrap
from pathlib import Path
results = bootstrap.install_launchers(home=Path('$COLLISION_HOME'), dry_run=False)
print(json.dumps(results))
" 2>&1)
COLLISION_CODE=$?
set -e
printf '%s' "$COLLISION_OUT" > "$ART/phase8_collision.json"
okval=$([ "$COLLISION_CODE" -eq 0 ] && echo 0 || echo 1)
chk "bootstrap.collision_probe_ran" HIGH "install_launchers() probe against pre-seeded foreign 'harness' file ran (exit=$COLLISION_CODE)" "$okval"

if [ "$COLLISION_CODE" -eq 0 ]; then
  set +e
  python3 "$ASSERT_PY" "$ART/phase8_collision.json" 'any(r["name"] == "harness" and r["status"] == "skipped-collision" for r in d)'
  ASSERT_CODE=$?
  set -e
  chk "bootstrap.collision_guard_skips_foreign" HIGH "pre-existing non-symlink 'harness' left alone (status=skipped-collision)" "$ASSERT_CODE"

  set +e
  python3 "$ASSERT_PY" "$ART/phase8_collision.json" 'any(r["name"] == "fleet" and r["status"] == "created" for r in d)'
  ASSERT_CODE=$?
  set -e
  chk "bootstrap.fleet_created_despite_collision" MEDIUM "unrelated 'fleet' launcher still created despite the 'harness' collision" "$ASSERT_CODE"
fi

EXPECT_FOREIGN_CONTENT="$(printf '#!/bin/sh\necho foreign-harness\n')"
ACTUAL_FOREIGN_CONTENT="$(cat "$COLLISION_HOME/.local/bin/harness")"
if [ "$ACTUAL_FOREIGN_CONTENT" = "$EXPECT_FOREIGN_CONTENT" ]; then okval=0; else okval=1; fi
chk "bootstrap.collision_file_content_untouched" HIGH "foreign harness file bytes unmodified after collision-guard skip" "$okval"
log ""

# ---------------------------------------------------------------------------
# 9. Phase 7 — plugin channel dry-run wrapping (codex in-cycle, claude deferred).
# ---------------------------------------------------------------------------
log "## 9. Plugin channel dry-run (Phase 7 boundary)"

set +e
P7_CODEX_OUT=$(harness install codex --plugin --dry-run --json)
P7_CODEX_CODE=$?
set -e
printf '%s' "$P7_CODEX_OUT" > "$ART/phase9_codex_plugin_dryrun.json"
okval=$([ "$P7_CODEX_CODE" -eq 0 ] && echo 0 || echo 1)
chk "plugin.codex_dryrun.exit0" HIGH "harness install codex --plugin --dry-run --json — exit=$P7_CODEX_CODE" "$okval"

set +e
python3 "$ASSERT_PY" "$ART/phase9_codex_plugin_dryrun.json" 'any(c["id"] == "codex.plugin.x" and "marketplace add" in c["detail"] and "plugin add" in c["detail"] for c in d["checks"])'
ASSERT_CODE=$?
set -e
chk "plugin.codex_cmds_planned" HIGH "planned 'codex plugin marketplace add' + 'codex plugin add' commands present in checks[]" "$ASSERT_CODE"

set +e
P7_CLAUDE_OUT=$(harness install claude --plugin --dry-run --json)
P7_CLAUDE_CODE=$?
set -e
printf '%s' "$P7_CLAUDE_OUT" > "$ART/phase9_claude_plugin_dryrun.json"
okval=$([ "$P7_CLAUDE_CODE" -eq 0 ] && echo 0 || echo 1)
chk "plugin.claude_dryrun.exit0" HIGH "harness install claude --plugin --dry-run --json — exit=$P7_CLAUDE_CODE" "$okval"

set +e
python3 "$ASSERT_PY" "$ART/phase9_claude_plugin_dryrun.json" 'any(c["id"] == "claude.plugin.x" and "deferred" in c["detail"] for c in d["checks"])'
ASSERT_CODE=$?
set -e
chk "plugin.claude_deferred_skip" HIGH "claude plugin channel reports deferred SKIP message (Phase 7 boundary — Claude plugin content generator out of cycle-1 scope)" "$ASSERT_CODE"
log ""

log "## Done — all phases executed, see Summary above for pass/fail tally."
