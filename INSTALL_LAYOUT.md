# Install Layout

This harness is runtime-neutral. The git repository should live outside vendor runtime homes, and each runtime home should project the harness through symlinks or adapter bootstrap files.

## Target Layout

```text
$HOME/agent_setting/        # canonical git repo: common core + adapters + projections
$HOME/.claude/              # Claude Code runtime home
$HOME/.codex/               # Codex runtime home
$HOME/.config/opencode/     # OpenCode global config home
$HOME/.local/share/opencode/  # OpenCode data home (DB, logs, snapshots)
```

Do not make `$HOME/.claude`, `$HOME/.codex`, or `$HOME/.config/opencode` the canonical repo. Those directories contain runtime-owned state such as credentials, sessions, logs, SQLite databases, caches, and shell snapshots.

## Claude Code Projection

Claude Code expects files under `$HOME/.claude`. Keep runtime-owned files there, and symlink harness-owned files from the versioned Claude projection:

```bash
export AGENT_HOME="$HOME/agent_setting"

for p in CLAUDE.md README.md core settings.json keybindings.json commands skills agents agent-modes hooks utilities tools scaffolds loops manifest.json statusline.sh track-toggle.sh; do
  ln -sfn "$AGENT_HOME/claude_setting/$p" "$HOME/.claude/$p"
done
```

Keep these local to `$HOME/.claude`: `.credentials.json`, `.dispatch/`, `cache/`, `daemon/`, `history.jsonl`, `ide/`, `projects/`, `sessions/`, `session-env/`, `shell-snapshots/`, runtime logs, and other runtime-generated state.

If present, existing `worklog-board/` and `worklog-board-wt/` directories under
`$HOME/.claude` are local worklog app workspaces, not harness projection
targets. Do not move their data during harness installation. Their notes data
root is `<agent-notes-root>`, which is mutable continuity state and should not
be committed to this repo. Adapter docs own concrete local path realizations.

## Codex Projection

Keep `$HOME/.codex` runtime-owned. Project the portable harness through a
stable pointer plus adapter-owned Codex-native Skills, custom Agents, plugin
marketplace, and hook bridges:

```bash
export AGENT_HOME="$HOME/agent_setting"
ln -sfn "$AGENT_HOME" "$HOME/.codex/agent-harness"
ln -sfn "$AGENT_HOME/codex_setting/AGENTS.md" "$HOME/.codex/AGENTS.md"
ln -sfn "$AGENT_HOME/codex_setting/README.md" "$HOME/.codex/agent-harness-readme.md"
ln -sfn "$AGENT_HOME/codex_setting/core" "$HOME/.codex/agent-core"
ln -sfn "$AGENT_HOME/codex_setting/capabilities" "$HOME/.codex/agent-capabilities"
ln -sfn "$AGENT_HOME/codex_setting/roles" "$HOME/.codex/agent-roles"
ln -sfn "$AGENT_HOME/codex_setting/bin" "$HOME/.codex/agent-bin"
ln -sfn "$AGENT_HOME/codex_setting/tools" "$HOME/.codex/agent-tools"
ln -sfn "$AGENT_HOME/codex_setting/utilities" "$HOME/.codex/agent-utilities"
ln -sfn "$AGENT_HOME/codex_setting/codex-skills" "$HOME/.codex/agent-skills"
ln -sfn "$AGENT_HOME/codex_setting/codex-agents" "$HOME/.codex/agent-agents"
ln -sfn "$AGENT_HOME/codex_setting/codex-plugin-marketplace" "$HOME/.codex/agent-plugin-marketplace"
ln -sfn "$AGENT_HOME/codex_setting/codex-hooks" "$HOME/.codex/agent-hooks"
ln -sfn "$AGENT_HOME/codex_setting/codex-hooks/hooks.json" "$HOME/.codex/hooks.json"
mkdir -p "$HOME/.codex/skills"
for d in "$AGENT_HOME/codex_setting/codex-skills"/*; do
  [ -d "$d" ] || continue
  ln -sfn "$d" "$HOME/.codex/skills/$(basename "$d")"
done
mkdir -p "$HOME/.codex/agents"
for f in "$AGENT_HOME/codex_setting/codex-agents"/*.toml; do
  [ -f "$f" ] || continue
  ln -sfn "$f" "$HOME/.codex/agents/$(basename "$f")"
done
```

