#!/bin/bash
# Drill set runner — 지침 회귀 테스트. 사용: run.sh [case_id ...]
# 행동 판정(assert) + 컨텍스트 소모 계측(턴·토큰·비용) — g0_overhead 가 세팅 고정 세금 추세.
set -u
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DEFAULT_AGENT_HOME=$(sh "$SCRIPT_DIR/../../utilities/agent-home.sh" 2>/dev/null || printf '%s\n' "${CLAUDE_HOME:-$HOME/.claude}")
AGENT_HOME="${AGENT_HOME:-$DEFAULT_AGENT_HOME}"
export AGENT_HOME
GOLD="${DRILL_HOME:-$AGENT_HOME/loops/drill}"   # DRILL_HOME override = worktree 테스트 (production default 불변)
# Adapter runner (core/adapter split): the CASES are portable, the RUNNER is
# adapter-specific. DRILL_ADAPTER / --adapter selects claude|codex|opencode.
# shellcheck source=../lib-runner.sh
. "$SCRIPT_DIR/../lib-runner.sh"
# shellcheck source=../lib.sh
. "$SCRIPT_DIR/../lib.sh"
ADAPTER="${DRILL_ADAPTER:-auto}"
CLAUDE_BIN="${CLAUDE_BIN:-$HOME/.local/bin/claude}"
RUNNER_ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || printf '%s' "$AGENT_HOME")
STAMP=$(date +%F_%H%M)
RESULTS="$GOLD/results/$STAMP"
mkdir -p "$RESULTS"

# 인자 파싱: --axis <축>(git/spec/memory/routing/artifact/meta) · --sample N(랜덤) · case_id...
# 기본(인자 0)=전수. 축·샘플·id 혼용 가능 (id 먼저 풀 좁히고 → axis 필터 → sample). 매번 전수
# 안 돌려도 되게: 지침 변경 축만 --axis, cron 추세는 --sample, 사람 전수는 인자 0.
AXIS=""; SAMPLE=""; LIST=""; ids=()
while [ $# -gt 0 ]; do
  case "$1" in
    --axis)    AXIS="${2:-}"; shift 2 ;;
    --sample)  SAMPLE="${2:-}"; shift 2 ;;
    --adapter) ADAPTER="${2:-auto}"; shift 2 ;;
    --list)    LIST=1; shift ;;
    *)         ids+=("$1"); shift ;;
  esac
done
REQUESTED_ADAPTER="$ADAPTER"
if ! select_loop_adapter "$REQUESTED_ADAPTER" drill; then
  echo "drill adapter unavailable (requested=$REQUESTED_ADAPTER, reason=${LOOP_ROUTE_REASON:-unknown}, claude=${LOOP_CLAUDE_STATE:-unknown}, codex=${LOOP_CODEX_STATE:-unknown})" >&2
  exit 2
fi
ADAPTER="$LOOP_SELECTED_ADAPTER"
export DRILL_REQUESTED_ADAPTER="$REQUESTED_ADAPTER"
export DRILL_ADAPTER="$ADAPTER"
# Runtime projection(~/.claude)으로 시작해도 Fleet은 physical harness repo의 한 registry만 본다.
AGENT_DISPATCH_JOBS="${AGENT_DISPATCH_JOBS:-$RUNNER_ROOT/.dispatch/jobs.log}"
export AGENT_DISPATCH_JOBS
echo "drill adapter=$ADAPTER requested=$REQUESTED_ADAPTER reason=$LOOP_ROUTE_REASON claude=$LOOP_CLAUDE_STATE codex=$LOOP_CODEX_STATE"
# Codex workspace-write deliberately protects .git metadata, while several
# disposable drill cases validate branch/worktree operations. Scope the wider
# sandbox to drill only; every other loop keeps lib-runner's workspace-write
# default. Auto failover can enter Codex after startup, so configure on every switch.
configure_drill_adapter() {
  [ "$ADAPTER" = "codex" ] || return 0
  export LOOP_CODEX_SANDBOX="${DRILL_CODEX_SANDBOX:-danger-full-access}"
  # Depth-1/2 Codex workers are nested processes. In workspace-write the parent
  # cannot update git metadata and its children inherit network denial, so carry
  # the drill-only sandbox choice through dispatch-headless.py as well.
  export CODEX_DISPATCH_SANDBOX="$LOOP_CODEX_SANDBOX"
  # A stage owner may spell out a narrower --sandbox after reading a generic
  # command template. Drill fixtures need the selected sandbox to remain an
  # invariant across nested depth-1/2 dispatch, so force it only for this loop.
  export CODEX_DISPATCH_SANDBOX_FORCE="$LOOP_CODEX_SANDBOX"
  # Fleet ancestry must follow the actual running Codex thread, not a model-
  # invented parent id/slug. The wrapper applies this dynamically in every
  # depth-1/2 session; depth 1 has no dispatch-job parent slug of its own.
  export CODEX_DISPATCH_PARENT_CURRENT_FORCE=1
}
configure_drill_adapter

