#!/usr/bin/env bash
# dispatch-wait.test.sh — SD-14 one-shot 대기 헬퍼 conformance (exit-code 매트릭스).
#   증명 대상: (0) 열린 자식 없음 → 수확, (2) 살아있음 → 재호출, (3) SUSPECT/DEAD → 진단.
#   liveness 를 재사용하므로 transcript mtime 으로 ALIVE/DEAD 를 조립해 판정을 유도한다.
set -uo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
WAIT="$SCRIPT_DIR/dispatch-wait.sh"
fails=0
ok()  { printf 'ok   - %s\n' "$1"; }
bad() { printf 'FAIL - %s\n' "$1"; fails=$((fails + 1)); }

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

agent_home="$tmp/agent_setting"
runtime_root="$tmp/dot-claude"
mkdir -p "$agent_home/.dispatch"
jobs="$agent_home/.dispatch/jobs.log"

# 공통: wt→enc 인코딩은 liveness 규칙과 동일(sed 's#[/._]#-#g').
mk_transcript() { # $1=wt  $2=age_touch(옵션; 없으면 now)
  local wt="$1" enc dir
  enc=$(printf '%s' "$wt" | sed 's#[/._]#-#g')
  dir="$runtime_root/projects/$enc"
  mkdir -p "$dir"
  : > "$dir/session.jsonl"
  [ -n "${2:-}" ] && touch -d "$2" "$dir/session.jsonl"
}

# --- Case 0a: jobs.log 없음 → exit 0 (열린 자식 없음) ---
out=$(AGENT_HOME="$agent_home" sh "$WAIT" --jobs "$tmp/nope.log" --parent x 2>&1); rc=$?
if [ "$rc" -eq 0 ]; then ok "missing jobs.log → exit 0 (harvest)"; else bad "missing jobs.log expected 0 got $rc [$out]"; fi

# --- Case 0b: parent 자식이 done 뿐 → exit 0 ---
: > "$jobs"
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-10T00:00:00" "done" "repo" "$tmp/wt/c1" "child1" "capability=code-plan,parent=conf" >> "$jobs"
out=$(AGENT_HOME="$agent_home" sh "$WAIT" --jobs "$jobs" --parent conf 2>&1); rc=$?
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q '열린 자식 없음'; then
  ok "no open children for parent → exit 0"
else bad "done-only children expected 0 got $rc [$out]"; fi

# --- Case 0b2: --jobs 생략 시 shared registry env를 사용 ---
out=$(AGENT_HOME="$agent_home" AGENT_DISPATCH_JOBS="$jobs" sh "$WAIT" --parent conf 2>&1); rc=$?
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q '열린 자식 없음'; then
  ok "AGENT_DISPATCH_JOBS selects the shared registry when --jobs is omitted"
else bad "shared registry done-only children expected 0 got $rc [$out]"; fi

# --- Case 0b2: --jobs 생략 시 shared registry env를 사용 ---
out=$(AGENT_HOME="$agent_home" AGENT_DISPATCH_JOBS="$jobs" sh "$WAIT" --parent conf 2>&1); rc=$?
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q '열린 자식 없음'; then
  ok "AGENT_DISPATCH_JOBS selects the shared registry when --jobs is omitted"
else bad "shared registry done-only children expected 0 got $rc [$out]"; fi

# --- Case 0c: open 자식이 있으나 parent 불일치 → exit 0 (내 자식 아님) ---
: > "$jobs"
mk_transcript "$tmp/wt/other"
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-10T00:00:00" "open" "repo" "$tmp/wt/other" "otherc" "capability=code-plan,parent=SOMEONE_ELSE" >> "$jobs"
out=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" sh "$WAIT" --jobs "$jobs" --parent conf 2>&1); rc=$?
if [ "$rc" -eq 0 ]; then ok "open child with different parent → exit 0 (not mine)"; else bad "foreign parent expected 0 got $rc [$out]"; fi

# --- Case 2: open 자식 ALIVE(fresh transcript) → max 짧게 → exit 2 (재호출) ---
: > "$jobs"
mk_transcript "$tmp/wt/alive"
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-10T00:00:00" "open" "repo" "$tmp/wt/alive" "alivec" "capability=code-execute,parent=conf" >> "$jobs"
out=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" sh "$WAIT" --jobs "$jobs" --parent conf --interval 1 --max 0 2>&1); rc=$?
if [ "$rc" -eq 2 ] && printf '%s' "$out" | grep -q '재호출'; then
  ok "alive open child, max reached → exit 2 (re-call)"
else bad "alive child expected 2 got $rc [$out]"; fi

# --- Case 3: open 자식 DEAD(transcript 없음) → exit 3 (진단) ---
: > "$jobs"
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-10T00:00:00" "open" "repo" "$tmp/wt/dead" "deadc" "capability=code-test,parent=conf" >> "$jobs"
out=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" sh "$WAIT" --jobs "$jobs" --parent conf --interval 1 --max 5 2>&1); rc=$?
if [ "$rc" -eq 3 ] && printf '%s' "$out" | grep -q 'SUSPECT/DEAD'; then
  ok "dead open child → exit 3 (diagnose)"
else bad "dead child expected 3 got $rc [$out]"; fi

# --- Case 4: --max 상한 클램프 확인 (600 초과 → 600, 소스 확증) ---
if grep -Fq 'MAX=600' "$WAIT"; then ok "--max clamped to 600 in source"; else bad "expected MAX clamp to 600"; fi

if [ "$fails" -eq 0 ]; then echo "dispatch-wait conformance: PASS"; exit 0; fi
echo "dispatch-wait conformance: $fails FAIL"; exit 1
