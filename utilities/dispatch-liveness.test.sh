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

if [ "$fails" -eq 0 ]; then
  echo "dispatch-liveness runtime-root regression: PASS"
  exit 0
fi
echo "dispatch-liveness runtime-root regression: $fails FAIL"
exit 1
