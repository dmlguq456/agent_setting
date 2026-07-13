#!/usr/bin/env sh
set -eu
role=$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]' | tr '_-' '  ' | awk '{$1=$1; print}')
case "$role" in
  'deep maker'|'deep reviewer'|'deep editor'|'deep orchestrator') model=${CLAUDE_MODEL_DEEP:-opus}; effort=${CLAUDE_EFFORT_DEEP:-high}; family=claude;;
  'fast implementer'|'fast reviewer'|'fast fact checker'|'fast writer'|'fast tool worker'|orchestrator|'external adversary'|'external adversary orchestrator') model=${CLAUDE_MODEL_BALANCED:-sonnet}; effort=${CLAUDE_EFFORT_BALANCED:-medium}; family=claude;;
  *) echo "claude model-map: unknown role: ${1:-}" >&2; exit 64;;
esac
printf 'adapter=claude\nfamily=%s\nexact_model_id=%s\nreasoning=%s\nprobe=opt-in:claude -p --no-session-persistence --permission-mode plan --max-turns 1 --model <id> --effort <level>\n' "$family" "$model" "$effort"
