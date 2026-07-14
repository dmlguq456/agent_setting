#!/usr/bin/env sh
# dispatch-wait — SD-14 one-shot wait-contract helper (OPERATIONS §5.10).
#   A headless main/conductor is a one-shot process, so ending the turn also
#   ends the process. After dispatching a stage, the conductor must poll for
#   completion in the same turn instead of ending on a notification wait.
#   This helper wraps dispatch-liveness.sh rather than reimplementing it.
#
#   Usage: dispatch-wait.sh [--parent <self-slug>] [--jobs <path>] [--interval <s>] [--max <s>]
#     --parent  Limit open rows to children with parent=<slug>; otherwise use all.
#     --jobs    jobs.log path (default: $AGENT_HOME/.dispatch/jobs.log).
#     --interval Poll interval in seconds (default 20).
#     --max     Maximum wait for this call (default 120, capped at 600).
#
#   exit 0: all target children are closed; harvest them.
#   exit 2: children remain alive at --max; call again.
#   exit 3: a child is SUSPECT/DEAD/EXITED; diagnose, then harvest or redispatch.
#   Each iteration emits one status line. No background/nohup waits are used.
#   Reusing liveness also incorporates anchored limit/auth death evidence (SD-15).
set -u   # POSIX sh/dash has no pipefail; this wrapper does not depend on pipelines.

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME="${AGENT_HOME:-$("$SCRIPT_DIR/agent-home.sh")}"
LIVENESS="$SCRIPT_DIR/dispatch-liveness.sh"

PARENT=""
JOBS=""
INTERVAL=20
MAX=120
while [ $# -gt 0 ]; do
  case "$1" in
    --parent) PARENT="${2:-}"; shift 2 ;;
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

# Select open child rows. With --parent, require an exact parent=<slug> field.
# Use the last status per slug so append-only done rows close earlier open rows.
open_children() {
  awk -F'\t' -v slug="$PARENT" '
    NF==6 {
      key=$5; st[key]=$2
      if (slug=="") { m[key]=1; if ($2=="open") ln[key]=$0; next }
      n=split($6, kv, ",")
      for (i=1;i<=n;i++) if (kv[i]=="parent=" slug) { m[key]=1 }
      if ($2=="open") ln[key]=$0
    }
    END { for (k in st) if (st[k]=="open" && m[k]) print ln[k] }' "$JOBS"
}

elapsed=0
while :; do
  rows=$(open_children)
  # Handle an empty string directly to avoid counting a phantom blank row.
  if [ -z "$rows" ]; then
    if [ -n "$PARENT" ]; then
      echo "✓ parent=$PARENT has no open children — ready to harvest (exit 0)"
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
    echo "⚠️ SUSPECT/DEAD child detected (open $n) — stop waiting and diagnose (exit 3)"
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
