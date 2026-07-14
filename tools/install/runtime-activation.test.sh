#!/usr/bin/env sh
# Phase 1 cross-runtime activation E2E.  One shell owns every environment
# override so no subprocess can fall back to the real runtime homes.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

HOME="$TMP/home"
XDG_CONFIG_HOME="$HOME/.config"
XDG_DATA_HOME="$HOME/.local/share"
SENTINEL_LOG="$TMP/external-calls.log"
SRC="$TMP/source-main"
SRC2="$TMP/source-worktree"
SRC_BAD="$TMP/source-bad"
SRC_LINK="$TMP/source-link"
BIN="$TMP/bin"
export HOME XDG_CONFIG_HOME XDG_DATA_HOME SENTINEL_LOG
mkdir -p "$HOME" "$BIN"
: > "$SENTINEL_LOG"

fail() {
  echo "not ok - $*" >&2
  exit 1
}

ok() {
  echo "ok - $*"
}

make_fixture() {
  root=$1
  mkdir -p \
    "$root/core" "$root/capabilities" "$root/roles" \
    "$root/adapters/codex/bin" "$root/adapters/codex/hooks" \
    "$root/adapters/codex/modes/dev" "$root/adapters/codex/skills/demo" \
    "$root/adapters/codex/agents" \
    "$root/adapters/codex/plugins/agent-harness-codex/.codex-plugin" \
    "$root/adapters/codex/plugins/agent-harness-codex/skills/demo" \
    "$root/adapters/claude/agent-modes/dev" "$root/adapters/claude/skills/demo" \
    "$root/adapters/claude/agents" "$root/adapters/claude/commands" \
    "$root/adapters/claude/hooks" "$root/adapters/claude/bin" \
    "$root/adapters/claude/tools/memory" "$root/adapters/claude/utilities" \
    "$root/adapters/claude/scaffolds" \
    "$root/adapters/claude/plugin-marketplace/plugins/agent-harness-claude/.claude-plugin" \
    "$root/adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/demo" \
    "$root/adapters/opencode/skills/demo" "$root/adapters/opencode/agents/demo" \
    "$root/adapters/opencode/commands" "$root/adapters/opencode/plugins"

  printf '%s\n' '# core fixture' > "$root/core/CORE.md"
  printf '%s\n' '# capability fixture' > "$root/capabilities/README.md"
  printf '%s\n' '# role fixture' > "$root/roles/README.md"

  printf '%s\n' '# Codex instructions' > "$root/adapters/codex/AGENTS.md"
  printf '%s\n' '#!/bin/sh' 'exit 0' > "$root/adapters/codex/bin/preflight.sh"
  chmod +x "$root/adapters/codex/bin/preflight.sh"
  printf '%s\n' '{"hooks":{}}' > "$root/adapters/codex/hooks/hooks.json"
  printf '%s\n' '# mode' > "$root/adapters/codex/modes/dev/refactor.md"
  printf '%s\n' '---' 'name: demo' 'description: demo' '---' '# demo codex' \
    > "$root/adapters/codex/skills/demo/SKILL.md"
  printf '%s\n' 'name = "demo"' 'description = "demo"' \
    > "$root/adapters/codex/agents/demo.toml"
  printf '%s\n' '{"name":"agent-harness-codex","version":"1.0.0"}' \
    > "$root/adapters/codex/plugins/agent-harness-codex/.codex-plugin/plugin.json"
  cp "$root/adapters/codex/skills/demo/SKILL.md" \
    "$root/adapters/codex/plugins/agent-harness-codex/skills/demo/SKILL.md"

  printf '%s\n' '# Claude instructions' > "$root/adapters/claude/CLAUDE.md"
  printf '%s\n' '# mode' > "$root/adapters/claude/agent-modes/dev/refactor.md"
  printf '%s\n' '---' 'name: demo' 'description: demo' '---' '# demo claude' \
    > "$root/adapters/claude/skills/demo/SKILL.md"
  printf '%s\n' '# demo agent' > "$root/adapters/claude/agents/demo.md"
  printf '%s\n' '# demo command' > "$root/adapters/claude/commands/demo.md"
  printf '%s\n' '#!/bin/sh' 'exit 0' > "$root/adapters/claude/hooks/demo.sh"
  chmod +x "$root/adapters/claude/hooks/demo.sh"
  printf '%s\n' '#!/bin/sh' 'exit 0' > "$root/adapters/claude/bin/preflight.sh"
  chmod +x "$root/adapters/claude/bin/preflight.sh"
  printf '%s\n' '# fixture memory' > "$root/adapters/claude/tools/memory/mem.py"
  printf '%s\n' '#!/bin/sh' 'exit 0' > "$root/adapters/claude/utilities/fixture.sh"
  chmod +x "$root/adapters/claude/utilities/fixture.sh"
  printf '%s\n' 'fixture' > "$root/adapters/claude/scaffolds/README.md"
  printf '%s\n' \
    '{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"sh $HOME/.claude/utilities/fixture.sh"}]}]}}' \
    > "$root/adapters/claude/settings.json"
  printf '%s\n' '{"name":"agent-harness-claude","version":"1.0.0"}' \
    > "$root/adapters/claude/plugin-marketplace/plugins/agent-harness-claude/.claude-plugin/plugin.json"
  cp "$root/adapters/claude/skills/demo/SKILL.md" \
    "$root/adapters/claude/plugin-marketplace/plugins/agent-harness-claude/skills/demo/SKILL.md"

  printf '%s\n' '# OpenCode instructions' > "$root/adapters/opencode/AGENTS.md"
  printf '%s\n' '---' 'name: demo' 'description: demo' '---' '# demo opencode' \
    > "$root/adapters/opencode/skills/demo/SKILL.md"
  printf '%s\n' '# demo agent' > "$root/adapters/opencode/agents/demo/demo.md"
  printf '%s\n' '# demo command' > "$root/adapters/opencode/commands/demo.md"
  printf '%s\n' 'export const AgentHarnessGuards = async () => ({})' \
    > "$root/adapters/opencode/plugins/agent-harness-guards.js"

  git -C "$root" init -q
  git -C "$root" config user.email fixture@example.com
  git -C "$root" config user.name fixture
  git -C "$root" add .
  git -C "$root" commit -qm fixture
}

