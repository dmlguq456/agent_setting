#!/bin/sh
# PostToolUse(Read): prd.md를 실제로 Read하면 세션 마커를 떨군다.
# 이 마커가 spec-skill-gate.sh의 통과 증거(= '인용'이 아닌 '실제 Read').
# 마커 내용 = prd.md mtime(Read 시점) → 이후 drift 비교용. POSIX sh, no jq.

input=$(cat 2>/dev/null)
[ -z "$input" ] && exit 0

fp=$(printf '%s' "$input" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//; s/"$//')
case "$fp" in
  */.agent_reports/spec/prd.md) ;;
  */.claude_reports/spec/prd.md) ;;
  *) exit 0 ;;
esac
[ -f "$fp" ] || exit 0

sid=$(printf '%s' "$input" | grep -o '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"session_id"[[:space:]]*:[[:space:]]*"//; s/"$//')
[ -z "$sid" ] && sid="nosession"

root=$(dirname "$(dirname "$(dirname "$fp")")")
key=$(printf '%s' "$root" | sed 's#[/ ]#_#g')
mtime=$(stat -c %Y "$fp" 2>/dev/null || echo 0)

mkdir -p "$HOME/.claude/.spec-grounding"
printf '%s\n' "$mtime" > "$HOME/.claude/.spec-grounding/${sid}__${key}"
exit 0
