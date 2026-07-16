#!/usr/bin/env bash
# dispatch-liveness.test.sh — harness-layer-sync §4.1 / HLS-6 회귀 테스트.
#   증명 대상: non-profile job 의 transcript 를 runtime-root(~/.claude/projects/)에서 찾아야 한다.
#   과거 버그: PROJ="$AGENT_HOME/projects" 라 하네스 소스 repo 를 봐 살아있는 job 을 DEAD 오탐(2026-07-09).
#   정정 후: PROJ 는 ${DISPATCH_RUNTIME_ROOT:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}}/projects 기준.
set -uo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
LIVENESS="$SCRIPT_DIR/dispatch-liveness.sh"
fails=0
ok()   { printf 'ok   - %s\n' "$1"; }
bad()  { printf 'FAIL - %s\n' "$1"; fails=$((fails + 1)); }

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

# 가짜 세팅: AGENT_HOME(소스 repo, projects 없음) 과 runtime-root(transcript 있음)를 분리한다.
agent_home="$tmp/agent_setting"          # 하네스 소스 repo — projects/ 없음 (구버그가 여기를 봤다)
runtime_root="$tmp/dot-claude"           # 런타임 세션 상태 루트 — 여기에 transcript 존재
mkdir -p "$agent_home/.dispatch"

# non-profile open job: wt 를 스크립트와 동일 규칙(sed 's#[/._]#-#g')으로 enc 인코딩.
wt="$tmp/wt/layer-sync-phase1"
enc=$(printf '%s' "$wt" | sed 's#[/._]#-#g')
proj_dir="$runtime_root/projects/$enc"
mkdir -p "$proj_dir"
: > "$proj_dir/session.jsonl"            # 방금 갱신된 transcript = ALIVE 신호 (mtime now)

jobs="$agent_home/.dispatch/jobs.log"
# 필드: ts \t status \t repo \t wt \t slug \t pipe  (pipe 에 profile= 없음 → non-profile 경로)
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-09T00:00:00" "open" "agent_setting" "$wt" "phase1" "pipe=autopilot-code" > "$jobs"

# --- Case A (정정본): 올바른 runtime-root → ALIVE, exit 0 ---
outA=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" bash "$LIVENESS" "$jobs" 2>&1)
rcA=$?
if [ "$rcA" -eq 0 ] && printf '%s' "$outA" | grep -q 'ALIVE'; then
  ok "non-profile job with transcript under runtime-root is ALIVE (exit 0)"
else
  bad "expected ALIVE/exit0 with correct runtime-root; got rc=$rcA out=[$outA]"
fi

# --- Case A2: 명시 인자 없이 shared registry env를 같은 정본으로 사용 ---
outA2=$(AGENT_HOME="$agent_home" AGENT_DISPATCH_JOBS="$jobs" DISPATCH_RUNTIME_ROOT="$runtime_root" bash "$LIVENESS" 2>&1)
rcA2=$?
if [ "$rcA2" -eq 0 ] && printf '%s' "$outA2" | grep -q 'ALIVE'; then
  ok "AGENT_DISPATCH_JOBS selects the shared registry when no path argument is given"
else
  bad "expected shared registry ALIVE/exit0; got rc=$rcA2 out=[$outA2]"
fi

# --- Case A2: 명시 인자 없이 shared registry env를 같은 정본으로 사용 ---
outA2=$(AGENT_HOME="$agent_home" AGENT_DISPATCH_JOBS="$jobs" DISPATCH_RUNTIME_ROOT="$runtime_root" bash "$LIVENESS" 2>&1)
rcA2=$?
if [ "$rcA2" -eq 0 ] && printf '%s' "$outA2" | grep -q 'ALIVE'; then
  ok "AGENT_DISPATCH_JOBS selects the shared registry when no path argument is given"
else
  bad "expected shared registry ALIVE/exit0; got rc=$rcA2 out=[$outA2]"
fi