make_fixture "$SRC"
mkdir -p "$HOME/.claude"
printf '%s\n' '{"theme":"user"}' > "$HOME/.claude/settings.json"

for command in curl wget npm bun codex claude opencode; do
  printf '%s\n' '#!/bin/sh' 'echo "$(basename "$0")" >> "$SENTINEL_LOG"' 'exit 97' \
    > "$BIN/$command"
  chmod +x "$BIN/$command"
done
PATH="$BIN:$PATH"
AGENT_HOME="$SRC"
export PATH AGENT_HOME

harness() {
  sh "$ROOT/tools/install/harness.sh" "$@"
}

if ! harness runtime activate --runtime all --mode linked --source "$SRC" --json \
  > "$TMP/linked-activate.json"; then
  cat "$TMP/linked-activate.json" >&2
  fail "initial linked activation failed"
fi
harness runtime status --runtime all --json > "$TMP/linked-status.json"
harness runtime doctor --runtime all --strict --json > "$TMP/linked-doctor.json"

python3 - "$TMP/linked-status.json" "$SRC" <<'PY'
import json, os, sys
data=json.load(open(sys.argv[1]))
assert data["exit"] == 0
expected={
 "codex":{"instructions":"new-session","skill":"auto-detect-reinvoke","agent":"new-session","hook_config":"new-session"},
 "claude":{"instructions":"new-session","skill":"reinvoke","agent":"new-session","hook_config":"new-session"},
 "opencode":{"instructions":"restart-required","skill":"restart-required","agent":"restart-required","hook_config":"restart-required"},
}
required={"runtime","mode","source_root","source_revision","active_revision","projection_digest","discovery_paths","duplicate_sources","freshness","session_action","external_dependencies"}
for row in data["runtimes"]:
    assert required <= set(row), (row["runtime"], required-set(row))
    assert row["mode"] == "linked" and row["freshness"] == "fresh"
    assert row["source_root"] == os.path.realpath(sys.argv[2])
    assert row["duplicate_sources"] == [] and row["external_dependencies"] == []
    assert row["session_action"] == expected[row["runtime"]]
PY
test -L "$HOME/.config/opencode/skills/demo" || fail "OpenCode plural skills projection missing"
test -L "$HOME/.config/opencode/agents/demo.md" || fail "OpenCode plural agents projection missing"
test -L "$HOME/.config/opencode/commands/demo.md" || fail "OpenCode plural commands projection missing"
test -L "$HOME/.config/opencode/plugins/agent-harness-guards.js" \
  || fail "OpenCode local plugin projection missing"