# --- conformance pre-stage (P-20) ---
# codex-adapter-parity audit P-20 (2026-07-04): 케이스 풀 구성(바로 아래 "풀: id 명시면...")
# 이전에 둔다 — axis 오타 등으로 cases=0 이 되면 아래 0-case 조기종료가 conformance 검증을
# 건너뛴 채 false-green(exit 0) 을 낼 수 있어서다. set -u 이므로 CONF_STATUS/CONF_FAIL 은
# 참조되기 전에 반드시 먼저 초기화한다(SKIP 경로에서 unbound 참조로 전체 run 이 abort 되는
# 것을 방지 — 아래 summary 행 emission 도 CONF_STATUS!=SKIP 로 guard 한다).
CONF_STATUS=SKIP; CONF_FAIL=0; CASE_FAIL=0

RUN_CONFORMANCE=0
if [ "${DRILL_CONFORMANCE_ONLY:-0}" = "1" ]; then
  # conformance 전용 실행 — --list/DRILL_SKIP_CONFORMANCE 여부와 무관하게 무조건 돈다.
  RUN_CONFORMANCE=1
elif [ -n "$LIST" ] || [ "${DRILL_SKIP_CONFORMANCE:-0}" = "1" ]; then
  RUN_CONFORMANCE=0
elif [ ${#ids[@]} -gt 0 ] || [ -n "$AXIS" ] || [ -n "$SAMPLE" ]; then
  # subset run(axis/sample/명시 id) 은 기본 auto-skip — 무관한 parity 로 좁은 런이 RED 되지
  # 않게. DRILL_CONFORMANCE=1 로 opt-in 강제 가능.
  [ "${DRILL_CONFORMANCE:-0}" = "1" ] && RUN_CONFORMANCE=1
else
  RUN_CONFORMANCE=1   # 전수(인자 0) 런 = conformance 기본 ON
fi

if [ "$RUN_CONFORMANCE" = "1" ]; then
  # codex-adapter-parity audit P-20 (2026-07-04): $AGENT_HOME 은 이 러너가 워크트리 안에서
  # 돌아도 (agent-home.sh 가 우선 검증하는) PRIMARY repo 로 해석될 수 있어, 그대로 쓰면
  # 워크트리가 아니라 엉뚱한 tree 를 검증하게 된다. 러너 자기 위치(SCRIPT_DIR) 기준 git
  # worktree root 를 따로 구해 그 tree 의 conformance 원본을 부른다. 두 conformance
  # 스크립트는 자기 위치를 서로 다르게 찾는다 — check-adaptation-boundary.sh 는 git
  # rev-parse 로 스스로 tree root 를 찾지만, portable-guards.test.sh 는 dirname/.. 상대경로로
  # ROOT 를 잡으므로 반드시 repo-root 원본을 직접 호출해야 한다(adapters/claude/ 미러본을
  # 부르면 ROOT 가 어긋나 codex/opencode 경로 참조가 깨진다).
  HARNESS_ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || printf '%s' "$AGENT_HOME")
  echo "== conformance (tree=$HARNESS_ROOT) =="
  echo "conformance=worktree / cases=primary"

  if bash "$HARNESS_ROOT/tools/check-adaptation-boundary.sh"; then
    CONF_STATUS=PASS
  else
    CONF_STATUS=FAIL
    CONF_FAIL=1
  fi

  # portable-guards.test.sh 는 informational(non-gating) — codex 바이너리가 없으면 env-gated
  # codex-doctor(--runtime/--runtime-strict) 가 항상 FAIL 을 섞어 내므로, 이를 게이트에 넣으면
  # 드릴이 케이스 전부 PASS 여도 영구 RED 가 된다. 결과만 보여주고 CONF_FAIL 에는 접지 않는다.
  if bash "$HARNESS_ROOT/hooks/portable-guards.test.sh"; then
    echo "conformance: portable-guards.test.sh PASS (informational)"
  else
    echo "conformance: portable-guards.test.sh FAIL (informational, non-gating — env-gated codex-doctor 가능성)"
  fi
fi

if [ "${DRILL_CONFORMANCE_ONLY:-0}" = "1" ]; then
  {
    echo "# Drill conformance-only run $STAMP"
    echo
    echo "| conformance | verdict |"
    echo "|---|---|"
    echo "| conformance | $CONF_STATUS |"
  } > "$RESULTS/summary.md"
  exit "$CONF_FAIL"
fi

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

declare -A verdicts metrics case_adapters
case_workdirs=()
for c in "${cases[@]}"; do
  grow=""
  case "$c" in growing:*) grow="(g)"; CASE_DIR="$GOLD/cases_growing/${c#growing:}" ;; *) CASE_DIR="$GOLD/cases/$c"; [ -d "$CASE_DIR" ] || CASE_DIR="$GOLD/cases_growing/$c" ;; esac
  [ -d "$CASE_DIR" ] || { echo "SKIP $c (없음)"; continue; }
  MAX_TURNS=""; TIMEOUT=1800; ADAPTERS=""
  [ -f "$CASE_DIR/config" ] && . "$CASE_DIR/config"
  # auto run은 앞 case가 남긴 새 limit marker를 다음 case 전에 다시 반영한다.
  if [ "$REQUESTED_ADAPTER" = "auto" ]; then
    if select_loop_adapter auto drill; then
      if [ "$ADAPTER" != "$LOOP_SELECTED_ADAPTER" ]; then
        echo "  adapter refresh $ADAPTER → $LOOP_SELECTED_ADAPTER ($LOOP_ROUTE_REASON)"
        ADAPTER="$LOOP_SELECTED_ADAPTER"
        export DRILL_ADAPTER="$ADAPTER"
        configure_drill_adapter
      fi
    else
      verdicts[$c]="FAIL(unavailable)"; metrics[$c]="0|0|0|0"; case_adapters[$c]="unavailable"
      CASE_FAIL=1
      echo "▶ $c → FAIL (both harnesses unavailable: $LOOP_ROUTE_REASON)"
      continue
    fi
  fi
  # per-case adapter pin: assert 가 특정 runtime 증거(codex JSONL tool 출력 등)를
  # 요구하는 케이스는 config ADAPTERS 로 고정 — 다른 adapter 런에선 FAIL 대신 SKIP.
  if [ -n "$ADAPTERS" ] && ! printf ' %s ' "$ADAPTERS" | grep -qF " $ADAPTER "; then
    verdicts[$c]="SKIP(adapter!=$ADAPTERS)"; metrics[$c]="0|0|0|0"
    case_adapters[$c]="$ADAPTER"
    echo "▶ $c → SKIP (requires adapter: $ADAPTERS, run=$ADAPTER)"; continue
  fi

  # 케이스 id 의 "growing:" 콜론이 assert 의 PYTHONPATH="$REPO"·clone 경로를 파괴한다
  WORK=$(mktemp -d "/tmp/drill-${c//:/_}-XXXX")
  case_workdirs+=("$WORK")
  echo "▶ $c (work=$WORK)"
  bash "$CASE_DIR/fixture.sh" "$WORK" || { verdicts[$c]="FIXTURE-ERR"; CASE_FAIL=1; continue; }

  T="$RESULTS/$c.transcript.txt"
  J="$RESULTS/$c.json"
  # Static-assert cases (AXIS=static) carry no user turn — they lint the live
  # repo deterministically (e.g. skill-conformance scan). Skip the adapter run,
  # emit a zero-cost metric, and go straight to assert.sh.
  if [ -f "$CASE_DIR/config" ] && grep -q '^AXIS=static' "$CASE_DIR/config"; then
    metrics[$c]="0|0|0|0"; : > "$T"; rc=0
  else
    # Adapter runner: writes $J (raw) + $T (normalized transcript), echoes
    # turns|in_tok|out_tok|cost. Same contract for claude|codex|opencode.
    metrics[$c]=$(run_case_on_adapter "$ADAPTER" "$CASE_DIR/prompt.md" "$WORK/repo" "$TIMEOUT" "${MAX_TURNS:-}" "$J" "$T")
    rc=$?
    # 새 limit이 이번 case에서 처음 드러난 경우, auto만 반대 하네스로 같은 case를 한 번 재실행.
    if [ "$rc" -ne 0 ] && [ "$REQUESTED_ADAPTER" = "auto" ]; then
      old_adapter="$ADAPTER"
      if select_loop_adapter auto drill && [ "$LOOP_SELECTED_ADAPTER" != "$old_adapter" ] && { [ -z "$ADAPTERS" ] || printf ' %s ' "$ADAPTERS" | grep -qF " $LOOP_SELECTED_ADAPTER "; }; then
        ADAPTER="$LOOP_SELECTED_ADAPTER"
        export DRILL_ADAPTER="$ADAPTER"
        configure_drill_adapter
        echo "  runtime failover $old_adapter → $ADAPTER ($LOOP_ROUTE_REASON)"
        metrics[$c]=$(run_case_on_adapter "$ADAPTER" "$CASE_DIR/prompt.md" "$WORK/repo" "$TIMEOUT" "${MAX_TURNS:-}" "$J" "$T")
        rc=$?
      fi
    fi
  fi
  case_adapters[$c]="$ADAPTER"

  # Spec-grounding marker home for assertions: guards write the marker to the
  # ADAPTER's resolved agent-home, so cases must read it there, not a literal
  # claude path. Default to this run's AGENT_HOME.
  export DRILL_MARKER_HOME="${DRILL_MARKER_HOME:-$AGENT_HOME}"

  assert_rc=0
  out=$(bash "$CASE_DIR/assert.sh" "$WORK" "$T" 2>&1) || assert_rc=$?
  if [ "$rc" -eq 0 ] && [ "$assert_rc" -eq 0 ]; then
    verdicts[$c]="PASS$grow"
  else
    verdicts[$c]="FAIL$grow"
    CASE_FAIL=1
    if [ "$rc" -ne 0 ]; then
      out="RUNTIME-FAIL: $ADAPTER exit $rc${out:+$'\n'$out}"
    fi
  fi
  echo "$out" | tee "$RESULTS/$c.assert.txt"
  echo "  → ${verdicts[$c]} ($ADAPTER exit $rc, ${metrics[$c]})"

  # FAIL 자동 진단도 선택 adapter를 사용한다. DRILL_ADAPTER=codex/opencode 런이
  # Claude Code 토큰을 암묵 소비하지 않도록 direct `claude -p` 경로는 두지 않는다.
  if [[ "${verdicts[$c]}" == FAIL* ]] && [ "$rc" -eq 0 ] && [ "${DRILL_AUTO_DIAG:-1}" = "1" ]; then
    DIAG_PROMPT="$WORK/diagnosis.prompt.md"
    {
      echo "drill set 케이스 FAIL 진단."
      echo "케이스 정의: $CASE_DIR (prompt.md=사용자 발화, assert.sh=판정)"
      echo "assert 출력: $RESULTS/$c.assert.txt"
      echo "transcript: $T"
      echo "fixture 결과물: $WORK"
      echo
      echo "이 자료를 읽고 (1) 위반 행동 (2) 닿지 않거나 모호한 지침 (3) 수정안 하나를 한국어로 간결히 답하라. 파일은 수정하지 마라."
    } > "$DIAG_PROMPT"
    diag_metrics=$(DRILL_FLEET_MODE=loop/drill-diagnosis DRILL_FLEET_WORKER_ROLE="diagnosis-$c" \
      run_case_on_adapter "$ADAPTER" "$DIAG_PROMPT" "$WORK/repo" 600 25 \
        "$RESULTS/$c.diagnosis.json" "$RESULTS/$c.diagnosis.md") || true
    [ -s "$RESULTS/$c.diagnosis.md" ] && echo "  진단서: $RESULTS/$c.diagnosis.md ($ADAPTER, ${diag_metrics:-?})"
  fi
