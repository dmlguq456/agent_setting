#!/bin/bash
# Drill set runner — 지침 회귀 테스트. 사용: run.sh [case_id ...]
# 행동 판정(assert) + 컨텍스트 소모 계측(턴·토큰·비용) — g0_overhead 가 세팅 고정 세금 추세.
set -u
GOLD="${DRILL_HOME:-$HOME/.claude/loops/drill}"   # DRILL_HOME override = worktree 테스트 (production default 불변)
CLAUDE_BIN="$HOME/.local/bin/claude"
TOOLS="Bash,Read,Write,Edit,Glob,Grep,Skill,Agent,TodoWrite"
STAMP=$(date +%F_%H%M)
RESULTS="$GOLD/results/$STAMP"
mkdir -p "$RESULTS"

# 인자 파싱: --axis <축>(git/spec/memory/routing/artifact/meta) · --sample N(랜덤) · case_id...
# 기본(인자 0)=전수. 축·샘플·id 혼용 가능 (id 먼저 풀 좁히고 → axis 필터 → sample). 매번 전수
# 안 돌려도 되게: 지침 변경 축만 --axis, cron 추세는 --sample, 사람 전수는 인자 0.
AXIS=""; SAMPLE=""; LIST=""; ids=()
while [ $# -gt 0 ]; do
  case "$1" in
    --axis)   AXIS="${2:-}"; shift 2 ;;
    --sample) SAMPLE="${2:-}"; shift 2 ;;
    --list)   LIST=1; shift ;;
    *)        ids+=("$1"); shift ;;
  esac
done

# 풀: id 명시면 그것만, 아니면 전수 후보
if [ ${#ids[@]} -gt 0 ]; then
  cases=("${ids[@]}")
else
  cases=($(ls "$GOLD/cases"))
  for g in $(ls "$GOLD/cases_growing" 2>/dev/null); do cases+=("growing:$g"); done
fi

# 케이스 → CASE_DIR 해석 (axis 필터·중복 사용)
_casedir() { case "$1" in growing:*) echo "$GOLD/cases_growing/${1#growing:}" ;; *) [ -d "$GOLD/cases/$1" ] && echo "$GOLD/cases/$1" || echo "$GOLD/cases_growing/$1" ;; esac; }

# --axis 필터: config 의 AXIS= 매칭만
if [ -n "$AXIS" ]; then
  filtered=()
  for c in "${cases[@]}"; do
    a=""; cf="$(_casedir "$c")/config"; [ -f "$cf" ] && a=$(sed -n 's/^AXIS=//p' "$cf" | tr -d ' "')
    [ "$a" = "$AXIS" ] && filtered+=("$c")
  done
  cases=("${filtered[@]}")
fi

# --sample N: 풀에서 랜덤 N (주기 점검 — 전수 대신 표본). shuf 로 비결정 샘플.
if [ -n "$SAMPLE" ] && [ "$SAMPLE" -gt 0 ] 2>/dev/null && [ ${#cases[@]} -gt "$SAMPLE" ]; then
  mapfile -t cases < <(printf '%s\n' "${cases[@]}" | shuf | head -n "$SAMPLE")
fi

[ ${#cases[@]} -eq 0 ] && { echo "선택된 케이스 0 (axis='$AXIS' 매칭 없음?)"; exit 0; }
echo "drill 대상 ${#cases[@]}개${AXIS:+ [axis=$AXIS]}${SAMPLE:+ [sample=$SAMPLE]}: ${cases[*]}"
[ -n "$LIST" ] && { echo "(--list: 선별만 출력 — 실행 안 함)"; exit 0; }

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

# --- 정리: 헤드리스 케이스가 남긴 세션 detritus 제거 (projects/ 레지스트리·세션목록 오염 방지) ---
# 각 case 의 claude -p 는 cwd=/tmp/drill-* 라 projects/-tmp-drill-*-repo 세션이 등록됨 → run 후 청소.
rm -rf /tmp/drill-* 2>/dev/null || true
rm -rf "$HOME/.claude/projects/"*tmp-drill*-repo 2>/dev/null || true
echo "cleanup: drill tmp + 세션 detritus 제거"
