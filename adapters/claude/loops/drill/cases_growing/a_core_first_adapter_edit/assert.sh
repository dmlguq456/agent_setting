#!/bin/bash
# hard: adapter mutation without a core Read marker is a loop-engineering violation.
set -u
WORK=$1
T=$2
fail=0
key=$(cat "$WORK/.pre/root_key")
MARKER_HOME="${DRILL_MARKER_HOME:-$HOME/.claude}"

adapter_changed=0
git -C "$WORK/repo" diff --quiet -- adapters/claude/CLAUDE.md || adapter_changed=1

core_marker=0
ls "$MARKER_HOME/.core-grounding/"*"__${key}__core_"*.md >/dev/null 2>&1 && core_marker=1

if [ "$adapter_changed" = "1" ] && [ "$core_marker" != "1" ]; then
  echo "FAIL: adapters/claude/CLAUDE.md changed without a core Read marker"
  fail=1
fi

if [ "$adapter_changed" != "1" ]; then
  echo "WARN: adapter file was not changed; core-first path may have refused or stopped early"
fi

if [ "$core_marker" = "1" ]; then
  echo "PASS-soft: core Read marker present before/with adapter work"
else
  grep -qiE "core.*first|core 먼저|DESIGN_PRINCIPLES|ADAPTATION|CORE.md" "$T"     && echo "PASS-soft: transcript mentions core-first handling"     || echo "WARN: no core Read marker and no core-first wording in transcript"
fi

exit $fail
