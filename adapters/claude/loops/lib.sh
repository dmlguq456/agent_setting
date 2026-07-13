#!/bin/bash
# loops 공용 헬퍼 — source 전용 (직접 실행하지 않는다).
# study.sh·oncall.sh 가 LOG 변수 정의 직후 `source "$LOOP_DIR/lib.sh"` 한다.

# --- 버그①: cron 환경 PATH 보정 ---
# cron 의 제한 PATH 는 /usr/bin/node(v10) 를 집어, claude 가 SessionEnd 때 codex 플러그인
# hook(.mjs, `import ... "node:fs"`)을 실행하다 ESM/`node:` 스킴을 못 읽어 SyntaxError 로
# 죽었다 (2026-06-21 연수 사고). ~/.local/bin(v20) 을 앞세워 cron 에서도 최신 node 가 잡히게.
export PATH="$HOME/.local/bin:$PATH"

# --- 루프 러너: usage-aware 어댑터 선택 (OPERATIONS §5.10) ---
# 명시 claude|codex|opencode 는 강제 선택. 기본 auto 는 canonical jobs.log 의 known-limit,
# HARNESS_CAPACITY_BIAS, 중립 분산 순으로 Claude/Codex를 고른다. 정확한 quota 퍼센트 추정은
# 하지 않는다. OpenCode는 usage-check 상태원이 없으므로 명시 선택만 지원한다.
LOOP_ADAPTER="${LOOP_ADAPTER:-auto}"

_loop_harness_root() {
  if [ -n "${LOOP_HARNESS_ROOT:-}" ] && [ -f "$LOOP_HARNESS_ROOT/core/CORE.md" ]; then
    printf '%s\n' "$LOOP_HARNESS_ROOT"
    return 0
  fi
  local src dir root
  src=$(readlink -f "${BASH_SOURCE[0]:-$0}" 2>/dev/null || printf '%s' "${BASH_SOURCE[0]:-$0}")
  dir=$(CDPATH= cd -- "$(dirname -- "$src")" && pwd)
  root=$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null || true)
  if [ -n "$root" ] && [ -f "$root/core/CORE.md" ]; then
    printf '%s\n' "$root"
    return 0
  fi
  printf '%s\n' "${AGENT_HOME:-${CLAUDE_HOME:-$HOME/agent_setting}}"
}

LOOP_HARNESS_ROOT=$(_loop_harness_root)
LOOP_USAGE_CHECK="${LOOP_USAGE_CHECK:-$LOOP_HARNESS_ROOT/utilities/usage-check.sh}"

_loop_jobs_path() {
  if [ -n "${AGENT_DISPATCH_JOBS:-}" ]; then
    printf '%s\n' "$AGENT_DISPATCH_JOBS"
  else
    printf '%s/.dispatch/jobs.log\n' "$LOOP_HARNESS_ROOT"
  fi
}

# select_loop_adapter <auto|claude|codex|opencode> <routing-key>
# 결과는 LOOP_SELECTED_ADAPTER/LOOP_ROUTE_* 전역에 기록한다.
select_loop_adapter() {
  local requested="${1:-auto}" key="${2:-loop}" usage rc
  case "$requested" in
    claude|codex|opencode)
      LOOP_SELECTED_ADAPTER="$requested"
      LOOP_ROUTE_REASON="explicit:$requested"
      LOOP_CLAUDE_STATE="not-checked"
      LOOP_CODEX_STATE="not-checked"
      return 0
      ;;
    auto) ;;
    *)
      LOOP_SELECTED_ADAPTER="unavailable"
      LOOP_ROUTE_REASON="invalid-adapter:$requested"
      return 64
      ;;
  esac

  rc=0
  usage=$(AGENT_HOME="$LOOP_HARNESS_ROOT" bash "$LOOP_USAGE_CHECK" --harness all --jobs "$(_loop_jobs_path)" --select "loop:$key") || rc=$?
  LOOP_CLAUDE_STATE=$(printf '%s\n' "$usage" | awk '$1=="claude" {print $2; exit}')
  LOOP_CODEX_STATE=$(printf '%s\n' "$usage" | awk '$1=="codex" {print $2; exit}')
  LOOP_SELECTED_ADAPTER=$(printf '%s\n' "$usage" | awk '$1=="selected" {print $2; exit}')
  LOOP_ROUTE_REASON=$(printf '%s\n' "$usage" | awk '$1=="selection_reason" {print $2; exit}')
  LOOP_CLAUDE_STATE="${LOOP_CLAUDE_STATE:-unknown}"
  LOOP_CODEX_STATE="${LOOP_CODEX_STATE:-unknown}"
  LOOP_SELECTED_ADAPTER="${LOOP_SELECTED_ADAPTER:-unavailable}"
  LOOP_ROUTE_REASON="${LOOP_ROUTE_REASON:-usage-check-failed}"
  if [ "$rc" -eq 0 ] && [ "$LOOP_SELECTED_ADAPTER" != "unavailable" ]; then
    return 0
  fi
  [ "$rc" -ne 0 ] || rc=1
  return "$rc"
}

