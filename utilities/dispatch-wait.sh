#!/usr/bin/env sh
# dispatch-wait — SD-14 one-shot wait-contract helper (OPERATIONS §5.10).
#   A headless main/conductor is a one-shot process, so ending the turn also
#   ends the process. After dispatching a stage, the conductor must poll for
#   completion in the same turn instead of ending on a notification wait.
#   This helper wraps dispatch-liveness.sh rather than reimplementing it.
#
#   Usage: dispatch-wait.sh [--parent <self-slug>] [--slug <row-slug>] [--attempt-id <id>]
#                           [--jobs <path>] [--interval <s>] [--max <s>]
#     --parent     Limit open rows to children with parent=<slug>; otherwise use all.
#     --slug       Limit to the row whose own slug (field 5) exactly matches.
#     --attempt-id Limit to the row whose attempt_id=<id> kv field exactly matches.
#     --jobs       jobs.log path (default: $AGENT_HOME/.dispatch/jobs.log).
#     --interval   Poll interval in seconds (default 20).
#     --max        Maximum wait for this call (default and cap: 600).
#   --parent/--slug/--attempt-id combine with AND when more than one is given.
#
#   exit 0: all target children are closed; harvest them.
#   exit 2: children remain alive at --max; call again.
#   exit 3: a child has terminal/SUSPECT/DEAD/EXITED evidence; harvest or diagnose.
#   Each iteration emits one status line. No background/nohup waits are used.
#   Reusing liveness also incorporates anchored limit/auth death evidence (SD-15).
set -u   # POSIX sh/dash has no pipefail; this wrapper does not depend on pipelines.

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME="${AGENT_HOME:-$("$SCRIPT_DIR/agent-home.sh")}"
LIVENESS="$SCRIPT_DIR/dispatch-liveness.sh"

PARENT=""
SLUG=""
ATTEMPT_ID=""
JOBS=""
INTERVAL=20
MAX=600
while [ $# -gt 0 ]; do
  case "$1" in
    --parent) PARENT="${2:-}"; shift 2 ;;
    --slug) SLUG="${2:-}"; shift 2 ;;
    --attempt-id) ATTEMPT_ID="${2:-}"; shift 2 ;;
    --jobs) JOBS="${2:-}"; shift 2 ;;
    --interval) INTERVAL="${2:-20}"; shift 2 ;;
    --max) MAX="${2:-120}"; shift 2 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "dispatch-wait: unknown arg '$1'" >&2; exit 64 ;;
  esac
done
[ -n "$JOBS" ] || JOBS="${AGENT_DISPATCH_JOBS:-$AGENT_HOME/.dispatch/jobs.log}"
# Clamp to a single shell-call timeout budget.
[ "$MAX" -gt 600 ] 2>/dev/null && MAX=600
[ "$INTERVAL" -ge 1 ] 2>/dev/null || INTERVAL=20

# Without jobs.log there are no children to wait for.
if [ ! -f "$JOBS" ]; then
  echo "(jobs.log not found: $JOBS) — no open children"
  exit 0
fi

# Select open child rows. --parent/--slug/--attempt-id combine with AND when
# more than one is set; each defaults to "no constraint" when empty.
# Use the last status per slug so append-only done rows close earlier open rows.
open_children() {
  awk -F'\t' -v parent="$PARENT" -v slugf="$SLUG" -v attemptf="$ATTEMPT_ID" '
    NF==6 {
      key=$5; st[key]=$2
      ok=1
      if (parent!="") {
        p=0; n=split($6, kv, ",")
        for (i=1;i<=n;i++) if (kv[i]=="parent=" parent) p=1
        if (!p) ok=0
      }
      if (slugf!="" && key!=slugf) ok=0
      if (attemptf!="") {
        a=0; n=split($6, kv, ",")
        for (i=1;i<=n;i++) if (kv[i]=="attempt_id=" attemptf) a=1
        if (!a) ok=0
      }
      if (ok) m[key]=1
      if ($2=="open") ln[key]=$0
    }
    END { for (k in st) if (st[k]=="open" && m[k]) print ln[k] }' "$JOBS"
}

elapsed=0
while :; do
  rows=$(open_children)
  # Handle an empty string directly to avoid counting a phantom blank row.
  if [ -z "$rows" ]; then
    desc=""
    [ -n "$PARENT" ] && desc="$desc parent=$PARENT"
    [ -n "$SLUG" ] && desc="$desc slug=$SLUG"
    [ -n "$ATTEMPT_ID" ] && desc="$desc attempt_id=$ATTEMPT_ID"
    if [ -n "$desc" ]; then
      echo "✓${desc} has no open children — ready to harvest (exit 0)"
    else
      echo "✓ no open children — ready to harvest (exit 0)"
    fi
    exit 0
  fi
  n=$(printf '%s\n' "$rows" | grep -c .)

  # Reuse liveness with only the selected children so exit 3 stays scoped.
  tmp=$(mktemp)
  printf '%s\n' "$rows" > "$tmp"
  live_out=$(AGENT_HOME="$AGENT_HOME" "$LIVENESS" "$tmp" 2>&1)
  live_rc=$?
  rm -f "$tmp"

  if [ "$live_rc" -eq 3 ]; then
    echo "⚠️ terminal/SUSPECT/DEAD child detected (open $n) — stop waiting and harvest or diagnose (exit 3)"
    printf '%s\n' "$live_out"
    exit 3
  fi

  if [ "$elapsed" -ge "$MAX" ]; then
    echo "… $n children still running after ${elapsed}s (max ${MAX}s) — call again (exit 2)"
    exit 2
  fi

  echo "… $n children ALIVE — poll again in ${INTERVAL}s (elapsed ${elapsed}s/${MAX}s)"
  sleep "$INTERVAL"
  elapsed=$((elapsed + INTERVAL))
done