test -L "$HOME/.claude/tools" || fail "Claude tools projection missing"
test -L "$HOME/.claude/utilities" || fail "Claude utilities projection missing"
python3 - "$HOME/.claude/settings.json" <<'PY'
import json, sys
data=json.load(open(sys.argv[1]))
assert data["theme"] == "user"
assert data["hooks"]["SessionStart"]
PY
ok "offline linked activation/status/doctor for all runtimes"

harness runtime status --runtime codex --json > "$TMP/codex-before.json"
printf '%s\n' '# live linked change' >> "$SRC/adapters/codex/skills/demo/SKILL.md"
harness runtime status --runtime codex --json > "$TMP/codex-after.json"
python3 - "$TMP/codex-before.json" "$TMP/codex-after.json" <<'PY'
import json, sys
before=json.load(open(sys.argv[1])); after=json.load(open(sys.argv[2]))
assert before["projection_digest"] != after["projection_digest"]
assert after["freshness"] == "session-reload-needed"
assert "+dirty:" in after["source_revision"]
PY
harness runtime refresh --runtime codex --json > "$TMP/codex-refresh.json"
python3 - "$TMP/codex-refresh.json" <<'PY'
import json, sys
assert json.load(open(sys.argv[1]))["freshness"] == "fresh"
PY
ok "linked digest changes immediately and refresh closes session marker"

git -C "$SRC" add .
git -C "$SRC" commit -qm linked-change
harness runtime activate --runtime all --mode packaged --source "$SRC" --json \
  > "$TMP/package-before.json"
python3 - "$TMP/package-before.json" "$HOME" <<'PY'
import json, os, sys
rows={row["runtime"]: row for row in json.load(open(sys.argv[1]))["runtimes"]}
for runtime, row in rows.items():
    assert "/.harness/bundles/" in row["active_root"]
    assert row["bundle_checksum"]
    home={
        "codex": os.path.join(sys.argv[2], ".codex"),
        "claude": os.path.join(sys.argv[2], ".claude"),
        "opencode": os.path.join(sys.argv[2], ".config", "opencode"),
    }[runtime]
    assert os.path.realpath(os.path.join(home, "skills", "demo")).startswith(row["active_root"])
PY
printf '%s\n' '# packaged source advance' >> "$SRC/adapters/opencode/skills/demo/SKILL.md"
git -C "$SRC" add .
git -C "$SRC" commit -qm packaged-advance
harness runtime status --runtime all --json > "$TMP/package-stale.json"
python3 - "$TMP/package-before.json" "$TMP/package-stale.json" <<'PY'
import json, sys
before={r["runtime"]:r for r in json.load(open(sys.argv[1]))["runtimes"]}
after={r["runtime"]:r for r in json.load(open(sys.argv[2]))["runtimes"]}
for runtime in before:
    assert after[runtime]["mode"] == "packaged"
    assert after[runtime]["active_revision"] == before[runtime]["active_revision"]
    assert after[runtime]["projection_digest"] == before[runtime]["projection_digest"]
    assert after[runtime]["freshness"] == "source-ahead"
PY
harness runtime refresh --runtime all --json > "$TMP/package-refreshed.json"
python3 - "$TMP/package-before.json" "$TMP/package-refreshed.json" <<'PY'
import json, sys
before={r["runtime"]:r for r in json.load(open(sys.argv[1]))["runtimes"]}
after={r["runtime"]:r for r in json.load(open(sys.argv[2]))["runtimes"]}
for runtime in before:
    assert after[runtime]["active_revision"] != before[runtime]["active_revision"]
    assert after[runtime]["freshness"] == "fresh"
PY
ok "packaged revision and digest stay immutable until refresh"

codex_bundle=$(python3 - "$TMP/package-refreshed.json" <<'PY'
import json, sys
for row in json.load(open(sys.argv[1]))["runtimes"]:
    if row["runtime"] == "codex":
        print(row["active_root"])
        break
PY
)
printf '%s\n' '# unauthorized bundle mutation' >> \
  "$codex_bundle/adapters/codex/skills/demo/SKILL.md"
