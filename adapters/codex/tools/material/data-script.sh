#!/usr/bin/env sh
# Codex adapter-owned material data-script launcher.
set -eu

usage() {
  cat <<'EOF'
usage: data-script.sh [--check] <script.py> [-- args...]

Checks or runs a Python data-analysis script through a Codex-owned material
tool-contract surface. With --check, only Python syntax is verified.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

printf 'adapter=codex\n'
printf 'runtime_surface=adapter-owned-data-script\n'
printf 'tool_contract=data-script\n'

if [ "$#" -eq 0 ]; then
  printf 'status=tool-contract\n'
  printf 'tool_contract_check=adapters/codex/bin/preflight.sh data-script --check <script.py>\n'
  printf 'fallback=satisfy-tool-contract-or-report-unavailable\n'
  exit 0
fi

check_only=0
if [ "${1:-}" = "--check" ]; then
  check_only=1
  shift
fi

[ "$#" -ge 1 ] || { echo "codex data-script: script path required" >&2; exit 64; }
script=$1
shift
if [ "${1:-}" = "--" ]; then
  shift
fi

if ! command -v python3 >/dev/null 2>&1; then
  printf 'status=tool-contract\n'
  printf 'reason=python-unavailable\n'
  exit 69
fi

if [ ! -f "$script" ]; then
  printf 'status=unavailable\n'
  printf 'reason=file-not-found\n'
  printf 'file=%s\n' "$script"
  exit 66
fi

printf 'file=%s\n' "$script"
if detail=$(python3 -c "import sys; compile(open(sys.argv[1], encoding='utf-8').read(), sys.argv[1], 'exec')" "$script" 2>&1); then
  printf 'check=python-compile\n'
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
