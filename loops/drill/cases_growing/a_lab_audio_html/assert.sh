#!/bin/bash
# a_lab_audio_html assert
# 검증 행동: 오디오 eval 결과를 lab 이 재생 가능한 HTML(<audio> 임베드)로 보고하는가
#   (SKILL line 445/469: audio→HTML — md 는 <audio> 차단, figure 만이면 md 인라인). craft.
# hard: experiments/ 하위 report HTML 에 <audio> 태그 존재.
WORK="$1"; T="$2"; REPO="$WORK/repo"
fail=0
EXP="$REPO/.claude_reports/experiments"
htmlaudio=$(grep -rliE '<audio' "$EXP" 2>/dev/null | head -1)
if [ -n "$htmlaudio" ]; then
  echo "PASS: <audio> 재생 HTML 보고서 ($(basename "$htmlaudio"))"
else
  echo "FAIL: 오디오 결과인데 <audio> 재생 HTML 없음 — audio→HTML 관습 누락 (SKILL line 469)"; fail=1
fi
[ -n "$(find "$EXP" -name '*.html' 2>/dev/null | head -1)" ] && echo "WARN-OK: HTML 보고서 생성됨" || echo "WARN: HTML 보고서 자체 없음 (md 만 만들었거나 미완)"
exit $fail
