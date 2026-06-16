#!/usr/bin/env bash
# mem-turn-nudge — 결정론 turn-counter 자기회고 (DESIGN_PRINCIPLES §0.5, spec v5 Cluster B/B2).
#   Hermes nudge_interval(=10, turn_context.py:191-215) 등가물의 우리 hook 모델.
#   UserPromptSubmit 마다 세션별 카운터++; N턴 도달 시 promote 회고 nudge(additionalContext) 주입 후 리셋.
#   memory.db write 감지(mtime 증가) 시 카운터 리셋 — Hermes turns_since_memory=0 등가 (write 하면 회고 불필요).
#   "언제 회고할지" 를 에이전트 판단이 아니라 결정론 카운터로 (§0.5). 등록: settings.json hooks.UserPromptSubmit.
set -euo pipefail

input=$(cat 2>/dev/null || true)
eval "$(printf '%s' "$input" | python3 -c '
import json, sys, shlex
try: d = json.load(sys.stdin)
except Exception: d = {}
print("EVENT="+shlex.quote(d.get("hook_event_name","") or ""))
print("SID="+shlex.quote(d.get("session_id","") or "default"))
' 2>/dev/null || true)"
EVENT="${EVENT:-}"; SID="${SID:-default}"
[ "$EVENT" = "UserPromptSubmit" ] || exit 0

N="${MEM_NUDGE_INTERVAL:-10}"
STORE="${MEM_STORE:-$HOME/.claude/memory}"
DB="$STORE/memory.db"
STATE="$STORE/.turn-state-$SID"

db_mtime=0; [ -f "$DB" ] && db_mtime=$(stat -c %Y "$DB" 2>/dev/null || echo 0)

counter=0; last_mtime=0
if [ -f "$STATE" ]; then
  counter=$(sed -n '1p' "$STATE" 2>/dev/null || echo 0)
  last_mtime=$(sed -n '2p' "$STATE" 2>/dev/null || echo 0)
fi
case "$counter" in (*[!0-9]*|"") counter=0 ;; esac
case "$last_mtime" in (*[!0-9]*|"") last_mtime=0 ;; esac

# memory write 발생(mtime 증가) → 카운터 리셋 (회고 불필요)
if [ "$db_mtime" -gt "$last_mtime" ]; then counter=0; fi
counter=$((counter + 1))

fire=0
if [ "$counter" -ge "$N" ]; then fire=1; counter=0; fi

mkdir -p "$STORE" 2>/dev/null || true
printf '%s\n%s\n' "$counter" "$db_mtime" > "$STATE" 2>/dev/null || true

# 오래된 세션 state GC (3일+ 비활성 — workflow-guard .untracked GC 패턴 동형, 2026-06-16). 무해 무시.
find "$STORE" -maxdepth 1 -name '.turn-state-*' -mmin +4320 -delete 2>/dev/null || true

if [ "$fire" = "1" ]; then
  MEM_MSG="🧠 turn-counter($N턴 기억 기록 없음) — 지금까지의 작업 맥락·결정·교훈 중 재사용 가치 있는 것을 \`mem note\`/\`mem add\` 로 promote 회고하세요 (없으면 무시). 기록하면 카운터 자동 리셋." \
  python3 -c 'import json,os; print(json.dumps({"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":os.environ["MEM_MSG"]}}, ensure_ascii=False))'
fi
exit 0
