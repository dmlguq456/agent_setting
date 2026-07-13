#!/bin/sh
# t0_t6_spec_pipeline_rebase.sh — code-test Phase 4 (T0~T6) for harness-installer
# cycle 3 (spec-pipeline trio ${CLAUDE_PLUGIN_DATA} rebasing).
#
# Hard isolation contract (cycle 1 INCIDENT_real_home_touched.md direct response,
# inherited from cycle 2 test_scripts/*.sh precedent, plan.md Phase 4 preamble):
#   - ONE `sh` process, ONE Bash tool invocation. HOME/AGENT_HOME/CLAUDE_CONFIG_DIR
#     are exported at the very top of THIS file and never carried across a tool-
#     call boundary.
#   - real-home file hashes are captured BEFORE HOME is reassigned, re-checked in
#     an EXIT trap.
#   - any real `claude` CLI invocation (none needed here — T6 uses
#     `harness verify claude --json`, which shells out to `claude plugin ...`
#     only for the plugin-registered check, itself unaffected by our target
#     check `claude.sync-native-plugin`) still gets a mktemp CLAUDE_CONFIG_DIR
#     defensively, matching contract clause 4.
#   - hook firing is reproduced WITHOUT a real plugin install: stdin JSON is
#     piped directly to the canonical hook scripts (materialized under the
#     generated plugin tree) with an explicit `AGENT_HOME=<mktemp>` env-prefix,
#     exactly the shape hooks.json now emits.
set -eu

REAL_REPO="/home/Uihyeop/agent_setting-wt/harness-installer-hooks"
PLAN_DIR="$REAL_REPO/.agent_reports/plans/2026-07-13_harness-installer-hooks"
LOGDIR="$PLAN_DIR/test_logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/t0_t6_spec_pipeline_rebase.md"
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
    echo "# code-test — T0~T6 spec-pipeline DATA-rebase (Phase 4) result"
    echo
    if [ "$GUARD_OK" = "1" ]; then
      echo "## [CRITICAL] real-home determinism guard FAILED"
      echo
      echo "STOP — a real runtime-home file changed during this run."
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
# Isolated env — single-shell export.
# ---------------------------------------------------------------------------
export HOME
HOME="$(mktemp -d)"
export AGENT_HOME="$REAL_REPO"
export CLAUDE_CONFIG_DIR
CLAUDE_CONFIG_DIR="$(mktemp -d)"

log "## Isolated env"
log "- HOME(temp)=$HOME"
log "- AGENT_HOME=$AGENT_HOME"
log "- CLAUDE_CONFIG_DIR(temp)=$CLAUDE_CONFIG_DIR"
log ""

GEN="$REAL_REPO/adapters/claude/bin/sync-native-plugin.py"
PLUGIN_ROOT="$REAL_REPO/adapters/claude/plugin-marketplace/plugins/agent-harness-claude"
HOOKS_DIR="$PLUGIN_ROOT/hooks"

cd "$REAL_REPO"
BASELINE_STATUS=$(git status --porcelain)
log "## 0. Pre-condition — git status baseline"
log '```'
log "$BASELINE_STATUS"
log '```'
log ""

# ===========================================================================
# T0 — static / generator basics.
# ===========================================================================
log "## T0 — static / generator basics"

set +e
SYN_OUT=$(python3 -m py_compile "$GEN" 2>&1)
SYN_CODE=$?
set -e
okval=$([ "$SYN_CODE" -eq 0 ] && echo 0 || echo 1)
chk "T0.py_compile" HIGH "py_compile sync-native-plugin.py — exit=$SYN_CODE" "$okval"

set +e
CHECK1_OUT=$(python3 "$GEN" --check 2>&1)
CHECK1_CODE=$?
set -e
okval=$([ "$CHECK1_CODE" -eq 0 ] && echo 0 || echo 1)
chk "T0.check_clean_exit0" HIGH "--check on already-generated tree — exit=$CHECK1_CODE (expect 0)" "$okval"

# mutate a generated file's content -> --check must go dirty (exit 1).
# (check() byte-compares content, not mtime — a bare `touch` alone is a no-op
# for staleness detection, so this appends a byte to actually dirty the file.)
TOUCHED="$HOOKS_DIR/hooks.json"
printf '\n' >> "$TOUCHED"
set +e
CHECK2_OUT=$(python3 "$GEN" --check 2>&1)
CHECK2_CODE=$?
set -e
okval=$([ "$CHECK2_CODE" -eq 1 ] && echo 0 || echo 1)
chk "T0.check_dirty_after_content_mutation" HIGH "--check exit=$CHECK2_CODE after appending a byte to hooks.json (expect 1)" "$okval"

