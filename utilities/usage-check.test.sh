#!/usr/bin/env bash
# usage-check.test.sh — SD-16(a) 사용량 조회 헬퍼 회귀.
#   증명: dead-limit 마커 → limited(reset), 마커 없음 → ok, jobs.log 부재 → unknown,
#   window 밖(오래된) 마커 → ok(만료), harness 스코프 필터.
set -uo pipefail
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
UC="$SCRIPT_DIR/usage-check.sh"
fails=0
ok()  { printf 'ok   - %s\n' "$1"; }
bad() { printf 'FAIL - %s\n' "$1"; fails=$((fails + 1)); }

tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
AH="$tmp/agent_setting"; mkdir -p "$AH/.dispatch" "$AH/core"; : > "$AH/core/CORE.md"
jobs="$AH/.dispatch/jobs.log"
now_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)
old_iso=$(date -u -d '10 hours ago' +%Y-%m-%dT%H:%M:%SZ)

# Case: fresh claude dead-session-limit marker → limited(3pm)
printf '%s\tdone\tr\tw\ts1\tcapability=code-plan,depth=2,harness=claude,parent=cx,note=dead-session-limit,reset=3pm\n' "$now_iso" > "$jobs"
out=$(AGENT_HOME="$AH" bash "$UC" --harness claude 2>&1)
[ "$out" = "claude limited(3pm)" ] && ok "fresh dead-limit → limited(reset)" || bad "expected 'claude limited(3pm)', got [$out]"

# Case: no marker → ok
printf '%s\topen\tr\tw\ts2\tcapability=code-plan,depth=2,harness=claude,parent=cx\n' "$now_iso" > "$jobs"
out=$(AGENT_HOME="$AH" bash "$UC" --harness claude 2>&1)
[ "$out" = "claude ok" ] && ok "no marker → ok" || bad "expected 'claude ok', got [$out]"

# Case: jobs.log missing → unknown
out=$(AGENT_HOME="$AH" bash "$UC" --harness claude --jobs "$tmp/none.log" 2>&1)
[ "$out" = "claude unknown" ] && ok "missing jobs.log → unknown" || bad "expected 'claude unknown', got [$out]"

# Case: stale marker (10h ago, window 300m) → expired → ok
printf '%s\tdone\tr\tw\ts3\tcapability=code-plan,depth=2,harness=claude,note=dead-session-limit,reset=1pm\n' "$old_iso" > "$jobs"
out=$(AGENT_HOME="$AH" bash "$UC" --harness claude 2>&1)
[ "$out" = "claude ok" ] && ok "stale marker beyond window → ok(expired)" || bad "expected 'claude ok', got [$out]"

# Case: harness scope — codex marker must not leak into claude
printf '%s\tdone\tr\tw\ts4\tcapability=code-plan,depth=2,harness=codex,owner_harness=codex,note=dead-usage-limit,reset=noon\n' "$now_iso" > "$jobs"
out=$(AGENT_HOME="$AH" bash "$UC" --harness all 2>&1)
echo "$out" | grep -q '^claude ok$' && echo "$out" | grep -q '^codex limited(noon)$' \
  && ok "harness scope: claude ok / codex limited" || bad "harness scope wrong: [$out]"

echo "— usage-check conformance: $([ $fails -eq 0 ] && echo PASS || echo "FAIL ($fails)")"
exit $fails
