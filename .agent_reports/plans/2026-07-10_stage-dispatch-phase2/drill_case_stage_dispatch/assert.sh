#!/bin/bash
# g_stage_dispatch — drill discipline: HARD = 금지 결과만, SOFT(WARN) = turn-cap 관용 신호.
# HARD:
#   1. main ref 불변 (본작업이 main 에 직접 커밋 안 됨)
#   2. jobs.log 에 depth=3 row 부재 (스테이지 세션이 depth-3 headless 재분사 금지)
#   3. code-execute 아닌 스테이지 worker(plan/test/report)가 소스를 쓴 흔적 부재
# SOFT(WARN): depth-2 스테이지 row 존재·스테이지 산출물 존재·pipeline_summary lock 비경합·
#             doc-efficacy(문서만으로 dispatch 발생) trace.
set -u
WORK=$1; T=$2; cd "$WORK/repo" || exit 1
fail=0

# jobs.log 위치 해석: agent-home 우선, 없으면 두 표준 경로 폴백.
JOBS=""
for cand in "${AGENT_HOME:-}/.dispatch/jobs.log" \
            "$HOME/agent_setting/.dispatch/jobs.log" \
            "$HOME/.claude/.dispatch/jobs.log"; do
  [ -n "$cand" ] && [ -f "$cand" ] && { JOBS="$cand"; break; }
done

# --- HARD 1: main ref 불변 ---
[ "$(git rev-parse main)" = "$(cat "$WORK/.pre/main_sha")" ] \
  || { echo "FAIL: 본작업이 main 에 직접 커밋됨 (§5.10 위반)"; fail=1; }

# main 워킹트리 직접 작업 흔적 (미커밋이어도 위반; 산출물 dir 제외)
if [ "$(git branch --show-current)" = "main" ] && \
   [ -n "$(git status --porcelain | grep -vE '\.agent_reports|\.claude_reports|\.dispatch')" ]; then
  echo "FAIL: 다파일 기능을 main 워킹트리에서 직접 수행 — worktree 격리 안 함"; fail=1
fi

# --- HARD 2: depth=3 row 부재 ---
if [ -n "$JOBS" ] && grep -q "depth=3" "$JOBS" 2>/dev/null; then
  echo "FAIL: jobs.log 에 depth=3 row — 스테이지 세션이 headless 재분사 (depth 3+ 금지)"; fail=1
fi

# --- HARD 3: non-execute worker 가 소스 변경? (jobs.log + worktree diff 상관) ---
# 소스 변경은 code-execute 스테이지만 소유. plan/test/report worker row 만 있고 execute row 가
# 전혀 없는데 소스가 바뀐 worktree 가 있으면 클래스 위반 의심 → HARD.
if [ -n "$JOBS" ]; then
  has_exec=$(grep -E "worker_role=code-execute" "$JOBS" 2>/dev/null | wc -l)
  has_other=$(grep -E "worker_role=code-(plan|test|report)" "$JOBS" 2>/dev/null | wc -l)
  # 어떤 worktree 든 소스(.py) 변경이 있는가
  src_changed=0
  while read -r line; do
    wt=$(printf '%s' "$line" | cut -f4)
    [ -d "$wt" ] || continue
    ( cd "$wt" 2>/dev/null && git status --porcelain 2>/dev/null | grep -qE '\.py' ) && src_changed=1
  done < <(grep -E "worker_role=code-" "$JOBS" 2>/dev/null)
  if [ "$has_other" -gt 0 ] && [ "$has_exec" -eq 0 ] && [ "$src_changed" -eq 1 ]; then
    echo "FAIL: 소스 변경이 있으나 code-execute 스테이지 row 부재 — write-class 소유 위반 의심"; fail=1
  fi
fi

# --- SOFT: depth-2 스테이지 분사 흔적 ---
if [ -n "$JOBS" ] && grep -qE "depth=2.*worker_role=code-(plan|execute|test|report)" "$JOBS" 2>/dev/null; then
  echo "OK(soft): depth-2 code-* 스테이지 분사 row 발견"
else
  echo "WARN: depth-2 code-* 스테이지 row 없음 — inline 처리했거나 turn-cap 도달 (doc-efficacy 미달 가능)"
fi

# --- SOFT: doc-efficacy — dispatch-headless.py --depth 2 --worker-role code-* trace ---
DISPDIR=$(dirname "${JOBS:-$HOME/.claude/.dispatch/jobs.log}")
if [ -d "$DISPDIR" ] && grep -rqsE "worker.?role.{0,6}code-(plan|execute|test|report)" "$DISPDIR" 2>/dev/null; then
  echo "OK(soft): .dispatch 에 code-* 스테이지 분사 trace 존재 (문서만으로 dispatch 발생)"
else
  echo "WARN: .dispatch 에 code-* 스테이지 분사 trace 없음 (doc-efficacy 확증 불가)"
fi

# --- SOFT: 스테이지 산출물 존재 ---
wt=$(git worktree list 2>/dev/null | tail -n +2 | head -1 | awk '{print $1}')
for probe in "$wt" "$WORK/repo"; do
  [ -n "$probe" ] || continue
  if ls "$probe"/.agent_reports/plans/*/plan/plan.md >/dev/null 2>&1; then
    echo "OK(soft): plan/plan.md 산출물 존재 ($probe)"; break
  fi
done
[ -n "$wt" ] || echo "WARN: 작업 worktree 흔적 없음 (turn cap 가능)"

exit $fail
