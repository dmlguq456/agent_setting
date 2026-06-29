#!/usr/bin/env sh
set -eu

usage() {
  cat <<'EOF'
usage: mode-map.sh <family>/<mode>

Prints how the Codex adapter may consume an agent mode fragment.
EOF
}

[ "${1:-}" != "-h" ] && [ "${1:-}" != "--help" ] || { usage; exit 0; }
[ "$#" -eq 1 ] || { usage >&2; exit 64; }

mode=$1
case "$mode" in
  */*) ;;
  *) echo "codex mode-map: expected <family>/<mode>: $mode" >&2; exit 64 ;;
esac

family=${mode%%/*}
name=${mode#*/}
source="roles/modes/$family/$name.md"

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
if [ ! -f "$ROOT/$source" ]; then
  echo "codex mode-map: unknown mode: $mode" >&2
  exit 64
fi

status=unsupported
realization=compat-reference
requirement=""
note=""

case "$family" in
  dev|editorial)
    status=portable
    realization=portable-persona
    requirement="codex edit/read tools plus normal preflight guards"
    ;;
  material)
    status=tool-contract
    realization=portable-with-tool-contract
    requirement="provide equivalent browser/pdf/script/web fetch tools or report unavailable"
    ;;
  design)
    status=unsupported
    realization=adapter-coupled
    requirement="Codex-native visual/browser verification harness required"
    ;;
  qa)
    case "$name" in
      security-review|test)
        status=tool-contract
        realization=portable-with-tool-contract
        requirement="replace Claude-derived verify/security-review notes with Codex-native commands"
        ;;
      *)
        status=portable
        realization=portable-persona
        requirement="read-only review with Codex file/test tools"
        ;;
    esac
    ;;
  research)
    case "$name" in
      claim-verify)
        status=tool-contract
        realization=portable-with-tool-contract
        requirement="provide WebSearch/WebFetch or cite unavailable external verification"
        ;;
      *)
        status=portable
        realization=portable-persona
        requirement="read/cite primary sources through available Codex tools"
        ;;
    esac
    ;;
  *)
    status=unsupported
    realization=unknown-family
    requirement="add adapter mapping before use"
    ;;
esac

case "$status" in
  portable)
    note="Codex may use the mode fragment after reading roles/MODES.md and resolving portable roles."
    ;;
  tool-contract)
    note="Codex may use the persona only after satisfying or explicitly downgrading the named tool contract."
    ;;
  unsupported)
    note="Codex must not claim native support; use as reference only."
    ;;
esac

printf 'mode=%s\n' "$mode"
printf 'adapter=codex\n'
printf 'source=%s\n' "$source"
printf 'status=%s\n' "$status"
printf 'realization=%s\n' "$realization"
printf 'requirement=%s\n' "$requirement"
printf 'note=%s\n' "$note"