set +e
SYNC_REGEN_OUT=$(python3 "$GEN" 2>&1)
SYNC_REGEN_CODE=$?
CHECK3_OUT=$(python3 "$GEN" --check 2>&1)
CHECK3_CODE=$?
set -e
okval=$([ "$SYNC_REGEN_CODE" -eq 0 ] && [ "$CHECK3_CODE" -eq 0 ] && echo 0 || echo 1)
chk "T0.regen_restores_clean" HIGH "sync() regen (exit=$SYNC_REGEN_CODE) then --check exit=$CHECK3_CODE (expect 0/0)" "$okval"

AFTER_REGEN_STATUS=$(git status --porcelain)
okval=$([ "$AFTER_REGEN_STATUS" = "$BASELINE_STATUS" ] && echo 0 || echo 1)
chk "T0.idempotent_round_trip_no_diff" HIGH "git status --porcelain identical to baseline after touch+regen round-trip" "$okval"

HJ_TEXT=$(cat "$HOOKS_DIR/hooks.json")
PRE_COUNT=$(python3 -c "import json;print(len(json.loads(open('$HOOKS_DIR/hooks.json').read())['hooks']['PreToolUse']))")
POST_COUNT=$(python3 -c "import json;print(len(json.loads(open('$HOOKS_DIR/hooks.json').read())['hooks']['PostToolUse']))")
okval=$([ "$PRE_COUNT" = "3" ] && [ "$POST_COUNT" = "2" ] && echo 0 || echo 1)
chk "T0.hooks_json_event_counts" HIGH "PreToolUse=$PRE_COUNT (expect 3) / PostToolUse=$POST_COUNT (expect 2)" "$okval"

STRUCT_OUT=$(python3 - "$HOOKS_DIR/hooks.json" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
pre = {h["matcher"]: h["hooks"][0]["command"] for h in d["hooks"]["PreToolUse"]}
post = {h["matcher"]: h["hooks"][0]["command"] for h in d["hooks"]["PostToolUse"]}
ok = True
# existing two — no AGENT_HOME prefix, unchanged shape (regression).
if pre.get("Edit|Write|MultiEdit|NotebookEdit") != 'sh "${CLAUDE_PLUGIN_ROOT}/hooks/git-state-guard.sh"':
    ok = False; print("git-state-guard command mismatch:", pre.get("Edit|Write|MultiEdit|NotebookEdit"))
if pre.get("Edit|Write|MultiEdit") != 'bash "${CLAUDE_PLUGIN_ROOT}/hooks/artifact-guard.sh"':
    ok = False; print("artifact-guard command mismatch:", pre.get("Edit|Write|MultiEdit"))
# spec trio — DATA env-prefix + PLUGIN_ROOT path both present, literal.
gate_cmd = pre.get("Skill", "")
if 'AGENT_HOME="${CLAUDE_PLUGIN_DATA}"' not in gate_cmd or '${CLAUDE_PLUGIN_ROOT}/hooks/spec-skill-gate.sh' not in gate_cmd:
    ok = False; print("spec-skill-gate command missing DATA-prefix or PLUGIN_ROOT path:", gate_cmd)
marker_cmd = post.get("Read", "")
if 'AGENT_HOME="${CLAUDE_PLUGIN_DATA}"' not in marker_cmd or '${CLAUDE_PLUGIN_ROOT}/hooks/spec-read-marker.sh' not in marker_cmd:
    ok = False; print("spec-read-marker command missing DATA-prefix or PLUGIN_ROOT path:", marker_cmd)
nudge_cmd = post.get("Edit|Write|MultiEdit", "")
if 'AGENT_HOME="${CLAUDE_PLUGIN_DATA}"' not in nudge_cmd or '${CLAUDE_PLUGIN_ROOT}/hooks/spec-sync-nudge.sh' not in nudge_cmd:
    ok = False; print("spec-sync-nudge command missing DATA-prefix or PLUGIN_ROOT path:", nudge_cmd)
print("OK" if ok else "MISMATCH")
sys.exit(0 if ok else 1)
PYEOF
)
STRUCT_CODE=$?
log '```'
log "$STRUCT_OUT"
log '```'
okval=$([ "$STRUCT_CODE" -eq 0 ] && echo 0 || echo 1)
chk "T0.hooks_json_command_shape" HIGH "existing 2 hooks unprefixed (regression-free) + spec 3 hooks carry DATA-prefix + PLUGIN_ROOT path" "$okval"

