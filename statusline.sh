#!/usr/bin/env bash
# Custom statusline — cwm HUD 대체 (의존성 없음, python3 로 JSON 파싱).
# 표시: 디렉토리 · git 브랜치 · spec-gate 상태 · context 사용량 · 모델.
# 입력: stdin JSON (Claude Code statusLine schema). 출력: 한 줄.
set -euo pipefail
input=$(cat)

# cwd / model / transcript_path 파싱
eval "$(printf '%s' "$input" | python3 -c '
import sys, json, shlex
try: d = json.load(sys.stdin)
except Exception: d = {}
cwd = d.get("cwd") or (d.get("workspace") or {}).get("current_dir") or "."
m = d.get("model") or {}
model = m.get("display_name") or m.get("id") or "?"
mid = (m.get("id") or "").lower()
tx = d.get("transcript_path") or ""
print("S_CWD="+shlex.quote(cwd))
print("S_MODEL="+shlex.quote(model))
print("S_MID="+shlex.quote(mid))
print("S_TX="+shlex.quote(tx))
' 2>/dev/null)"
: "${S_CWD:=$PWD}" "${S_MODEL:=?}" "${S_MID:=}" "${S_TX:=}"

dir=$(basename "$S_CWD")

# git 브랜치
branch=""
command -v git >/dev/null 2>&1 && branch=$(git -C "$S_CWD" rev-parse --abbrev-ref HEAD 2>/dev/null || true)

# artifact-guard 상태: 📌tracked(pipeline 강제) ↔ ✏️untracked(ad-hoc 직접편집)
gate=""; gate_open=0
d="$S_CWD"
for _ in $(seq 1 40); do
  if [ -f "$d/.claude_reports/spec/pipeline_state.yaml" ] || ls "$d"/.claude_reports/spec/*/pipeline_state.yaml >/dev/null 2>&1; then
    if [ -f "$d/.claude_reports/.untracked" ]; then
      mod=$(stat -c %Y "$d/.claude_reports/.untracked" 2>/dev/null || echo 0)
      [ $(( $(date +%s) - mod )) -lt 3600 ] && gate_open=1
    fi
    [ "$gate_open" = "1" ] && gate="⚡untracked(ad-hoc)" || gate="📌tracked(pipeline)"
    break
  fi
  [ "$d" = "/" ] && break
  d=$(dirname "$d")
done

# context 사용량 (transcript 마지막 usage / window)
ctx=""; ctx_pct=0
if [ -n "$S_TX" ] && [ -f "$S_TX" ]; then
  ctx_pct=$(tail -n 400 "$S_TX" 2>/dev/null | python3 -c '
import sys, json
mid = sys.argv[1]
win = 1_000_000 if "1m" in mid else 200_000
last = None
for line in sys.stdin:
    try: d = json.loads(line)
    except Exception: continue
    u = (d.get("message") or {}).get("usage")
    if u: last = u
if last:
    t = (last.get("input_tokens",0) + last.get("cache_creation_input_tokens",0)
         + last.get("cache_read_input_tokens",0))
    print(min(99, round(100*t/win)))
else:
    print(-1)
' "$S_MID" 2>/dev/null || echo -1)
fi

# ANSI 색
DIM=$'\033[2m'; CYAN=$'\033[36m'; YEL=$'\033[33m'; GRN=$'\033[32m'; RED=$'\033[31m'; RST=$'\033[0m'

out="${CYAN}${dir}${RST}"
[ -n "$branch" ] && out="${out} ${DIM}⎇${RST}${YEL}${branch}${RST}"
if [ -n "$gate" ]; then
  [ "$gate_open" = "1" ] && gc="$YEL" || gc="$GRN"
  out="${out} ${gc}${gate}${RST}"
fi
if [ "${ctx_pct:-(-1)}" -ge 0 ] 2>/dev/null; then
  if   [ "$ctx_pct" -ge 80 ]; then cc="$RED"
  elif [ "$ctx_pct" -ge 50 ]; then cc="$YEL"
  else cc="$GRN"; fi
  segs=10
  filled=$(( (ctx_pct * segs + 50) / 100 ))
  [ "$filled" -gt "$segs" ] && filled=$segs
  bar=""
  i=0; while [ "$i" -lt "$filled" ]; do bar="${bar}█"; i=$((i+1)); done
  while [ "$i" -lt "$segs" ]; do bar="${bar}░"; i=$((i+1)); done
  out="${out} ${DIM}🧠 context${RST} ${cc}${bar} ${ctx_pct}%${RST}"
fi
out="${out} ${DIM}${S_MODEL}${RST}"
printf '%s' "$out"
