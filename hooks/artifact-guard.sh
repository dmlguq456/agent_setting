#!/usr/bin/env bash
# PreToolUse(Edit|Write|MultiEdit) — .claude_reports 산출물의 _생성 순서_ 만 강제.
# 모드: 📌tracked(기본) ↔ ⚡untracked(.claude_reports/.untracked.<session_id> 존재 시 → 전부 우회).
#       /track 토글, SessionStart 가 stale flag GC.
#
# 강제 (tracked): 신규 산출물은 앞 단계 산출물이 있어야 _만들_ 수 있다 (없으면 exit 2):
#   · 신규 spec(prd/stack/ship/api_contract/data_model/ui_flow) ← research/ 또는 analysis_project/
#   · 신규 plan ← spec/
#   · 신규 documents ← research/ 또는 analysis_project/
# 비차단 (convention): 기존 산출물 _편집_ · 소스 코드 · experiments/ · user_profile/ (README·assets·_internal).
#   소유 스킬 경유·코드의 autopilot-code 유도는 workflow-guard-hook 라우팅 리마인더 + convention.
# 단일 출처: WORKFLOW.md §0 (tracked 계약).
set -euo pipefail

input=$(cat)
eval "$(printf '%s' "$input" | python3 -c '
import sys, json, shlex
try: d = json.load(sys.stdin)
except Exception: d = {}
ti = d.get("tool_input") or {}
print("FP="+shlex.quote(ti.get("file_path","") or ""))
print("SID="+shlex.quote(d.get("session_id","") or ""))
' 2>/dev/null)"
fp="${FP:-}"; sid="${SID:-}"
[ -z "$fp" ] && exit 0
case "$fp" in */_internal/*) exit 0 ;; esac   # 기계관리 스냅샷 → 통과

# ---- 프로젝트 루트 (.claude_reports 보유) ----
d=$(dirname "$fp"); root=""
for _ in $(seq 1 40); do
  [ -d "$d/.claude_reports" ] && { root="$d"; break; }
  [ "$d" = "/" ] && break
  d=$(dirname "$d")
done
# .claude_reports 디렉토리가 아직 없어도, 경로가 .../.claude_reports/... 면 그 prefix 로 root 유도
# — 프로젝트 _최초_ 산출물 1건이 순서 게이트를 건너뛰던 구멍을 메움 (codex #8, 2026-06-22).
if [ -z "$root" ]; then
  case "$fp" in */.claude_reports/*) root="${fp%%/.claude_reports/*}" ;; esac
fi
[ -z "$root" ] && exit 0
cr="$root/.claude_reports"

# ---- ⚡untracked 우회 (세션별 flag .untracked.<session_id> — 동시 세션 격리) ----
flagbase="$cr/.untracked"; [ -d "$cr" ] || flagbase="$root/.untracked"
[ -n "$sid" ] && flag="$flagbase.$sid" || flag="$flagbase"
[ -f "$flag" ] && exit 0

# ---- 존재 판정 헬퍼 ----
has_spec(){ [ -f "$cr/spec/pipeline_state.yaml" ] || ls "$cr"/spec/*/pipeline_state.yaml >/dev/null 2>&1; }
has_research(){ ls -A "$cr/research" >/dev/null 2>&1 || ls -A "$cr/analysis_project" >/dev/null 2>&1; }
block(){ printf '───────────────────────────────────────────\n⛔ %s\n   %s\n───────────────────────────────────────────\n   우회: /track → ⚡untracked (이 세션만)\n' "$1" "$2" >&2; exit 2; }

base=$(basename "$fp")

# ---- (1) 생성 순서 게이트: 신규 산출물은 앞 단계 산출물이 있어야 _만들_ 수 있다 ----
# 기존 산출물 _편집_ 은 차단하지 않는다 (소유 스킬 경유는 convention — hook 이 소유 스킬과
# 직접편집을 구분 못 하고, 막으면 정당한 autopilot-spec update 도 막혀 세션째 untrack 유발).
# 막는 건 _순서 위반_ 뿐: 앞 단계 없이 다음 산출물을 새로 만드는 것.
case "$fp" in
  */.claude_reports/spec/*)
    case "$base" in
      prd.md|stack.md|stack_decision.md|ship.md|api_contract.md|data_model.md|ui_flow.md)
        [ -f "$fp" ] || has_research || block "신규 spec 작성 전 research/analyze 필요 ($base)" "→ autopilot-research / analyze-project 먼저" ;;
    esac ;;
  */.claude_reports/plans/*)
    [ -f "$fp" ] || has_spec || block "신규 plan 작성 전 spec 필요" "→ autopilot-spec 먼저" ;;
  */.claude_reports/documents/*)
    [ -f "$fp" ] || has_research || block "신규 문서 작성 전 research/analyze 필요 ($base)" "→ autopilot-research / analyze-project 먼저" ;;
esac

# 소스 코드 편집은 hook 으로 막지 않는다 — autopilot-code 경유는 UserPromptSubmit 라우팅
# 리마인더 + convention (예전 "code←plan floor" 은 stale 플랜 하나로도 통과해 실효 없어 제거).
exit 0