if harness runtime doctor --runtime codex --strict --json > "$TMP/tampered.json"; then
  fail "strict doctor accepted a modified packaged bundle"
fi
python3 - "$TMP/tampered.json" <<'PY'
import json, sys
assert json.load(open(sys.argv[1]))["freshness"] == "cache-stale"
PY
harness runtime refresh --runtime codex --json >/dev/null
ok "packaged bundle checksum detects mutation and refresh rebuilds it"

harness runtime activate --runtime all --mode linked --source "$SRC" --json \
  > "$TMP/relinked.json"
mkdir -p "$HOME/.codex/plugins/cache/fixture/codex/.codex-plugin"
printf '%s\n' '{"name":"agent-harness-codex"}' \
  > "$HOME/.codex/plugins/cache/fixture/codex/.codex-plugin/plugin.json"
printf '%s\n' '[plugins."agent-harness-codex@fixture"]' 'enabled = true' \
  > "$HOME/.codex/config.toml"
mkdir -p "$HOME/.claude/plugins/cache/fixture/claude/.claude-plugin"
printf '%s\n' '{"name":"agent-harness-claude"}' \
  > "$HOME/.claude/plugins/cache/fixture/claude/.claude-plugin/plugin.json"
mkdir -p "$HOME/.claude/plugins"
printf '%s\n' \
  '{"version":2,"plugins":{"agent-harness-claude@fixture":[{"scope":"user","installPath":"fixture"}],"foreign@fixture":[{"scope":"user"}]}}' \
  > "$HOME/.claude/plugins/installed_plugins.json"
python3 - "$HOME/.claude/settings.json" <<'PY'
import json, sys
path=sys.argv[1]
data=json.load(open(path))
data["enabledPlugins"]={"agent-harness-claude@fixture": True, "foreign@fixture": True}
with open(path, "w") as handle:
    json.dump(data, handle)
PY
printf '%s\n' '{"plugin":["agent-harness-opencode@1.0.0"],"theme":"user"}' \
  > "$HOME/.config/opencode/opencode.json"

for runtime in codex claude opencode; do
  harness runtime status --runtime "$runtime" --json > "$TMP/duplicate-$runtime.json" || true
  python3 - "$TMP/duplicate-$runtime.json" <<'PY'
import json, sys
row=json.load(open(sys.argv[1]))
assert row["freshness"] == "duplicate" and row["duplicate_sources"]
PY
  if harness runtime doctor --runtime "$runtime" --strict --json >/dev/null 2>&1; then
    fail "$runtime strict doctor accepted duplicate discovery"
  fi
done
ok "Codex native+plugin, Claude native+plugin, OpenCode local+npm duplicates detected"

harness runtime activate --runtime all --mode linked --source "$SRC" --json \
  > "$TMP/deduplicated.json"
harness runtime doctor --runtime all --strict --json >/dev/null
python3 - "$HOME/.config/opencode/opencode.json" <<'PY'
import json, sys
data=json.load(open(sys.argv[1]))
assert data["plugin"] == [] and data["theme"] == "user"
PY
python3 - "$HOME/.claude/plugins/installed_plugins.json" <<'PY'
import json, sys
plugins=json.load(open(sys.argv[1]))["plugins"]
assert "agent-harness-claude@fixture" not in plugins
assert "foreign@fixture" in plugins
PY
python3 - "$HOME/.claude/settings.json" <<'PY'
import json, sys
settings=json.load(open(sys.argv[1]))
assert settings["theme"] == "user"
assert len(settings["hooks"]["SessionStart"]) == 1
assert settings["enabledPlugins"]["agent-harness-claude@fixture"] is False
assert settings["enabledPlugins"]["foreign@fixture"] is True
PY
python3 - "$HOME/.codex/config.toml" <<'PY'
import sys
text=open(sys.argv[1]).read()
assert '[plugins."agent-harness-codex@fixture"]' in text
assert 'enabled = false' in text
PY
test -d "$HOME/.codex/.harness/disabled-plugins" || fail "Codex plugin quarantine missing"
test -d "$HOME/.claude/.harness/disabled-plugins" || fail "Claude plugin quarantine missing"
ok "linked reactivation removes external plugin discovery without downloads"

