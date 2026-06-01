#!/usr/bin/env bash
# Toggle pipeline chain-enforcement opt-in for the current project.
# 마커 .claude_reports/.pipeline 있으면 → 코드 작업이 spec+plan 순서를 강제받음
# (artifact-guard.sh §2 순서 체인). 없으면 → 코드 편집 자유(산출물 추적만).
# /track 과 별개: /track 은 세션 bypass(.untracked), /pipeline 은 프로젝트 강제 on/off.
set -euo pipefail

# 프로젝트 루트: 가까운 .claude_reports → git toplevel → cwd 순.
d="$PWD"; root=""
for _ in $(seq 1 40); do
  [ -d "$d/.claude_reports" ] && { root="$d"; break; }
  [ "$d" = "/" ] && break
  d=$(dirname "$d")
done
if [ -z "$root" ]; then
  root=$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
fi

cr="$root/.claude_reports"
marker="$cr/.pipeline"

if [ -f "$marker" ]; then
  rm -f "$marker"
  echo "🔓 pipeline 강제 OFF — 코드 편집 자유 (산출물 추적만 유지). [$root]"
else
  mkdir -p "$cr"
  touch "$marker"
  echo "🔗 pipeline 강제 ON — 코드 작업은 spec+plan 순서 전제 (research→spec→plan→code). 작은 변경도 autopilot-code --qa quick 트레일. [$root]"
fi
