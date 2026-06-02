#!/usr/bin/env bash
# workflow-guard-hook — 모드 신호 + flag GC. (WORKFLOW·post-it 읽기는 _지침_ 이 담당, hook 주입 X.)
#   UserPromptSubmit: 매 프롬프트 _모드 신호_ (cr_root 프로젝트) — 📌tracked(WORKFLOW 따름·skill 경유)
#                     vs ⚡untracked(면제·자유). instruction 이 못 보는 _런타임 flag 상태_ 를 Claude 에 전달.
#   SessionStart    : 잔여 ⚡untracked flag GC 만.
# WORKFLOW.md(라우팅 계약)·post-it(세션 연속성) 은 CLAUDE.md 부트스트랩+도메인 트리거 _지침_ 으로 Read.
# 등록: ~/.claude/settings.json 의 hooks.SessionStart + hooks.UserPromptSubmit.
set -euo pipefail

input=$(cat 2>/dev/null || true)
eval "$(printf '%s' "$input" | python3 -c '
import json, sys, shlex
try: d = json.load(sys.stdin)
except Exception: d = {}
print("EVENT="+shlex.quote(d.get("hook_event_name","") or ""))
print("SID="+shlex.quote(d.get("session_id","") or ""))
' 2>/dev/null || true)"
EVENT="${EVENT:-}"; SID="${SID:-}"

# ---- 프로젝트 cwd 판정 (git work tree 또는 .claude_reports/ 보유) ----
is_project=0
if command -v git >/dev/null 2>&1 && git -C "$PWD" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  is_project=1
fi

# cwd 에서 위로 올라가며 .claude_reports/ 와 spec-backed 루트 탐색.
d="$PWD"; cr_root=""; spec_root=""
for _ in $(seq 1 40); do
  [ -z "$cr_root" ] && [ -d "$d/.claude_reports" ] && cr_root="$d"
  if [ -z "$spec_root" ]; then
    if [ -f "$d/.claude_reports/spec/pipeline_state.yaml" ] || ls "$d"/.claude_reports/spec/*/pipeline_state.yaml >/dev/null 2>&1; then
      spec_root="$d"
    fi
  fi
  { [ "$d" = "/" ] || [ "$d" = "$HOME" ]; } && break
  d=$(dirname "$d")
done
[ -n "$cr_root" ] && is_project=1

# ⚡untracked 세션별 flag 판정.
untracked=0
if [ -n "$cr_root" ]; then
  flag="$cr_root/.claude_reports/.untracked"; [ -n "$SID" ] && flag="$flag.$SID"
  [ -f "$flag" ] && untracked=1
fi

emit() {  # $1 = hookEventName, stdin = ctx 본문
  local ctx j
  ctx=$(cat)
  j=$(printf '%s' "$ctx" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
  printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":%s}}\n' "$1" "$j"
}

# ============================================================
# UserPromptSubmit — 매 프롬프트 thin reminder (tracked 일 때만)
# ============================================================
if [ "$EVENT" = "UserPromptSubmit" ]; then
  # .claude_reports 없음 → tracked/untracked 토글 자체가 무관 → 침묵.
  [ -z "$cr_root" ] && exit 0
  # 모드를 _양쪽 다 명시_ — Claude 가 "WORKFLOW 를 지킬지" 를 매 프롬프트 positive 하게 결정.
  if [ "$untracked" = "1" ]; then
    touch "$flag" 2>/dev/null || true   # heartbeat — 활성 세션이면 mtime 갱신 → GC 가 _비활성_ 만 지움 (장기 세션 안전)
    emit UserPromptSubmit <<'EOF'
🧭 ⚡untracked — WORKFLOW 면제. 산출물·소스 코드 직접 편집 자유 (추적·trail 없음). 정식 파이프로 돌리려면 /track.
EOF
  else
    spec_tail=""
    [ -n "$spec_root" ] && spec_tail=" spec-backed → 수정·기능은 WORKFLOW §7 (spec-drift 체크 → autopilot-code)."
    emit UserPromptSubmit <<EOF
🧭 📌tracked — WORKFLOW(§0/§7) 따름. 작업(코드/스펙/문서/실험)이면 직접 편집 말고 autopilot-* skill 경유; 산출물은 만든 스킬로. 단발·throwaway 만 직접.${spec_tail}
EOF
  fi
  exit 0
fi

# ============================================================
# SessionStart (default) — 1일+ _비활성_ ⚡untracked flag GC.
# flag mtime = heartbeat: 활성 세션은 UserPromptSubmit 마다 touch 로 갱신 → 1일 넘게 켜둔
# 장기 세션의 flag 는 안 지워짐. mtime +1440 = "마지막 활동 1일 전" = 크래시·종료된 세션 잔재.
# WORKFLOW.md·post-it 읽기는 _지침_ (CLAUDE.md 부트스트랩 + 도메인 트리거) 이 담당 — hook 주입 X.
# ============================================================
if [ -n "$cr_root" ]; then
  find "$cr_root/.claude_reports" -maxdepth 1 -name '.untracked.*' -mmin +1440 -delete 2>/dev/null || true
fi
exit 0
