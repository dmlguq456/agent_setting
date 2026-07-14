#!/usr/bin/env sh
# Canonical-only change, stale edit rejection, and second-run determinism.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TMP=$(mktemp -d)
MANIFEST="$ROOT/harness-manifest.json"
TARGET="$ROOT/adapters/codex/skills/post-it/SKILL.md"
cp "$MANIFEST" "$TMP/harness-manifest.json"

restore() {
  cp "$TMP/harness-manifest.json" "$MANIFEST"
  python3 "$ROOT/tools/generate.py" >/dev/null 2>&1 || true
  rm -rf "$TMP"
}
trap restore EXIT HUP INT TERM

python3 - "$MANIFEST" <<'PY'
import json, sys
path=sys.argv[1]
data=json.load(open(path))
data["capabilities"]["post-it"]["summary"] = "GENERATOR_SENTINEL portable metadata"
with open(path, "w", encoding="utf-8") as handle:
    json.dump(data, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
PY

python3 "$ROOT/tools/generate.py" >/dev/null
grep -q "GENERATOR_SENTINEL" "$ROOT/adapters/claude/skills/post-it/SKILL.md"
grep -q "GENERATOR_SENTINEL" "$ROOT/adapters/codex/skills/post-it/SKILL.md"
grep -q "GENERATOR_SENTINEL" "$ROOT/adapters/opencode/skills/post-it/SKILL.md"

cp "$TMP/harness-manifest.json" "$MANIFEST"
python3 "$ROOT/tools/generate.py" >/dev/null
python3 "$ROOT/tools/generate.py" --check >/dev/null

find "$ROOT/capabilities" "$ROOT/adapters/claude/skills" "$ROOT/adapters/codex/skills" "$ROOT/adapters/codex/agents" "$ROOT/adapters/codex/modes" "$ROOT/adapters/opencode/skills" "$ROOT/adapters/opencode/commands" "$ROOT/adapters/opencode/agents" -type f -print | sort | xargs sha256sum > "$TMP/first.sha"
python3 "$ROOT/tools/generate.py" >/dev/null
find "$ROOT/capabilities" "$ROOT/adapters/claude/skills" "$ROOT/adapters/codex/skills" "$ROOT/adapters/codex/agents" "$ROOT/adapters/codex/modes" "$ROOT/adapters/opencode/skills" "$ROOT/adapters/opencode/commands" "$ROOT/adapters/opencode/agents" -type f -print | sort | xargs sha256sum > "$TMP/second.sha"
cmp "$TMP/first.sha" "$TMP/second.sha"

cp "$TARGET" "$TMP/generated-skill"
printf '\nmanual generated edit\n' >> "$TARGET"
if python3 "$ROOT/tools/generate.py" --check >/dev/null 2>&1; then
  echo "not ok - manual generated edit was accepted" >&2
  exit 1
fi
cp "$TMP/generated-skill" "$TARGET"
python3 "$ROOT/tools/generate.py" --check >/dev/null

ORIENTATION_FIXTURE="$TMP/orientation-fixture"
mkdir -p \
  "$ORIENTATION_FIXTURE/.claude_reports/analysis_project/code" \
  "$ORIENTATION_FIXTURE/.claude_reports/experiments/example"
printf '%s\n' 'existing analysis' > "$ORIENTATION_FIXTURE/.claude_reports/analysis_project/code/summary.md"
printf '%s\n' 'run log' > "$ORIENTATION_FIXTURE/.claude_reports/experiments/_RUNLOG.md"
printf '%s\n' 'story' > "$ORIENTATION_FIXTURE/.claude_reports/experiments/example/STORY.md"

resolved=$("$ROOT/utilities/artifact-root.sh" "$ORIENTATION_FIXTURE")
[ "$resolved" = "$ORIENTATION_FIXTURE/.claude_reports" ] || {
  echo "not ok - legacy artifact root was not selected for orientation" >&2
  exit 1
}
mkdir -p "$ORIENTATION_FIXTURE/.agent_reports"
resolved=$("$ROOT/utilities/artifact-root.sh" "$ORIENTATION_FIXTURE")
[ "$resolved" = "$ORIENTATION_FIXTURE/.agent_reports" ] || {
  echo "not ok - canonical artifact root did not take precedence" >&2
  exit 1
}

grep -Fq '### 0.1. Read-Only Orientation Before Capability Routing' "$ROOT/core/WORKFLOW.md"
grep -Fq 'Read-only orientation invokes no capability and writes no artifact' "$ROOT/core/WORKFLOW.md"
grep -Fq '## Routing Boundary' "$ROOT/capabilities/analyze-project.md"
grep -Fq 'orientation and is not an `analyze-project` trigger by itself' "$ROOT/capabilities/analyze-project.md"
grep -Fq 'Pointer follow-through' "$ROOT/core/MEMORY.md"

for projected in \
  "$ROOT/skills/analyze-project/SKILL.md" \
  "$ROOT/adapters/claude/skills/analyze-project/SKILL.md" \
  "$ROOT/adapters/codex/skills/analyze-project/SKILL.md" \
  "$ROOT/adapters/opencode/skills/analyze-project/SKILL.md"; do
  grep -Fq 'not for read-only context recovery' "$projected" || {
    echo "not ok - orientation exclusion missing from $projected" >&2
    exit 1
  }
done

echo "generated-projections: PASS"
