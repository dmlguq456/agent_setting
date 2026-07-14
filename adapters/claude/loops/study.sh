#!/bin/bash
# Weekly study loop comparing external developments with the current harness.
set -u
AGENT_HOME="${AGENT_HOME:-${CLAUDE_HOME:-$HOME/.claude}}"
LOOP_DIR="$AGENT_HOME/loops"
LOG="$LOOP_DIR/study.log"
source "$LOOP_DIR/lib.sh"   # PATH correction and retry wrapper.
# Temporary hold guard: .hold contains YYYY-MM-DD and resumes automatically after expiry.
if [ -f "$LOOP_DIR/.hold" ]; then _h=$(cat "$LOOP_DIR/.hold" 2>/dev/null); _t=$(date +%F);
  if [ -z "$_h" ] || [[ "$_t" < "$_h" ]] || [ "$_t" = "$_h" ]; then
    echo "[held until ${_h:-indefinite}] $(date -Iseconds)" >> "$LOG" 2>/dev/null || true; exit 0;
  fi;
fi

mkdir -p /home/nas/user/Uihyeop/notes/study

{
  echo "=== study run $(date -Iseconds) ==="
  cd /home/nas/user/Uihyeop || exit 1
  run_claude_retry 2400 "$LOOP_DIR/study.md" \
    --allowedTools "Bash,Read,Glob,Grep,Write,WebSearch,WebFetch"
  echo "=== exit $? $(date -Iseconds) ==="
} >> "$LOG"

tail -n 2000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