python3 - "$HOME/.config/opencode/opencode.json" <<'PY'
import json, sys
path=sys.argv[1]
data=json.load(open(path))
data["note"]="agent-harness is documentation, not a plugin entry"
data["plugin"]=[
    ["agent-harness-opencode@1.2.3", {"fixture": True}],
    ["foreign-opencode-plugin@1.0.0", {"foreign": True}],
]
with open(path, "w") as handle:
    json.dump(data, handle)
PY
if harness runtime doctor --runtime opencode --strict --json >/dev/null 2>&1; then
  fail "OpenCode tuple plugin entry was not detected"
fi
harness runtime activate --runtime opencode --mode linked --source "$SRC" --json \
  >/dev/null
python3 - "$HOME/.config/opencode/opencode.json" <<'PY'
import json, sys
data=json.load(open(sys.argv[1]))
assert data["note"] == "agent-harness is documentation, not a plugin entry"
assert data["plugin"] == [["foreign-opencode-plugin@1.0.0", {"foreign": True}]]
PY
printf '%s\n' '{' \
  '  // "plugin": ["agent-harness-opencode@comment-only"],' \
  '  "theme": "user",' \
  '}' > "$HOME/.config/opencode/opencode.jsonc"
harness runtime activate --runtime opencode --mode linked --source "$SRC" --json \
  >/dev/null || fail "OpenCode JSONC comment caused a false duplicate"
printf '%s\n' '{"plugin":[]} /* unterminated' \
  > "$HOME/.config/opencode/opencode.jsonc"
if harness runtime activate --runtime opencode --mode linked --source "$SRC" --json \
  >/dev/null 2>&1; then
  fail "OpenCode activation accepted an unterminated JSONC block comment"
fi
printf '%s\n' '{' \
  '  "plugin": [[' \
  '    "agent-harness-opencode@1.0.0",' \
  '    {"fixture": true},' \
  '  ]],' \
  '}' \
  > "$HOME/.config/opencode/opencode.jsonc"
opencode_state_before=$(sha256sum "$HOME/.config/opencode/.harness/activation.json" | cut -d ' ' -f 1)
if harness runtime activate --runtime opencode --mode linked --source "$SRC" --json \
  > "$TMP/jsonc-blocked.json" 2>/dev/null; then
  fail "OpenCode JSONC external plugin was silently left active"
fi
opencode_state_after=$(sha256sum "$HOME/.config/opencode/.harness/activation.json" | cut -d ' ' -f 1)
test "$opencode_state_before" = "$opencode_state_after" \
  || fail "blocked OpenCode JSONC activation changed state"
rm "$HOME/.config/opencode/opencode.jsonc"
ok "OpenCode plugin parsing handles tuples, comments, and unsafe JSONC rewrites"

git clone -q "$SRC" "$SRC2"
git -C "$SRC2" config user.email fixture@example.com
git -C "$SRC2" config user.name fixture
printf '%s\n' '# second source' >> "$SRC2/adapters/codex/skills/demo/SKILL.md"
mkdir -p "$SRC2/adapters/codex/skills/keep" "$SRC2/.venv/bin"
cp "$SRC2/adapters/codex/skills/demo/SKILL.md" \
  "$SRC2/adapters/codex/skills/keep/SKILL.md"
ln -s /usr/bin/python3 "$SRC2/.venv/bin/python"
git -C "$SRC2" add .
git -C "$SRC2" commit -qm second-source

mkdir -p "$HOME/.codex/sessions" "$HOME/.claude/session" \
  "$HOME/.config/opencode" "$HOME/.local/share/opencode"
printf '%s\n' credential > "$HOME/.codex/auth.json"
printf '%s\n' session > "$HOME/.codex/sessions/foreign"
printf '%s\n' session > "$HOME/.claude/session/foreign"
printf '%s\n' database > "$HOME/.config/opencode/foreign.db"
printf '%s\n' auth > "$HOME/.local/share/opencode/auth.json"
foreign_hash() {
  sha256sum \
    "$HOME/.codex/auth.json" "$HOME/.codex/sessions/foreign" \
    "$HOME/.claude/session/foreign" "$HOME/.config/opencode/foreign.db" \
    "$HOME/.local/share/opencode/auth.json" | sha256sum | cut -d ' ' -f 1
}