For a project-scoped install, symlink the same generated TOML files into the
project's `.codex/agents/` directory instead of `$HOME/.codex/agents/`.

Do not symlink Claude-native surfaces such as `settings.json`, `commands/`,
root `skills/`, root `agents/`, `statusline.sh`, or `hooks/` into `$HOME/.codex`. Codex-native
Skill projections must come from `codex_setting/codex-skills`, which is
generated from `capabilities/`. Codex-native custom Agent projections must come
from `codex_setting/codex-agents`, which is generated from `roles/`.
Codex-native plugin installation must use
`codex_setting/codex-plugin-marketplace`, which points at the adapter-owned
repo-local marketplace. Codex-native hook configuration must come from
`codex_setting/codex-hooks`, which points at adapter-owned hook bridges.
Future Codex-specific bootstrap files should live under
`adapters/codex/` and be symlinked or generated into `codex_setting/` without
moving Codex credentials, logs, sessions, or SQLite state into the repo.

## OpenCode Projection

OpenCode loads config from `opencode.json` / `opencode.jsonc` (project or
global `~/.config/opencode/`) and reads instruction files listed in the
`instructions` array. Keep `$HOME/.config/opencode` and
`$HOME/.local/share/opencode` runtime-owned and expose a stable pointer:

```bash
export AGENT_HOME="$HOME/agent_setting"
ln -sfn "$AGENT_HOME" "$HOME/.config/opencode/agent-harness"
```

