#!/bin/bash
# 검토함 미연결-노트 sweep 루프 — crontab 호출 (20 5 * * *, note 05:03 뒤).
# card_id=null 노트 → 연결 제안(link-note/new-card) 을 notes/_triage/ 에 emit.
# DB write 0 (제안 파일만)·idempotent — note 루프 migrate clobber 와 무관·안전.
set -u
# cron 은 최소 PATH 라 nvm node/npx 부재 → 명시 prepend (npx 가 내부에서 node 재탐색하므로 PATH 로 고정).
export PATH="$HOME/.local/bin:$HOME/.nvm/versions/node/v20.20.2/bin:$PATH"
LOOP_DIR="$HOME/.claude/loops"
LOG="$LOOP_DIR/triage-sweep.log"
BOARD=/home/nas/user/Uihyeop/worklog-board
# --- 일시 hold 가드 (.hold 만료일 YYYY-MM-DD, 그날까지 skip 후 자동 재개) ---
if [ -f "$LOOP_DIR/.hold" ]; then _h=$(cat "$LOOP_DIR/.hold" 2>/dev/null); _t=$(date +%F);
  if [ -z "$_h" ] || [[ "$_t" < "$_h" ]] || [ "$_t" = "$_h" ]; then
    echo "[held until ${_h:-indefinite}] $(date -Iseconds)" >> "$LOG" 2>/dev/null || true; exit 0;
  fi;
fi
{
  echo "=== triage-sweep run $(date -Iseconds) ==="
  cd "$BOARD" || exit 1
  set -a; . "$BOARD/.env.local" 2>/dev/null; set +a   # CARDS_DIR/LAYER2_DIR 등
  timeout 600 "$HOME/.local/bin/npx" tsx scripts/generate-link-proposals.ts --apply 2>&1
  echo "=== exit $? $(date -Iseconds) ==="
} >> "$LOG"
tail -n 1000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
