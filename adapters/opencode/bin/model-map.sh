#!/usr/bin/env sh
set -eu
case "${1:-}" in -h|--help|'') echo 'usage: model-map.sh <portable-role>'; exit 0;; esac
# OpenCode model inventory/acceptance is runtime-configured and intentionally unknown.
printf 'adapter=opencode\nstatus=unknown\nfamily=unknown\nexact_model_id=unknown\nreasoning=unknown\nreason=runtime-model-inventory-probe-not-supported\n'
