#!/bin/bash
# 연수 루프 — 주 1회 (crontab: 17 6 * * 0) 외부 동향 × 현 세팅 대조 → 개선 제안서.
set -u
LOOP_DIR="$HOME/.claude/loops"
LOG="$LOOP_DIR/study.log"
# --- 일시 hold 가드 (토큰 절약, .hold 파일에 만료일 YYYY-MM-DD, 그날까지 skip 후 자동 재개) ---
if [ -f "$LOOP_DIR/.hold" ]; then _h=$(cat "$LOOP_DIR/.hold" 2>/dev/null); _t=$(date +%F);
  if [ -z "$_h" ] || [[ "$_t" < "$_h" ]] || [ "$_t" = "$_h" ]; then
    echo "[held until ${_h:-indefinite}] $(date -Iseconds)" >> "$LOG" 2>/dev/null || true; exit 0;
  fi;
fi

mkdir -p /home/nas/user/Uihyeop/notes/study

{
  echo "=== study run $(date -Iseconds) ==="
  cd /home/nas/user/Uihyeop || exit 1
  timeout 2400 "$HOME/.local/bin/claude" -p "$(cat "$LOOP_DIR/study.md")" \
    --allowedTools "Bash,Read,Glob,Grep,Write,WebSearch,WebFetch" \
    2>&1
  echo "=== exit $? $(date -Iseconds) ==="
} >> "$LOG"

tail -n 2000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
