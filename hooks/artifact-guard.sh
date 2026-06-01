#!/usr/bin/env bash
# PreToolUse(Edit|Write|MultiEdit) — 산출물 추적 + 파이프 순서 체인 강제.
# 모드: 📌tracked(기본) ↔ ⚡untracked(.claude_reports/.untracked 존재 시 → 전부 우회, /track 으로 토글).
#
# 강제 2종 (tracked 모드):
#   (1) 산출물 추적 [모든 .claude_reports 프로젝트] — spec/ canonical·plans/·documents/·
#       experiments/·user_profile/0*.md 직접 Edit 차단(exit 2) → 소유 스킬 경유.
#   (2) 순서 체인 [spec/ 있는 프로젝트 자동] — 의존 산출물 없이 다음 단계 진입 차단:
#         · 소스 코드 Edit/Write → spec/ + plans/ plan 존재 필요 (spec 없는 프로젝트는 자유).
#         · 신규 spec 작성       → research/ 또는 analysis_project/ 필요.
#         · 신규 plan 작성        → spec/ 필요.
#       spec 유무로 자동 scope — ~/.claude 설정 repo(spec 없음) 등 footgun 회피.
# 단일 출처: CLAUDE.md §0 / WORKFLOW.md §0.
set -euo pipefail

input=$(cat)
fp=$(printf '%s' "$input" | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin); ti = d.get("tool_input") or {}
    print(ti.get("file_path", "") or "")
except Exception:
    print("")
' 2>/dev/null)
[ -z "$fp" ] && exit 0
case "$fp" in */_internal/*) exit 0 ;; esac   # 기계관리 스냅샷 → 통과

# ---- 프로젝트 루트 (.claude_reports 또는 user_profile 보유) ----
d=$(dirname "$fp"); root=""
for _ in $(seq 1 40); do
  { [ -d "$d/.claude_reports" ] || [ -d "$d/user_profile" ]; } && { root="$d"; break; }
  [ "$d" = "/" ] && break
  d=$(dirname "$d")
done
[ -z "$root" ] && exit 0
cr="$root/.claude_reports"

# ---- ⚡untracked 우회 ----
flag="$cr/.untracked"; [ -d "$cr" ] || flag="$root/.untracked"
[ -f "$flag" ] && exit 0

# ---- 존재 판정 헬퍼 ----
has_spec(){ [ -f "$cr/spec/pipeline_state.yaml" ] || ls "$cr"/spec/*/pipeline_state.yaml >/dev/null 2>&1; }
has_plan(){ ls -d "$cr"/plans/*/ >/dev/null 2>&1; }
has_research(){ ls -A "$cr/research" >/dev/null 2>&1 || ls -A "$cr/analysis_project" >/dev/null 2>&1; }
block(){ printf '───────────────────────────────────────────\n⛔ %s\n   %s\n───────────────────────────────────────────\n   우회: touch %s (또는 /track) → ⚡untracked\n' "$1" "$2" "$flag" >&2; exit 2; }

base=$(basename "$fp")

# ---- (1) 산출물 추적: tracked 산출물 직접 Edit 차단 ----
case "$fp" in
  */.claude_reports/spec/*)
    case "$base" in
      prd.md|stack.md|stack_decision.md|ship.md|api_contract.md|data_model.md|ui_flow.md)
        [ -f "$fp" ] || has_research || block "신규 spec 작성 전 research/analyze 필요 ($base)" "→ autopilot-research / analyze-project 먼저"
        block "tracked 산출물 직접 편집 차단 (spec: $base)" "→ autopilot-spec update (자체 버전관리)" ;;
      *) exit 0 ;;
    esac ;;
  */.claude_reports/plans/*)
    [ -f "$fp" ] || has_spec || block "신규 plan 작성 전 spec 필요" "→ autopilot-spec 먼저"
    block "tracked 산출물 직접 편집 차단 (plans: $base)" "→ autopilot-code" ;;
  */.claude_reports/documents/*)   block "tracked 산출물 직접 편집 차단 (documents: $base)" "→ autopilot-draft / autopilot-refine" ;;
  */.claude_reports/experiments/*) block "tracked 산출물 직접 편집 차단 (experiments: $base)" "→ autopilot-lab" ;;
  */.claude/user_profile/0*.md)    block "tracked 산출물 직접 편집 차단 (user_profile: $base)" "→ analyze-user / memo --scope user" ;;
esac

# ---- (2) 순서 체인: 소스 코드 — spec 관리 프로젝트면 자동 강제 ----
case "$fp" in
  "$cr"/*) exit 0 ;;          # .claude_reports 내부 비추적 파일(research 등) → 통과
esac
has_spec || exit 0           # spec 없는 프로젝트(설정 repo·일반 repo) → 코드 편집 자유
has_plan || block "코드 작업 전 plan 필요 — 모든 코드 변경은 plans/ 트레일을 남긴다" "→ autopilot-code --qa quick (작은 변경도 경량 plan 트레일)"
exit 0
