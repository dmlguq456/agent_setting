#!/usr/bin/env sh
set -eu
role=$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]' | tr '_-' '  ' | awk '{$1=$1; print}')
case "$role" in
  'deep maker'|'deep reviewer'|'deep editor'|'deep orchestrator'|'external adversary') model=${CODEX_MODEL_SOL:-gpt-5.6-sol}; reasoning=${CODEX_REASONING_SOL:-high}; family=gpt;;
  'fast implementer') model=${CODEX_MODEL_TERRA:-gpt-5.6-terra}; reasoning=${CODEX_REASONING_TERRA:-medium}; family=gpt;;
  orchestrator|'external adversary orchestrator') model=${CODEX_MODEL_BALANCED:-${CODEX_MODEL_TERRA:-gpt-5.6-terra}}; reasoning=${CODEX_REASONING_BALANCED:-${CODEX_REASONING_TERRA:-medium}}; family=gpt;;
  'fast reviewer'|'fast fact checker'|'fast writer'|'fast tool worker') model=${CODEX_MODEL_LUNA:-gpt-5.6-luna}; reasoning=${CODEX_REASONING_LUNA:-medium}; family=gpt;;
  *) echo "codex model-map: unknown role: ${1:-}" >&2; exit 64;;
esac
printf 'adapter=codex\nfamily=%s\nexact_model_id=%s\nreasoning=%s\nprobe=opt-in:codex exec --ephemeral --sandbox read-only --model <id> -c model_reasoning_effort=<level>\n' "$family" "$model" "$reasoning"
