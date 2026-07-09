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

if [ "$fails" -eq 0 ]; then
  echo "dispatch-liveness runtime-root regression: PASS"
  exit 0
fi
echo "dispatch-liveness runtime-root regression: $fails FAIL"
exit 1
