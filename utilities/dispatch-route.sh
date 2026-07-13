#!/usr/bin/env sh
# Deterministic, read-only dispatch candidate selector.
set -eu

stage=; capability=; intensity=standard; qa=; required=; adapter=; family=; role=; maker_family=; jobs=
while [ $# -gt 0 ]; do
  case "$1" in
    --stage) stage=${2:?}; shift 2;; --capability) capability=${2:?}; shift 2;;
    --intensity) intensity=${2:?}; shift 2;; --qa) qa=${2:?}; shift 2;;
    --required-surface) required="${required}${required:+,}${2:?}"; shift 2;;
    --adapter) adapter=${2:?}; shift 2;; --family) family=${2:?}; shift 2;;
    --role) role=${2:?}; shift 2;; --maker-family) maker_family=${2:?}; shift 2;;
    --jobs) jobs=${2:?}; shift 2;; -h|--help) echo 'usage: dispatch-route.sh --stage <stage> [--adapter claude|codex|opencode] [--family claude|gpt|unknown] [--role <portable-role>] [--maker-family claude|gpt] [--jobs <jobs.log>]'; exit 0;;
    *) echo "dispatch-route: unknown arg $1" >&2; exit 64;;
  esac
done
[ -n "$stage" ] || { echo 'dispatch-route: --stage is required' >&2; exit 64; }
case "$adapter" in ''|claude|codex|opencode) ;; *) echo "dispatch-route: unknown adapter: $adapter" >&2; exit 64;; esac
case "$family" in ''|claude|gpt|unknown) ;; *) echo "dispatch-route: unknown family: $family" >&2; exit 64;; esac
case "$maker_family" in ''|claude|gpt|unknown) ;; *) echo "dispatch-route: unknown maker family: $maker_family" >&2; exit 64;; esac
case "$adapter:$family" in claude:gpt|codex:claude|opencode:claude|opencode:gpt) echo 'dispatch-route: adapter/family conflict' >&2; exit 64;; esac

case "$stage" in
  plan|planning|architecture|decomposition) default_role='deep maker'; affinity=codex;;
  *review*|*test*|checker) default_role='deep reviewer'; affinity=diverse;;
  *) default_role='deep orchestrator'; affinity=neutral;;
esac
[ -n "$role" ] || role=$default_role
usage_script="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/usage-check.sh"
if [ -n "$jobs" ]; then usage=$($usage_script --harness all --jobs "$jobs"); else usage=$($usage_script --harness all); fi
state() { printf '%s\n' "$usage" | awk -v h="$1" '$1==h {print $2}'; }
bias=$(printf '%s\n' "$usage" | awk '$1=="bias" {print $2; exit}')
family_of() { [ "$1" = codex ] && printf gpt || printf claude; }
eligible() { s=$(state "$1"); [ "$s" != limited ] && [ "${s#limited(}" = "$s" ]; }

if [ "$adapter" = opencode ] || [ "$family" = unknown ]; then
  echo status=unknown; echo adapter=opencode; echo family=unknown; echo "role=$role"; echo exact_model_id=unknown; echo reasoning=unknown
  echo trace.1=explicit=${adapter:-none};eligibility=opencode-runtime-inventory-unknown
  echo unknown=opencode-runtime-model-inventory-unavailable
  exit 0
fi

choose=$adapter
[ -n "$choose" ] || case "$family" in gpt) choose=codex;; claude) choose=claude;; esac
if [ -z "$choose" ]; then
  case "$affinity:$maker_family" in
    codex:*) choose=codex;;
    diverse:claude) choose=codex;;
    diverse:gpt) choose=claude;;
    diverse:*) choose=${bias:-claude};;
    neutral:*) choose=${bias:-claude};;
  esac
fi
case "$choose" in claude|codex) ;; *) echo 'dispatch-route: no known candidate' >&2; exit 64;; esac

rejected=; fallback=
if ! eligible "$choose"; then
  s=$(state "$choose"); rejected="$choose:usage-$s"
  other=claude; [ "$choose" = claude ] && other=codex
  if eligible "$other"; then
    fallback="$other:known-limit-on-$choose"; choose=$other
  else
    echo status=unavailable; echo "role=$role"; echo "rejected.1=$rejected"; echo "rejected.2=$other:usage-$(state "$other")"; echo 'fallback.1=none:no-eligible-known-candidate'; exit 1
  fi
fi
case "$choose" in
  codex) map="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)/adapters/codex/bin/model-map.sh";;
  claude) map="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)/adapters/claude/bin/model-map.sh";;
esac
mapped=$($map "$role")
get() { printf '%s\n' "$mapped" | awk -F= -v k="$1" '$1==k {sub(/^[^=]*=/, ""); print; exit}'; }
echo status=eligible; echo "adapter=$choose"; echo "family=$(family_of "$choose")"; echo "role=$role"; echo "exact_model_id=$(get exact_model_id)"; echo "reasoning=$(get reasoning)"
[ -z "$rejected" ] || echo "rejected.1=$rejected"
[ -z "$fallback" ] || echo "fallback.1=$fallback"
echo "trace.1=explicit=${adapter:-none};family=${family:-none};eligibility=usage-$(state "$choose")"
echo "trace.2=affinity=$affinity;maker_family=${maker_family:-unknown};required=${required:-none};bias=${bias:-unknown}"
