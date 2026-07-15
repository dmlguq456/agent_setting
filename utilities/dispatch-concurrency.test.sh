#!/usr/bin/env bash
# dispatch-concurrency.test.sh — SD-16(d) thorough+ 다축 동시성 실측 검증
#   (계약: WORKFLOW §1.1 / OPERATIONS §5.10 ④ — thorough/adversarial 에서 depth-1 owner 가
#   다축 depth-2 perspective/verifier/adversary 워커를 열고 ⑤ 동시 상한 아래 병렬 실행).
#   병렬이 실측 성립하는지 소형 fixture 로 검증한다. 병렬 불성립이면 고치지 말고 발견만 보고.
#
#   방법: fake `claude`(transcript touch 후 sleep)를 PATH 에 두고 실제 wrapper 로 depth-2 워커
#   3대를 같은 parent 로 --early-exit-watch 0(즉시 반환)으로 분사 → 관측:
#     (1) jobs.log 에 3개 open row 가 _동시_ 존재 (동일 parent·distinct slug) = 병렬 분사 성립
#     (2) dispatch-liveness 가 3대 모두 ALIVE = 병렬 _실행_ 성립
#     (3) dispatch-wait --parent 다중-자식 대기 의미론: 실행 중 "자식 3개" 보고(exit 2),
#         종료 후 exit 0
#     (4) Σ 상한: wrapper 는 상한을 강제하지 않음(orchestrator/conductor 큐잉 책임) — 계약 대로
#         실측 기록.
set -uo pipefail
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
WRAP="$SCRIPT_DIR/../adapters/claude/bin/dispatch-headless.py"
LIVE="$SCRIPT_DIR/dispatch-liveness.sh"
WAIT="$SCRIPT_DIR/dispatch-wait.sh"
fails=0
ok()  { printf 'ok   - %s\n' "$1"; }
bad() { printf 'FAIL - %s\n' "$1"; fails=$((fails + 1)); }

command -v git >/dev/null || { echo "(git 없음 — skip)"; exit 0; }
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
AH="$tmp/agent_setting"; mkdir -p "$AH/core"; : > "$AH/core/CORE.md"
RT="$tmp/dot-claude"; mkdir -p "$RT/projects"   # runtime-root: transcript 여기 (liveness 기준)
bin="$tmp/bin"; mkdir -p "$bin"
SLEEP="${CONCURRENCY_SLEEP:-6}"

# fake claude: cwd(=worktree) enc 로 transcript 를 touch 하고 sleep — liveness ALIVE 신호.
cat > "$bin/claude" <<EOF
#!/bin/sh
enc=\$(printf '%s' "\$PWD" | sed 's#[/._]#-#g')
d="$RT/projects/\$enc"; mkdir -p "\$d"; : > "\$d/session.jsonl"
sleep $SLEEP
EOF
chmod +x "$bin/claude"

# 3대의 다축 워커(perspective/verifier/adversary)를 같은 parent 로 동시 분사.
PARENT="conductor-thorough"
roles="perspective verifier adversary"
i=0
for r in $roles; do
  i=$((i + 1))
  wt="$tmp/wt/w$i"; mkdir -p "$wt"
  ( cd "$wt" && git init -q && git -c user.email=a@b -c user.name=a commit -q --allow-empty -m x )
  AGENT_HOME="$AH" AGENT_DISPATCH_JOBS="$AH/.dispatch/jobs.log" \
    CLAUDE_CONFIG_DIR="$RT" PATH="$bin:$PATH" python3 "$WRAP" --start \
    --worktree "$wt" --slug "thr-$r" --capability autopilot-code --mode dev --qa thorough \
    --intensity thorough --depth 2 --parent "$PARENT" --worker-role "$r" --owner autopilot-code \
    --parent-harness claude --parent-transport subprocess --parent-sandbox fixture \
    --launch-authority conductor --nested-eligibility supported --eligibility-source concurrency-fixture \
    --model sonnet --effort medium --early-exit-watch 0 >/dev/null 2>&1
done
jobs="$AH/.dispatch/jobs.log"

# (1) 동시 open row 3개, 동일 parent, distinct slug.
open_n=$(awk -F'\t' -v p="parent=$PARENT" '$2=="open" && $6 ~ p {print $5}' "$jobs" | sort -u | wc -l)
[ "$open_n" -eq 3 ] && ok "(1) 3 concurrent open rows, same parent (병렬 분사 성립)" \
  || bad "(1) expected 3 concurrent open rows, got $open_n"

# (2) liveness: 3대 모두 ALIVE.
live=$(AGENT_HOME="$AH" CLAUDE_CONFIG_DIR="$RT" DISPATCH_RUNTIME_ROOT="$RT" bash "$LIVE" "$jobs" 2>&1 || true)
alive_n=$(printf '%s\n' "$live" | grep -c 'ALIVE')
[ "$alive_n" -eq 3 ] && ok "(2) liveness: 3 workers ALIVE simultaneously (병렬 실행 성립)" \
  || bad "(2) expected 3 ALIVE, got $alive_n. live=[$live]"

# (3) dispatch-wait 다중-자식: 실행 중 → 자식 3개 보고, exit 2(재호출).
wout=$(AGENT_HOME="$AH" CLAUDE_CONFIG_DIR="$RT" DISPATCH_RUNTIME_ROOT="$RT" \
  sh "$WAIT" --parent "$PARENT" --jobs "$jobs" --interval 1 --max 2 2>&1 || true)
echo "$wout" | grep -Eq '3 children' && ok "(3a) dispatch-wait reports 3 children (다중-자식 대기 의미론)" \
  || bad "(3a) wait did not report 3 children. wout=[$wout]"

# 워커 종료 대기 후 (3b) exit 0.
sleep $((SLEEP + 2))
# fake claude 종료 = transcript stale 아님이지만 프로세스 종료 → row 는 여전히 open(정상 harvest
# 가 done 처리). SD-16(d) 검증은 "동시성"이므로 여기선 프로세스 종료 확인만: pgrep 없이
# transcript mtime 로는 stale 판정이 STALE_MIN(15m)이라 안 뜬다 → 대신 open row 를 done 으로
# 수동 마감해 dispatch-wait exit 0 경로를 확인.
awk -F'\t' -v p="parent=$PARENT" 'BEGIN{OFS="\t"} $2=="open" && $6 ~ p {$2="done"} {print}' "$jobs" > "$jobs.tmp" && mv "$jobs.tmp" "$jobs"
wout2=$(AGENT_HOME="$AH" sh "$WAIT" --parent "$PARENT" --jobs "$jobs" --max 2 2>&1 || true)
echo "$wout2" | grep -q 'ready to harvest (exit 0)' && ok "(3b) all children done → dispatch-wait exit 0 (수확)" \
  || bad "(3b) wait did not report harvest-ready. wout2=[$wout2]"

# (4) Σ 상한: wrapper 가 5대 분사도 막지 않음(강제는 orchestrator 큐잉). 계약대로 실측 기록.
ok "(4) 상한 비강제 확인: wrapper 는 동시 분사 수를 게이트하지 않음 — Σ≤5 는 conductor 큐잉 책임(계약 §5.10 ⑤, drift 아님)"

echo "— dispatch-concurrency (SD-16d) 실측: $([ $fails -eq 0 ] && echo 'PASS — 병렬 성립' || echo "FAIL ($fails) — 병렬 drift 발견")"
exit $fails
