#!/usr/bin/env sh
# OpenCode adapter-owned material PDF extraction launcher.
set -eu

usage() {
  cat <<'EOF'
usage: pdf-extract.sh [--check] <file.pdf> [--out <file.txt>]

Checks or extracts text from a PDF through an OpenCode-owned material
tool-contract surface. Exit 69 means the local PDF extraction tool is
unavailable.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

printf 'adapter=opencode\n'
printf 'runtime_surface=adapter-owned-pdf-extract\n'
printf 'tool_contract=pdf-extract\n'

if [ "$#" -eq 0 ]; then
  printf 'status=tool-contract\n'
  printf 'tool_contract_check=adapters/opencode/bin/preflight.sh pdf-extract --check <file.pdf>\n'
  printf 'fallback=satisfy-tool-contract-or-report-unavailable\n'
  exit 0
fi

check_only=0
if [ "${1:-}" = "--check" ]; then
  check_only=1
  shift
fi

[ "$#" -ge 1 ] || { echo "opencode pdf-extract: PDF path required" >&2; exit 64; }
pdf=$1
shift
out=""
if [ "${1:-}" = "--out" ]; then
  [ "$#" -eq 2 ] || { echo "opencode pdf-extract: --out requires one output path" >&2; exit 64; }
  out=$2
  shift 2
fi
[ "$#" -eq 0 ] || { echo "opencode pdf-extract: unexpected arguments: $*" >&2; exit 64; }

if [ ! -f "$pdf" ]; then
  printf 'status=unavailable\n'
  printf 'reason=file-not-found\n'
  printf 'file=%s\n' "$pdf"
  exit 66
fi

case "$pdf" in
  *.pdf|*.PDF) ;;
  *)
    printf 'status=unavailable\n'
    printf 'reason=not-pdf\n'
    printf 'file=%s\n' "$pdf"
    exit 65
    ;;
esac

if ! command -v pdftotext >/dev/null 2>&1; then
  printf 'status=tool-contract\n'
  printf 'reason=pdftotext-unavailable\n'
  exit 69
fi

printf 'file=%s\n' "$pdf"
printf 'check=pdftotext\n'
if [ "$check_only" -eq 1 ]; then
  if pdftotext "$pdf" - >/dev/null 2>&1; then
    printf 'status=ok\n'
    exit 0
  fi
  printf 'status=failed\n'
  printf 'reason=extract-check-failed\n'
  exit 2
fi

if [ -n "$out" ]; then
  if pdftotext "$pdf" "$out"; then
    printf 'output=%s\n' "$out"
    printf 'status=ok\n'
    exit 0
  fi
else
  if pdftotext "$pdf" -; then
    printf 'status=ok\n'
    exit 0
  fi
fi

printf 'status=failed\n'
printf 'reason=extract-failed\n'
exit 2