okval=$([ -x "$PLUGIN_ROOT/utilities/agent-home.sh" ] && echo 0 || echo 1)
chk "T0.utilities_bundle_exec" HIGH "utilities/agent-home.sh exists + exec bit" "$okval"

SH_COUNT=$(find "$HOOKS_DIR" -maxdepth 1 -name '*.sh' | wc -l | tr -d ' ')
NON_EXEC=$(find "$HOOKS_DIR" -maxdepth 1 -name '*.sh' ! -perm -u+x | wc -l | tr -d ' ')
okval=$([ "$SH_COUNT" = "5" ] && [ "$NON_EXEC" = "0" ] && echo 0 || echo 1)
chk "T0.hooks_dir_five_sh_exec" HIGH "hooks/ has $SH_COUNT .sh files (expect 5), $NON_EXEC missing exec bit (expect 0)" "$okval"

log ""

# ===========================================================================
# Fixture used by T1/T2 — a spec-backed cwd with .agent_reports/spec/prd.md.
# ===========================================================================
FIXTURE=$(mktemp -d)
mkdir -p "$FIXTURE/.agent_reports/spec"
printf '# PRD fixture\ncontent line\n' > "$FIXTURE/.agent_reports/spec/prd.md"
FIXTURE_KEY=$(printf '%s' "$FIXTURE" | sed 's#[/ ]#_#g')

read_marker_json() {
  # $1 = session id
  printf '{"session_id":"%s","file_path":"%s/.agent_reports/spec/prd.md","hook_event_name":"PostToolUse"}' \
    "$1" "$FIXTURE"
}
gate_json() {
  # $1 = session id, $2 = skill
  printf '{"session_id":"%s","skill":"%s","hook_event_name":"PreToolUse"}' "$1" "$2"
}

log "## Fixture"
log "- FIXTURE=$FIXTURE"
log "- FIXTURE_KEY=$FIXTURE_KEY"
log ""

# ===========================================================================
# T1 — marker rebasing (single AGENT_HOME=<mktemp>).
# ===========================================================================
log "## T1 — marker rebasing"

DATA1=$(mktemp -d)
S1="t1sess"
MARKER1="$DATA1/.spec-grounding/${S1}__${FIXTURE_KEY}"

read_marker_json "$S1" | AGENT_HOME="$DATA1" sh "$HOOKS_DIR/spec-read-marker.sh"
okval=$([ -f "$MARKER1" ] && echo 0 || echo 1)
chk "T1.marker_created_under_mktemp_data" HIGH "marker at \$DATA/.spec-grounding/... exists" "$okval"

okval=$([ ! -d "$HOME/.spec-grounding" ] && echo 0 || echo 1)
chk "T1.no_marker_under_temp_home" HIGH "no .spec-grounding leaked into the script's own \$HOME" "$okval"

set +e
GATE1_OUT=$(cd "$FIXTURE" && gate_json "$S1" "autopilot-code" | AGENT_HOME="$DATA1" sh "$HOOKS_DIR/spec-skill-gate.sh" 2>&1)
GATE1_CODE=$?
set -e
okval=$([ "$GATE1_CODE" -eq 0 ] && [ -z "$GATE1_OUT" ] && echo 0 || echo 1)
chk "T1.gate_passes_with_marker" HIGH "gate exit=$GATE1_CODE, stdout empty (no deny) when marker present" "$okval"

rm -f "$MARKER1"
set +e
GATE2_OUT=$(cd "$FIXTURE" && gate_json "$S1" "autopilot-code" | AGENT_HOME="$DATA1" sh "$HOOKS_DIR/spec-skill-gate.sh" 2>&1)
GATE2_CODE=$?
set -e
okval=$(echo "$GATE2_OUT" | grep -q '"permissionDecision":"deny"' && echo 0 || echo 1)
chk "T1.gate_denies_without_marker" HIGH "gate emits deny JSON when marker absent (out: $(printf '%s' "$GATE2_OUT" | head -c 160))" "$okval"