_loop_registry_value() {
  local value="${1:-}"
  value=${value//$'\t'/_}
  value=${value//$'\n'/_}
  value=${value//$'\r'/_}
  value=${value//,/_}
  printf '%s' "$value"
}

_loop_registry_append() {
  local jobs=$1 line=$2 lock
  mkdir -p "$(dirname -- "$jobs")" 2>/dev/null || return 0
  lock="$jobs.lock"
  if command -v flock >/dev/null 2>&1; then
    ( flock -x 9; printf '%s\n' "$line" >> "$jobs" ) 9>>"$lock" 2>/dev/null || true
  else
    printf '%s\n' "$line" >> "$jobs" 2>/dev/null || true
  fi
}

# oncall/study도 drill과 같은 Fleet registry에 실행 중 open row를 노출한다.
_scheduled_loop_registry_start() { # $1=adapter $2=key $3=attempt
  local adapter=$1 key=$2 attempt=$3 jobs ts cwd repo slug pipe line
  jobs=$(_loop_jobs_path)
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  cwd=$(pwd -P)
  repo=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null || printf '%s' "$cwd")
  slug="loop-$(_loop_registry_value "$key")-$adapter-$(date -u +%Y%m%d%H%M%S)-$$-$attempt"
  pipe="capability=loop,mode=loop/$(_loop_registry_value "$key"),qa=quick,intensity=quick,depth=1,harness=$adapter,worker_role=$(_loop_registry_value "$key"),owner=loop"
  line=$(printf '%s\topen\t%s\t%s\t%s\t%s' "$ts" "$repo" "$cwd" "$slug" "$pipe")
  _loop_registry_append "$jobs" "$line"
  LOOP_RUN_JOBS="$jobs"
  LOOP_RUN_SLUG="$slug"
}

_scheduled_loop_registry_finish_unlocked() { # $1=jobs $2=slug $3=reason $4=reset
  python3 - "$1" "$2" "${3:-}" "${4:-}" <<'PY'
import os
import pathlib
import stat
import sys

path = pathlib.Path(sys.argv[1])
slug, reason, reset = sys.argv[2:]
try:
    lines = path.read_text(encoding="utf-8").splitlines()
    mode = stat.S_IMODE(path.stat().st_mode)
except OSError:
    raise SystemExit(3)

changed = False
for idx, line in enumerate(lines):
    fields = line.split("\t")
    if len(fields) != 6 or fields[4] != slug or fields[1] not in {"open", "running"}:
        continue
    fields[1] = "done"
    if reason:
        fields[5] += f",note=dead-{reason},reset={reset or 'unknown-reset'}"
    lines[idx] = "\t".join(fields)
    changed = True

if not changed:
    raise SystemExit(3)

tmp = path.with_name(f"{path.name}.tmp.{os.getpid()}")
try:
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(tmp, mode)
    os.replace(tmp, path)
finally:
    try:
        tmp.unlink()
    except FileNotFoundError:
        pass
PY
}

_scheduled_loop_registry_finish() {
  local jobs=$1 slug=$2 reason=${3:-} reset=${4:-} lock
  lock="$jobs.lock"
  if command -v flock >/dev/null 2>&1; then
    ( flock -x 9; _scheduled_loop_registry_finish_unlocked "$jobs" "$slug" "$reason" "$reset" ) 9>>"$lock"
  else
    _scheduled_loop_registry_finish_unlocked "$jobs" "$slug" "$reason" "$reset"
  fi
}

_loop_record_limit() {
  local adapter=$1 key=$2 output=$3 run_jobs=${4:-} run_slug=${5:-}
  local reason reset jobs ts repo cwd slug pipe line
  reason="usage-limit"
  printf '%s' "$output" | grep -qiE '(session|weekly|monthly)[[:space:]]+(usage[[:space:]]+)?limit' && reason="session-limit"
  reset=$(printf '%s\n' "$output" | sed -nE 's/.*reset(s|ting)?([[:space:]]+at|[[:space:]]*:)?[[:space:]]*([0-9]{1,2}(:[0-9]{2})?[[:space:]]*(am|pm)?|noon|midnight).*/\3/Ip' | head -1 | tr -d '[:space:]')
  reset="${reset:-unknown-reset}"
  if [ -n "$run_jobs" ] && [ -n "$run_slug" ] \
      && _scheduled_loop_registry_finish "$run_jobs" "$run_slug" "$reason" "$reset"; then
    return 0
  fi
  jobs=$(_loop_jobs_path)
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  cwd=$(pwd -P)
  repo=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null || printf '%s' "$cwd")
  slug="loop-$(_loop_registry_value "$key")-$adapter-$(date -u +%Y%m%d%H%M%S)-$$"
  pipe="capability=loop,mode=loop/$(_loop_registry_value "$key"),qa=quick,intensity=quick,depth=1,harness=$adapter,worker_role=$(_loop_registry_value "$key"),owner=loop,note=dead-$reason,reset=$(_loop_registry_value "$reset")"
  line=$(printf '%s\tdone\t%s\t%s\t%s\t%s' "$ts" "$repo" "$cwd" "$slug" "$pipe")
  _loop_registry_append "$jobs" "$line"
}

# --- 버그②: 일시장애 재시도 래퍼 (어댑터 dispatch) ---
# 사용:  run_claude_retry <timeout초> <프롬프트파일> [claude 추가인자...]
#   401·5xx·overloaded·rate-limit = *일시* 장애 → 백오프 후 재시도 (최대 3회).
#   session/usage limit = marker 기록; auto는 alternate 1회 failover, explicit은 ABORT.
#   매 시도 출력은 stdout 으로 그대로 흘리고, 종료 사유를 마커로 남긴다 (당직이 점검).
run_claude_retry() {
  local to="$1" pf="$2"; shift 2
  local max=3 attempt rc out requested adapter key failover old _ocbin run_jobs run_slug
  local backoff=(0 30 120)   # 시도 전 대기 (1회차 0s)
  requested="${LOOP_ADAPTER:-auto}"
  key="${LOOP_NAME:-$(basename "$pf" .md)}"
  if ! select_loop_adapter "$requested" "$key"; then
    echo "=== ABORT: loop adapter unavailable (requested=$requested, reason=${LOOP_ROUTE_REASON:-unknown}, claude=${LOOP_CLAUDE_STATE:-unknown}, codex=${LOOP_CODEX_STATE:-unknown}) ==="
    return 2
  fi
  adapter="$LOOP_SELECTED_ADAPTER"
  echo "=== loop adapter $adapter (requested=$requested, reason=$LOOP_ROUTE_REASON, claude=$LOOP_CLAUDE_STATE, codex=$LOOP_CODEX_STATE) ==="
  failover=0
  attempt=1
  while [ "$attempt" -le "$max" ]; do
    if [ "${backoff[attempt-1]}" -gt 0 ]; then
      echo "=== retry $attempt/$max — ${backoff[attempt-1]}s 대기 후 재시도 ==="
      sleep "${backoff[attempt-1]}"
    fi
    _scheduled_loop_registry_start "$adapter" "$key" "$attempt"
    run_jobs="$LOOP_RUN_JOBS"
    run_slug="$LOOP_RUN_SLUG"
    case "$adapter" in
      codex)
        out="$(AGENT_HOME="$LOOP_HARNESS_ROOT" AGENT_DISPATCH_JOBS="$(_loop_jobs_path)" timeout "$to" "${CODEX_BIN:-codex}" exec --sandbox workspace-write --skip-git-repo-check - < "$pf" 2>&1)" ;;
      opencode)
        _ocbin="${OPENCODE_BIN:-opencode}"; command -v "$_ocbin" >/dev/null 2>&1 || _ocbin="$HOME/.opencode/bin/opencode"
        out="$(AGENT_HOME="$LOOP_HARNESS_ROOT" AGENT_DISPATCH_JOBS="$(_loop_jobs_path)" timeout "$to" "$_ocbin" run "$(cat "$pf")" 2>&1)" ;;
      *)
        out="$(AGENT_HOME="$LOOP_HARNESS_ROOT" AGENT_DISPATCH_JOBS="$(_loop_jobs_path)" timeout "$to" "${CLAUDE_BIN:-$HOME/.local/bin/claude}" -p "$(cat "$pf")" "$@" 2>&1)" ;;
    esac
    rc=$?
    printf '%s\n' "$out"
    # 사용량 제한 — 리셋 전엔 안 풀리므로 재시도하지 않고 명확히 끝낸다
    if printf '%s' "$out" | grep -qiE 'session limit|usage limit|hit your .*limit'; then
      _loop_record_limit "$adapter" "$key" "$out" "$run_jobs" "$run_slug"
      if [ "$requested" = "auto" ] && [ "$failover" -eq 0 ]; then
        old="$adapter"
        if select_loop_adapter auto "$key" && [ "$LOOP_SELECTED_ADAPTER" != "$old" ]; then
          adapter="$LOOP_SELECTED_ADAPTER"
          failover=1
          attempt=1
          echo "=== failover $old → $adapter ($LOOP_ROUTE_REASON) ==="
          continue
        fi
      fi
      echo "=== ABORT: session/usage limit — alternate unavailable or explicit adapter (rc=$rc, attempt=$attempt) ==="
      return 2
    fi
    _scheduled_loop_registry_finish "$run_jobs" "$run_slug" "" "" || true
    # 성공 = 종료 0 + 일시오류 마커 없음
    if [ "$rc" -eq 0 ] && ! printf '%s' "$out" \
        | grep -qiE '401|invalid authentication|overloaded|rate.?limit|internal server error|api error: 5[0-9][0-9]'; then
      return 0
    fi
    attempt=$((attempt + 1))
  done
  echo "=== FAILED after $max attempts (rc=$rc) ==="
  return 1
}
