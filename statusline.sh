#!/usr/bin/env bash
# Custom statusline (의존성 없음, python3 로 stdin JSON 파싱).
# 표시: 디렉토리 │ git 브랜치 │ spec-gate │ context │ 모델 + 5h/7d 사용량 (세로선 파티션).
# 입력: stdin JSON (Claude Code statusLine schema). 출력: 한 줄.
# 5h/7d 사용량 = stdin 의 rate_limits.{five_hour,seven_day}.used_percentage — /usage 와 동일한 공식 값.
# context     = stdin 의 context_window.current_usage / window (model id 에 1m 있으면 1M, 아니면 200k).
set -euo pipefail
input=$(cat)
printf '%s' "$input" > "$HOME/.claude/.statusline-last.json" 2>/dev/null || true  # 디버그·필드 탐사용 (최신 입력 1건)

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
import time
def rlrem(k):
    rs = (rl.get(k) or {}).get("resets_at")
    if not isinstance(rs, (int, float)): return ""
    s = int(rs - time.time())
    if s <= 0: return ""
    dd, r = divmod(s, 86400); hh, r = divmod(r, 3600); mm = r // 60
    return f"{dd}d{hh}h" if dd else (f"{hh}h{mm:02d}m" if hh else f"{mm}m")
cw = (d.get("context_window") or {}).get("current_usage") or {}
ctok = cw.get("input_tokens", 0) + cw.get("cache_creation_input_tokens", 0) + cw.get("cache_read_input_tokens", 0)
win = 1_000_000 if "1m" in mid else 200_000
cpct = min(99, round(100 * ctok / win)) if ctok else -1
print("S_CWD=" + shlex.quote(cwd))
print("S_MODEL=" + shlex.quote(model))
print("S_SID=" + shlex.quote(sid))
print("S_5H=" + shlex.quote(rlpct("five_hour")))
print("S_7D=" + shlex.quote(rlpct("seven_day")))
print("S_5H_RST=" + shlex.quote(rlrem("five_hour")))
print("S_7D_RST=" + shlex.quote(rlrem("seven_day")))
print("S_CTX=" + shlex.quote(str(cpct)))
' 2>/dev/null)"
: "${S_CWD:=$PWD}" "${S_MODEL:=?}" "${S_SID:=}" "${S_5H:=}" "${S_7D:=}" "${S_5H_RST:=}" "${S_7D_RST:=}" "${S_CTX:=-1}"

dir=$(basename "$S_CWD")