# --- Case B (구버그 재현): runtime-root 를 projects 없는 AGENT_HOME 으로 → DEAD 오탐, exit 3 ---
outB=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$agent_home" bash "$LIVENESS" "$jobs" 2>&1)
rcB=$?
if [ "$rcB" -eq 3 ] && printf '%s' "$outB" | grep -q 'DEAD'; then
  ok "wrong root (old AGENT_HOME-rooted behavior) reproduces the DEAD false positive (exit 3)"
else
  bad "expected DEAD/exit3 when root lacks projects/; got rc=$rcB out=[$outB]"
fi

# --- Case C: 기본값이 runtime-root(~/.claude) 계열이지 AGENT_HOME 이 아님을 소스로 확증 ---
if grep -Fq 'RUNTIME_ROOT="${DISPATCH_RUNTIME_ROOT:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}}"' "$LIVENESS" \
  && grep -Fq 'PROJ="$RUNTIME_ROOT/projects"' "$LIVENESS"; then
  ok "PROJ is derived from runtime-root, not AGENT_HOME"
else
  bad "dispatch-liveness.sh must derive PROJ from RUNTIME_ROOT (${DISPATCH_RUNTIME_ROOT:-CLAUDE_CONFIG_DIR:-\$HOME/.claude})"
fi

# ===== SD-15b (§8.6.1): 로그-패턴 DEAD 판정 앵커링 =====
logs="$agent_home/.dispatch/logs"
mkdir -p "$logs"

# --- Case D: 정상 완주 conductor — 최종 보고문이 limit 을 논하지만 transcript 는 신선 → ALIVE.
#     (완주 신호 = 신선 transcript 가 로그 prose 매치를 이긴다. SD-15b 오탐 실측의 회귀.)
wtD="$tmp/wt/rpt-cycle"; encD=$(printf '%s' "$wtD" | sed 's#[/._]#-#g')
mkdir -p "$runtime_root/projects/$encD"; : > "$runtime_root/projects/$encD/s.jsonl"
cat > "$logs/rptslug.111.log" <<'EOF'
사이클 요약: SD-15 wrapper 가 launch 직후 조기 exit 를 감지해, 로그 말미에 "You've hit your session limit" 같은 종료 라인이 있으면 jobs.log row 를 dead-session-limit 으로 즉시 마감하도록 개정했습니다. 이 보고문은 limit 을 주제로 서술하지만 세션은 정상 완주했습니다.
검증: 신규·기존 스위트 전부 통과. 다음 단계는 문서-효력 재검증입니다.
EOF
jobsD="$agent_home/.dispatch/jobs.log"
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-10T00:00:00" "open" "agent_setting" "$wtD" "rptslug" "pipe=autopilot-code" > "$jobsD"
outD=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" bash "$LIVENESS" "$jobsD" 2>&1); rcD=$?
if [ "$rcD" -eq 0 ] && printf '%s' "$outD" | grep -q 'ALIVE' && ! printf '%s' "$outD" | grep -q 'DEAD'; then
  ok "fresh transcript excludes DEAD even when the log discusses limits (SD-15b)"
else
  bad "expected ALIVE (fresh transcript wins over log prose); got rc=$rcD out=[$outD]"
fi

# --- Case E: transcript 부재 + 로그 말미 짧은 단독 CLI limit 라인 → DEAD(로그 limit/auth 패턴).
wtE="$tmp/wt/dead-launch"   # projects/ 에 transcript 를 만들지 않음
printf 'launching…\nYou'\''ve hit your session limit · resets 3pm (Asia/Seoul)\n' > "$logs/deadslug.222.log"
jobsE="$agent_home/.dispatch/jobs.log"
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-10T00:00:00" "open" "agent_setting" "$wtE" "deadslug" "pipe=autopilot-code" > "$jobsE"
outE=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" bash "$LIVENESS" "$jobsE" 2>&1); rcE=$?
if [ "$rcE" -eq 3 ] && printf '%s' "$outE" | grep -q 'DEAD' && printf '%s' "$outE" | grep -q 'limit/auth'; then
  ok "terse trailing CLI limit line with no transcript → DEAD(limit) (SD-15b)"