done

{
  echo "# Drill run $STAMP"
  echo
  echo "| case | adapter | verdict | turns | in_tok | out_tok | cost\$ |"
  echo "|---|---|---|---|---|---|---|"
  # codex-adapter-parity audit P-20 (2026-07-04): conformance 는 케이스가 아니므로 구분되는
  # prefix("conformance |")로 별행 삽입 — metrics.csv(아래)는 ${cases[@]}만 순회해 안전하지만,
  # summary.md 행을 케이스로 파싱하는 다른 도구가 있다면 오카운트하지 않도록. SKIP 이면(=subset
  # auto-skip 등) 아예 행을 내지 않는다.
  [ "$CONF_STATUS" != SKIP ] && echo "| conformance | - | $CONF_STATUS | - | - | - | - |"
  for c in "${cases[@]}"; do
    IFS='|' read -r mt mi mo mc <<< "${metrics[$c]:-?|?|?|?}"
    echo "| $c | ${case_adapters[$c]:-$ADAPTER} | ${verdicts[$c]:-?} | $mt | $mi | $mo | $mc |"
  done
} | tee "$RESULTS/summary.md"

# 추세 누적 (지침 부풀림 감시 — 특히 g0_overhead 의 in_tok)
for c in "${cases[@]}"; do
  echo "$STAMP,$c,${verdicts[$c]:-?},${metrics[$c]:-?|?|?|?}" | tr '|' ',' >> "$GOLD/metrics.csv"
