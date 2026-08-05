#!/usr/bin/env bash
# End-to-end SD-45 route-record path through the real hooks/spec-skill-gate.sh
# (plan.md Step 1.5, round_1 finding 2 fail-open audit).
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SPEC="$ROOT/hooks/spec-skill-gate.sh"

PASS=0
FAIL=0
ok() { PASS=$((PASS+1)); printf '  ok  %s\n' "$1"; }
bad() { FAIL=$((FAIL+1)); printf '  BAD %s\n' "$1"; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export AGENT_HOME="$TMP/agent_home"
# This suite may itself run as a route-bound dispatch worker (AGENT_ARTIFACT_ROOT
# / AGENT_ROUTE_FILE / AGENT_ROUTE_ID pointing at the real registry); unset them
# so the fixture project resolves its own isolated artifact root.
unset AGENT_ARTIFACT_ROOT AGENT_ROUTE_FILE AGENT_ROUTE_ID

PROJECT="$TMP/proj"
ARTROOT="$PROJECT/.agent_reports"
mkdir -p "$ARTROOT/spec"
printf '# prd\n' > "$ARTROOT/spec/prd.md"

ROUTE="$TMP/route.json"
write_route() {
  satisfied=$1
  cat > "$ROUTE" <<JSON
{
  "schema_version": 2,
  "tracking": "tracked",
  "tracked_gate_evidence": {
    "workflow_mode": "tracked",
    "spec_read": {"satisfied": $satisfied, "source": "current"}
  },
  "cwd": "$PROJECT",
  "artifact_root": "$ARTROOT",
  "route_id": "rt-fixture"
}
JSON
}

# 1. record-only pass, no marker on disk.
write_route true
touch -d '+1 hour' "$ROUTE" 2>/dev/null || touch -A 010000 "$ROUTE" 2>/dev/null || sleep 1 && touch "$ROUTE"
if AGENT_ROUTE_ID=rt-fixture "$SPEC" --skill autopilot-code --cwd "$PROJECT" --session freshsid --route "$ROUTE"; then
  ok "record-only pass with no marker on disk"
else
  bad "record-only pass should succeed with a satisfied, fresh route record"
fi

# 2. flip spec_read.satisfied to false -> deny.
write_route false
touch "$ROUTE"
if AGENT_ROUTE_ID=rt-fixture "$SPEC" --skill autopilot-code --cwd "$PROJECT" --session freshsid --route "$ROUTE" 2>/tmp/deny1.err; then
  bad "unsatisfied spec_read should deny"
else
  [ "$?" -eq 2 ] && ok "unsatisfied spec_read denies (rc=2)" || ok "unsatisfied spec_read denies"
fi

# 3. restore satisfied, then touch the prd after the route -> stale deny.
write_route true
touch "$ROUTE"
sleep 1
touch "$ARTROOT/spec/prd.md"
if AGENT_ROUTE_ID=rt-fixture "$SPEC" --skill autopilot-code --cwd "$PROJECT" --session freshsid --route "$ROUTE"; then
  bad "stale route (prd touched after route) should deny"
else
  ok "stale route (prd newer than route) denies"
fi

# 4. add the session-local marker -> passes via the marker path even though
#    the route is stale, proving fix 1 never weakens the existing marker path.
key=$(printf '%s' "$PROJECT" | sed 's#[/ ]#_#g')
mkdir -p "$AGENT_HOME/.spec-grounding"
prd_mtime=$(stat -c %Y "$ARTROOT/spec/prd.md" 2>/dev/null || stat -f %m "$ARTROOT/spec/prd.md")
printf '%s' "$prd_mtime" > "$AGENT_HOME/.spec-grounding/freshsid__${key}"
if AGENT_ROUTE_ID=rt-fixture "$SPEC" --skill autopilot-code --cwd "$PROJECT" --session freshsid --route "$ROUTE"; then
  ok "marker path still passes when the route is stale (fall-through intact)"
else
  bad "marker path should still satisfy the gate independent of route staleness"
fi

echo "spec_skill_gate_route: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
