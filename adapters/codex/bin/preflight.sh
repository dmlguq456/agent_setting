#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)

usage() {
  cat <<'EOF'
usage: preflight.sh write <file> [session-id]
       preflight.sh read <file> [session-id]
       preflight.sh capability <name> [cwd] [session-id]
       preflight.sh skill <name> [cwd] [session-id]
       preflight.sh mode [cwd] [session-id]

Runs portable checks that Codex can call without consuming Claude hook JSON or
settings.json.
EOF
}

cmd=${1:-}
case "$cmd" in
  write)
    [ "$#" -ge 2 ] || { echo "codex preflight: write requires a file path" >&2; exit 64; }
    file=$2
    sid=${3:-codex}
    "$ROOT/hooks/git-state-guard.sh" --file "$file"
    "$ROOT/hooks/artifact-guard.sh" --file "$file" --session "$sid"
    "$ROOT/hooks/builtin-memory-guard.sh" --file "$file"
    ;;
  read)
    [ "$#" -ge 2 ] || { echo "codex preflight: read requires a file path" >&2; exit 64; }
    file=$2
    sid=${3:-codex}
    "$ROOT/hooks/spec-read-marker.sh" --file "$file" --session "$sid"
    ;;
  capability|skill)
    [ "$#" -ge 2 ] || { echo "codex preflight: $cmd requires a capability name" >&2; exit 64; }
    name=$2
    cwd=${3:-$PWD}
    sid=${4:-codex}
    "$ROOT/hooks/spec-skill-gate.sh" --skill "$name" --cwd "$cwd" --session "$sid"
    ;;
  mode)
    cwd=${2:-$PWD}
    sid=${3:-codex}
    "$ROOT/utilities/workflow-guard-hook.sh" --event prompt --cwd "$cwd" --session "$sid" --format text
    ;;
  -h|--help|"")
    usage
    exit 0
    ;;
  *)
    echo "codex preflight: unknown command: $cmd" >&2
    usage >&2
    exit 64
    ;;
esac
