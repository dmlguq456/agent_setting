#!/usr/bin/env sh
set -eu

usage() {
  cat <<'EOF'
usage: role-map.sh <portable-role>

Prints a Codex adapter mapping for a portable model role.

Config knobs:
  AGENT_MODEL_FAST / AGENT_REASONING_FAST
  AGENT_MODEL_DEEP / AGENT_REASONING_DEEP
  AGENT_MODEL_EXTERNAL / AGENT_REASONING_EXTERNAL
  AGENT_MODEL_ORCHESTRATOR / AGENT_REASONING_ORCHESTRATOR
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
role_set=""

case "$role" in
  "variable reviewer")
    family=role-set
    role_set="fast reviewer,deep reviewer,external adversary"
    ;;
  "variable research reviewer")
    family=role-set
    role_set="fast fact checker,deep reviewer,external adversary"
    ;;
  "fast implementer by default")
    family=role-set
    role_set="fast implementer"
    ;;
  "deep maker plus fast tool worker")
    family=role-set
    role_set="deep maker,fast tool worker"
    ;;
  "deep maker plus verifier")
    family=role-set
    role_set="deep maker,fast reviewer"
    ;;
  "deep maker / fast reviewer by mode")
    family=role-set
    role_set="deep maker,fast reviewer"
    ;;
  "external adversary plus orchestrator")
    family=role-set
    role_set="external adversary,orchestrator"
    ;;
esac

if [ -z "$role_set" ]; then
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
      echo "codex role-map: unknown portable role: $raw" >&2
      usage >&2
      exit 64
      ;;
  esac
fi

case "$family" in
  fast)
    model=${AGENT_MODEL_FAST:-codex-default}
    reasoning=${AGENT_REASONING_FAST:-runtime-default}
    [ "$model" = "codex-default" ] && status=default || status=configured
    ;;
  deep)
    model=${AGENT_MODEL_DEEP:-codex-default}
    reasoning=${AGENT_REASONING_DEEP:-runtime-default}
    [ "$model" = "codex-default" ] && status=default || status=configured
    ;;
  external)
    model=${AGENT_MODEL_EXTERNAL:-external-command}
    reasoning=${AGENT_REASONING_EXTERNAL:-runtime-default}
    [ "$available" -eq 1 ] && status=configured
    ;;
  orchestrator)
    model=${AGENT_MODEL_ORCHESTRATOR:-${AGENT_MODEL_FAST:-codex-default}}
    reasoning=${AGENT_REASONING_ORCHESTRATOR:-${AGENT_REASONING_FAST:-runtime-default}}
    [ "$model" = "codex-default" ] && status=default || status=configured
    ;;
  role-set)
    model=role-set
    reasoning=select-by-mode
    status=role-set
    ;;
esac

printf 'role=%s\n' "$canonical"
printf 'adapter=codex\n'
printf 'source=roles/README.md\n'
printf 'family=%s\n' "$family"
if [ -n "$role_set" ]; then
  printf 'role_set=%s\n' "$role_set"
fi
printf 'model=%s\n' "$model"
printf 'reasoning=%s\n' "$reasoning"
printf 'available=%s\n' "$available"
printf 'status=%s\n' "$status"
[ -z "$external_cmd_bin" ] || printf 'external_command=%s\n' "$AGENT_EXTERNAL_CMD"
[ -z "$reason" ] || printf 'reason=%s\n' "$reason"
