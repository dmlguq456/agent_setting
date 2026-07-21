#!/usr/bin/env sh
# Phase 2 product-profile activation E2E against the real generated source.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

HOME="$TMP/home"
XDG_CONFIG_HOME="$HOME/.config"
XDG_DATA_HOME="$HOME/.local/share"
AGENT_HOME="$ROOT"
export HOME XDG_CONFIG_HOME XDG_DATA_HOME AGENT_HOME
mkdir -p "$HOME"

harness() {
  sh "$ROOT/tools/install/harness.sh" "$@"
}

fail() {
  echo "not ok - $*" >&2
  exit 1
}

count_dirs() {
  find "$1" -mindepth 1 -maxdepth 1 -type l | wc -l | tr -d ' '
}

count_links() {
  find "$1" -type l | wc -l | tr -d ' '
}

check_profile() {
  profile=$1
  expected_capabilities=$2
  expected_roles=$3
  expected_modes=$4
  harness runtime activate --runtime all --mode linked --source "$ROOT" --profile "$profile" --json > "$TMP/$profile.json"

  python3 - "$TMP/$profile.json" "$profile" "$expected_capabilities" "$expected_roles" <<'PY'
import json, sys
data=json.load(open(sys.argv[1]))
rows=data["runtimes"]
for row in rows:
    assert row["profile"] == sys.argv[2], row
    assert row["profile_counts"]["capabilities"] == int(sys.argv[3]), row
    assert row["profile_counts"]["roles"] == int(sys.argv[4]), row
    assert len(row["profile_capabilities"]) == int(sys.argv[3]), row
    assert row["freshness"] == "fresh", row
PY

  test "$(count_dirs "$HOME/.codex/skills")" = "$expected_capabilities" || fail "$profile Codex skill count"
  test "$(count_dirs "$HOME/.claude/skills")" = "$expected_capabilities" || fail "$profile Claude skill count"
  test "$(count_dirs "$HOME/.config/opencode/skills")" = "$expected_capabilities" || fail "$profile OpenCode skill count"
  test "$(count_dirs "$HOME/.config/opencode/commands")" = "$expected_capabilities" || fail "$profile OpenCode command count"

  # Kernel helpers only (memory-scout): runtime team agents retired 2026-07-22 (재홈).
  expected_agents=1
  test "$(count_dirs "$HOME/.codex/agents")" = "$expected_agents" || fail "$profile Codex agent count"
  test "$(count_dirs "$HOME/.claude/agents")" = "$expected_agents" || fail "$profile Claude agent count"
  test "$(count_dirs "$HOME/.config/opencode/agents")" = "$expected_agents" || fail "$profile OpenCode agent count"

  test "$(count_links "$HOME/.codex/agent-modes")" = "$expected_modes" || fail "$profile Codex mode count"
  # Claude agent-modes runtime surface retired: units project through home/roles/units.
  test ! -e "$HOME/.claude/agent-modes" || fail "$profile Claude agent-modes surface should be retired"

  test -L "$HOME/.codex/hooks.json" || fail "$profile lost Codex kernel hooks"
  test -L "$HOME/.claude/hooks/artifact-guard.sh" || fail "$profile lost Claude kernel hooks"
  test -L "$HOME/.config/opencode/plugins/agent-harness-guards.js" || fail "$profile lost OpenCode kernel guard plugin"
}

check_profile starter 6 5 10
test ! -e "$HOME/.codex/skills/autopilot-design" || fail "starter exposed a design-only capability"
test ! -e "$HOME/.codex/agent-modes/design/maker.md" || fail "starter exposed a design mode"

check_profile builder 14 7 19
test -L "$HOME/.codex/skills/autopilot-spec" || fail "builder omitted autopilot-spec"
test ! -e "$HOME/.codex/skills/autopilot-draft" || fail "builder exposed a full-only document capability"

# full codex mode links = 27: internal design/_design_rules has no native projection.
check_profile full 27 8 27
# codex-review-team wrapper retired 2026-07-22 (재홈): cross-harness review is a
# dispatched unit; only the memory-scout kernel helper is projected.
test ! -e "$HOME/.claude/agents/codex-review-team.md" || fail "full re-projected the retired codex-review-team wrapper"

# User-facing verify follows activation state instead of legacy projection checks.
harness verify --json > "$TMP/verify.json"
python3 - "$TMP/verify.json" <<'PY'
import json, sys
row=json.load(open(sys.argv[1]))
assert row["exit"] == 0, row
assert len(row["checks"]) == 3, row
assert all(item["ok"] for item in row["checks"]), row
assert all(item["id"].endswith(".runtime-activation") for item in row["checks"]), row
PY

# Duplicate remediation must preserve the already selected profile and source.
python3 - "$ROOT" <<'PY'
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "tools", "install"))
import runtime_activation as activation
activation.duplicate_sources = lambda runtime, scope="global": ["native+plugin"]
row = activation.status("codex")
assert "--profile full" in row["next_action"], row
assert f"--source {sys.argv[1]}" in row["next_action"], row
PY

# A profile reports and removes an untracked native link left by an older
# all-capabilities installer, while preserving unrelated user entries.
ln -s "$ROOT/adapters/codex/agents/external-adversary.toml" \
  "$HOME/.codex/agents/legacy-external.toml"
printf '%s\n' 'user-owned' > "$HOME/.codex/agents/user-owned.toml"
harness runtime status --runtime codex --json > "$TMP/profile-extra.json" || true
python3 - "$TMP/profile-extra.json" <<'PY'
import json, sys
row=json.load(open(sys.argv[1]))
assert row["freshness"] == "duplicate", row
assert "profile-extra:agents/legacy-external.toml" in row["duplicate_sources"], row
PY

# A source with the canonical manifest but no explicit flag selects builder.
harness runtime activate --runtime codex --mode linked --source "$ROOT" --json > "$TMP/default.json"
python3 - "$TMP/default.json" <<'PY'
import json, sys
row=json.load(open(sys.argv[1]))
assert row["profile"] == "builder", row
assert row["profile_counts"]["capabilities"] == 14, row
PY
test ! -e "$HOME/.codex/agents/legacy-external.toml" \
  || fail "profile refresh retained a legacy harness agent"
test -f "$HOME/.codex/agents/user-owned.toml" \
  || fail "profile refresh removed a user-owned agent"

# Installer --profile is an explicit alias to linked activation, never plugin.
harness install opencode --profile starter --json > "$TMP/install-profile.json"
python3 - "$TMP/install-profile.json" <<'PY'
import json, sys
row=json.load(open(sys.argv[1]))
assert row["profile"] == "starter", row
assert row["channel"] == "linked", row
assert row["freshness"] == "fresh", row
PY

# Profile activation never accepts the legacy project scope, including dry-run.
if harness install codex --profile starter --scope project --dry-run --json > "$TMP/project-dry-run.json"; then
  fail "profile dry-run accepted unsupported project scope"
else
  test "$?" = "3" || fail "profile dry-run returned the wrong blocked exit"
fi
python3 - "$TMP/project-dry-run.json" <<'PY'
import json, sys
row=json.load(open(sys.argv[1]))
assert row["exit"] == 3, row
assert "outside Phase 1" in row["lines"][0], row
PY

echo "profile-activation: PASS"