Add the adapter bootstrap to the `instructions` array in your
`opencode.json` / `opencode.jsonc`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [
    "$HOME/agent_setting/opencode_setting/AGENTS.md"
  ],
  "skills": {
    "paths": [
      "$HOME/agent_setting/opencode_setting/opencode-skills"
    ]
  }
}
```

Project the adapter-owned surfaces:

```bash
ln -sfn "$AGENT_HOME/opencode_setting/AGENTS.md" "$HOME/.config/opencode/agent-agents.md"
ln -sfn "$AGENT_HOME/opencode_setting/README.md" "$HOME/.config/opencode/agent-harness-readme.md"
ln -sfn "$AGENT_HOME/opencode_setting/core" "$HOME/.config/opencode/agent-core"
ln -sfn "$AGENT_HOME/opencode_setting/capabilities" "$HOME/.config/opencode/agent-capabilities"
ln -sfn "$AGENT_HOME/opencode_setting/roles" "$HOME/.config/opencode/agent-roles"
ln -sfn "$AGENT_HOME/opencode_setting/bin" "$HOME/.config/opencode/agent-bin"
ln -sfn "$AGENT_HOME/opencode_setting/tools" "$HOME/.config/opencode/agent-tools"
ln -sfn "$AGENT_HOME/opencode_setting/utilities" "$HOME/.config/opencode/agent-utilities"
ln -sfn "$AGENT_HOME/opencode_setting/opencode-skills" "$HOME/.config/opencode/agent-skills"
ln -sfn "$AGENT_HOME/opencode_setting/opencode-agents" "$HOME/.config/opencode/agent-agents"
ln -sfn "$AGENT_HOME/opencode_setting/opencode-commands" "$HOME/.config/opencode/agent-commands"
mkdir -p "$HOME/.config/opencode/agent"
for f in "$AGENT_HOME/opencode_setting/opencode-agents"/*/*.md; do
  [ -f "$f" ] || continue
  ln -sfn "$f" "$HOME/.config/opencode/agent/$(basename "$f")"
done
mkdir -p "$HOME/.config/opencode/command"
for f in "$AGENT_HOME/opencode_setting/opencode-commands"/*.md; do
  [ -f "$f" ] || continue
  ln -sfn "$f" "$HOME/.config/opencode/command/$(basename "$f")"
done
mkdir -p "$HOME/.config/opencode/plugins"
ln -sfn "$AGENT_HOME/opencode_setting/opencode-plugins/agent-harness-guards.js" "$HOME/.config/opencode/plugins/agent-harness-guards.js"
```

Do not symlink Claude-native surfaces such as `settings.json`, `commands/`,
`skills/`, `statusline.sh`, or `hooks/` into `$HOME/.config/opencode`.
OpenCode has native `.opencode/skill/`, `.opencode/command/`, `.opencode/agent/`,
and JS/TS plugin hook surfaces. OpenCode-native Skill and Agent projections
must come from `opencode_setting/opencode-skills` and
`opencode_setting/opencode-agents`; OpenCode-native commands must come from
`opencode_setting/opencode-commands`; OpenCode-native guard plugins must come
from `opencode_setting/opencode-plugins`. Future OpenCode-specific bootstrap files
should live under `adapters/opencode/` and be symlinked or generated into
`opencode_setting/` without moving OpenCode credentials, DB state, logs,
sessions, or snapshots into the repo.

## Migration Order

1. Commit and push the current repo.
2. Stop long-running runtime processes that may write into `$HOME/.claude`, `$HOME/.codex`, `$HOME/.config/opencode`, or `$HOME/.local/share/opencode`.
3. Move or clone the repo to `$HOME/agent_setting`.
4. In each runtime home, replace harness-owned files/directories with symlinks to `$HOME/agent_setting`.
5. Set `AGENT_HOME=$HOME/agent_setting` in shell/profile or runtime wrapper.
6. Run validation:

```bash
cd "$HOME/agent_setting"
python3 tools/build-manifest.py --check
python3 -m py_compile tools/build-manifest.py tools/memory/mem.py
sh utilities/agent-home.sh
tools/check-adaptation-boundary.sh
adapters/codex/bin/sync-native-skills.py --check
adapters/codex/bin/sync-native-agents.py --check
adapters/codex/bin/sync-native-plugin.py --check
codex_setting/bin/preflight.sh capability-info autopilot-code
codex_setting/bin/preflight.sh role fast reviewer >/tmp/codex-role.txt
rg '^adapter=codex$' /tmp/codex-role.txt
rg '^family=fast$' /tmp/codex-role.txt
codex_setting/bin/preflight.sh mode-info dev/backend >/tmp/codex-mode.txt
rg '^adapter=codex$' /tmp/codex-mode.txt
rg '^status=portable$' /tmp/codex-mode.txt
codex_setting/bin/preflight.sh mode-info material/data-script >/tmp/codex-data-script-mode.txt
rg '^tool_contract=data-script$' /tmp/codex-data-script-mode.txt
rg '^runtime_surface=adapter-owned-data-script$' /tmp/codex-data-script-mode.txt
test -x codex_setting/tools/material/data-script.sh
codex_setting/bin/preflight.sh mode-info qa/test >/tmp/codex-test-mode.txt
rg '^tool_contract=verification-runner$' /tmp/codex-test-mode.txt
rg '^runtime_surface=adapter-owned-verification-runner$' /tmp/codex-test-mode.txt
test -x codex_setting/tools/qa/verification-runner.sh
codex_setting/bin/preflight.sh visual-harness >/tmp/codex-visual-contract.txt
rg '^adapter=codex$' /tmp/codex-visual-contract.txt
rg '^runtime_surface=adapter-owned-visual-harness$' /tmp/codex-visual-contract.txt
test -x codex_setting/tools/design/visual-harness.sh
tmp_codex_bootstrap_home=$(mktemp -d)
ln -s "$PWD/codex_setting/AGENTS.md" "$tmp_codex_bootstrap_home/AGENTS.md"
CODEX_HOME="$tmp_codex_bootstrap_home" codex debug prompt-input 'bootstrap check' >/tmp/codex-bootstrap.json
rg 'AGENTS.md — Codex Adapter Bootstrap' /tmp/codex-bootstrap.json
rg 'adapters/codex/bin/preflight.sh capability-info' /tmp/codex-bootstrap.json
rg 'codex_setting/codex-hooks' /tmp/codex-bootstrap.json
! rg 'adapters/claude/CLAUDE.md.*portable bootstrap' /tmp/codex-bootstrap.json
tmp_codex_home=$(mktemp -d)
mkdir -p "$tmp_codex_home/skills"
for d in "$PWD/codex_setting/codex-skills"/*; do ln -s "$d" "$tmp_codex_home/skills/$(basename "$d")"; done
CODEX_HOME="$tmp_codex_home" codex debug prompt-input autopilot-code >/tmp/codex-skills.json
! rg '/.claude/skills' /tmp/codex-skills.json
tmp_codex_plugin_home=$(mktemp -d)
CODEX_HOME="$tmp_codex_plugin_home" codex plugin marketplace add "$PWD/codex_setting/codex-plugin-marketplace" --json >/tmp/codex-plugin-marketplace.json
CODEX_HOME="$tmp_codex_plugin_home" codex plugin add agent-harness-codex@agent-harness --json >/tmp/codex-plugin-add.json
CODEX_HOME="$tmp_codex_plugin_home" codex debug prompt-input autopilot-code >/tmp/codex-plugin-skills.json
! rg 'adapters/claude/skills' /tmp/codex-plugin-skills.json
tmp_codex_hook_home=$(mktemp -d)
mkdir -p "$tmp_codex_hook_home"
ln -s "$PWD/codex_setting/codex-hooks/hooks.json" "$tmp_codex_hook_home/hooks.json"
python3 - "$tmp_codex_hook_home/hooks.json" <<'PY'
import json
import sys
from pathlib import Path

hook_json = Path(sys.argv[1])
data = json.loads(hook_json.read_text(encoding="utf-8"))
hooks = data.get("hooks", {})
assert "SessionStart" in hooks, hooks
assert "UserPromptSubmit" in hooks, hooks
assert "PreToolUse" in hooks, hooks
assert "PostToolUse" in hooks, hooks
body = hook_json.read_text(encoding="utf-8")
assert "sessionstart-lifecycle.py" in body, hook_json
assert "userprompt-lifecycle.py" in body, hook_json
assert "pretooluse-write-guard.py" in body, hook_json
assert "posttooluse-design-check.py" in body, hook_json
PY
! rg 'adapters/claude/hooks|statusline.sh|settings.json' "$tmp_codex_hook_home/hooks.json"
tmp_codex_agent_home=$(mktemp -d)
mkdir -p "$tmp_codex_agent_home/agents"
for f in "$PWD/codex_setting/codex-agents"/*.toml; do ln -s "$f" "$tmp_codex_agent_home/agents/$(basename "$f")"; done
python3 - "$tmp_codex_agent_home/agents" <<'PY'
import re
import sys
from pathlib import Path

agents = sorted(Path(sys.argv[1]).glob("*.toml"))
assert len(agents) == 8, agents
for agent in agents:
    body = agent.read_text(encoding="utf-8")
    assert re.search(r'^name = "[^"]+"$', body, re.MULTILINE), agent
    assert re.search(r'^description = "[^"]+"$', body, re.MULTILINE), agent
    assert re.search(r'^developer_instructions = """\n.+\n"""$', body, re.MULTILINE | re.DOTALL), agent
PY
! rg 'adapters/claude/agents' "$tmp_codex_agent_home/agents"
opencode_setting/bin/preflight.sh capability-info autopilot-code
adapters/opencode/bin/sync-native-skills.py --check
adapters/opencode/bin/sync-native-agents.py --check
adapters/opencode/bin/sync-native-commands.py --check
tmp_opencode_bootstrap_home=$(mktemp -d)
opencode_setting/bin/preflight.sh role fast reviewer >/tmp/opencode-role.txt
rg '^adapter=opencode$' /tmp/opencode-role.txt
rg '^family=fast$' /tmp/opencode-role.txt
opencode_setting/bin/preflight.sh mode-info dev/backend >/tmp/opencode-mode.txt
rg '^adapter=opencode$' /tmp/opencode-mode.txt
rg '^status=portable$' /tmp/opencode-mode.txt
opencode_setting/bin/preflight.sh mode-info material/data-script >/tmp/opencode-data-script-mode.txt
rg '^tool_contract=data-script$' /tmp/opencode-data-script-mode.txt
rg '^runtime_surface=adapter-owned-data-script$' /tmp/opencode-data-script-mode.txt
test -x opencode_setting/tools/material/data-script.sh
opencode_setting/bin/preflight.sh mode-info qa/test >/tmp/opencode-test-mode.txt
rg '^tool_contract=verification-runner$' /tmp/opencode-test-mode.txt
rg '^runtime_surface=adapter-owned-verification-runner$' /tmp/opencode-test-mode.txt
test -x opencode_setting/tools/qa/verification-runner.sh
opencode_setting/bin/preflight.sh visual-harness >/tmp/opencode-visual-contract.txt
rg '^adapter=opencode$' /tmp/opencode-visual-contract.txt
rg '^runtime_surface=adapter-owned-visual-harness$' /tmp/opencode-visual-contract.txt
test -x opencode_setting/tools/design/visual-harness.sh
mkdir -p "$tmp_opencode_bootstrap_home/.config/opencode" "$tmp_opencode_bootstrap_home/.local/share"
OPENCODE_CONFIG_CONTENT="{\"instructions\":[\"$PWD/opencode_setting/AGENTS.md\"],\"skills\":{\"paths\":[\"$PWD/opencode_setting/opencode-skills\"]}}" \
  HOME="$tmp_opencode_bootstrap_home" \
  XDG_CONFIG_HOME="$tmp_opencode_bootstrap_home/.config" \
  XDG_DATA_HOME="$tmp_opencode_bootstrap_home/.local/share" \
  opencode debug config --pure >/tmp/opencode-bootstrap.json
rg 'opencode_setting/AGENTS.md' /tmp/opencode-bootstrap.json
rg 'opencode_setting/opencode-skills' /tmp/opencode-bootstrap.json
! rg '/.claude/' /tmp/opencode-bootstrap.json
tmp_opencode_home=$(mktemp -d)
mkdir -p "$tmp_opencode_home/.config/opencode/agent" "$tmp_opencode_home/.config/opencode/command" "$tmp_opencode_home/.local/share"
for f in "$PWD/opencode_setting/opencode-agents"/*/*.md; do ln -s "$f" "$tmp_opencode_home/.config/opencode/agent/$(basename "$f")"; done
for f in "$PWD/opencode_setting/opencode-commands"/*.md; do ln -s "$f" "$tmp_opencode_home/.config/opencode/command/$(basename "$f")"; done
HOME="$tmp_opencode_home" XDG_CONFIG_HOME="$tmp_opencode_home/.config" XDG_DATA_HOME="$tmp_opencode_home/.local/share" opencode debug agent plan-team --pure >/tmp/opencode-agent.json
HOME="$tmp_opencode_home" XDG_CONFIG_HOME="$tmp_opencode_home/.config" XDG_DATA_HOME="$tmp_opencode_home/.local/share" opencode debug config --pure >/tmp/opencode-command.json
! rg '/.claude/' /tmp/opencode-agent.json
! rg '/.claude/' /tmp/opencode-command.json
tmp_opencode_plugin_project=$(mktemp -d)
mkdir -p "$tmp_opencode_plugin_project/.opencode/plugins"
ln -s "$PWD/opencode_setting/opencode-plugins/agent-harness-guards.js" "$tmp_opencode_plugin_project/.opencode/plugins/agent-harness-guards.js"
(cd "$tmp_opencode_plugin_project" && HOME="$tmp_opencode_home" XDG_CONFIG_HOME="$tmp_opencode_home/.config" XDG_DATA_HOME="$tmp_opencode_home/.local/share" opencode debug config >/tmp/opencode-plugin.json)
rg 'agent-harness-guards.js' /tmp/opencode-plugin.json
! rg 'adapters/claude/hooks' /tmp/opencode-plugin.json
OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1 \
OPENCODE_CONFIG_CONTENT="{\"skills\":{\"paths\":[\"$PWD/opencode_setting/opencode-skills\"]}}" \
  opencode debug skill --pure >/tmp/opencode-skills.json
! rg '"location": ".*/\.claude/skills' /tmp/opencode-skills.json
```

Do not run drill automatically during migration; it invokes headless runtime sessions and can spend tokens. Run a targeted drill only after the symlink projection is confirmed.
