#!/bin/bash
# usage-aware loop adapter routing regression. Real Claude/Codex CLIs are never invoked.
set -uo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

fails=0
ok() { printf 'ok   - %s\n' "$1"; }
bad() { printf 'FAIL - %s\n' "$1"; fails=$((fails + 1)); }

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
jobs="$tmp/jobs.log"
: > "$jobs"
export AGENT_DISPATCH_JOBS="$jobs"
export LOOP_USAGE_CHECK="$LOOP_HARNESS_ROOT/utilities/usage-check.sh"

HARNESS_ROUTE_SLOT=0 select_loop_adapter auto oncall
[ "$LOOP_SELECTED_ADAPTER" = claude ] && [ "$LOOP_ROUTE_REASON" = neutral-spread:0 ] && ok "auto neutral slot 0 selects Claude" || bad "neutral slot 0 selection"
HARNESS_ROUTE_SLOT=1 select_loop_adapter auto oncall
[ "$LOOP_SELECTED_ADAPTER" = codex ] && [ "$LOOP_ROUTE_REASON" = neutral-spread:1 ] && ok "auto neutral slot 1 selects Codex" || bad "neutral slot 1 selection"
select_loop_adapter opencode oncall
[ "$LOOP_SELECTED_ADAPTER" = opencode ] && [ "$LOOP_ROUTE_REASON" = explicit:opencode ] && ok "explicit OpenCode remains available" || bad "explicit OpenCode selection"

now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf '%s\tdone\tr\tw\tc\tharness=claude,note=dead-session-limit,reset=11:59pm\n' "$now" > "$jobs"
printf '%s\tdone\tr\tw\tx\tharness=codex,note=dead-usage-limit,reset=11:59pm\n' "$now" >> "$jobs"
if select_loop_adapter auto oncall; then
  bad "both limited should be unavailable"
elif [ "$?" -eq 1 ] && [ "$LOOP_SELECTED_ADAPTER" = unavailable ] && [ "$LOOP_ROUTE_REASON" = both-limited ]; then
  ok "both limited blocks launch"
else
  bad "both limited unavailable metadata"
fi

# A new limit discovered during oncall must be recorded and fail over once.
: > "$jobs"
prompt="$tmp/prompt.md"
printf 'fixture prompt\n' > "$prompt"
fake_claude="$tmp/claude"
fake_codex="$tmp/codex"
printf '%s\n' '#!/bin/sh' 'grep -q "harness=claude" "$AGENT_DISPATCH_JOBS" || exit 3' 'echo "You have hit your session limit · resets 11:59pm"' 'exit 1' > "$fake_claude"
printf '%s\n' '#!/bin/sh' 'grep -q "harness=codex" "$AGENT_DISPATCH_JOBS" || exit 3' 'cat >/dev/null' 'echo codex-ok' 'exit 0' > "$fake_codex"
chmod +x "$fake_claude" "$fake_codex"

LOOP_ADAPTER=auto
HARNESS_CAPACITY_BIAS=claude
CLAUDE_BIN="$fake_claude"
CODEX_BIN="$fake_codex"
export LOOP_ADAPTER HARNESS_CAPACITY_BIAS CLAUDE_BIN CODEX_BIN
out=$(run_claude_retry 5 "$prompt")
rc=$?
if [ "$rc" -eq 0 ] && printf '%s\n' "$out" | grep -q '^=== failover claude → codex (known-limit:claude) ===$' && printf '%s\n' "$out" | grep -q '^codex-ok$'; then
  ok "oncall runner immediately fails over Claude → Codex"
else
  bad "runtime limit failover (rc=$rc out=$out)"
fi
claude_row=$(grep 'harness=claude' "$jobs")
codex_row=$(grep 'harness=codex' "$jobs")
if [ "$(wc -l < "$jobs")" -eq 2 ] \
    && [ "$(grep -c $'\topen\t' "$jobs")" -eq 0 ] \
    && printf '%s\n' "$claude_row" | grep -q $'\tdone\t' \
    && printf '%s\n' "$claude_row" | grep -q 'note=dead-session-limit' \
    && printf '%s\n' "$claude_row" | grep -q 'reset=11:59pm' \
    && printf '%s\n' "$codex_row" | grep -q $'\tdone\t'; then
  ok "loop attempts are visible and close in one canonical registry"
else
  bad "loop Fleet rows [$(tr '\n' ';' < "$jobs")]"
fi

echo "— loop adapter routing: $([ "$fails" -eq 0 ] && echo PASS || echo "FAIL ($fails)")"
exit "$fails"
