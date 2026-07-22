#!/bin/bash
# HARD: persistent code analysis exists, source is unchanged, downstream spec/plan was not substituted.
set -u
WORK="$1"; T="$2"; fail=0

analysis=$(find "$WORK" -path '*/.agent_reports/analysis_project/code/*' -type f \
  \( -name '*.md' -o -name '*.yaml' \) 2>/dev/null | head -1)
if [ -n "$analysis" ] && [ -s "$analysis" ]; then
  echo "PASS: persistent analyze-project artifact exists ($analysis)"
else
  echo "FAIL: explicit initial analysis request produced no analysis_project/code artifact"; fail=1
fi

repo=$(find "$WORK" -type d -name .git -printf '%h\n' 2>/dev/null | head -1)
if [ -n "$repo" ]; then
  (cd "$repo" && git ls-files -s) > "$WORK/.pre/source-index.current"
fi
if [ -n "$repo" ] && cmp -s "$WORK/.pre/source-index.current" "$WORK/.pre/source-index.baseline"; then
  echo "PASS: tracked source index unchanged"
else
  echo "FAIL: analysis request changed or removed tracked source"; fail=1
fi

if [ -z "$(find "$WORK" \( -path '*/.agent_reports/spec/prd.md' -o -path '*/.agent_reports/plans/*/plan.md' \) -type f 2>/dev/null | head -1)" ]; then
  echo "PASS: downstream spec/code plan not substituted for analyze-project"
else
  echo "FAIL: initial analysis request was over-routed to spec/code planning"; fail=1
fi

exit $fail
