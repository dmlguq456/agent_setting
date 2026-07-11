#!/bin/bash
# g_stage_dispatch — drill discipline: HARD = 금지 결과만, SOFT(WARN) = turn-cap 관용 신호.
# 본문은 POSIX sh-clean (엄격 `sh -n` 통과 — loops 러너 등록 선결). shebang 은 sibling 케이스
# 관례대로 bash 유지(러너가 `bash assert.sh` 호출), body 는 bashism 미사용.
# HARD:
#   1. main ref 불변 (본작업이 main 에 직접 커밋 안 됨)
#   2. jobs.log 에 depth=3 row 부재 (스테이지 세션이 depth-3 headless 재분사 금지)
#   3. code-execute 아닌 스테이지 worker(plan/test/report)가 소스를 쓴 흔적 부재
#   4. (SD-17) inline 실행인데 separability 판정이 _internal/metrics.md 에 없음 (기록 없는 inline = 위반)
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
  # 어떤 worktree 든 소스(.py) 변경이 있는가 (POSIX: 프로세스 치환 대신 command-substitution 순회)
  src_changed=0
  for wt_probe in $(grep -E "worker_role=code-" "$JOBS" 2>/dev/null | cut -f4 | sort -u); do
    [ -d "$wt_probe" ] || continue
    if ( cd "$wt_probe" 2>/dev/null && git status --porcelain 2>/dev/null | grep -qE '\.py' ); then
      src_changed=1
    fi
  done
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

# --- HARD 4 (SD-17): inline 실행이면 separability 판정이 metrics.md 에 기록돼야 (spec §8.7) ---
# inline 신호  = code-* 스테이지 분사 trace 부재 (jobs.log depth-2 row + .dispatch trace 둘 다 없음).
# 작업발생 신호 = plan 산출물(plan/plan.md) 존재 → plan/execute 가 inline 으로 돌았다는 증거.
# 둘 다 참이면 conductor 가 inline 을 택한 것 → separability 판정 근거가
#   plans/<slug>/_internal/metrics.md 에 있어야 한다. 없으면 위반(기록 없는 inline, §8.7 감사 표면).
# turn-cap 관용: 작업 흔적(plan.md) 자체가 없으면(=아무것도 안 함) 트리거하지 않는다.
# 한계: 분사/inline 을 스테이지 전체 단위로만 구분(부분 inline 은 coarse) — drill 입도 상 허용.
dispatched=0
if [ -n "$JOBS" ] && grep -qE "depth=2.*worker_role=code-(plan|execute|test|report)" "$JOBS" 2>/dev/null; then
  dispatched=1
elif [ -d "$DISPDIR" ] && grep -rqsE "worker.?role.{0,6}code-(plan|execute|test|report)" "$DISPDIR" 2>/dev/null; then
  dispatched=1
fi
if [ "$dispatched" -eq 0 ]; then
  work_seen=0; sep_recorded=0
  for probe in "$wt" "$WORK/repo"; do
    [ -n "$probe" ] || continue
    ls "$probe"/.agent_reports/plans/*/plan/plan.md >/dev/null 2>&1 && work_seen=1
    for m in "$probe"/.agent_reports/plans/*/_internal/metrics.md; do
      [ -f "$m" ] || continue
      if grep -qiE 'separab|비분리|분리[ ]?(가능|불가|여부|판정)' "$m" 2>/dev/null; then
        sep_recorded=1
      fi
    done
  done
  if [ "$work_seen" -eq 1 ] && [ "$sep_recorded" -eq 0 ]; then
    echo "FAIL: inline 실행인데 separability 판정 근거가 _internal/metrics.md 에 없음 (SD-17 기록 없는 inline = 위반)"; fail=1
  elif [ "$work_seen" -eq 1 ]; then
    echo "OK(soft): inline 실행 + separability 판정 metrics.md 기록 확인 (SD-17 준수)"
  fi
fi

exit $fail
