#!/usr/bin/env sh
set -eu
# Concrete model IDs and default efforts live only in ../config/models.conf.
# This script owns role->tier routing (semantic), never concrete model literals.
dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$dir/../config/models.conf"
role=$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]' | tr '_-' '  ' | awk '{$1=$1; print}')
family=gpt
case "$role" in
  'deep maker'|'deep reviewer'|'deep editor'|'deep orchestrator'|'external adversary')
    model=${CODEX_MODEL_SOL:-$CFG_TIER_DEEP_MODEL}; reasoning=${CODEX_REASONING_SOL:-$CFG_TIER_DEEP_EFFORT};;
  orchestrator|'external adversary orchestrator')
    model=${CODEX_MODEL_BALANCED:-${CODEX_MODEL_LUNA:-$CFG_TIER_LIGHT_MODEL}}; reasoning=${CODEX_REASONING_BALANCED:-${CODEX_REASONING_LUNA:-$CFG_TIER_LIGHT_EFFORT}};;
  'fast implementer'|'fast reviewer'|'fast fact checker'|'fast writer'|'fast tool worker')
    model=${CODEX_MODEL_LUNA:-$CFG_TIER_LIGHT_MODEL}; reasoning=${CODEX_REASONING_LUNA:-$CFG_TIER_LIGHT_EFFORT};;
  *) echo "codex model-map: unknown role: ${1:-}" >&2; exit 64;;
esac
printf 'adapter=codex\nfamily=%s\nexact_model_id=%s\nreasoning=%s\nprobe=opt-in:codex exec --ephemeral --sandbox read-only --model <id> -c model_reasoning_effort=<level>\n' "$family" "$model" "$reasoning"
