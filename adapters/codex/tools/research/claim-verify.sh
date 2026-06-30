#!/usr/bin/env sh
# Codex adapter-owned research claim-verify launcher.
set -eu

usage() {
  cat <<'EOF'
usage: claim-verify.sh [--check] <claim> [--out <file>]

Checks or runs a configured external claim verification provider through a
Codex-owned research tool-contract surface. Set CODEX_CLAIM_VERIFY_CMD or
AGENT_CLAIM_VERIFY_CMD to an executable provider command. Exit 69 means no
provider is configured or available.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

printf 'adapter=codex\n'
printf 'runtime_surface=adapter-owned-claim-verify\n'
printf 'tool_contract=external-claim-verification\n'

if [ "$#" -eq 0 ]; then
  printf 'status=tool-contract\n'
  printf 'tool_contract_check=adapters/codex/bin/preflight.sh claim-verify --check <claim>\n'
  printf 'fallback=satisfy-tool-contract-or-report-unavailable\n'
  exit 0
fi

check_only=0
out=""
claim=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --check)
      check_only=1
      shift
      ;;
    --out)
      [ "$#" -ge 2 ] || { echo "codex claim-verify: --out requires a file" >&2; exit 64; }
      out=$2
      shift 2
      ;;
    --*)
      echo "codex claim-verify: unknown option: $1" >&2
      exit 64
      ;;
    *)
      if [ -z "$claim" ]; then
        claim=$1
      else
        claim="$claim $1"
      fi
      shift
      ;;
  esac
done

[ -n "$claim" ] || { echo "codex claim-verify: claim required" >&2; exit 64; }

provider=${CODEX_CLAIM_VERIFY_CMD:-${AGENT_CLAIM_VERIFY_CMD:-}}
if [ -z "$provider" ] || ! command -v "$provider" >/dev/null 2>&1; then
  printf 'status=tool-contract\n'
  printf 'reason=claim-verify-provider-unavailable\n'
  printf 'claim=%s\n' "$claim"
  exit 69
fi

printf 'provider=%s\n' "$provider"
printf 'claim=%s\n' "$claim"
if [ "$check_only" -eq 1 ]; then
  printf 'check=provider-available\n'
  printf 'status=ok\n'
  exit 0
fi

if [ -n "$out" ]; then
  "$provider" "$claim" >"$out"
  rc=$?
  printf 'output=%s\n' "$out"
else
  "$provider" "$claim"
  rc=$?
fi
if [ "$rc" -eq 0 ]; then
  printf 'status=ok\n'
else
  printf 'status=failed\n'
fi
exit "$rc"
