#!/usr/bin/env sh
set -eu

usage() {
  cat <<'EOF'
usage: mode-map.sh <family>/<mode>

Prints how the OpenCode adapter may consume an agent mode fragment.
EOF
}

[ "${1:-}" != "-h" ] && [ "${1:-}" != "--help" ] || { usage; exit 0; }
[ "$#" -eq 1 ] || { usage >&2; exit 64; }

mode=$1
case "$mode" in
  */*) ;;
  *) echo "opencode mode-map: expected <family>/<mode>: $mode" >&2; exit 64 ;;
esac

family=${mode%%/*}
name=${mode#*/}
source="roles/modes/$family/$name.md"

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v git >/dev/null 2>&1 && ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null); then
  :
else
  ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)
fi
if [ ! -f "$ROOT/$source" ]; then
  echo "opencode mode-map: unknown mode: $mode" >&2
  exit 64
fi

status=unsupported
realization=compat-reference
requirement=""
tool_contract=""
note=""

case "$family" in
  dev|editorial)
    status=portable
    realization=portable-persona
    requirement="opencode edit/read tools plus normal preflight guards"
    ;;
  material)
    status=tool-contract
    realization=portable-with-tool-contract
    case "$name" in
      browser-fetch) tool_contract=browser-fetch ;;
      data-script) tool_contract=data-script ;;
      figure-gen) tool_contract=figure-gen ;;
      pdf-extract) tool_contract=pdf-extract ;;
      web-image-search) tool_contract=web-image-search ;;
      *) tool_contract=material-tooling ;;
    esac
    requirement="provide the named browser/pdf/script/web tool contract or report unavailable"
    ;;
  design)
    status=unsupported
    realization=adapter-coupled
    requirement="opencode-native visual/browser verification harness required"
    ;;
  qa)
    case "$name" in
      security-review|test)
        status=tool-contract
        realization=portable-with-tool-contract
        case "$name" in
          security-review) tool_contract=security-review ;;
          test) tool_contract=verification-runner ;;
        esac
        requirement="replace Claude-derived verify/security-review notes with OpenCode-native commands"
        ;;
      *)
        status=portable
        realization=portable-persona
        requirement="read-only review with OpenCode file/test tools"
        ;;
    esac
    ;;
  research)
    case "$name" in
      claim-verify)
        status=tool-contract
        realization=portable-with-tool-contract
        tool_contract=external-claim-verification
        requirement="provide webfetch/websearch or cite unavailable external verification"
        ;;
      *)
        status=portable
        realization=portable-persona
        requirement="read/cite primary sources through available OpenCode tools"
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
    note="OpenCode may use the mode fragment after reading roles/MODES.md and resolving portable roles."
    ;;
  tool-contract)
    note="OpenCode may use the persona only after satisfying or explicitly downgrading the named tool contract."
    ;;
  unsupported)
    note="OpenCode must not claim native support; use as reference only."
    ;;
esac

printf 'mode=%s\n' "$mode"
printf 'adapter=opencode\n'
printf 'source=%s\n' "$source"
printf 'status=%s\n' "$status"
printf 'realization=%s\n' "$realization"
if [ -n "$tool_contract" ]; then
  printf 'tool_contract=%s\n' "$tool_contract"
fi
printf 'requirement=%s\n' "$requirement"
printf 'note=%s\n' "$note"