state_before=$(sha256sum "$HOME/.codex/.harness/activation.json" | cut -d ' ' -f 1)
link_before=$(readlink "$HOME/.codex/skills/demo")
foreign_before=$(foreign_hash)
HARNESS_RUNTIME_FAIL_AFTER=2
export HARNESS_RUNTIME_FAIL_AFTER
if harness runtime activate --runtime codex --mode linked \
  --source "$SRC2" --json > "$TMP/rollback.json" 2>/dev/null; then
  fail "failure injection unexpectedly succeeded"
fi
unset HARNESS_RUNTIME_FAIL_AFTER
state_after=$(sha256sum "$HOME/.codex/.harness/activation.json" | cut -d ' ' -f 1)
link_after=$(readlink "$HOME/.codex/skills/demo")
foreign_after=$(foreign_hash)
test "$state_before" = "$state_after" || fail "activation state was not rolled back"
test "$link_before" = "$link_after" || fail "runtime link was not rolled back"
test "$foreign_before" = "$foreign_after" || fail "runtime-owned foreign state changed"
ok "injected failure rolls back projection and preserves runtime-owned state"

for runtime in claude codex opencode; do
  case "$runtime" in
    claude) global_state="$HOME/.claude/.harness/activation.json" ;;
    codex) global_state="$HOME/.codex/.harness/activation.json" ;;
    opencode) global_state="$HOME/.config/opencode/.harness/activation.json" ;;
  esac
  scope_before=$(sha256sum "$global_state" | cut -d ' ' -f 1)
  if harness runtime activate --runtime "$runtime" --scope project --mode linked \
    --source "$SRC" --json >/dev/null 2>&1; then
    fail "$runtime project scope silently mutated a runtime home"
  fi
  scope_after=$(sha256sum "$global_state" | cut -d ' ' -f 1)
  test "$scope_before" = "$scope_after" \
    || fail "unsupported $runtime project scope changed global activation state"
done
ok "project-scoped runtime activation is explicitly blocked for all runtimes"

printf '%s\n' credential-still-owned > "$HOME/.codex/auth.json"
mkdir -p "$HOME/.codex/.harness/transactions/forged"
printf '%s\n' \
  "{\"schema\":1,\"runtime\":\"codex\",\"status\":\"applying\",\"records\":[{\"dest\":\"$HOME/.codex/auth.json\",\"state\":\"missing\",\"backup\":null,\"target\":null}]}" \
  > "$HOME/.codex/.harness/transactions/forged/journal.json"
if harness runtime activate --runtime codex --mode linked --source "$SRC" --json \
  >/dev/null 2>&1; then
  fail "forged transaction journal was accepted"
fi
test "$(cat "$HOME/.codex/auth.json")" = credential-still-owned \
  || fail "forged journal changed runtime credentials"
rm -rf "$HOME/.codex/.harness/transactions/forged"
ok "journal recovery rejects non-harness destinations"

printf '%s\n' backup-victim > "$TMP/backup-victim"
mkdir -p "$HOME/.codex/.harness/transactions/backup-escape"
python3 - \
  "$HOME/.codex/.harness/transactions/backup-escape/journal.json" \
  "$HOME/.codex/AGENTS.md" "$TMP/backup-victim" <<'PY'
import json
import sys

journal, destination, backup = sys.argv[1:]
with open(journal, "w", encoding="utf-8") as handle:
    json.dump(
        {
            "schema": 1,
            "runtime": "codex",
            "status": "applying",
            "records": [
                {
                    "dest": destination,
                    "state": "copied",
                    "backup": backup,
                    "target": None,
                }
            ],
        },
        handle,
    )
PY
if harness runtime activate --runtime codex --mode linked --source "$SRC" --json \
  >/dev/null 2>&1; then
  fail "transaction journal accepted a backup outside its transaction root"
fi
test "$(cat "$TMP/backup-victim")" = backup-victim \
  || fail "backup escape journal changed its external target"
rm -rf "$HOME/.codex/.harness/transactions/backup-escape"
ok "journal recovery rejects backup paths outside the transaction root"

rmdir "$HOME/.codex/.harness/transactions"
mkdir -p "$TMP/outside-transactions"
printf '%s\n' state-victim > "$TMP/outside-transactions/sentinel"
ln -s "$TMP/outside-transactions" "$HOME/.codex/.harness/transactions"
if harness runtime activate --runtime codex --mode linked --source "$SRC" --json \
  >/dev/null 2>&1; then
  fail "activation accepted a symlinked transaction directory"
