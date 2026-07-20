#!/bin/bash
# Nightly reconnaissance loop, invoked from crontab.
# Produces one notes/oncall report and may ingest bounded proposal evidence;
# it never edits or commits source, runtime config, plugins, or memory.
set -u
AGENT_HOME="${AGENT_HOME:-${CLAUDE_HOME:-$HOME/.claude}}"
LOOP_DIR="$AGENT_HOME/loops"
LOG="$LOOP_DIR/oncall.log"
source "$LOOP_DIR/lib.sh"   # PATH correction and retry wrapper.
# Temporary hold guard: .hold contains YYYY-MM-DD and resumes automatically after expiry.
if [ -f "$LOOP_DIR/.hold" ]; then _h=$(cat "$LOOP_DIR/.hold" 2>/dev/null); _t=$(date +%F);
  if [ -z "$_h" ] || [[ "$_t" < "$_h" ]] || [ "$_t" = "$_h" ]; then
    echo "[held until ${_h:-indefinite}] $(date -Iseconds)" >> "$LOG" 2>/dev/null || true; exit 0;
  fi;
fi

mkdir -p /home/nas/user/Uihyeop/notes/oncall

{
  echo "=== oncall run $(date -Iseconds) ==="
  cd /home/nas/user/Uihyeop || exit 1
  run_claude_retry 900 "$LOOP_DIR/oncall.md" \
    --model sonnet \
    --allowedTools "Bash,Read,Glob,Grep,Write"
  echo "=== exit $? $(date -Iseconds) ==="
} >> "$LOG"

# Bound the log to the most recent 2,000 lines.
tail -n 2000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
