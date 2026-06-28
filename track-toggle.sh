#!/usr/bin/env bash
# Toggle artifact-guard mode for the project containing cwd — 세션별(.untracked.<session_id>).
# 📌tracked (flag 없음) ↔ ⚡untracked. 한 레포에 여러 세션 띄워도 각 세션 독립.
# 이 세션 동안만 유지 (SessionStart 가 오래된 flag GC, 세션 종료 후 무의미해짐).
# /track slash command 에서 호출. 단독 실행도 가능.
set -euo pipefail

d="$PWD"; root=""; reports_dir=""
for _ in $(seq 1 40); do
  [ -d "$d/.agent_reports" ] && { root="$d"; reports_dir=".agent_reports"; break; }
  [ -d "$d/.claude_reports" ] && { root="$d"; reports_dir=".claude_reports"; break; }
  [ "$d" = "/" ] && break
  d=$(dirname "$d")
done
[ -z "$root" ] && { echo "⚠️  상위 트리에 .agent_reports/.claude_reports 가 없어요 — 토글 대상 프로젝트가 아닙니다."; exit 0; }

sid="${CLAUDE_CODE_SESSION_ID:-}"
[ -n "$sid" ] && f="$root/$reports_dir/.untracked.$sid" || f="$root/$reports_dir/.untracked"
if [ -f "$f" ]; then
  rm -f "$f"
  echo "📌 tracked 모드 — 이 세션, 산출물 직접 편집 차단·코드는 spec+plan 전제."
else
  touch "$f"
  echo "⚡ untracked 모드 — 이 세션만 전부 우회(직접 편집 허용·snapshot 없음). [$root]"
fi
