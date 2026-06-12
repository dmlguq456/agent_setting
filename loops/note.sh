#!/bin/bash
# autopilot-note 야간 루프 — crontab 에서 호출 (3 5 * * *)
# 전날 산출물을 worklog-board Layer 2 노트로 라우팅 (idempotent).
# 인자 없으면 default (--scope yesterday --qa light), 수동 호출 시 인자 전달 가능.
set -u
LOOP_DIR="$HOME/.claude/loops"
LOG="$LOOP_DIR/note.log"
# --- 일시 hold 가드 (토큰 절약, .hold 파일에 만료일 YYYY-MM-DD, 그날까지 skip 후 자동 재개) ---
if [ -f "$LOOP_DIR/.hold" ]; then _h=$(cat "$LOOP_DIR/.hold" 2>/dev/null); _t=$(date +%F);
  if [ -z "$_h" ] || [[ "$_t" < "$_h" ]] || [ "$_t" = "$_h" ]; then
    echo "[held until ${_h:-indefinite}] $(date -Iseconds)" >> "$LOG" 2>/dev/null || true; exit 0;
  fi;
fi

ARGS="${*:---scope yesterday --qa light}"

{
  echo "=== note run $(date -Iseconds) args: $ARGS ==="
  cd /home/nas/user/Uihyeop || exit 1
  timeout 2400 "$HOME/.local/bin/claude" -p "/autopilot-note $ARGS" \
    --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Skill,Agent,TodoWrite" \
    2>&1
  echo "=== exit $? $(date -Iseconds) ==="
} >> "$LOG"

tail -n 2000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
