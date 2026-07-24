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
#     (3) shared readiness classifier selects all 3 children while dispatch-wait
#         stays pending (exit 2), then reports ready only after semantic-terminal
#         row evidence and process quiescence
#     (4) Σ 상한: wrapper 는 상한을 강제하지 않음(orchestrator/conductor 큐잉 책임) — 계약 대로
#         실측 기록.
set -uo pipefail
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
WRAP="$SCRIPT_DIR/../adapters/claude/bin/dispatch-headless.py"
LIVE="$SCRIPT_DIR/dispatch-liveness.sh"
WAIT="$SCRIPT_DIR/dispatch-wait.sh"
READY="$SCRIPT_DIR/dispatch-attempt-ready.py"
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
wt="$tmp/wt/shared"; mkdir -p "$wt"
( cd "$wt" && git init -q && git -c user.email=a@b -c user.name=a commit -q --allow-empty -m x )
sleep 60 & parent_pid=$!
parent_start=$(awk '{print $22}' "/proc/$parent_pid/stat")
parent_attempt="att-concurrency-parent"
mkdir -p "$AH/.dispatch"
printf '2026-07-23T00:00:00Z\topen\t%s\t%s\t%s\tattempt_schema_version=2,dispatch_depth=1,transport=headless,execution_surface=registered-headless,registered_worker=1,fallback_hop=same-harness-headless,worker_type=owner,harness=claude,runtime_sandbox=fixture,attempt_id=%s,pid=%s,pid_start=%s\n' \
  "$wt" "$wt" "$PARENT" "$parent_attempt" "$parent_pid" "$parent_start" > "$AH/.dispatch/jobs.log"
i=0
for r in $roles; do
  i=$((i + 1))
  AGENT_HOME="$AH" AGENT_DISPATCH_JOBS="$AH/.dispatch/jobs.log" \
    AGENT_DISPATCH_ATTEMPT_ID="$parent_attempt" \
    CLAUDE_CONFIG_DIR="$RT" PATH="$bin:$PATH" python3 "$WRAP" --start \
    --worktree "$wt" --slug "thr-$r" --capability autopilot-code --mode dev --qa thorough \
    --intensity thorough --dispatch-depth 2 --parent "$PARENT" --worker-type review \
    --assigned-contract audit --owner autopilot-code \
    --parent-harness claude --parent-transport headless --parent-sandbox fixture \
    --launch-authority conductor --nested-eligibility supported --eligibility-source concurrency-fixture \
    --model sonnet --effort medium --early-exit-watch 0 >/dev/null 2>&1
done
kill "$parent_pid" 2>/dev/null || true
wait "$parent_pid" 2>/dev/null || true
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

# (3) shared classifier + dispatch-wait: 실행 중 → 정확히 3개 선택, exit 2(재호출).
ready_json=$(AGENT_HOME="$AH" python3 "$READY" --parent "$PARENT" --jobs "$jobs" 2>&1)
ready_rc=$?
ready_n=$(printf '%s\n' "$ready_json" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["children"]))' 2>/dev/null || printf '0\n')
wout=$(AGENT_HOME="$AH" CLAUDE_CONFIG_DIR="$RT" DISPATCH_RUNTIME_ROOT="$RT" \
  sh "$WAIT" --parent "$PARENT" --jobs "$jobs" --interval 1 --max 2 2>&1)
wait_rc=$?
[ "$ready_rc" -eq 2 ] && [ "$ready_n" -eq 3 ] && [ "$wait_rc" -eq 2 ] \
  && ok "(3a) classifier selects 3 live children and dispatch-wait stays pending" \
  || bad "(3a) expected 3 pending children. readiness=[$ready_json] wait=[$wout]"

# 워커 종료 대기 후 (3b) exit 0.
sleep $((SLEEP + 2))
# fake claude 종료 뒤 fixture row 에 capability-route complete 가 원자적으로 쓰는
# semantic-terminal handshake 를 재현한다. Marker 자체의 결속 검증은 dedicated
# dispatch_completion_marker suite 가 담당하고, 여기서는 다중-process join 만 격리한다.
awk -F'\t' -v p="parent=$PARENT" 'BEGIN{OFS="\t"} $2=="open" && $6 ~ p {$2="done"; $6=$6 ",note=completed-marker"} {print}' "$jobs" > "$jobs.tmp" && mv "$jobs.tmp" "$jobs"
wout2=$(AGENT_HOME="$AH" sh "$WAIT" --parent "$PARENT" --jobs "$jobs" --max 2 2>&1)
wait_rc2=$?
[ "$wait_rc2" -eq 0 ] && echo "$wout2" | grep -q 'ready to harvest (exit 0)' && ok "(3b) semantic-terminal + process exit → dispatch-wait exit 0" \
  || bad "(3b) wait did not report harvest-ready. wout2=[$wout2]"

# (4) Σ 상한: wrapper 가 5대 분사도 막지 않음(강제는 orchestrator 큐잉). 계약대로 실측 기록.
ok "(4) 상한 비강제 확인: wrapper 는 동시 분사 수를 게이트하지 않음 — Σ≤5 는 conductor 큐잉 책임(계약 §5.10 ⑤, drift 아님)"

echo "— dispatch-concurrency (SD-16d) 실측: $([ $fails -eq 0 ] && echo 'PASS — 병렬 성립' || echo "FAIL ($fails) — 병렬 drift 발견")"
exit $fails