fi
test "$(cat "$TMP/outside-transactions/sentinel")" = state-victim \
  || fail "symlinked transaction directory changed external state"
rm "$HOME/.codex/.harness/transactions"
mkdir "$HOME/.codex/.harness/transactions"
ok "activation rejects symlinked harness transaction storage"

mkdir "$HOME/.codex/.harness/transactions/empty-crash"
harness runtime activate --runtime codex --mode linked --source "$SRC" --json \
  >/dev/null
test ! -e "$HOME/.codex/.harness/transactions/empty-crash" \
  || fail "empty pre-journal crash directory was not recovered"
ok "activation recovers an empty pre-journal crash directory"

git clone -q "$SRC" "$SRC_LINK"
mkdir -p "$TMP/outside-skill"
printf '%s\n' '# outside' > "$TMP/outside-skill/SKILL.md"
rm -rf "$SRC_LINK/adapters/codex/skills/demo"
ln -s "$TMP/outside-skill" "$SRC_LINK/adapters/codex/skills/demo"
if harness runtime activate --runtime codex --mode linked --source "$SRC_LINK" --json \
  >/dev/null 2>&1; then
  fail "linked activation accepted a source-root escape symlink"
fi
ok "linked activation rejects external source symlinks"

git clone -q "$SRC" "$SRC_BAD"
rm -rf "$SRC_BAD/adapters/codex/bin" "$SRC_BAD/adapters/codex/hooks"
claude_state_before=$(sha256sum "$HOME/.claude/.harness/activation.json" | cut -d ' ' -f 1)
claude_settings_before=$(sha256sum "$HOME/.claude/settings.json" | cut -d ' ' -f 1)
claude_link_before=$(readlink "$HOME/.claude/skills/demo")
if harness runtime activate --runtime all --mode linked --source "$SRC_BAD" --json \
  > "$TMP/global-rollback.json" 2>/dev/null; then
  fail "multi-runtime activation unexpectedly accepted incomplete Codex surfaces"
fi
claude_state_after=$(sha256sum "$HOME/.claude/.harness/activation.json" | cut -d ' ' -f 1)
claude_settings_after=$(sha256sum "$HOME/.claude/settings.json" | cut -d ' ' -f 1)
claude_link_after=$(readlink "$HOME/.claude/skills/demo")
test "$claude_state_before" = "$claude_state_after" \
  || fail "multi-runtime rollback did not restore Claude activation state"
test "$claude_settings_before" = "$claude_settings_after" \
  || fail "multi-runtime rollback did not restore Claude settings"
test "$claude_link_before" = "$claude_link_after" \
  || fail "multi-runtime rollback did not restore Claude discovery"
python3 - "$TMP/global-rollback.json" <<'PY'
import json, sys
data=json.load(open(sys.argv[1]))
assert data["exit"] == 3
assert data["runtimes"][0]["runtime"] == "claude"
assert data["runtimes"][0]["rolled_back"] is True
PY
ok "multi-runtime activation rolls back earlier runtimes when a later runtime blocks"

harness runtime activate --runtime codex --mode linked --source "$SRC2" --json \
  > "$TMP/source-two.json"
python3 - "$TMP/source-two.json" "$SRC2" <<'PY'
import json, os, sys
row=json.load(open(sys.argv[1]))
assert row["source_root"] == os.path.realpath(sys.argv[2])
assert row["active_revision"] == row["source_revision"]
assert row["freshness"] == "fresh"
PY
ok "absolute source path distinguishes the explicitly activated worktree"

rm -rf "$SRC2/adapters/codex/skills/demo"
harness runtime status --runtime codex --json > "$TMP/removed-skill.json" || true
python3 - "$TMP/removed-skill.json" <<'PY'
import json, sys
row=json.load(open(sys.argv[1]))
assert row["freshness"] == "missing"
assert "refresh" in row["next_action"]
PY
harness runtime refresh --runtime codex --json >/dev/null
test ! -e "$HOME/.codex/skills/demo" && test ! -L "$HOME/.codex/skills/demo" \
  || fail "refresh left a removed skill symlink behind"
ok "linked status and refresh remove deleted owned discovery entries"

test ! -s "$SENTINEL_LOG" || fail "external command invoked: $(tr '\n' ' ' < "$SENTINEL_LOG")"
ok "activation path used no runtime, marketplace, network, npm, or bun command"

echo "runtime-activation: PASS"
