#!/bin/sh
# Portable file-list verification runner (CONVENTIONS §4.2).
#
# Verification and scan commands must not depend on the invoking shell's
# dialect: zsh does not word-split unquoted expansions, so newline-joined
# file lists silently collapse into a single path, and Bash-only builtins
# such as `mapfile` fail outright.  This helper owns the file-list plumbing
# with null-delimited passing so the caller never word-splits anything.
#
# Usage:
#   verify-files.sh [--root DIR] [--name GLOB]... [--path GLOB]...
#                   [--exclude-path GLOB]... [--max-args N]
#                   { --print0 | -- COMMAND [ARG...] }
#
#   --root DIR          search root (default: current directory)
#   --name GLOB         include files whose basename matches GLOB (OR-joined)
#   --path GLOB         include files whose full path matches GLOB (OR-joined)
#   --exclude-path GLOB prune any path matching GLOB
#   --max-args N        pass at most N files per COMMAND invocation
#   --print0            print the matched list NUL-delimited instead of running
#
# The matched list is deterministic (sorted, NUL-safe).  Run mode keeps xargs
# semantics: 0 on success, 123 when any COMMAND invocation failed; usage
# errors exit 2.  An empty match runs nothing and exits 0.

# Keep behavior identical when an agent runs this file with zsh directly.
if [ -n "${ZSH_VERSION:-}" ]; then
  emulate sh 2>/dev/null || true
fi
set -eu

usage() {
  sed -n '2,24p' "$0" | sed 's/^#\( \{0,1\}\)\{0,1\}//'
}

fail_usage() {
  printf 'verify-files: %s\n' "$1" >&2
  usage >&2
  exit 2
}

root=.
max_args=""
mode=""
us=$(printf '\037')
names=""
paths=""
excludes=""

while [ $# -gt 0 ]; do
  case $1 in
    --root)
      [ $# -ge 2 ] || fail_usage "--root requires a value"
      root=$2; shift 2 ;;
    --name)
      [ $# -ge 2 ] || fail_usage "--name requires a value"
      names="${names}${us}$2"; shift 2 ;;
    --path)
      [ $# -ge 2 ] || fail_usage "--path requires a value"
      paths="${paths}${us}$2"; shift 2 ;;
    --exclude-path)
      [ $# -ge 2 ] || fail_usage "--exclude-path requires a value"
      excludes="${excludes}${us}$2"; shift 2 ;;
    --max-args)
      [ $# -ge 2 ] || fail_usage "--max-args requires a value"
      case $2 in
        ''|*[!0-9]*) fail_usage "--max-args must be a positive integer" ;;
      esac
      max_args=$2; shift 2 ;;
    --print0)
      mode=print0; shift ;;
    --help|-h)
      usage; exit 0 ;;
    --)
      shift
      [ $# -gt 0 ] || fail_usage "-- requires a command"
      mode=run
      break ;;
    *)
      fail_usage "unknown argument: $1" ;;
  esac
done

[ -n "$mode" ] || fail_usage "choose --print0 or -- COMMAND"
[ -d "$root" ] || fail_usage "root is not a directory: $root"

# Emit "<flag>\037<pattern>" pairs as an OR-joined find expression appended to
# the function-local positional parameters.  Word-splitting is confined to the
# unit-separator IFS and globbing is disabled while patterns expand.
# list_files builds its own positional scope, so the caller's "$@" (the run
# command) stays untouched.
list_files() {
  set --
  if [ -n "$excludes" ]; then
    set -- "$@" '('
    first=1
    old_ifs=$IFS
    IFS=$us
    set -f
    for pattern in $excludes; do
      [ -n "$pattern" ] || continue
      if [ "$first" -eq 1 ]; then first=0; else set -- "$@" -o; fi
      set -- "$@" -path "$pattern"
    done
    set +f
    IFS=$old_ifs
    set -- "$@" ')' -prune -o
  fi
  if [ -n "$names$paths" ]; then
    set -- "$@" '('
    first=1
    old_ifs=$IFS
    IFS=$us
    set -f
    for pattern in $names; do
      [ -n "$pattern" ] || continue
      if [ "$first" -eq 1 ]; then first=0; else set -- "$@" -o; fi
      set -- "$@" -name "$pattern"
    done
    for pattern in $paths; do
      [ -n "$pattern" ] || continue
      if [ "$first" -eq 1 ]; then first=0; else set -- "$@" -o; fi
      set -- "$@" -path "$pattern"
    done
    set +f
    IFS=$old_ifs
    set -- "$@" ')'
  fi
  find "$root" "$@" -type f -print0 | LC_ALL=C sort -z
}

if [ "$mode" = "print0" ]; then
  list_files
  exit 0
fi

if [ -n "$max_args" ]; then
  list_files | xargs -0 -r -n "$max_args" -- "$@"
else
  list_files | xargs -0 -r -- "$@"
fi
