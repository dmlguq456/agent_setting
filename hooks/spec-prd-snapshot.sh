#!/usr/bin/env bash
# PreToolUse hook — spec 파일(prd.md/stack.md) 직접 편집 시 자동 버전 snapshot.
# 목적: autopilot-spec update mode 를 우회한 ad-hoc Edit/Write 에서도 버전 이력이
#       절대 유실되지 않도록 harness 가 강제. (글로벌 CLAUDE.md §0(A))
# jq 미설치 환경 → python3 로 JSON 파싱. 차단하지 않음(snapshot 만 보장).

input=$(cat)

fp=$(printf '%s' "$input" | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
    ti = d.get("tool_input") or {}
    print(ti.get("file_path", "") or "")
except Exception:
    print("")
' 2>/dev/null)

[ -z "$fp" ] && exit 0

# spec 의 prd.md / stack.md 만 대상
case "$fp" in
  */.claude_reports/spec/prd.md|*/.claude_reports/spec/stack.md) ;;
  *) exit 0 ;;
esac

# 존재하는 파일을 _고치는_ 경우만 snapshot (신규 생성은 보존할 이전 버전 없음)
[ -f "$fp" ] || exit 0

specdir=$(dirname "$fp")
vroot="$specdir/_internal/versions"
mkdir -p "$vroot" 2>/dev/null

# 다음 버전 번호 = 기존 v{N} 최대 + 1
max=0
for d in "$vroot"/v[0-9]*; do
  [ -d "$d" ] || continue
  n=${d##*/v}
  case "$n" in *[!0-9]*) continue ;; esac
  [ "$n" -gt "$max" ] && max="$n"
done
next=$((max + 1))
vdir="$vroot/v$next"
mkdir -p "$vdir" 2>/dev/null
cp -p "$fp" "$vdir/$(basename "$fp")" 2>/dev/null

msg="spec 파일 직접 편집 감지 ($(basename "$fp")) — autopilot-spec update mode 가 canonical 경로. 이전 버전 자동 snapshot됨: _internal/versions/v$next/. 직접 Edit 대신 update mode 사용 권장."

python3 -c '
import json, sys
m = sys.argv[1]
print(json.dumps({
    "hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": m},
    "systemMessage": m
}))
' "$msg" 2>/dev/null

exit 0
