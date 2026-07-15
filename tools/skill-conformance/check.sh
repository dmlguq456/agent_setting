#!/usr/bin/env bash
# Deterministic skill-design conformance gate.
# Combines scan.sh observations with the explicit invocation classification
# registry so deterministic checks and drill g7 cannot silently accept a forbidden frontmatter flip.
set -uo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$ROOT" ]; then
  ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
fi
SCAN="$SCRIPT_DIR/scan.sh"
DEFAULT_POLICY="$SCRIPT_DIR/invocation-policy.tsv"
POLICY="${SKILL_INVOCATION_POLICY:-$DEFAULT_POLICY}"

default_scope=0
if [ "$#" -eq 0 ]; then
  default_scope=1
  set -- \
    "$ROOT/skills" \
    "$ROOT/adapters/claude/skills" \
    "$ROOT/adapters/codex/skills" \
    "$ROOT/adapters/opencode/skills"
fi

fail=0
if [ ! -x "$SCAN" ]; then
  echo "FAIL: skill scan executable missing: $SCAN"
  exit 1
fi
if [ ! -f "$POLICY" ]; then
  echo "FAIL: invocation policy missing: $POLICY"
  exit 1
fi

declare -a policy_names=()
declare -A policy_class=()
parent_count=0
entry_count=0
while IFS=$'\t' read -r name class _rest; do
  name=${name%$'\r'}
  class=${class%$'\r'}
  [ -z "$name" ] && continue
  [[ "$name" == \#* ]] && continue
  case "$class" in
    user-only|parent-invoked|entry-router) ;;
    *) echo "FAIL: unknown invocation class '$class' for $name"; fail=1; continue ;;
  esac
  if [ -n "${policy_class[$name]+x}" ]; then
    echo "FAIL: duplicate invocation policy row: $name"
    fail=1
    continue
  fi
  policy_names+=("$name")
  policy_class[$name]="$class"
  [ "$class" = "parent-invoked" ] && parent_count=$((parent_count + 1))
  [ "$class" = "entry-router" ] && entry_count=$((entry_count + 1))
done < "$POLICY"

if [ "${#policy_names[@]}" -eq 0 ]; then
  echo "FAIL: invocation policy has no classified skills: $POLICY"
  exit 1
fi
if [ "$POLICY" = "$DEFAULT_POLICY" ] && [ "$parent_count" -ne 13 ]; then
  echo "FAIL: canonical parent-invoked registry must contain 13 skills (found $parent_count)"
  fail=1
fi
if [ "$POLICY" = "$DEFAULT_POLICY" ] && [ "$entry_count" -ne 13 ]; then
  echo "FAIL: canonical entry-router registry must contain 13 skills (found $entry_count)"
  fail=1
fi

portable_names=$(find "$ROOT/capabilities" -maxdepth 1 -type f -name '*.md' ! -name README.md \
  -exec basename {} .md \; 2>/dev/null | sort)
if [ -z "$portable_names" ]; then
  echo "FAIL: portable capability domain is empty: $ROOT/capabilities"
  exit 1
fi

