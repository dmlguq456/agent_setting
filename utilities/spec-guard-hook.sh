#!/usr/bin/env bash
# SessionStart router injection — WORKFLOW.md 라우팅 코어를 매 세션 컨텍스트로 주입.
# 목적: 수동 Read 의존 제거 + 하드 순서 게이트(research/analyze → spec → code)와
#       동일-스킬-수정 불변식을 ad-hoc Edit 우회로부터 차단.
# 등록: ~/.claude/settings.json 의 hooks.SessionStart.
# 동작 2단:
#   (1) 프로젝트 cwd (git work tree 또는 .claude_reports/ 보유) 면 WORKFLOW 라우팅 코어 주입.
#   (2) 그중 spec-backed (spec/pipeline_state.yaml) 면 §7 사후 수정 디테일 추가.
# 단일 출처: 글로벌 CLAUDE.md §0 + WORKFLOW.md §0/§7.
set -euo pipefail

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

# 프로젝트 아닌 scratch/home dir 면 조용히 종료.
[ "$is_project" = "0" ] && exit 0

# ---- (1) WORKFLOW 라우팅 코어 (항상) ----
read -r -d '' ctx <<'EOF' || true
🧭 WORKFLOW 단일 라우터 — 작업 흐름 불변식 (~/.claude/WORKFLOW.md §0, CLAUDE.md §0)

모든 작업 발화는 WORKFLOW §2 작업-본질 매핑을 먼저 거친다. 직접 처리·codex 플러그인·빌트인 스킬도 WORKFLOW 가 배치하는 자리에서만 쓴다.

■ 하드 순서 게이트 (앞 단계 산출물 없이 다음 단계 진입 금지):
  [코드]  research / analyze-project(code) → autopilot-spec (spec/) → autopilot-code (plans/)
  [문서]  research / analyze-project(paper·doc) → autopilot-draft → autopilot-refine
  · spec 없이 코드 작업 X — 코드 요청인데 spec/ 없으면 autopilot-spec 먼저.
  · 사전 산출물 없이 spec X — research/ 또는 analysis_project/ 없으면 그것 먼저.
  · throwaway 1 회성만 예외 (반복되면 spec 승격).

■ 동일 스킬 수정 = 버전 트래킹: 산출물은 그것을 만든 스킬로만 수정한다.
  spec→autopilot-spec update / plans→autopilot-code / documents→autopilot-draft·refine / experiments→autopilot-lab.
  추적 산출물 직접 Edit 은 artifact-guard hook 이 차단(exit 2). 예외 = .untracked touch(또는 /track) → 그 세션만 직접 편집(snapshot 없음).
EOF

# ---- (2) spec-backed 면 §7 디테일 추가 ----
if [ -n "$spec_root" ]; then
  proj=$(basename "$spec_root")
  read -r -d '' spec_ctx <<EOF || true

⚠️ SPEC-BACKED 프로젝트 감지 — ${proj}/.claude_reports/spec/ → WORKFLOW §7 (사후 수정 라우팅) 필수:
0. 손대기 전 기존 산출물 파악 — spec/prd.md · pipeline_state.yaml · 최근 plans/* 를 먼저 읽어 상태 파악.
1. (필요 시) analyze 갱신 — analysis_project/code/ stale·낯선 영역이면 analyze-project --mode code 먼저.
2. spec-drift 사전 체크 (code 경유 _전_) — prd.md 대조. spec-significant(route/schema/UI-flow/외부연동/마이그레이션) 또는 기존 drift → autopilot-spec update (prd + _internal/versions/v{N}/ snapshot). 명확하면 자율 진행, 애매하면 사용자 확인.
3. autopilot-code 경유 — 작은 자연어 요청도 --qa quick 으로 plans/<date>_<slug>/ 에 산출물 남김.
EOF
  ctx="${ctx}${spec_ctx}"
fi

ctx_json=$(printf '%s' "$ctx" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":%s}}\n' "$ctx_json"
