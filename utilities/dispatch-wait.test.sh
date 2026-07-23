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
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q 'no open children'; then
  ok "no open children for parent → exit 0"
else bad "done-only children expected 0 got $rc [$out]"; fi

# --- Case 0b2: --jobs 생략 시 shared registry env를 사용 ---
out=$(AGENT_HOME="$agent_home" AGENT_DISPATCH_JOBS="$jobs" sh "$WAIT" --parent conf 2>&1); rc=$?
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q 'no open children'; then
  ok "AGENT_DISPATCH_JOBS selects the shared registry when --jobs is omitted"
else bad "shared registry done-only children expected 0 got $rc [$out]"; fi

# --- Case 0b2: --jobs 생략 시 shared registry env를 사용 ---
out=$(AGENT_HOME="$agent_home" AGENT_DISPATCH_JOBS="$jobs" sh "$WAIT" --parent conf 2>&1); rc=$?
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q 'no open children'; then
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
if [ "$rc" -eq 2 ] && printf '%s' "$out" | grep -q 'call again'; then
  ok "alive open child, max reached → exit 2 (re-call)"
else bad "alive child expected 2 got $rc [$out]"; fi

# --- Case 3: open 자식 DEAD(transcript 없음) → exit 3 (진단) ---
: > "$jobs"
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-10T00:00:00" "open" "repo" "$tmp/wt/dead" "deadc" "capability=code-test,parent=conf" >> "$jobs"
out=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" sh "$WAIT" --jobs "$jobs" --parent conf --interval 1 --max 5 2>&1); rc=$?
if [ "$rc" -eq 3 ] && printf '%s' "$out" | grep -q 'SUSPECT/DEAD'; then
  ok "dead open child → exit 3 (diagnose)"
else bad "dead child expected 3 got $rc [$out]"; fi

# --- Case 3b: supplemental controlled current/open Codex terminal rows.
# Real foreground FAIL/BLOCKED rows close before return; these byte-shaped logs
# exercise wait/liveness without weakening current-row filtering.
term_wt="$tmp/wt/terminal"
term_root="$tmp/canonical/.agent_reports"
mkdir -p "$term_wt" "$term_root"
git -C "$term_wt" init -q
for verdict in PASS FAIL BLOCKED; do
  lower=$(printf '%s' "$verdict" | tr '[:upper:]' '[:lower:]')
  blocker="private-$lower"
  [ "$verdict" = "PASS" ] && blocker="none"
  log="$tmp/wait-$lower.codex.jsonl"
  python3 - "$log" "$verdict" "$blocker" <<'PY'
import json, pathlib, sys
path, verdict, blocker = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
rows = [
    {"type":"item.completed","item":{"type":"command_execution","exit_code":0,"aggregated_output":"RAW_WAIT_SENTINEL"}},
    {"type":"item.completed","item":{"type":"agent_message","text":f"artifact: -\nverdict: {verdict}\nblocker: {blocker}"}},
    {"type":"turn.completed"},
]
path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
PY
  : > "$jobs"
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-22T00:00:00" "open" "repo" "$term_wt" "wait-$lower" \
    "attempt_schema_version=2,dispatch_depth=2,transport=headless,execution_surface=registered-headless,registered_worker=1,fallback_hop=same-harness-headless,attempt_id=att-wait-$lower,parent=conf,harness=codex,artifact_root=$term_root,log_file=$log" >> "$jobs"
  out=$(AGENT_HOME="$agent_home" AGENT_ARTIFACT_ROOT="$term_root" sh "$WAIT" --jobs "$jobs" --parent conf --interval 1 --max 5 2>&1); rc=$?
  expected="EXITED"
  [ "$verdict" = "PASS" ] && expected="COMPLETED"
  if [ "$rc" -eq 3 ] && printf '%s' "$out" | grep -q 'terminal/SUSPECT/DEAD child detected' \
      && printf '%s' "$out" | grep -q "$expected.*turn.completed $verdict" \
      && ! printf '%s' "$out" | grep -q 'RAW_WAIT_SENTINEL\|private-fail\|private-blocked'; then
    ok "supplemental open Codex $verdict row → typed wait exit 3 without raw leakage"
  else
    bad "supplemental Codex $verdict expected typed wait exit3 got $rc [$out]"
  fi
