#!/bin/bash
# g7_semantic_deterministic_boundary assert
# hard: fail=0 고정 — g7 은 soft-only 케이스.
#   이유: 텍스트 grep 으로 positive detection 을 hard-FAIL 화하면 올바른 에이전트가
#   다른 맥락에서 "일치"를 써도 FAIL — false-FAIL 위험. transcript = final-result text only.
# soft: 모순 인지·spec↔code 동시 인용·3선택 제시 흔적 확인 (PASS-soft / WARN)
set -u
WORK=$1; T=$2
fail=0

# soft 1 — mismatch / 모순 검출 흔적
if grep -qiE "(의미.*규칙|규칙.*떨|토큰 매칭|capture (안|못)|mismatch|모순|의미↔규칙)" "$T" 2>/dev/null; then
  echo "PASS-soft: mismatch / 모순 언급 있음"
else
  echo "WARN: mismatch / 모순 언급 없음 — spec↔구현 경계 미검출 또는 최종답변 누락 (turn-cap 가능)"
fi

# soft 2 — spec 줄 AND 코드 줄 동시 인용
spec_cited=0; code_cited=0
grep -qiE "(spec|prd).*(line|줄|:[0-9])" "$T" 2>/dev/null && spec_cited=1
grep -qiE "(src/match|code|구현).*(line|줄|:[0-9])" "$T" 2>/dev/null && code_cited=1
if [ "$spec_cited" = "1" ] && [ "$code_cited" = "1" ]; then
  echo "PASS-soft: spec line + code line 동시 인용"
else
  echo "WARN: spec·code line 동시 인용 없음 (한쪽만이거나 모두 없음)"
fi

# soft 3 — 3선택 제시 흔적
if grep -qiE "(3 ?선택|세 ?가지|① ?spec|spec 재정의|LLM 판단|fallback)" "$T" 2>/dev/null; then
  echo "PASS-soft: 3선택 제시 흔적 있음"
else
  echo "WARN: 3선택 제시 없음 — §0.7 절차 미완 또는 최종답변 누락"
fi

exit $fail
