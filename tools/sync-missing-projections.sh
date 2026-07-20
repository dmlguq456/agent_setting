#!/bin/sh
# Fill missing Claude concrete counterparts for manually mirrored source
# domains (loops/, scaffolds/). Copies only paths that do not exist on the
# adapter side, so intentional adapter-owned divergence is never overwritten.
# Detection ownership stays with tools/check-adaptation-boundary.sh; this is
# the matching recovery command for its missing-counterpart failures.
set -eu

cd "$(dirname "$0")/.."

created=0

sync_path() {
  domain=$1
  p=$2
  # Gitignored runtime output is outside projection parity (same exception
  # as check_claude_loop_projection).
  git check-ignore -q "$p" 2>/dev/null && return 0
  rel=${p#"$domain"/}
  adapter_p="adapters/claude/$domain/$rel"
  [ -e "$adapter_p" ] && return 0
  if [ -d "$p" ]; then
    mkdir -p "$adapter_p"
  elif [ -f "$p" ]; then
    mkdir -p "$(dirname "$adapter_p")"
    cp -p "$p" "$adapter_p"
  else
    return 0
  fi
  echo "created $adapter_p"
  created=$((created + 1))
}

# Source walks mirror the corresponding check-adaptation-boundary.sh checks.
for p in $(find loops -mindepth 1 -print); do
  sync_path loops "$p"
done
for p in $(find scaffolds -mindepth 1 ! -name '.*' -print); do
  sync_path scaffolds "$p"
done

if [ "$created" -eq 0 ]; then
  echo "all Claude loop/scaffold counterparts already present"
else
  echo "filled $created missing counterpart(s); review and commit them with the source change"
fi
