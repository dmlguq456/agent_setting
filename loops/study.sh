#!/bin/bash
# 연수 루프 — 주 1회 (crontab: 17 6 * * 0) 외부 동향 × 현 세팅 대조 → 개선 제안서.
set -u
LOOP_DIR="$HOME/.claude/loops"
LOG="$LOOP_DIR/study.log"
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
