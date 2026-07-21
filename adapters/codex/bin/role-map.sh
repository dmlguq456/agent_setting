#!/usr/bin/env sh
set -eu

# Concrete model IDs and default efforts live only in ../config/models.conf.
_cmdir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$_cmdir/../config/models.conf"

usage() {
  cat <<'EOF'
usage: role-map.sh <portable-role|role-profile|pipeline-stage>

Prints a Codex adapter mapping for a portable model role or role profile.

Config knobs:
  AGENT_MODEL_FAST / AGENT_REASONING_FAST
  AGENT_MODEL_DEEP / AGENT_REASONING_DEEP
  AGENT_MODEL_TERRA / AGENT_REASONING_TERRA
  AGENT_MODEL_LUNA / AGENT_REASONING_LUNA
  AGENT_MODEL_BALANCED / AGENT_REASONING_BALANCED
  AGENT_MODEL_EXTERNAL / AGENT_REASONING_EXTERNAL
  AGENT_MODEL_ORCHESTRATOR / AGENT_REASONING_ORCHESTRATOR
  AGENT_EXTERNAL_CMD
EOF
}

[ "${1:-}" != "-h" ] && [ "${1:-}" != "--help" ] || { usage; exit 0; }
[ "$#" -ge 1 ] || { usage >&2; exit 64; }

raw=$*
role=$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]' | tr '_-' '  ' | awk '{$1=$1; print}')

profile=""
pipeline_stage=""
profile_portable_role=""
profile_role_input=""
case "$role" in
  "planning"|"plan team")
    profile=plan-team
    pipeline_stage=planning
    profile_portable_role="deep maker"
    profile_role_input="deep maker"
    ;;
  "implementation"|"dev team")
    profile=dev-team
    pipeline_stage=implementation
    profile_portable_role="fast implementer by default"
    profile_role_input="fast implementer"
    ;;
  "verification"|"qa team")
    profile=qa-team
    pipeline_stage=verification
    profile_portable_role="variable reviewer"
    profile_role_input="fast reviewer"
    ;;
  "report"|"reporting"|"editorial team")
    profile=editorial-team
    pipeline_stage=report
    profile_portable_role="deep maker / fast reviewer by mode"
    profile_role_input="fast reviewer"
    ;;
  "research team")
    profile=research-team
    profile_portable_role="variable research reviewer"
    profile_role_input="deep reviewer"
    ;;
  "material team")
    profile=material-team
    profile_portable_role="deep maker plus fast tool worker"
    profile_role_input="fast tool worker"
    ;;
  "design team")
    profile=design-team
    profile_portable_role="deep maker plus verifier"
    profile_role_input="deep maker"
    ;;
  "external adversary"|"external adversary team")
    if [ "$role" = "external adversary team" ]; then
      profile=external-adversary
      profile_portable_role="external adversary plus orchestrator"
      profile_role_input="external adversary"
    fi
    ;;
esac

if [ -n "$profile" ]; then
  printf 'role=%s\n' "$role"
  printf 'adapter=codex\n'
  printf 'source=roles/README.md\n'
  printf 'family=role-profile\n'
  printf 'role_profile=%s\n' "$profile"
  [ -z "$pipeline_stage" ] || printf 'pipeline_stage=%s\n' "$pipeline_stage"
  printf 'native_agent_path=adapters/codex/agents/%s.toml\n' "$profile"
  printf 'portable_model_role=%s\n' "$profile_portable_role"
  printf 'codex_role_map_input=%s\n' "$profile_role_input"
  printf 'concrete_role_check=preflight.sh role %s\n' "$profile_role_input"
  printf 'model=role-profile\n'
  printf 'reasoning=select-via-codex-agent\n'
  printf 'available=1\n'
  printf 'status=role-profile\n'
  exit 0
fi

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
    "fast reviewer"|"fast fact checker"|"fast fact-checker"|"fast writer"|"fast tool worker")
      family=fast
      ;;
    "fast implementer")
      family=implementer
      ;;
    "deep reviewer"|"deep maker"|"deep editor"|"deep orchestrator")
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
      family=balanced
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
    model=${AGENT_MODEL_LUNA:-${AGENT_MODEL_FAST:-$CFG_TIER_LIGHT_MODEL}}
    reasoning=${AGENT_REASONING_LUNA:-${AGENT_REASONING_FAST:-$CFG_TIER_LIGHT_EFFORT}}
    [ -n "${AGENT_MODEL_LUNA:-}${AGENT_REASONING_LUNA:-}${AGENT_MODEL_FAST:-}${AGENT_REASONING_FAST:-}" ] && status=configured || status=default
    ;;
  implementer)
    model=${AGENT_MODEL_SOL:-${AGENT_MODEL_DEEP:-$CFG_TIER_DEEP_MODEL}}
    reasoning=${AGENT_REASONING_SOL:-$CFG_ROLE_FAST_IMPLEMENTER_EFFORT}
    [ -n "${AGENT_MODEL_SOL:-}${AGENT_REASONING_SOL:-}${AGENT_MODEL_DEEP:-}" ] && status=configured || status=default
    ;;
  deep)
    model=${AGENT_MODEL_DEEP:-$CFG_TIER_DEEP_MODEL}
    reasoning=${AGENT_REASONING_DEEP:-$CFG_TIER_DEEP_EFFORT}
    [ -n "${AGENT_MODEL_DEEP:-}${AGENT_REASONING_DEEP:-}" ] && status=configured || status=default
    ;;
  external)
    if [ "$available" -eq 0 ] && [ -z "${AGENT_MODEL_EXTERNAL:-}" ] && [ -z "${AGENT_EXTERNAL_CMD:-}" ]; then
      model=unconfigured
    elif [ -n "${AGENT_EXTERNAL_CMD:-}" ] && [ -z "${AGENT_MODEL_EXTERNAL:-}" ]; then
      model=external-command
    else
      model=${AGENT_MODEL_EXTERNAL:-$CFG_TIER_DEEP_MODEL}
    fi
    reasoning=${AGENT_REASONING_EXTERNAL:-$CFG_TIER_DEEP_EFFORT}
    [ "$available" -eq 1 ] && status=configured
    ;;
  balanced)
    model=${AGENT_MODEL_BALANCED:-${AGENT_MODEL_ORCHESTRATOR:-$CFG_TIER_LIGHT_MODEL}}
    reasoning=${AGENT_REASONING_BALANCED:-${AGENT_REASONING_ORCHESTRATOR:-$CFG_TIER_LIGHT_EFFORT}}
    [ -n "${AGENT_MODEL_BALANCED:-}${AGENT_REASONING_BALANCED:-}${AGENT_MODEL_ORCHESTRATOR:-}${AGENT_REASONING_ORCHESTRATOR:-}" ] && status=configured || status=default
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