else
  bad "expected DEAD(limit/auth) for terse trailing line; got rc=$rcE out=[$outE]"
fi

# --- Case F: stale transcript + limit 이 로그 _본문 산문_(긴 라인)에만 등장 → 앵커링으로 미매치 →
#     SUSPECT(mtime 정지), NOT DEAD(limit). (긴 prose 라인은 death 라인으로 인정 안 함.)
wtF="$tmp/wt/hang-cycle"; encF=$(printf '%s' "$wtF" | sed 's#[/._]#-#g')
mkdir -p "$runtime_root/projects/$encF"; : > "$runtime_root/projects/$encF/s.jsonl"
touch -d '40 minutes ago' "$runtime_root/projects/$encF/s.jsonl"
# limit 문구가 긴 산문 라인(>200)에만 있고, 말미 라인은 무관한 짧은 문장.
printf 'note: 이 실행은 rate limit 회피 라우팅과 session limit 마커 처리 로직을 길게 서술하는 산문이며 한 줄이 매우 길어 앵커 임계 200자를 넘도록 의도적으로 늘려 두었다 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n작업 계속 진행 중\n' > "$logs/hangslug.333.log"
jobsF="$agent_home/.dispatch/jobs.log"
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-10T00:00:00" "open" "agent_setting" "$wtF" "hangslug" "pipe=autopilot-code" > "$jobsF"
outF=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" bash "$LIVENESS" "$jobsF" 2>&1); rcF=$?
# 검사: SUSPECT verdict 라인은 있고, DEAD _verdict_ 라인(⚠️ DEAD …)은 없어야 한다
# (요약 힌트 "→ SUSPECT/DEAD:" 는 verdict 가 아니므로 매칭에서 제외).
if printf '%s' "$outF" | grep -q '⚠️ SUSPECT' && ! printf '%s' "$outF" | grep -q '⚠️ DEAD'; then
  ok "limit only in long prose line (not terse trailing) → SUSPECT not DEAD (SD-15b anchoring)"
else
  bad "expected SUSPECT (anchoring rejects prose limit match); got rc=$rcF out=[$outF]"
fi