# recreate marker, then bump prd.md mtime forward -> reverse-drift deny.
read_marker_json "$S1" | AGENT_HOME="$DATA1" sh "$HOOKS_DIR/spec-read-marker.sh"
touch -d '+2 minutes' "$FIXTURE/.agent_reports/spec/prd.md"
set +e
GATE3_OUT=$(cd "$FIXTURE" && gate_json "$S1" "autopilot-code" | AGENT_HOME="$DATA1" sh "$HOOKS_DIR/spec-skill-gate.sh" 2>&1)
GATE3_CODE=$?
set -e
okval=$(echo "$GATE3_OUT" | grep -q '"permissionDecision":"deny"' && echo 0 || echo 1)
chk "T1.gate_denies_on_reverse_drift" HIGH "gate emits deny JSON after prd.md mtime advances past marker (out: $(printf '%s' "$GATE3_OUT" | head -c 160))" "$okval"

log ""

# ===========================================================================
# T2 — dual-firing safety ($A settings.json-shaped vs $B plugin-DATA-shaped).
# ===========================================================================
log "## T2 — dual-firing safety"

# fresh marker state for T2 (re-read once so both gates have a starting pass).
A=$(mktemp -d)
B=$(mktemp -d)
S2="t2sess"

read_marker_json "$S2" | AGENT_HOME="$A" sh "$HOOKS_DIR/spec-read-marker.sh"
read_marker_json "$S2" | AGENT_HOME="$B" sh "$HOOKS_DIR/spec-read-marker.sh"

MARKER_A="$A/.spec-grounding/${S2}__${FIXTURE_KEY}"
MARKER_B="$B/.spec-grounding/${S2}__${FIXTURE_KEY}"
okval=$([ -f "$MARKER_A" ] && [ -f "$MARKER_B" ] && echo 0 || echo 1)
chk "T2.markers_created_in_own_dirs" HIGH "marker present under both \$A and \$B independently" "$okval"

# cross-contamination: neither dir should contain the other's tree/session key mixed in
# (structurally guaranteed by separate AGENT_HOME roots, asserted explicitly here).
A_COUNT=$(find "$A/.spec-grounding" -type f | wc -l | tr -d ' ')
B_COUNT=$(find "$B/.spec-grounding" -type f | wc -l | tr -d ' ')
okval=$([ "$A_COUNT" = "1" ] && [ "$B_COUNT" = "1" ] && echo 0 || echo 1)
chk "T2.no_cross_contamination" HIGH "\$A/.spec-grounding has $A_COUNT file(s), \$B/.spec-grounding has $B_COUNT file(s) (expect 1/1, no leakage)" "$okval"

set +e
GATE_A1=$(cd "$FIXTURE" && gate_json "$S2" "autopilot-code" | AGENT_HOME="$A" sh "$HOOKS_DIR/spec-skill-gate.sh" 2>&1); GATE_A1_CODE=$?
GATE_B1=$(cd "$FIXTURE" && gate_json "$S2" "autopilot-code" | AGENT_HOME="$B" sh "$HOOKS_DIR/spec-skill-gate.sh" 2>&1); GATE_B1_CODE=$?
set -e
okval=$([ "$GATE_A1_CODE" -eq 0 ] && [ -z "$GATE_A1" ] && [ "$GATE_B1_CODE" -eq 0 ] && [ -z "$GATE_B1" ] && echo 0 || echo 1)
chk "T2.both_gates_pass_with_own_marker" HIGH "gate(\$A) and gate(\$B) both pass on first firing" "$okval"

# idempotency: run each gate a second time -> still passes, no new marker files written.
set +e
GATE_A2=$(cd "$FIXTURE" && gate_json "$S2" "autopilot-code" | AGENT_HOME="$A" sh "$HOOKS_DIR/spec-skill-gate.sh" 2>&1); GATE_A2_CODE=$?
GATE_B2=$(cd "$FIXTURE" && gate_json "$S2" "autopilot-code" | AGENT_HOME="$B" sh "$HOOKS_DIR/spec-skill-gate.sh" 2>&1); GATE_B2_CODE=$?
set -e
A_COUNT2=$(find "$A/.spec-grounding" -type f | wc -l | tr -d ' ')
B_COUNT2=$(find "$B/.spec-grounding" -type f | wc -l | tr -d ' ')
okval=$([ "$GATE_A2_CODE" -eq 0 ] && [ -z "$GATE_A2" ] && [ "$GATE_B2_CODE" -eq 0 ] && [ -z "$GATE_B2" ] \
  && [ "$A_COUNT2" = "1" ] && [ "$B_COUNT2" = "1" ] && echo 0 || echo 1)
