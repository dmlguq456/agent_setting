#!/usr/bin/env bash
# SessionStart guard — spec-backed cwd 감지 시 spec-first 라우팅을 컨텍스트로 강제 주입.
# 목적: 새 세션에서 Claude 가 WORKFLOW.md §7 / CLAUDE.md §9 를 우회하고
#       ad-hoc 직접 Edit 으로 가는 것을 차단 (수동 기억 의존 → deterministic 강제).
# 등록: ~/.claude/settings.json 의 hooks.SessionStart.
# 동작: cwd 에 .claude_reports/spec/*/pipeline_state.yaml 있으면만 additionalContext 출력.
#       없으면 조용히 종료 (일반 cwd 엔 영향 0).
set -euo pipefail

spec=$(ls .claude_reports/spec/*/pipeline_state.yaml 2>/dev/null | head -1 || true)
[ -z "$spec" ] && exit 0

proj=$(basename "$(dirname "$spec")")

read -r -d '' ctx <<EOF || true
⚠️ SPEC-BACKED 프로젝트 감지 — .claude_reports/spec/${proj}/

이 cwd 의 코드·기능·수정 요청은 ad-hoc 직접 Edit 으로 끝내지 않는다. 반드시 ~/.claude/WORKFLOW.md §7 (사후 수정 라우팅) 을 탄다:

0. 손대기 전 기존 산출물 파악 (1순위) — spec/${proj}/prd.md · pipeline_state.yaml · 최근 plans/${proj}/* 를 필요에 따라 먼저 읽어 프로젝트 상태를 잡는다.
1. (필요 시) analyze 갱신 — analysis_project/code/ stale·낯선 영역이면 analyze-project --mode code 먼저.
2. spec-drift 사전 체크 (code 경유 _전_, 최우선) — prd.md 대조. spec-significant (route/schema/UI-flow/외부연동/마이그레이션) 또는 기존 drift → autopilot-spec update 모드 (prd 갱신 + _internal/versions/v{N}/ 스냅샷). drift 명확하면 자율 진행, 애매하면 사용자 확인.
3. autopilot-code 경유 — 작은 자연어 요청도 --qa quick 으로 산출물 남기며 진행 → plans/${proj}/<date>_<slug>/.

직접 Edit 허용 = 순수 typo·1줄 포맷뿐. WORKFLOW.md 를 아직 안 읽었으면 지금 Read 한다.
EOF

ctx_json=$(printf '%s' "$ctx" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":%s}}\n' "$ctx_json"
