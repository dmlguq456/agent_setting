#!/usr/bin/env bash
# Custom statusline (의존성 없음, python3 로 stdin JSON 파싱).
# 표시: 디렉토리 │ git 브랜치 │ spec-gate │ context │ 모델 + 5h/7d 사용량 (세로선 파티션).
# 입력: stdin JSON (Claude Code statusLine schema). 출력: 한 줄.
# 5h/7d 사용량 = stdin 의 rate_limits.{five_hour,seven_day}.used_percentage — /usage 와 동일한 공식 값.
# context     = stdin 의 context_window.current_usage / window (model id 에 1m 있으면 1M, 아니면 200k).
set -euo pipefail
input=$(cat)

eval "$(printf '%s' "$input" | python3 -c '
import sys, json, shlex
try: d = json.load(sys.stdin)
except Exception: d = {}
cwd = d.get("cwd") or (d.get("workspace") or {}).get("current_dir") or "."
m = d.get("model") or {}
model = m.get("display_name") or m.get("id") or "?"
mid = (m.get("id") or "").lower()
sid = d.get("session_id") or ""
rl = d.get("rate_limits") or {}
def rlpct(k):
    v = (rl.get(k) or {}).get("used_percentage")
    return str(int(v)) if isinstance(v, (int, float)) else ""
cw = (d.get("context_window") or {}).get("current_usage") or {}
ctok = cw.get("input_tokens", 0) + cw.get("cache_creation_input_tokens", 0) + cw.get("cache_read_input_tokens", 0)
win = 1_000_000 if "1m" in mid else 200_000
cpct = min(99, round(100 * ctok / win)) if ctok else -1
print("S_CWD=" + shlex.quote(cwd))
print("S_MODEL=" + shlex.quote(model))
print("S_SID=" + shlex.quote(sid))
print("S_5H=" + shlex.quote(rlpct("five_hour")))
print("S_7D=" + shlex.quote(rlpct("seven_day")))
print("S_CTX=" + shlex.quote(str(cpct)))
' 2>/dev/null)"
: "${S_CWD:=$PWD}" "${S_MODEL:=?}" "${S_SID:=}" "${S_5H:=}" "${S_7D:=}" "${S_CTX:=-1}"

dir=$(basename "$S_CWD")

# git 브랜치
branch=""
command -v git >/dev/null 2>&1 && branch=$(git -C "$S_CWD" rev-parse --abbrev-ref HEAD 2>/dev/null || true)

# artifact-guard 상태: 📌tracked(pipeline 강제) ↔ ⚡untracked(ad-hoc 직접편집)
gate=""; gate_open=0
d="$S_CWD"
for _ in $(seq 1 40); do
  if [ -d "$d/.claude_reports" ]; then
    if [ -n "$S_SID" ]; then [ -f "$d/.claude_reports/.untracked.$S_SID" ] && gate_open=1; else [ -f "$d/.claude_reports/.untracked" ] && gate_open=1; fi
    [ "$gate_open" = "1" ] && gate="⚡untracked(ad-hoc)" || gate="📌tracked(pipeline)"
    break
  fi
  [ "$d" = "/" ] && break
  d=$(dirname "$d")
done

# ANSI 색 + 퍼센트 색 헬퍼 (녹 <50 / 황 <80 / 적 ≥80)
DIM=$'\033[2m'; CYAN=$'\033[36m'; YEL=$'\033[33m'; GRN=$'\033[32m'; RED=$'\033[31m'; RST=$'\033[0m'
pcol(){ if [ "${1:-0}" -ge 80 ] 2>/dev/null; then printf '%s' "$RED"; elif [ "${1:-0}" -ge 50 ] 2>/dev/null; then printf '%s' "$YEL"; else printf '%s' "$GRN"; fi; }

# --- 세그먼트 배열 → 세로선(│) 파티션으로 join ---
segs_arr=()
segs_arr+=("${CYAN}${dir}${RST}")
[ -n "$branch" ] && segs_arr+=("${DIM}⎇${RST}${YEL}${branch}${RST}")
if [ -n "$gate" ]; then
  [ "$gate_open" = "1" ] && gc="$YEL" || gc="$GRN"
  segs_arr+=("${gc}${gate}${RST}")
fi
if [ "${S_CTX}" -ge 0 ] 2>/dev/null; then
  cc=$(pcol "$S_CTX")
  segs=10; filled=$(( (S_CTX * segs + 50) / 100 )); [ "$filled" -gt "$segs" ] && filled=$segs
  bar=""; i=0
  while [ "$i" -lt "$filled" ]; do bar="${bar}█"; i=$((i+1)); done
  while [ "$i" -lt "$segs" ]; do bar="${bar}░"; i=$((i+1)); done
  segs_arr+=("${DIM}🧠${RST} ${cc}${bar} ${S_CTX}%${RST}")
fi

# 모델 + 5h/7d 사용량 (stdin rate_limits = /usage 공식 값, 분모 추측 없음)
model_seg="${DIM}${S_MODEL}${RST}"
u=""
[ -n "$S_5H" ] && u="${u} ${DIM}5h${RST} $(pcol "$S_5H")${S_5H}%${RST}"
[ -n "$S_7D" ] && u="${u} ${DIM}7d${RST} $(pcol "$S_7D")${S_7D}%${RST}"
[ -n "$u" ] && model_seg="${model_seg} ${u}"
segs_arr+=("$model_seg")

# join with 세로선 파티션
out=""; sep=" ${DIM}│${RST} "
for s in "${segs_arr[@]}"; do [ -z "$out" ] && out="$s" || out="${out}${sep}${s}"; done
printf '%s' "$out"