chk "T2.gate_idempotent_side_effect_zero" HIGH "2nd firing of both gates still passes, marker file counts unchanged (\$A=$A_COUNT2 \$B=$B_COUNT2)" "$okval"

# asymmetric case: delete $B's marker only -> $A still passes, $B denies (deny-wins fail-safe).
rm -f "$MARKER_B"
set +e
GATE_A3=$(cd "$FIXTURE" && gate_json "$S2" "autopilot-code" | AGENT_HOME="$A" sh "$HOOKS_DIR/spec-skill-gate.sh" 2>&1); GATE_A3_CODE=$?
GATE_B3=$(cd "$FIXTURE" && gate_json "$S2" "autopilot-code" | AGENT_HOME="$B" sh "$HOOKS_DIR/spec-skill-gate.sh" 2>&1); GATE_B3_CODE=$?
set -e
okval=$([ "$GATE_A3_CODE" -eq 0 ] && [ -z "$GATE_A3" ] && echo "$GATE_B3" | grep -q '"permissionDecision":"deny"' && echo 0 || echo 1)
chk "T2.asymmetric_deny_wins_failsafe" HIGH "\$B marker removed -> \$A still passes, \$B denies (conservative re-Read forced, no side effect since gate is read-only)" "$okval"

log ""

# ===========================================================================
# T3 — fail-open / non-plugin regression.
# ===========================================================================
log "## T3 — fail-open / non-plugin regression"

S3A="t3a"
set +e
FAILOPEN1_OUT=$(read_marker_json "$S3A" | env -u AGENT_HOME sh "$HOOKS_DIR/spec-read-marker.sh" 2>&1)
FAILOPEN1_CODE=$?
set -e
FALLBACK_MARKER1="$HOME/.claude/.spec-grounding/${S3A}__${FIXTURE_KEY}"
okval=$([ "$FAILOPEN1_CODE" -eq 0 ] && [ -f "$FALLBACK_MARKER1" ] && echo 0 || echo 1)
chk "T3.unset_agent_home_falls_back_no_crash" HIGH "AGENT_HOME unset -> agent-home.sh fallback resolves (\$HOME/.claude, no \$HOME/agent_setting present), marker written there, exit=$FAILOPEN1_CODE, no crash" "$okval"

S3B="t3b"
set +e
FAILOPEN2_OUT=$(read_marker_json "$S3B" | AGENT_HOME= sh "$HOOKS_DIR/spec-read-marker.sh" 2>&1)
FAILOPEN2_CODE=$?
set -e
FALLBACK_MARKER2="$HOME/.claude/.spec-grounding/${S3B}__${FIXTURE_KEY}"
okval=$([ "$FAILOPEN2_CODE" -eq 0 ] && [ -f "$FALLBACK_MARKER2" ] && echo 0 || echo 1)
chk "T3.empty_agent_home_degrades_no_crash" HIGH "AGENT_HOME=\"\" (empty) -> ':-' fallback still resolves (not just unset), no crash, exit=$FAILOPEN2_CODE" "$okval"

CANON_DIFF=$(git diff --stat -- hooks/)
okval=$([ -z "$CANON_DIFF" ] && echo 0 || echo 1)
chk "T3.canonical_hooks_unmodified" HIGH "git diff --stat -- hooks/ empty (canonical hook bodies untouched, invariant)" "$okval"

log ""

# ===========================================================================
# T4 — self-contained (no PLUGIN_ROOT escape).
# ===========================================================================
log "## T4 — self-contained path confinement"

HJ_ESCAPE=$(grep -o '\.\./[^"]*' "$HOOKS_DIR/hooks.json" || true)
okval=$([ -z "$HJ_ESCAPE" ] && echo 0 || echo 1)
chk "T4.hooks_json_no_relative_escape" HIGH "hooks.json command strings contain no '../' (all \${CLAUDE_PLUGIN_ROOT}/\${CLAUDE_PLUGIN_DATA}-relative)" "$okval"

