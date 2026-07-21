#!/usr/bin/env sh
set -eu
# Concrete model IDs and default efforts live only in ../config/models.conf.
# This script owns role->tier routing (semantic), never concrete model literals.
dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$dir/../config/models.conf"
role=$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]' | tr '_-' '  ' | awk '{$1=$1; print}')
family=claude
case "$role" in
  'deep maker'|'deep reviewer'|'deep editor'|'deep orchestrator')
    model=${CLAUDE_MODEL_DEEP:-$CFG_TIER_DEEP_MODEL}; effort=${CLAUDE_EFFORT_DEEP:-$CFG_TIER_DEEP_EFFORT};;
  'fast implementer'|'fast reviewer'|'fast fact checker'|'fast writer'|'fast tool worker'|orchestrator|'external adversary'|'external adversary orchestrator')
    model=${CLAUDE_MODEL_BALANCED:-$CFG_TIER_LIGHT_MODEL}; effort=${CLAUDE_EFFORT_BALANCED:-$CFG_TIER_LIGHT_EFFORT};;
  *) echo "claude model-map: unknown role: ${1:-}" >&2; exit 64;;
esac
printf 'adapter=claude\nfamily=%s\nexact_model_id=%s\nreasoning=%s\nprobe=opt-in:claude -p --no-session-persistence --permission-mode plan --max-turns 1 --model <id> --effort <level>\n' "$family" "$model" "$effort"
