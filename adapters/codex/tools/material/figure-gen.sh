#!/usr/bin/env sh
# Codex adapter-owned material figure-gen launcher.
set -eu

usage() {
  cat <<'EOF'
usage: figure-gen.sh [--check] <script.py> [-- args...]
       figure-gen.sh --verify-report <manifest.json> <report.md>

Checks or runs a generated matplotlib/seaborn figure script through a
Codex-owned material tool-contract surface. With --check, only Python syntax
and matplotlib availability are verified. --verify-report runs the portable
fail-closed spectrogram metadata, claim-evidence, and visual-review gate.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

printf 'adapter=codex\n'
printf 'runtime_surface=adapter-owned-figure-gen\n'
printf 'tool_contract=figure-gen\n'

if [ "$#" -eq 0 ]; then
  printf 'status=tool-contract\n'
  printf 'tool_contract_check=adapters/codex/bin/preflight.sh figure-gen --check <script.py>\n'
  printf 'fallback=satisfy-tool-contract-or-report-unavailable\n'
  exit 0
fi

if [ "${1:-}" = "--verify-report" ]; then
  shift
  [ "$#" -eq 2 ] || { echo "codex figure-gen: --verify-report requires manifest and report" >&2; exit 64; }
  SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
  if command -v git >/dev/null 2>&1 && ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null); then
    :
  else
    ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../../.." && pwd)
  fi
  if ! command -v python3 >/dev/null 2>&1 || [ ! -f "$ROOT/tools/figure-semantic-verify.py" ]; then
    printf 'status=tool-contract\nreason=figure-semantic-verifier-unavailable\n'
    exit 69
  fi
  exec python3 "$ROOT/tools/figure-semantic-verify.py" --manifest "$1" --report "$2"
fi

check_only=0
if [ "${1:-}" = "--check" ]; then
  check_only=1
  shift
fi

[ "$#" -ge 1 ] || { echo "codex figure-gen: script path required" >&2; exit 64; }
script=$1
shift
if [ "${1:-}" = "--" ]; then
  shift
fi

if [ ! -f "$script" ]; then
  printf 'status=unavailable\n'
  printf 'reason=file-not-found\n'
  printf 'file=%s\n' "$script"
  exit 66
fi

if ! command -v python3 >/dev/null 2>&1; then
  printf 'status=tool-contract\n'
  printf 'reason=python-unavailable\n'
  exit 69
fi

if ! python3 - <<'PY' >/dev/null 2>&1
import matplotlib
PY
then
  printf 'status=tool-contract\n'
  printf 'reason=matplotlib-unavailable\n'
  exit 69
fi

printf 'file=%s\n' "$script"
if detail=$(python3 -c "import sys; compile(open(sys.argv[1], encoding='utf-8').read(), sys.argv[1], 'exec')" "$script" 2>&1); then
  printf 'check=python-compile\n'
  printf 'check_matplotlib=available\n'
else
  printf 'status=failed\n'
  printf 'reason=syntax-error\n'
  printf 'detail=%s\n' "$(printf '%s' "$detail" | tr '\n' ' ')"
  exit 2
fi

if [ "$check_only" -eq 1 ]; then
  printf 'status=ok\n'
  exit 0
fi

python3 "$script" "$@"
rc=$?
if [ "$rc" -eq 0 ]; then
  printf 'status=ok\n'
else
  printf 'status=failed\n'
fi
exit "$rc"
