#!/bin/bash
# Drill set runner — 지침 회귀 테스트. 사용: run.sh [case_id ...]
# 행동 판정(assert) + 컨텍스트 소모 계측(턴·토큰·비용) — g0_overhead 가 세팅 고정 세금 추세.
set -u
GOLD="$HOME/.claude/loops/drill"
CLAUDE_BIN="$HOME/.local/bin/claude"
TOOLS="Bash,Read,Write,Edit,Glob,Grep,Skill,Agent,TodoWrite"
STAMP=$(date +%F_%H%M)
RESULTS="$GOLD/results/$STAMP"
mkdir -p "$RESULTS"

cases=("$@")
if [ ${#cases[@]} -eq 0 ]; then
  cases=($(ls "$GOLD/cases"))
  for g in $(ls "$GOLD/cases_growing" 2>/dev/null); do cases+=("growing:$g"); done
fi

declare -A verdicts metrics
for c in "${cases[@]}"; do
  grow=""
  case "$c" in growing:*) grow="(g)"; CASE_DIR="$GOLD/cases_growing/${c#growing:}" ;; *) CASE_DIR="$GOLD/cases/$c"; [ -d "$CASE_DIR" ] || CASE_DIR="$GOLD/cases_growing/$c" ;; esac
  [ -d "$CASE_DIR" ] || { echo "SKIP $c (없음)"; continue; }
  MAX_TURNS=""; TIMEOUT=1800
  [ -f "$CASE_DIR/config" ] && . "$CASE_DIR/config"

  WORK=$(mktemp -d "/tmp/drill-$c-XXXX")
  echo "▶ $c (work=$WORK)"
  bash "$CASE_DIR/fixture.sh" "$WORK" || { verdicts[$c]="FIXTURE-ERR"; continue; }

  T="$RESULTS/$c.transcript.txt"
  J="$RESULTS/$c.json"
  ( cd "$WORK/repo" && timeout "$TIMEOUT" "$CLAUDE_BIN" -p "$(cat "$CASE_DIR/prompt.md")" \
      --allowedTools "$TOOLS" --output-format json ${MAX_TURNS:+--max-turns "$MAX_TURNS"} ) \
      > "$J" 2> "$RESULTS/$c.stderr.txt"
  rc=$?

  # JSON → transcript(result 본문) + 계측 (turns|in_tok|out_tok|cost)
  metrics[$c]=$(python3 - "$J" "$T" <<'PYEOF'
import json, sys
try: d = json.load(open(sys.argv[1]))
except Exception: d = {}
open(sys.argv[2], 'w').write(d.get('result', '') or '')
u = d.get('usage', {})
tin = u.get('input_tokens',0)+u.get('cache_creation_input_tokens',0)+u.get('cache_read_input_tokens',0)
print(f"{d.get('num_turns','?')}|{tin}|{u.get('output_tokens',0)}|{round(d.get('total_cost_usd') or 0,3)}")
PYEOF
)

  if out=$(bash "$CASE_DIR/assert.sh" "$WORK" "$T" 2>&1); then
    verdicts[$c]="PASS$grow"
  else
    verdicts[$c]="FAIL$grow"
  fi
  echo "$out" | tee "$RESULTS/$c.assert.txt"
  echo "  → ${verdicts[$c]} (claude exit $rc, ${metrics[$c]})"

  # FAIL 자동 진단 — 원인 추정 + 수정안 초안까지 (적용은 사용자 서명)
  if [ "${verdicts[$c]}" = "FAIL" ]; then
    timeout 600 "$CLAUDE_BIN" -p "drill set 케이스 FAIL 진단. 케이스 정의: $CASE_DIR (prompt.md=사용자 발화, assert.sh=판정). assert 출력: $RESULTS/$c.assert.txt. transcript: $T. fixture 결과물: $WORK.
이 자료를 읽고 (1) 위반 행동이 정확히 무엇이었나 (2) 어느 지침이 닿지 않았거나 모호했나 (3) 수정안 — 지침 diff 초안 또는 hook 승격 제안 중 택1, 적용 명령 포함 — 을 $RESULTS/$c.diagnosis.md 에 한국어로 간결히 작성하라. 지침 파일을 직접 수정하지 말 것 (진단·제안만)." \
      --allowedTools "Bash,Read,Glob,Grep,Write" --max-turns 25 >> "$RESULTS/$c.diagnosis.log" 2>&1
    [ -f "$RESULTS/$c.diagnosis.md" ] && echo "  진단서: $RESULTS/$c.diagnosis.md"
  fi
done

{
  echo "# Drill run $STAMP"
  echo
  echo "| case | verdict | turns | in_tok | out_tok | cost\$ |"
  echo "|---|---|---|---|---|---|"
  for c in "${cases[@]}"; do
    IFS='|' read -r mt mi mo mc <<< "${metrics[$c]:-?|?|?|?}"
    echo "| $c | ${verdicts[$c]:-?} | $mt | $mi | $mo | $mc |"
  done
} | tee "$RESULTS/summary.md"

# 추세 누적 (지침 부풀림 감시 — 특히 g0_overhead 의 in_tok)
for c in "${cases[@]}"; do
  echo "$STAMP,$c,${verdicts[$c]:-?},${metrics[$c]:-?|?|?|?}" | tr '|' ',' >> "$GOLD/metrics.csv"
done

# 옵션: 응답규율 채점 pass (약자 풀이·번역체·약속-행동) — transcript 일괄 LLM 채점
if [ "${RUN_JUDGE:-0}" = "1" ]; then
  "$CLAUDE_BIN" -p "$(cat "$GOLD/judge.md")

대상 transcript 디렉토리: $RESULTS (각 *.transcript.txt)" \
    --allowedTools "Read,Glob,Grep,Write" > "$RESULTS/judge.md" 2>&1
  echo "judge → $RESULTS/judge.md"
fi
