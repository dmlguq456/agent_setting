#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)

usage() {
  cat <<'EOF'
usage: distill-worker.sh <session-id> [cwd]

Builds a Codex transcript distillation proposal with a constrained Codex exec
worker. The worker is opt-in and does not mutate memory by itself.

Set CODEX_DISTILL_ENABLE=1 to run it.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

[ "$#" -ge 1 ] || { usage >&2; exit 64; }

sid=$1
cwd=${2:-$PWD}

if [ "${CODEX_DISTILL_ENABLE:-}" != "1" ]; then
  exit 0
fi

if ! command -v codex >/dev/null 2>&1; then
  echo "codex distill worker: codex command not found" >&2
  exit 69
fi

delta=$(
  AGENT_HOME="${AGENT_HOME:-$ROOT}" \
  python3 "$ROOT/tools/memory/mem.py" distill "$sid" --source codex 2>/dev/null || true
)

if [ -z "$(printf '%s' "$delta" | tr -d '[:space:]')" ]; then
  exit 0
fi

store=${MEM_STORE:-$ROOT/memory}
mkdir -p "$store"
prompt_file="$store/.codex-distill-prompt-$sid"
out_file="$store/.codex-distill-out-$sid"

cat > "$prompt_file" <<EOF
You are a memory distillation worker.

Constraints:
- Do not call tools. If a tool surface is available, do not use it.
- Use only the transcript delta below.
- Output JSON Lines only, with one action object per line.
- Do not output Markdown, commentary, or code fences.

Allowed actions:
- {"action":"add","tier":"working","type":"fact|decision|todo|preference|context","body":"..."}
- {"action":"add","tier":"durable","type":"fact|decision|todo|preference|context","body":"..."}
- {"action":"reinforce","id":"...","evidence":"..."}
- {"action":"prune","id":"...","reason":"..."}
- {"action":"graduate","id":"...","evidence":"..."}
- {"action":"reattribute","id":"...","subject":"..."}
- {"action":"merge","ids":["..."],"canonical":"..."}

Transcript delta:
<<<DELTA
$delta
DELTA
EOF

if [ -n "${CODEX_DISTILL_MODEL:-}" ]; then
  codex exec \
    --cd "$cwd" \
    --sandbox read-only \
    --ask-for-approval never \
    --ephemeral \
    --ignore-rules \
    --output-last-message "$out_file" \
    -m "$CODEX_DISTILL_MODEL" \
    - < "$prompt_file" >/dev/null
else
  codex exec \
    --cd "$cwd" \
    --sandbox read-only \
    --ask-for-approval never \
    --ephemeral \
    --ignore-rules \
    --output-last-message "$out_file" \
    - < "$prompt_file" >/dev/null
fi

if [ "${CODEX_DISTILL_APPLY:-}" = "1" ] && [ -f "$out_file" ]; then
  AGENT_HOME="${AGENT_HOME:-$ROOT}" python3 "$ROOT/tools/memory/apply-distill-actions.py" \
    "$out_file" "$ROOT/tools/memory/mem.py" --mode increment
fi

[ -f "$out_file" ] && cat "$out_file"
