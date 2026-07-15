#!/bin/bash
# Nightly read-only reconnaissance loop, invoked from crontab.
# Produces one notes/oncall report and never edits or commits source.
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

# NAS mount guard (2026-07-15 incident): if /home/nas is not mounted, the mkdir
# below would create shadow dirs on the root fs and cd would "succeed" against
# an empty tree. Fail loudly instead; the retry lands after remount.
if ! mountpoint -q /home/nas; then
  echo "[oncall] SKIP: /home/nas not mounted — exit 1 $(date -Iseconds)" >> "$LOG" 2>/dev/null || true
  exit 1
fi
mkdir -p /home/nas/user/Uihyeop/notes/oncall

{
  echo "=== oncall run $(date -Iseconds) ==="
  cd /home/nas/user/Uihyeop || exit 1
  run_claude_retry 900 "$LOOP_DIR/oncall.md" \
    --model sonnet \
    --allowedTools "Bash,Read,Glob,Grep,Write"
  rc=$?
  # Success requires today's heartbeat report file: a clean exit without the
  # file is a silent failure (e.g. an empty-prompt run), not a pass.
  today_report="/home/nas/user/Uihyeop/notes/oncall/$(date +%F).md"
  if [ "$rc" -eq 0 ] && [ ! -f "$today_report" ]; then
    echo "=== FAIL: exit 0 but heartbeat report missing ($today_report) ==="
    rc=1
  fi
  echo "=== exit $rc $(date -Iseconds) ==="
} >> "$LOG"

# Bound the log to the most recent 2,000 lines.
tail -n 2000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
