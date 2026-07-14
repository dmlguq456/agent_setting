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
grep -q "GENERATOR_SENTINEL" "$ROOT/adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/post-it/SKILL.md"
grep -q "GENERATOR_SENTINEL" "$ROOT/adapters/codex/skills/post-it/SKILL.md"
grep -q "GENERATOR_SENTINEL" "$ROOT/adapters/codex/plugins/agent-harness-codex/skills/post-it/SKILL.md"
grep -q "GENERATOR_SENTINEL" "$ROOT/adapters/opencode/skills/post-it/SKILL.md"

cp "$TMP/harness-manifest.json" "$MANIFEST"
python3 "$ROOT/tools/generate.py" >/dev/null
python3 "$ROOT/tools/generate.py" --check >/dev/null

find "$ROOT/capabilities" "$ROOT/adapters/claude/skills" "$ROOT/adapters/claude/plugin-marketplace/plugins/agent-harness-claude" "$ROOT/adapters/codex/skills" "$ROOT/adapters/codex/agents" "$ROOT/adapters/codex/modes" "$ROOT/adapters/codex/plugins/agent-harness-codex" "$ROOT/adapters/opencode/skills" "$ROOT/adapters/opencode/commands" "$ROOT/adapters/opencode/agents" -type f -print | sort | xargs sha256sum > "$TMP/first.sha"
python3 "$ROOT/tools/generate.py" >/dev/null
find "$ROOT/capabilities" "$ROOT/adapters/claude/skills" "$ROOT/adapters/claude/plugin-marketplace/plugins/agent-harness-claude" "$ROOT/adapters/codex/skills" "$ROOT/adapters/codex/agents" "$ROOT/adapters/codex/modes" "$ROOT/adapters/codex/plugins/agent-harness-codex" "$ROOT/adapters/opencode/skills" "$ROOT/adapters/opencode/commands" "$ROOT/adapters/opencode/agents" -type f -print | sort | xargs sha256sum > "$TMP/second.sha"
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
recall_line=$(grep -n -m1 'Choose one targeted memory query' "$ROOT/core/WORKFLOW.md" | cut -d: -f1)
artifact_line=$(grep -n -m1 'Use the adapter status surface' "$ROOT/core/WORKFLOW.md" | cut -d: -f1)
[ "$recall_line" -lt "$artifact_line" ] || {
  echo "not ok - targeted recall must precede artifact discovery" >&2
  exit 1
}
grep -Fq 'latest specification or user-confirmed decision' "$ROOT/core/WORKFLOW.md"
grep -Fq 'durable project fact' "$ROOT/core/WORKFLOW.md"
grep -Fq 'latest experiment contract' "$ROOT/core/WORKFLOW.md"
grep -Fq 'A shortened or ellipsized snippet is never final evidence' "$ROOT/core/MEMORY.md"
grep -Fq 'read the full body by record ID' "$ROOT/core/WORKFLOW.md"
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
  grep -Fq 'agent-chosen memory recall' "$projected" || {
    echo "not ok - recall-first orientation missing from $projected" >&2
    exit 1
  }
done

for figure_contract in \
  "$ROOT/roles/modes/material/figure-gen.md" \
  "$ROOT/adapters/claude/agent-modes/material/figure-gen.md" \
  "$ROOT/adapters/codex/modes/material/figure-gen.md"; do
  grep -Fq 'METRIC_BAND_HZ' "$figure_contract" || {
    echo "not ok - metric/display separation missing from $figure_contract" >&2
    exit 1
  }
  grep -Fq '24000' "$figure_contract" || {
    echo "not ok - full-band maximum missing from $figure_contract" >&2
    exit 1
  }
done

grep -Fq -- '--verify-report' "$ROOT/adapters/codex/tools/material/figure-gen.sh"
grep -Fq -- '--verify-report' "$ROOT/adapters/opencode/tools/material/figure-gen.sh"
grep -Fq -- '--verify-report semantic gate' "$ROOT/adapters/codex/bin/mode-map.sh"
grep -Fq -- '--verify-report semantic gate' "$ROOT/adapters/opencode/bin/mode-map.sh"
codex_mode=$($ROOT/adapters/codex/bin/preflight.sh mode-info material/figure-gen)
opencode_mode=$($ROOT/adapters/opencode/bin/preflight.sh mode-info material/figure-gen)
printf '%s\n' "$codex_mode" | grep -Fq 'report_tool_contract_check=adapters/codex/bin/preflight.sh figure-gen --verify-report <manifest.json> <report.md>'
printf '%s\n' "$opencode_mode" | grep -Fq 'report_tool_contract_check=adapters/opencode/bin/preflight.sh figure-gen --verify-report <manifest.json> <report.md>'
test -x "$ROOT/tools/figure-semantic-verify.py"
test -f "$ROOT/tools/figure-semantic-manifest.schema.json"
test -L "$ROOT/adapters/claude/tools/figure-semantic-verify.py"
grep -Fq '### Step 4c: Report figure semantic gate' "$ROOT/skills/autopilot-draft/references/pipeline-steps.md"
grep -Fq 'PNG existence, dimensions, count, and links alone are not a pass' "$ROOT/skills/code-test/SKILL.md"
cmp -s "$ROOT/adapters/codex/skills/analyze-project/SKILL.md" \
  "$ROOT/adapters/codex/plugins/agent-harness-codex/skills/analyze-project/SKILL.md"
cmp -s "$ROOT/adapters/claude/skills/code-test/SKILL.md" \
  "$ROOT/adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/code-test/SKILL.md"
python3 "$ROOT/tools/figure-semantic-verify.test.py" >/dev/null

WRAPPER_FIXTURE="$TMP/figure-wrapper"
mkdir -p "$WRAPPER_FIXTURE"
python3 - "$ROOT" "$WRAPPER_FIXTURE" <<'PY'
import importlib.util, json, sys
from pathlib import Path

root, target = map(Path, sys.argv[1:])
source = root / "tools/figure-semantic-verify.test.py"
spec = importlib.util.spec_from_file_location("figure_fixture", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
png = target / "spectrogram.png"
module.write_png(png)
report = target / "report.md"
report.write_text(
    "# Result\n\n![Spectrogram](spectrogram.png)\n\n이 그림은 **전 대역**\n에너지를 보여준다.\n",
    encoding="utf-8",
)
valid = module.valid_manifest(png)
(target / "valid.json").write_text(json.dumps(valid, ensure_ascii=False), encoding="utf-8")
invalid = json.loads(json.dumps(valid))
invalid["figure_groups"][0]["max_hz"] = 1000
(target / "bad-max.json").write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
PY

for adapter in codex opencode; do
  "$ROOT/adapters/$adapter/bin/preflight.sh" figure-gen --verify-report \
    "$WRAPPER_FIXTURE/valid.json" "$WRAPPER_FIXTURE/report.md" >/dev/null
  if "$ROOT/adapters/$adapter/bin/preflight.sh" figure-gen --verify-report \
      "$WRAPPER_FIXTURE/bad-max.json" "$WRAPPER_FIXTURE/report.md" >/dev/null 2>&1; then
    echo "not ok - $adapter report wrapper accepted max_hz=1000" >&2
    exit 1
  else
    rc=$?
    [ "$rc" -eq 2 ] || {
      echo "not ok - $adapter report wrapper returned $rc instead of 2" >&2
      exit 1
    }
  fi
done

echo "generated-projections: PASS"
