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

echo "generated-projections: PASS"