# git 브랜치 + 위험 상태 플래그 (⚠️ merge/rebase 진행 중 · 💀 머지 완료된 죽은 브랜치)
branch=""; gflag=""
if command -v git >/dev/null 2>&1; then
  branch=$(git -C "$S_CWD" rev-parse --abbrev-ref HEAD 2>/dev/null || true)
  if [ -n "$branch" ]; then
    gd=$(git -C "$S_CWD" rev-parse --git-dir 2>/dev/null || true)
    if [ -n "$gd" ]; then
      case "$gd" in /*) ;; *) gd="$S_CWD/$gd" ;; esac
      if [ -f "$gd/MERGE_HEAD" ]; then gflag="⚠️merge"
      elif [ -d "$gd/rebase-merge" ] || [ -d "$gd/rebase-apply" ]; then gflag="⚠️rebase"
      else
        def=$(git -C "$S_CWD" symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@' || true); def=${def:-main}
        if [ "$branch" != "$def" ] && [ "$branch" != "HEAD" ] && git -C "$S_CWD" rev-parse -q --verify "origin/$def" >/dev/null 2>&1; then
          [ "$(git -C "$S_CWD" rev-list --count "origin/$def..HEAD" 2>/dev/null)" = "0" ] && gflag="💀merged"
        fi
      fi
    fi
  fi
fi

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
segs_arr+=("📁 ${CYAN}${dir}${RST}")
if [ -n "$branch" ]; then
  bseg="${DIM}⎇${RST}${YEL}${branch}${RST}"
  [ -n "$gflag" ] && bseg="${bseg} ${RED}${gflag}${RST}"
  # 병렬 작업장 카운터 — 이 repo 에 연결된 추가 worktree 수 (§5.10 디스패치·잔존 감지)
  wt=$(git -C "$S_CWD" worktree list --porcelain 2>/dev/null | grep -c '^worktree ' || true)
  [ "${wt:-1}" -gt 1 ] 2>/dev/null && bseg="${bseg} ${YEL}🚧 $((wt-1))${RST}"
  segs_arr+=("$bseg")
else segs_arr+=("${DIM}⎇ no-git${RST}"); fi

# 도는 headless 파이프·루프 상세 ("N shells" 배지의 중간 단계 — 무엇이·얼마나·뭘 하는지)
jobs_lbl=$(ps -eo etime=,args= 2>/dev/null | python3 -c '
import sys, re
C = {"draft":"35","apply":"35","refine":"33","code":"32","spec":"36","research":"34","lab":"96","design":"95","ship":"32","note":"37","oncall":"37","study":"37","drill":"37"}
def paint(key, s): return f"\033[{C.get(key,'33')}m{s}\033[0m"
def mins(et):
    et = et.strip(); d = 0
    if "-" in et: d, et = et.split("-", 1)
    parts = [int(x) for x in et.split(":")]
    while len(parts) < 3: parts.insert(0, 0)
    tot = int(d) * 1440 + parts[0] * 60 + parts[1]
    return f"{tot//60}h{tot%60:02d}m" if tot >= 60 else f"{tot}m"
seen = {}
for line in sys.stdin:
    line = line.rstrip("\n")
    if not line: continue
    etime, _, args = line.lstrip().partition(" ")
    m = re.search(r"/autopilot-([a-z-]+)", args)
    if m and "claude" in args:
        key = m.group(1)
        mode = re.search(r"--mode (\w+)", args); qa = re.search(r"--qa (\w+)", args)
        tail = args[m.end():]
        full = re.sub(r"--\w+ \S+", "", tail).strip()
        desc = " ".join(full.split()[:2])
        QA = {"quick":"qck","light":"lgt","standard":"std","thorough":"thr","adversarial":"adv"}
        parts = [mode.group(1)] if mode else []
        if qa: parts.append(QA.get(qa.group(1), qa.group(1)))
        opts = "·".join(parts)
        lbl = key + (f"({opts})" if opts else "") + f" — ⏳{mins(etime)}" + (f" — {desc}" if desc else "")
    else:
        l = re.search(r"loops/(oncall|note|study|drill)", args)
        if not l: continue
        key = l.group(1); lbl = f"{key} — ⏳{mins(etime)}"
    seen.setdefault(key, paint(key, lbl))
out = list(seen.values())[:2]
if len(seen) > 2: out.append(f"+{len(seen)-2}")
print(" │ ".join(out))
' 2>/dev/null || true)

# 당직 보고 미처리 nudge (✅ 처리됨·"이상 없음" heartbeat 는 표시 안 함)
latest_oncall=$(ls -t /home/nas/user/Uihyeop/notes/oncall/*.md 2>/dev/null | head -1 || true)
if [ -n "$latest_oncall" ] && ! grep -qE '✅|이상 없음' "$latest_oncall" 2>/dev/null; then
  segs_arr+=("${YEL}📋당직${RST}")
fi
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

# 모델 │ 5h/7d 사용량+리셋 잔여시간 (stdin rate_limits = /usage 공식 값, 분모 추측 없음)
segs_arr+=("✨ ${DIM}${S_MODEL}${RST}")
u=""
[ -n "$S_5H" ] && { u="${u} ${DIM}5h${RST} $(pcol "$S_5H")${S_5H}%${RST}"; [ -n "$S_5H_RST" ] && u="${u}${DIM}(↻${S_5H_RST})${RST}"; }
[ -n "$S_7D" ] && { u="${u} ${DIM}7d${RST} $(pcol "$S_7D")${S_7D}%${RST}"; [ -n "$S_7D_RST" ] && u="${u}${DIM}(↻${S_7D_RST})${RST}"; }
[ -n "$u" ] && segs_arr+=("${u# }")

# join with 세로선 파티션
out=""; sep=" ${DIM}│${RST} "
for s in "${segs_arr[@]}"; do [ -z "$out" ] && out="$s" || out="${out}${sep}${s}"; done
printf '%s' "$out"
[ -n "${jobs_lbl:-}" ] && printf '\n%s' "${DIM}⚙ running:${RST} ${jobs_lbl}"
