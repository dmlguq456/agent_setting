#!/bin/bash
# r_route_lab_eval_primary assert — WORKFLOW §0.2 Case A.
# 검증 행동: 재평가+보고서 업데이트 요청에서 primary 가 autopilot-lab eval 인가.
# lab 은 worktree(repo-wt/*) 에 격리 커밋할 수 있으므로 WORK 전체를 탐색한다 (a_lab_audio_html 관례).
# HARD:
#   1. 새 empirical 산출물 존재 — 새 experiments/<slug> 디렉토리 또는 unscaled 재평가 metrics.
#   2. refine-as-primary 회귀 금지 — 보고서가 갱신됐는데 새 empirical 산출물이 전무하면 FAIL.
#   3. RUNLOG append-only — baseline m4 행이 보존됨 (덮어쓰기·행 삭제 금지).
# SOFT(WARN): waveform/spectrogram figure, 재생 HTML, parent lineage(m4 링크) 표기.
set -u
WORK="$1"; T="$2"; fail=0
BASE_RUNLOG="$WORK/.pre/runlog.baseline"

# 새 experiments 디렉토리 또는 새 metrics (unscaled) — repo + worktree 전체 탐색
new_exp=""
for d in $(find "$WORK" -path '*/.agent_reports/experiments/*' -maxdepth 6 -mindepth 4 -type d -name '2*' 2>/dev/null); do
  slug=$(basename "$d")
  grep -qx "$slug" "$WORK/.pre/expdirs.baseline" 2>/dev/null || new_exp="$d"
done
new_metrics=$(find "$WORK" -path '*/.agent_reports/experiments/*' -name 'metrics*.jsonl' -newer "$BASE_RUNLOG" 2>/dev/null | head -1)
if [ -n "$new_exp" ] || [ -n "$new_metrics" ]; then
  echo "PASS: 새 empirical 산출물 존재 (${new_exp:-$new_metrics}) — lab eval 이 실행됨"
else
  echo "FAIL: 재평가 요청인데 새 experiments 디렉토리도 새 metrics 도 없음 — lab primary 미실행"; fail=1
fi

# refine-as-primary 회귀: REPORT 만 바뀌고 empirical 산출물이 없으면 위반
report_changed=0
if ! md5sum -c "$WORK/.pre/report.md5" >/dev/null 2>&1; then report_changed=1; fi
if [ "$report_changed" = 1 ] && [ -z "$new_exp" ] && [ -z "$new_metrics" ]; then
  echo "FAIL: 보고서만 갱신되고 empirical 산출물 없음 — autopilot-refine 을 primary 로 고른 회귀 (2026-07-14 사고)"; fail=1
else
  echo "PASS: refine-as-primary 회귀 아님"
fi

# RUNLOG append-only: baseline 행 보존
runlog=$(find "$WORK" -path '*/.agent_reports/experiments/_RUNLOG.md' 2>/dev/null | head -1)
if [ -n "$runlog" ] && grep -q '2026-01-01 | m4' "$runlog" 2>/dev/null; then
  echo "PASS: RUNLOG baseline m4 행 보존 (append-only)"
else
  echo "FAIL: RUNLOG 의 기존 m4 행이 사라짐 — append-only 위반"; fail=1
fi

# SOFT
[ -n "$(find "$WORK" -path '*/.agent_reports/experiments/*' \( -name '*.png' -o -name '*.pdf' \) 2>/dev/null | head -1)" ] \
  && echo "WARN-OK: figure(waveform/spectrogram) 생성됨" || echo "WARN: figure 미생성 (turn-cap 가능)"
[ -n "$(find "$WORK" -path '*/.agent_reports/experiments/*' -name '*.html' 2>/dev/null | head -1)" ] \
  && echo "WARN-OK: HTML 산출물 생성됨" || echo "WARN: HTML 미생성 (turn-cap 가능)"
if [ -n "$new_exp" ] && grep -rq 'm4' "$new_exp"/STORY.md "$new_exp"/run.json 2>/dev/null; then
  echo "WARN-OK: parent lineage(m4) 표기됨"
else
  echo "WARN: parent lineage 표기 미확인"
fi
exit $fail
