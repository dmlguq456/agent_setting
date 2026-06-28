#!/bin/sh
# PreToolUse(Skill): spec 청사진을 _변경_ 하는 skill(autopilot-code/spec)을 spec-backed cwd에서
# 호출할 때, 이번 세션에 prd.md를 '실제 Read'(마커 존재)하지 않았으면 DENY.
# prd.md가 Read 이후 갱신됐으면(역방향 drift)도 DENY → 재Read 강제.
# self-report가 아니라 검증 가능한 하드 게이트. POSIX sh, no jq.
# (autopilot-note 제외 — digest skill 이라 spec 청사진을 안 바꿈. 2026-06-16 audit #16.)

input=$(cat 2>/dev/null)
[ -z "$input" ] && exit 0

skill=$(printf '%s' "$input" | grep -o '"skill"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"skill"[[:space:]]*:[[:space:]]*"//; s/"$//')
case "$skill" in
  autopilot-code|autopilot-spec) ;;
  *) exit 0 ;;   # spec-governed 아닌 skill → 통과
esac

# spec-backed root 탐색 (cwd + 상위)
dir=$PWD
prd=""
root=""
for _ in 0 1 2 3; do
  if [ -f "$dir/.agent_reports/spec/prd.md" ]; then prd="$dir/.agent_reports/spec/prd.md"; root="$dir"; break; fi
  if [ -f "$dir/.claude_reports/spec/prd.md" ]; then prd="$dir/.claude_reports/spec/prd.md"; root="$dir"; break; fi
  parent=$(dirname "$dir")
  [ "$parent" = "$dir" ] && break
  dir=$parent
done
[ -z "$prd" ] && exit 0   # spec-backed 아님 → 통과

sid=$(printf '%s' "$input" | grep -o '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"session_id"[[:space:]]*:[[:space:]]*"//; s/"$//')
[ -z "$sid" ] && sid="nosession"
key=$(printf '%s' "$root" | sed 's#[/ ]#_#g')
marker="$HOME/.claude/.spec-grounding/${sid}__${key}"
cur=$(stat -c %Y "$prd" 2>/dev/null || echo 0)

deny() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1"
  exit 0
}

if [ ! -f "$marker" ]; then
  deny "spec-backed cwd인데 prd.md를 이번 세션에 Read하지 않음. $prd 를 Read 도구로 직접 읽은 뒤 다시 호출하세요. 코드 주석·brief 인용은 무효 — 실제 Read만 게이트를 통과합니다."
fi

read_mtime=$(cat "$marker" 2>/dev/null || echo 0)
if [ "$cur" -gt "$read_mtime" ]; then
  deny "prd.md가 마지막 Read 이후 갱신됨(역방향 drift). $prd 를 다시 Read한 뒤 호출하세요."
fi

exit 0   # 마커 존재 + 최신 → 통과