# ===== pid 신호 서열 (공유-worktree transcript aliasing, 2026-07-13) =====
if [ -d /proc ]; then
  # --- Case G: pid= 실행 중 (cmdline 에 claude) → transcript 없어도 ALIVE(pid), exit 0.
  bash -c 'exec -a claude sleep 30' & pidG=$!
  wtG="$tmp/wt/pid-alive"   # projects/ transcript 없음 — pid 신호가 1순위임을 증명
  jobsG="$agent_home/.dispatch/jobs.log"
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-13T00:00:00" "open" "agent_setting" "$wtG" "pidalive" "capability=x,pid=$pidG" > "$jobsG"
  outG=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" bash "$LIVENESS" "$jobsG" 2>&1); rcG=$?
  if [ "$rcG" -eq 0 ] && printf '%s' "$outG" | grep -q 'ALIVE.*pid'; then
    ok "live pid (claude cmdline) → ALIVE(pid) without any transcript"
  else
    bad "expected ALIVE(pid)/exit0 for live pid; got rc=$rcG out=[$outG]"
  fi
  kill "$pidG" 2>/dev/null; wait "$pidG" 2>/dev/null

  # --- Case G2: Codex row validates the codex cmdline and recorded start ticks.
  bash -c 'exec -a codex sleep 30' & pidG2=$!
  startG2=$(awk '{print $22}' "/proc/$pidG2/stat")
  jobsG2="$agent_home/.dispatch/jobs.log"
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-15T00:00:00" "open" "agent_setting" "$tmp/wt/codex-pid" "codexpid" "capability=x,harness=codex,pid=$pidG2,pid_start=$startG2" > "$jobsG2"
  outG2=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" bash "$LIVENESS" "$jobsG2" 2>&1); rcG2=$?
  if [ "$rcG2" -eq 0 ] && printf '%s' "$outG2" | grep -q 'ALIVE.*harness=codex.*classifier=tools.fleet.model.classify_attempt_evidence'; then
    ok "Codex live pid + matching start ticks → ALIVE(pid)"
  else
    bad "expected Codex ALIVE(pid); got rc=$rcG2 out=[$outG2]"
  fi
  kill "$pidG2" 2>/dev/null; wait "$pidG2" 2>/dev/null

  # --- Case H (본 수정의 회귀 핵심): pid 종료 + *신선* transcript → EXITED, exit 3.
  #     구버전은 conductor 활동이 만든 신선 transcript 때문에 ALIVE 오탐(수확 ~50분 지연 실측).
  sleep 0.1 & pidH=$!; wait "$pidH" 2>/dev/null   # 즉시 종료한 pid 확보
  wtH="$tmp/wt/pid-exited"; encH=$(printf '%s' "$wtH" | sed 's#[/._]#-#g')
  mkdir -p "$runtime_root/projects/$encH"; : > "$runtime_root/projects/$encH/s.jsonl"   # 신선 transcript (aliasing 조건)
  jobsH="$agent_home/.dispatch/jobs.log"
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-13T00:00:00" "open" "agent_setting" "$wtH" "pidexited" "capability=x,pid=$pidH" > "$jobsH"
  outH=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" bash "$LIVENESS" "$jobsH" 2>&1); rcH=$?
  if [ "$rcH" -eq 3 ] && printf '%s' "$outH" | grep -q '⚠️ EXITED' && ! printf '%s' "$outH" | grep -q 'ALIVE'; then
    ok "dead pid + fresh transcript → EXITED not ALIVE (shared-worktree aliasing closed)"
  else
    bad "expected EXITED/exit3 (pid beats fresh transcript); got rc=$rcH out=[$outH]"
  fi

  # --- Case I: pid 없는 legacy row 는 기존 transcript-mtime 판정 유지 (Case A 재확인 겸).
  wtI="$tmp/wt/legacy-row"; encI=$(printf '%s' "$wtI" | sed 's#[/._]#-#g')
  mkdir -p "$runtime_root/projects/$encI"; : > "$runtime_root/projects/$encI/s.jsonl"
  jobsI="$agent_home/.dispatch/jobs.log"
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-13T00:00:00" "open" "agent_setting" "$wtI" "legacyrow" "capability=x" > "$jobsI"
  outI=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" bash "$LIVENESS" "$jobsI" 2>&1); rcI=$?
  if [ "$rcI" -eq 0 ] && printf '%s' "$outI" | grep -q 'ALIVE.*transcript'; then
    ok "pid-less legacy row still judged by transcript mtime (fallback intact)"
  else
    bad "expected legacy transcript ALIVE for pid-less row; got rc=$rcI out=[$outI]"
  fi
else
  echo "skip - /proc 없음: pid 신호 케이스 G/H/I 생략 (fallback 경로는 A~F 가 커버)"
fi

# --- Case J (O1): PID-less Codex legacy row uses the active wrapper JSONL, not Claude projects/.
jobsJ="$agent_home/.dispatch/jobs.log"
: > "$logs/codexlegacy.codex.jsonl"
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "2026-07-15T00:00:00" "open" "agent_setting" "$tmp/wt/codex-legacy" "codexlegacy" "capability=x,harness=codex" > "$jobsJ"
outJ=$(AGENT_HOME="$agent_home" DISPATCH_RUNTIME_ROOT="$runtime_root" bash "$LIVENESS" "$jobsJ" 2>&1); rcJ=$?
if [ "$rcJ" -eq 0 ] && printf '%s' "$outJ" | grep -q 'ALIVE.*Codex dispatch log'; then
  ok "PID-less Codex row uses fresh .codex.jsonl fallback (O1 false-DEAD closed)"
else
  bad "expected Codex log fallback ALIVE; got rc=$rcJ out=[$outJ]"
fi

if [ "$fails" -eq 0 ]; then
  echo "dispatch-liveness runtime-root regression: PASS"
  exit 0
fi
echo "dispatch-liveness runtime-root regression: $fails FAIL"
exit 1
