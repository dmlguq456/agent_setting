#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
usage: mem-distill-worker.sh <mode> <model> <prompt-file>

Claude Code realization of the portable memory distillation worker contract.
Reads a prompt file and writes JSON-lines proposals to stdout.
EOF
}

[ "${1:-}" != "-h" ] && [ "${1:-}" != "--help" ] || { usage; exit 0; }
[ "$#" -eq 3 ] || { usage >&2; exit 64; }

mode=$1
model=$2
prompt_file=$3

case "$mode" in
  increment|curate) ;;
  *) echo "mem-distill-worker: unknown mode: $mode" >&2; exit 64 ;;
esac

case "$model" in
  fast-distiller)
    model="${CLAUDE_MEM_DISTILL_MODEL:-claude-sonnet-4-6}"
    ;;
  deep-curator)
    model="${CLAUDE_MEM_DISTILL_MODEL_SESSIONEND:-claude-opus-4-8}"
    ;;
esac

[ -f "$prompt_file" ] || { echo "mem-distill-worker: prompt file not found: $prompt_file" >&2; exit 64; }
command -v claude >/dev/null 2>&1 || exit 0

# timeout 은 모드별: curate 는 opus deep-curator 가 큰 프롬프트(delta+snapshot+artifacts)로
# 사고시간이 길어 120s 에 잘림(2026-07-03 실측 — 생성 전 killed → action 0 + marker 전진 데이터 손실).
# 분사는 setsid detach 라 긴 timeout 이 세션 종료를 블록하지 않는다. dispatch 의 stale GC(60min) 안.
case "$mode" in
  curate) worker_timeout="${MEM_DISTILL_TIMEOUT_CURATE:-600}" ;;
  *)      worker_timeout="${MEM_DISTILL_TIMEOUT:-120}" ;;
esac
if command -v timeout >/dev/null 2>&1; then
  timeout_cmd=(timeout "$worker_timeout")
else
  timeout_cmd=()
fi

DISALLOW='Bash Read Write Edit Glob Grep Agent NotebookEdit WebFetch WebSearch Task'

MEM_DISTILL=1 setsid "${timeout_cmd[@]}" claude -p "$(cat "$prompt_file")" \
  --model "$model" \
  --disallowedTools "$DISALLOW"
