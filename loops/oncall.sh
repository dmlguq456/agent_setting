#!/bin/bash
# 야간 정찰 루프 — crontab 에서 호출 (37 5 * * *)
# read-only 점검 + notes/oncall/ 보고 1개. 수정·커밋 없음.
set -u
LOOP_DIR="$HOME/.claude/loops"
LOG="$LOOP_DIR/oncall.log"
mkdir -p /home/nas/user/Uihyeop/notes/oncall

{
  echo "=== oncall run $(date -Iseconds) ==="
  cd /home/nas/user/Uihyeop || exit 1
  timeout 900 "$HOME/.local/bin/claude" -p "$(cat "$LOOP_DIR/oncall.md")" \
    --model sonnet \
    --allowedTools "Bash,Read,Glob,Grep,Write" \
    2>&1
  echo "=== exit $? $(date -Iseconds) ==="
} >> "$LOG"

# 로그 비대 방지 — 최근 2000줄만 유지
tail -n 2000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