done

# --- Case 4: --max 상한 클램프 확인 (600 초과 → 600, 소스 확증) ---
if grep -Fq 'MAX=600' "$WAIT"; then ok "--max clamped to 600 in source"; else bad "expected MAX clamp to 600"; fi

# --- Case t1: --slug 정확 일치. 타 slug의 open row는 무시되고, 대상 slug가
# jobs.log에 없으면 exit 0 (no open children, 필터 표기) ---
: > "$jobs"
mk_transcript "$tmp/wt/other-slug"
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-23T00:00:00" "open" "repo" "$tmp/wt/other-slug" "other-slug" "capability=code-plan,parent=conf" >> "$jobs"
out=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" sh "$WAIT" --jobs "$jobs" --slug missing-slug 2>&1); rc=$?
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q 'slug=missing-slug has no open children'; then
  ok "--slug exact match ignores unrelated open rows, absent target → exit 0"
else bad "--slug filter expected 0 got $rc [$out]"; fi

# --- Case t2: --slug 대상 open + 이후 done row → last-status로 닫힘 처리 exit 0 ---
: > "$jobs"
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-23T00:00:00" "open" "repo" "$tmp/wt/target" "target-slug" "capability=code-plan,parent=conf" >> "$jobs"
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-23T00:01:00" "done" "repo" "$tmp/wt/target" "target-slug" "capability=code-plan,parent=conf" >> "$jobs"
out=$(AGENT_HOME="$agent_home" sh "$WAIT" --jobs "$jobs" --slug target-slug 2>&1); rc=$?
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q 'no open children'; then
  ok "--slug target closed by later done row (last-status) → exit 0"
else bad "--slug last-status expected 0 got $rc [$out]"; fi

# --- Case t3: --attempt-id 일치 행만 선택 (불일치 attempt_id의 open row는 무시) ---
: > "$jobs"
mk_transcript "$tmp/wt/attempt-other"
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-23T00:00:00" "open" "repo" "$tmp/wt/attempt-other" "attempt-slug" "capability=code-plan,parent=conf,attempt_id=att-other" >> "$jobs"
out=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" sh "$WAIT" --jobs "$jobs" --attempt-id att-target 2>&1); rc=$?
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q 'attempt_id=att-target has no open children'; then
  ok "--attempt-id exact match ignores rows with a different attempt_id"
else bad "--attempt-id filter expected 0 got $rc [$out]"; fi

# --- Case t4: --parent + --slug AND 결합 (같은 slug, 다른 parent는 제외) ---
: > "$jobs"
mk_transcript "$tmp/wt/and-match"
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-23T00:00:00" "open" "repo" "$tmp/wt/and-match" "and-slug" "capability=code-plan,parent=conf" >> "$jobs"
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-23T00:00:00" "open" "repo" "$tmp/wt/and-other" "and-slug-2" "capability=code-plan,parent=OTHER" >> "$jobs"
out=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" sh "$WAIT" --jobs "$jobs" --parent conf --slug and-slug --interval 1 --max 0 2>&1); rc=$?
if [ "$rc" -eq 2 ] && printf '%s' "$out" | grep -q 'call again'; then
  ok "--parent + --slug AND selects only the matching row (excludes and-slug-2)"
else bad "--parent+--slug AND expected 2 got $rc [$out]"; fi

# --- Case t5: 무관 DEAD row 존재 + --slug 필터 → 대상 slug가 jobs.log에
# 없으면 exit 3이 아니라 exit 0 (2026-07-23 스코프 결함의 회귀 케이스) ---
: > "$jobs"
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-23T00:00:00" "open" "repo" "$tmp/wt/unrelated-dead" "unrelated-dead" "capability=code-test,parent=conf" >> "$jobs"
out=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" sh "$WAIT" --jobs "$jobs" --slug my-target-slug --max 1 2>&1); rc=$?
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q 'slug=my-target-slug has no open children'; then
  ok "unrelated DEAD row does not steal exit 3 when --slug scopes to an absent target (regression)"
else bad "--slug scope regression expected 0 got $rc [$out]"; fi

if [ "$fails" -eq 0 ]; then echo "dispatch-wait conformance: PASS"; exit 0; fi
echo "dispatch-wait conformance: $fails FAIL"; exit 1
