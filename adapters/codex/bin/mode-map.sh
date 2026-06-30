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

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v git >/dev/null 2>&1 && ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null); then
  :
else
  ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)
fi
if [ ! -f "$ROOT/$source" ]; then
  echo "codex mode-map: unknown mode: $mode" >&2
  exit 64
fi

status=unsupported
realization=compat-reference
requirement=""
tool_contract=""
tool_contract_check=""
runtime_surface=""
fallback=""
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
    fallback="satisfy-tool-contract-or-report-unavailable"
    case "$name" in
      browser-fetch) tool_contract=browser-fetch ;;
      data-script)
        tool_contract=data-script
        tool_contract_check="adapters/codex/bin/preflight.sh data-script --check <script.py>"
        runtime_surface=adapter-owned-data-script
        ;;
      figure-gen) tool_contract=figure-gen ;;
      pdf-extract) tool_contract=pdf-extract ;;
      web-image-search) tool_contract=web-image-search ;;
      *) tool_contract=material-tooling ;;
    esac
    if [ "$name" = "data-script" ]; then
      requirement="run the adapter-owned Python data-script launcher for generated analysis scripts, or report unavailable"
    else
      requirement="provide the named browser/pdf/script/web tool contract or report unavailable"
    fi
    ;;
  design)
    status=unsupported
    realization=adapter-coupled
    tool_contract=visual-harness
    tool_contract_check="adapters/codex/bin/preflight.sh visual-harness <file.html>"
    runtime_surface=adapter-owned-visual-harness
    fallback=reference-only
    requirement="adapter-owned visual harness must be run for concrete design outputs; mode fragment remains reference-only"
    ;;
  qa)
    case "$name" in
      security-review|test)
        status=tool-contract
        realization=portable-with-tool-contract
        fallback="satisfy-tool-contract-or-report-unavailable"
        case "$name" in
          security-review) tool_contract=security-review ;;
          test)
            tool_contract=verification-runner
            tool_contract_check="adapters/codex/bin/preflight.sh verification-runner --check -- <command>"
            runtime_surface=adapter-owned-verification-runner
            ;;
        esac
        if [ "$name" = "test" ]; then
          requirement="run explicit verification commands through the adapter-owned verification runner, or report unavailable"
        else
          requirement="replace Claude-derived security-review notes with Codex-native commands"
        fi
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
        fallback="satisfy-tool-contract-or-report-unavailable"
        tool_contract=external-claim-verification
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
if [ -n "$tool_contract" ]; then
  printf 'tool_contract=%s\n' "$tool_contract"
fi
if [ -n "$tool_contract_check" ]; then
  printf 'tool_contract_check=%s\n' "$tool_contract_check"
fi
if [ -n "$runtime_surface" ]; then
  printf 'runtime_surface=%s\n' "$runtime_surface"
fi
if [ -n "$fallback" ]; then
  printf 'fallback=%s\n' "$fallback"
fi
printf 'requirement=%s\n' "$requirement"
printf 'note=%s\n' "$note"
