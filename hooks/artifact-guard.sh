#!/usr/bin/env bash
# PreToolUse(Edit|Write|MultiEdit) — 산출물 추적 + 파이프 순서 체인 강제.
# 모드: 📌tracked(기본) ↔ ⚡untracked(.claude_reports/.untracked.<session_id> 존재 시 → 전부 우회).
#       세션별 flag — 한 레포에 여러 세션 띄워도 격리. /track 토글, SessionStart 가 stale GC.
#
# 강제 2종 (tracked 모드):
#   (1) 산출물 추적 [모든 .claude_reports 프로젝트] — spec/ canonical·plans/·documents/·
#       experiments/ 직접 Edit 차단(exit 2) → 소유 스킬 경유.
#       (user_profile/0*.md 는 convention — agent read-only + analyze-user/post-it 권장, hook 비강제.)
#   (2) 순서 체인 [spec/ 있는 프로젝트 자동] — 의존 산출물 없이 다음 단계 진입 차단:
#         · 소스 코드 Edit/Write → spec/ + plans/ plan 존재 필요 (spec 없는 프로젝트는 자유).
#         · 신규 spec 작성       → research/ 또는 analysis_project/ 필요.
#         · 신규 plan 작성        → spec/ 필요.
#         · 신규 문서(documents) 작성 → research/ 또는 analysis_project/ 필요 (문서 트랙 대칭).
#       spec 유무로 자동 scope — ~/.claude 설정 repo(spec 없음) 등 footgun 회피.
# 단일 출처: CLAUDE.md §0 / WORKFLOW.md §0.
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
[ -z "$root" ] && exit 0
cr="$root/.claude_reports"

# ---- ⚡untracked 우회 (세션별 flag .untracked.<session_id> — 동시 세션 격리) ----
flagbase="$cr/.untracked"; [ -d "$cr" ] || flagbase="$root/.untracked"
[ -n "$sid" ] && flag="$flagbase.$sid" || flag="$flagbase"
[ -f "$flag" ] && exit 0

# ---- 존재 판정 헬퍼 ----
has_spec(){ [ -f "$cr/spec/pipeline_state.yaml" ] || ls "$cr"/spec/*/pipeline_state.yaml >/dev/null 2>&1; }
has_plan(){ ls -d "$cr"/plans/*/ >/dev/null 2>&1; }
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

# ---- (2) 순서 체인: 소스 코드 — spec 관리 프로젝트면 자동 강제 ----
case "$fp" in
  "$cr"/*) exit 0 ;;          # .claude_reports 내부 비추적 파일(research 등) → 통과
esac
has_spec || exit 0           # spec 없는 프로젝트(설정 repo·일반 repo) → 코드 편집 자유
has_plan || block "코드 작업 전 plan 필요 — 모든 코드 변경은 plans/ 트레일을 남긴다" "→ autopilot-code --qa quick (작은 변경도 경량 plan 트레일)"
exit 0
