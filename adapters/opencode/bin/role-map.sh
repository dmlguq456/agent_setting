#!/usr/bin/env sh
set -eu

usage() {
  cat <<'EOF'
usage: role-map.sh <portable-role>

Prints an OpenCode adapter mapping for a portable model role.

OpenCode uses provider/model-id strings and a variant field for reasoning
profile selection. There is no numeric reasoning-effort config field.

Config knobs:
  AGENT_MODEL_FAST / AGENT_VARIANT_FAST
  AGENT_MODEL_DEEP / AGENT_VARIANT_DEEP
  AGENT_MODEL_EXTERNAL / AGENT_VARIANT_EXTERNAL
  AGENT_MODEL_ORCHESTRATOR / AGENT_VARIANT_ORCHESTRATOR
  AGENT_EXTERNAL_CMD
EOF
}

[ "${1:-}" != "-h" ] && [ "${1:-}" != "--help" ] || { usage; exit 0; }
[ "$#" -ge 1 ] || { usage >&2; exit 64; }

raw=$*
role=$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]' | tr '_-' '  ' | awk '{$1=$1; print}')

family=fast
canonical=$role
available=1
status=default
reason=""
external_cmd_bin=""

case "$role" in
  "fast reviewer"|"fast fact checker"|"fast fact-checker"|"fast writer"|"fast implementer"|"fast tool worker")
    family=fast
    ;;
  "deep reviewer"|"deep maker"|"deep editor")
    family=deep
    ;;
  "external adversary")
    family=external
    if [ -z "${AGENT_MODEL_EXTERNAL:-}" ] && [ -z "${AGENT_EXTERNAL_CMD:-}" ]; then
      available=0
      status=unavailable
      reason="set AGENT_MODEL_EXTERNAL or AGENT_EXTERNAL_CMD for an independent external adversary"
    elif [ -n "${AGENT_EXTERNAL_CMD:-}" ]; then
      external_cmd_bin=${AGENT_EXTERNAL_CMD%% *}
      if ! command -v "$external_cmd_bin" >/dev/null 2>&1; then
        available=0
        status=unavailable
        reason="AGENT_EXTERNAL_CMD not found: $external_cmd_bin"
      fi
    fi
    ;;
  "orchestrator"|"external adversary orchestrator")
    family=orchestrator
    ;;
  *)
    echo "opencode role-map: unknown portable role: $raw" >&2
    usage >&2
    exit 64
    ;;
esac

case "$family" in
  fast)
    model=${AGENT_MODEL_FAST:-opencode-default}
    variant=${AGENT_VARIANT_FAST:-runtime-default}
    [ "$model" = "opencode-default" ] && status=default || status=configured
    ;;
  deep)
    model=${AGENT_MODEL_DEEP:-opencode-default}
    variant=${AGENT_VARIANT_DEEP:-runtime-default}
    [ "$model" = "opencode-default" ] && status=default || status=configured
    ;;
  external)
    model=${AGENT_MODEL_EXTERNAL:-external-command}
    variant=${AGENT_VARIANT_EXTERNAL:-runtime-default}
    [ "$available" -eq 1 ] && status=configured
    ;;
  orchestrator)
    model=${AGENT_MODEL_ORCHESTRATOR:-${AGENT_MODEL_FAST:-opencode-default}}
    variant=${AGENT_VARIANT_ORCHESTRATOR:-${AGENT_VARIANT_FAST:-runtime-default}}
    [ "$model" = "opencode-default" ] && status=default || status=configured
    ;;
esac

printf 'role=%s\n' "$canonical"
printf 'adapter=opencode\n'
printf 'source=roles/README.md\n'
printf 'family=%s\n' "$family"
printf 'model=%s\n' "$model"
printf 'variant=%s\n' "$variant"
printf 'available=%s\n' "$available"
printf 'status=%s\n' "$status"
[ -z "$external_cmd_bin" ] || printf 'external_command=%s\n' "$AGENT_EXTERNAL_CMD"
[ -z "$reason" ] || printf 'reason=%s\n' "$reason"
