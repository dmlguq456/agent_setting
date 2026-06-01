#!/usr/bin/env bash
# PreToolUse(Edit|Write|MultiEdit) — canonical 산출물의 tracking 의도를 강제.
# 모델:
#   📌tracked (기본)   — spec/ canonical 파일 직접 Edit 차단(exit 2) → autopilot-spec
#                        update 경유(자체 버전관리). 추적되지 않는 ad-hoc 수정 방지.
#   ✏️untracked (flag) — .claude_reports/.untracked (mtime<60분) 있으면 직접 편집 허용,
#                        snapshot 안 함 = 명시적 비추적. autopilot 파이프 편집도 이 flag 로 통과.
# flag 생성 = 산출물-편집 스킬 호출 직전 또는 일회성 직접 수정 시 touch .untracked (CLAUDE.md §0).
# 단일 출처: CLAUDE.md §0(0b) + WORKFLOW.md §0(b).
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

# ---- 대상 판정: spec/ 아래 canonical 파일만 ----
case "$fp" in
  */.claude_reports/spec/*) ;;
  *) exit 0 ;;
esac
case "$fp" in */_internal/*) exit 0 ;; esac
base=$(basename "$fp")
case "$base" in
  prd.md|stack.md|stack_decision.md|ship.md|api_contract.md|data_model.md|ui_flow.md) ;;
  *) exit 0 ;;
esac

# ---- 프로젝트 루트(.claude_reports 보유) 탐색 ----
d=$(dirname "$fp"); root=""
for _ in $(seq 1 40); do
  [ -d "$d/.claude_reports" ] && { root="$d"; break; }
  [ "$d" = "/" ] && break
  d=$(dirname "$d")
done
[ -z "$root" ] && exit 0
flag="$root/.claude_reports/.untracked"

# ---- untracked flag 신선도 (mtime < 3600s) ----
if [ -f "$flag" ]; then
  mod=$(stat -c %Y "$flag" 2>/dev/null || echo 0)
  [ $(( $(date +%s) - mod )) -lt 3600 ] && exit 0   # untracked 모드 → 직접 편집 허용, snapshot 없음
fi

# ---- tracked 모드(기본): ad-hoc 직접 편집 차단 ----
cat >&2 <<MSG
───────────────────────────────────────────
📌 tracked 산출물 — 직접 편집 차단 ($base)
───────────────────────────────────────────
이 파일은 추적되는 산출물이다 (CLAUDE.md §0(0b) / WORKFLOW §0(b)).
  · 정식 수정 → autopilot-spec update mode (prd 갱신 + 자체 버전 snapshot)
  · 추적 불필요한 일회성 직접 수정이면 → touch $flag (✏️untracked, TTL 60분)
───────────────────────────────────────────
MSG
exit 2