done

# 옵션: 응답규율 채점 pass (약자 풀이·번역체·약속-행동) — transcript 일괄 LLM 채점
if [ "${RUN_JUDGE:-0}" = "1" ]; then
  JUDGE_PROMPT="$RESULTS/judge.prompt.md"
  {
    cat "$GOLD/judge.md"
    echo
    echo "대상 transcript 디렉토리: $RESULTS (각 *.transcript.txt). 파일을 수정하지 말고 채점 보고서만 응답하라."
  } > "$JUDGE_PROMPT"
  judge_metrics=$(run_case_on_adapter "$ADAPTER" "$JUDGE_PROMPT" "$RUNNER_ROOT" 600 25 \
    "$RESULTS/judge.json" "$RESULTS/judge.md") || true
  echo "judge → $RESULTS/judge.md ($ADAPTER, ${judge_metrics:-?})"
fi

# --- 정리: 헤드리스 케이스가 남긴 세션 detritus 제거 (레지스트리·세션목록 오염 방지) ---
# 각 case 의 헤드리스 run 은 cwd=/tmp/drill-* 라 세션이 등록됨 → 이 실행이 만든
# 정확한 경로만 청소한다. 동시 실행 중인 다른 drill의 /tmp/drill-* 는 건드리지 않는다.
for work in "${case_workdirs[@]}"; do
  enc=$(printf '%s' "$work/repo" | sed 's#[/._]#-#g')
  rm -rf "$AGENT_HOME/projects/$enc" 2>/dev/null || true
  rm -rf "$work" 2>/dev/null || true
done
echo "cleanup: drill tmp + 세션 detritus 제거 (adapter=$ADAPTER)"

# codex-adapter-parity audit P-20 (2026-07-04): 기본은 report-and-continue — conformance 가
# FAIL 이어도 케이스는 항상 실행된다. 하지만 cleanup 까지 끝난 뒤에는 boundary guard FAIL 이
# 케이스 전부 PASS 여도 전체 run 을 non-zero 로 끝내야 한다(F4). CONF_STATUS=SKIP 이면
# CONF_FAIL=0 이라도 fixture/runtime/assert 실패가 있으면 non-zero 로 끝낸다.
if [ "$CONF_FAIL" -ne 0 ] || [ "$CASE_FAIL" -ne 0 ]; then
  exit 1
fi
exit 0