# the only '../' path-escape reference in the DATA-rebased spec trio must be
# '../utilities/agent-home.sh', resolving to a path INSIDE PLUGIN_ROOT (not
# outside the plugin tree). Scoped to the 3 spec hooks only — git-state-guard.sh/
# artifact-guard.sh are pre-existing (cycle 2), out of this cycle's scope, and
# artifact-guard.sh has an unrelated "..." prose comment
# (".../.agent_reports/...") that false-matches a naive '\.\./' grep.
BODY_ESCAPES=$(grep -rho '\.\./[A-Za-z0-9_./-]*' \
  "$HOOKS_DIR/spec-skill-gate.sh" "$HOOKS_DIR/spec-read-marker.sh" "$HOOKS_DIR/spec-sync-nudge.sh" | sort -u)
BAD_ESCAPES=$(printf '%s\n' "$BODY_ESCAPES" | grep -v '^\.\./utilities/agent-home\.sh$' || true)
okval=$([ -z "$BAD_ESCAPES" ] && echo 0 || echo 1)
chk "T4.hook_bodies_only_utilities_escape" HIGH "spec trio bodies reference only '../utilities/agent-home.sh' (found: $(printf '%s' "$BODY_ESCAPES" | tr '\n' ' '))" "$okval"

RESOLVED_UTIL=$(readlink -f "$HOOKS_DIR/../utilities" 2>/dev/null || true)
EXPECTED_UTIL=$(readlink -f "$PLUGIN_ROOT/utilities" 2>/dev/null || true)
okval=$([ -n "$RESOLVED_UTIL" ] && [ "$RESOLVED_UTIL" = "$EXPECTED_UTIL" ] && echo 0 || echo 1)
chk "T4.utilities_relpath_stays_inside_plugin_root" HIGH "hooks/../utilities resolves to $RESOLVED_UTIL == PLUGIN_ROOT/utilities ($EXPECTED_UTIL) — no escape outside PLUGIN_ROOT" "$okval"

log ""

# ===========================================================================
# T5 — real-home determinism (asserted structurally here; authoritative check
# is the EXIT trap above, which covers the whole script including T0-T4/T6).
# ===========================================================================
log "## T5 — real-home determinism guard"
log "- structural: see trap-based guard in the report header (whole-script coverage)."
chk "T5.guard_scaffolding_present" HIGH "sha256 baseline captured pre-HOME-reassignment + EXIT trap re-check wired (see report header)" "0"
log ""

# ===========================================================================
# T6 — integration smoke.
# ===========================================================================
log "## T6 — integration smoke"

set +e
MANIFEST_OUT=$(python3 "$REAL_REPO/tools/build-manifest.py" --check 2>&1)
MANIFEST_CODE=$?
set -e
okval=$([ "$MANIFEST_CODE" -eq 0 ] && echo "$MANIFEST_OUT" | grep -qi 'up-to-date' && echo 0 || echo 1)
chk "T6.build_manifest_up_to_date" HIGH "build-manifest.py --check exit=$MANIFEST_CODE, output: $MANIFEST_OUT" "$okval"

set +e
VERIFY_OUT=$(sh "$REAL_REPO/tools/install/harness.sh" verify claude --json 2>&1)
VERIFY_CODE=$?
set -e
SYNC_CHECK_OK=$(printf '%s' "$VERIFY_OUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
except Exception as exc:
    print('PARSE_ERROR', exc); sys.exit(1)
for c in d.get('checks', []):
    if c.get('id') == 'claude.sync-native-plugin':
        print('FOUND', c.get('ok'), c.get('detail'))
        sys.exit(0 if c.get('ok') else 1)
print('NOT_FOUND')
sys.exit(1)
" 2>&1)
SYNC_CHECK_CODE=$?
okval=$([ "$SYNC_CHECK_CODE" -eq 0 ] && echo 0 || echo 1)
chk "T6.harness_verify_sync_native_plugin_ok" HIGH "harness verify claude --json (exit=$VERIFY_CODE) -> claude.sync-native-plugin: $SYNC_CHECK_OK" "$okval"

log ""
log "## Write-set confinement (post-run)"
FINAL_STATUS=$(cd "$REAL_REPO" && git status --porcelain)
okval=$([ "$FINAL_STATUS" = "$BASELINE_STATUS" ] && echo 0 || echo 1)
chk "confinement.git_status_matches_baseline" HIGH "repo git status --porcelain unchanged by this entire test run (T0's own touch+regen round-trip already restored clean; T1-T6 write only to mktemp dirs)" "$okval"