for skills_dir in "$@"; do
  if [ ! -d "$skills_dir" ]; then
    echo "FAIL: skills directory missing: $skills_dir"
    fail=1
    continue
  fi
  if ! tsv=$(bash "$SCAN" "$skills_dir" 2>/dev/null); then
    echo "FAIL: scan.sh failed: $skills_dir"
    fail=1
    continue
  fi

  header=$(printf '%s\n' "$tsv" | head -1)
  if [ "$(printf '%s\n' "$header" | cut -f1)" != "name" ] || \
     [ "$(printf '%s\n' "$header" | cut -f4)" != "disable_model" ] || \
     [ "$(printf '%s\n' "$header" | cut -f6)" != "use_when" ]; then
    echo "FAIL: scan.sh TSV schema drift: $skills_dir"
    fail=1
    continue
  fi
  body=$(printf '%s\n' "$tsv" | tail -n +2)

  if [ "$default_scope" -eq 1 ]; then
    actual_names=$(printf '%s\n' "$body" | awk -F'\t' 'NF{print $1}' | sort)
    missing=$(comm -23 <(printf '%s\n' "$portable_names") <(printf '%s\n' "$actual_names"))
    extra=$(comm -13 <(printf '%s\n' "$portable_names") <(printf '%s\n' "$actual_names"))
    [ -n "$missing" ] && { echo "FAIL: portable capabilities missing from $skills_dir: $missing"; fail=1; }
    [ -n "$extra" ] && { echo "FAIL: non-portable skills present in $skills_dir: $extra"; fail=1; }
  fi

  case "$skills_dir" in
    "$ROOT/adapters/codex/skills"|"$ROOT/adapters/opencode/skills") native_generated=1 ;;
    *) native_generated=0 ;;
  esac

  bad_len=$(printf '%s\n' "$body" | awk -F'\t' '$3=="N"{print $1}')
  [ -n "$bad_len" ] && { echo "FAIL: SKILL.md >=500 lines in $skills_dir: $bad_len"; fail=1; }
  bad_depth=$(printf '%s\n' "$body" | awk -F'\t' '$9=="N"{print $1}')
  [ -n "$bad_depth" ] && { echo "FAIL: references/ depth >1 in $skills_dir: $bad_depth"; fail=1; }

  for name in "${policy_names[@]}"; do
    row=$(printf '%s\n' "$body" | awk -F'\t' -v n="$name" '$1==n{print; exit}')
    if [ -z "$row" ]; then
      echo "FAIL: classified skill missing from $skills_dir: $name"
      fail=1
      continue
    fi
    disable=$(printf '%s\n' "$row" | cut -f4)
    use_when=$(printf '%s\n' "$row" | cut -f6)
    case "${policy_class[$name]}" in
      user-only)
        if [ "$native_generated" -eq 0 ]; then
          [ "$disable" = "true" ] || { echo "FAIL: $name is user-only but disable_model=$disable ($skills_dir)"; fail=1; }
        fi
        ;;
      parent-invoked)
        [ "$disable" = "false" ] || { echo "FAIL: $name is parent-invoked but disable_model=$disable ($skills_dir)"; fail=1; }
        ;;
      entry-router)
        [ "$disable" = "false" ] || { echo "FAIL: $name is entry-router but disable_model=$disable ($skills_dir)"; fail=1; }
        [ "$use_when" = "Y" ] || { echo "FAIL: $name is entry-router but use_when=$use_when ($skills_dir)"; fail=1; }
        ;;
    esac
  done

  if [ "$native_generated" -eq 1 ]; then
    while IFS= read -r name; do
      [ -n "$name" ] || continue
      skill="$skills_dir/$name/SKILL.md"
      if ! grep -Fq "capabilities/$name.md" "$skill"; then
        echo "FAIL: native skill lacks portable source pointer: $skill"
        fail=1
      fi
    done <<EOF
$portable_names
EOF
  fi

  while IFS= read -r name; do
    [ -z "$name" ] && continue
    if [ "${policy_class[$name]:-}" != "user-only" ]; then
      echo "FAIL: unexpected disable-model-invocation=true without user-only classification: $name ($skills_dir)"
      fail=1
    fi
  done < <(printf '%s\n' "$body" | awk -F'\t' '$4=="true"{print $1}')

  # User-facing language follows the portable audience-language contract.
  # Reject fixed Korean-output directives while allowing conditional Korean
  # mirrors, examples, tokenization fixtures, and existing schema literals.
  fixed_language_re='Korean output|output in Korean|in Korean:[[:space:]]*$|Print to user \(Korean\)|print to chat \(Korean\)|Korean summary|Korean brief|보고는 한국어로|사용자 대화는 한국어|사용자 출력은 자연스러운 한국어'
  while IFS= read -r hit; do
    [ -z "$hit" ] && continue
    echo "FAIL: fixed user-facing language directive: $hit"
    fail=1
  done < <(grep -RInE --include='*.md' "$fixed_language_re" "$skills_dir" 2>/dev/null || true)
done

if [ "$fail" -eq 0 ]; then
  echo "PASS: skill conformance (portable domain + four Skill trees + invocation policy ${#policy_names[@]} classifications + audience-language neutrality)"
fi
exit "$fail"
