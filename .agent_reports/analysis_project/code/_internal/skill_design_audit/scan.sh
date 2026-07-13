#!/usr/bin/env bash
# Skill-Design Audit — Step 1-2 deterministic scan (Pocock rubric)
# Step 1: frontmatter invocation classification (model vs user, "Use when" trigger)
# Step 2: quantitative norms (<500 lines, references 1-depth, description 3rd person / "Use when")
# Output: TSV to stdout + raw dumps. Run from worktree root.
set -euo pipefail
SKILLS_DIR="${1:-skills}"

printf "name\tbody_lines\tline_ok\tdisable_model\tinvocation\tuse_when\tdesc_has_hangul\tref_dir\tref_depth_ok\tref_files\n"

for f in "$SKILLS_DIR"/*/SKILL.md; do
  name=$(basename "$(dirname "$f")")
  # frontmatter block = between first two '---'
  fm=$(awk 'BEGIN{c=0} /^---[[:space:]]*$/{c++; next} c==1{print} c>=2{exit}' "$f")
  body_lines=$(wc -l < "$f" | tr -d ' ')
  line_ok=$([ "$body_lines" -lt 500 ] && echo "Y" || echo "N")

  disable=$(printf '%s\n' "$fm" | grep -iE '^\s*disable-model-invocation:\s*true' >/dev/null 2>&1 && echo "true" || echo "false")
  invocation=$([ "$disable" = "true" ] && echo "user" || echo "model")

  desc=$(printf '%s\n' "$fm" | awk -F': ' '/^description:/{sub(/^description:[[:space:]]*/,""); print; exit}')
  # "Use when" trigger presence (case-insensitive, English trigger)
  use_when=$(printf '%s\n' "$desc" | grep -iE 'use when' >/dev/null 2>&1 && echo "Y" || echo "N")
  # description contains Hangul (Korean blurb — 3rd-person English norm check)
  desc_hangul=$(printf '%s\n' "$desc" | grep -P '[\x{AC00}-\x{D7A3}]' >/dev/null 2>&1 && echo "Y" || echo "N")

  # references: 1-depth check — references/ exists? any subdirectory under it (=2-depth violation)?
  refdir="$(dirname "$f")/references"
  if [ -d "$refdir" ]; then
    ref_dir="Y"
    nsub=$(find "$refdir" -mindepth 1 -type d | wc -l | tr -d ' ')
    ref_depth_ok=$([ "$nsub" -eq 0 ] && echo "Y" || echo "N")
    ref_files=$(find "$refdir" -maxdepth 1 -type f -name '*.md' | wc -l | tr -d ' ')
  else
    ref_dir="N"; ref_depth_ok="-"; ref_files="0"
  fi

  printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
    "$name" "$body_lines" "$line_ok" "$disable" "$invocation" "$use_when" "$desc_hangul" "$ref_dir" "$ref_depth_ok" "$ref_files"
done
