#!/bin/bash
# 야간 정찰 루프 — crontab 에서 호출 (37 5 * * *)
# read-only 점검 + notes/oncall/ 보고 1개. 수정·커밋 없음.
set -u
LOOP_DIR="$HOME/.claude/loops"
LOG="$LOOP_DIR/oncall.log"
# --- 일시 hold 가드 (토큰 절약, .hold 파일에 만료일 YYYY-MM-DD, 그날까지 skip 후 자동 재개) ---
if [ -f "$LOOP_DIR/.hold" ]; then _h=$(cat "$LOOP_DIR/.hold" 2>/dev/null); _t=$(date +%F);
  if [ -z "$_h" ] || [[ "$_t" < "$_h" ]] || [ "$_t" = "$_h" ]; then
    echo "[held until ${_h:-indefinite}] $(date -Iseconds)" >> "$LOG" 2>/dev/null || true; exit 0;
  fi;
fi

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
