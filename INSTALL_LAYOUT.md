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

Codex does not currently consume the full harness natively. Keep `$HOME/.codex` runtime-owned and expose a stable pointer:

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
```

Do not symlink Claude-native surfaces such as `settings.json`, `commands/`,
`skills/`, `statusline.sh`, or `hooks/` into `$HOME/.codex`. Future
Codex-specific bootstrap files should live under `adapters/codex/` and be
symlinked or generated into `codex_setting/` without moving Codex credentials,
logs, sessions, or SQLite state into the repo.

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
```

Do not symlink Claude-native surfaces such as `settings.json`, `commands/`,
`skills/`, `statusline.sh`, or `hooks/` into `$HOME/.config/opencode`.
OpenCode has native `.opencode/skill/`, `.opencode/command/`, `.opencode/agent/`,
and JS/TS plugin hook surfaces; future OpenCode-specific bootstrap files
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
codex_setting/bin/preflight.sh capability-info autopilot-code
opencode_setting/bin/preflight.sh capability-info autopilot-code
adapters/opencode/bin/sync-native-skills.py --check
OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1 opencode debug skill --pure >/tmp/opencode-skills.json
! rg '"location": ".*/\.claude/skills' /tmp/opencode-skills.json
```

Do not run drill automatically during migration; it invokes headless runtime sessions and can spend tokens. Run a targeted drill only after the symlink projection is confirmed.
