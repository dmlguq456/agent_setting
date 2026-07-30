#!/bin/sh
# Optional app-neutral artifact sink adapter.
# Registration is one absolute executable path in AGENT_ARTIFACT_SINK_COMMAND.
set -u

unavailable() {
  printf '%s\n' 'state=unavailable' 'reason=extension-unavailable'
  exit 69
}

handler=${AGENT_ARTIFACT_SINK_COMMAND:-}
case "$handler" in
  /*) ;;
  *) unavailable ;;
esac
case "$handler" in
  *[[:space:]]*|*\;*|*\|*|*\&*|*\>*|*\<*|*\**|*\?*|*\[*|*\]*|*\(*|*\)*|*\`*|*\$*) unavailable ;;
esac
[ -f "$handler" ] && [ -x "$handler" ] && [ ! -L "$handler" ] || unavailable
handler_real=$(realpath -- "$handler" 2>/dev/null) || unavailable
[ "$handler" = "$handler_real" ] || unavailable
handler=$handler_real

case "${1:-}" in
  --check)
    [ "$#" -eq 1 ] || exit 64
    exec "$handler" --check
    ;;
  emit)
    shift
    source_path=""
    source_capability=""
    project_root=""
    completed_at=""
    while [ "$#" -gt 0 ]; do
      case "$1" in
        --source) [ "$#" -ge 2 ] || exit 64; source_path=$2; shift 2 ;;
        --capability) [ "$#" -ge 2 ] || exit 64; source_capability=$2; shift 2 ;;
        --project-root) [ "$#" -ge 2 ] || exit 64; project_root=$2; shift 2 ;;
        --completed-at) [ "$#" -ge 2 ] || exit 64; completed_at=$2; shift 2 ;;
        *) exit 64 ;;
      esac
    done
    ;;
  *) exit 64 ;;
esac

[ -n "$source_path" ] && [ -n "$source_capability" ] && [ -n "$project_root" ] || exit 64
case "$source_capability" in
  ''|[!a-z]*|*[!a-z0-9-]*) exit 64 ;;
esac
[ "${#source_capability}" -le 64 ] || exit 64
[ -f "$source_path" ] && [ ! -L "$source_path" ] || exit 64
source_path=$(realpath -- "$source_path" 2>/dev/null) || exit 64
project_root=$(realpath -- "$project_root" 2>/dev/null) || exit 64
[ -f "$source_path" ] && [ -d "$project_root" ] || exit 64
case "$source_path" in "$project_root"/*) ;; *) exit 64 ;; esac
[ -n "$completed_at" ] || completed_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)

umask 077
receipt=$(mktemp "${TMPDIR:-/tmp}/artifact-receipt.XXXXXX") || exit 70
trap 'rm -f -- "$receipt"' EXIT HUP INT TERM
python3 - "$receipt" "$source_path" "$source_capability" "$project_root" "$completed_at" <<'PY'
import json, os, sys
from datetime import datetime
target, source, capability, root, completed_at = sys.argv[1:]
try:
    parsed = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError
except ValueError:
    raise SystemExit(64)
value = {
    "schema_version": 1,
    "event": "artifact.completed",
    "source_path": source,
    "source_capability": capability,
    "project_root": root,
    "status": "completed",
    "completed_at": completed_at,
}
with open(target, "w", encoding="utf-8") as handle:
    json.dump(value, handle, ensure_ascii=False, separators=(",", ":"))
    handle.write("\n")
os.chmod(target, 0o600)
PY
write_status=$?
[ "$write_status" -eq 0 ] || { [ "$write_status" -eq 64 ] && exit 64; exit 70; }
"$handler" --receipt "$receipt"
