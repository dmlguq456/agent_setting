# Install Layout

This harness is runtime-neutral. The git repository should live outside vendor runtime homes, and each runtime home should project the harness through symlinks or adapter bootstrap files.

## Target Layout

```text
$HOME/agent_setting/        # canonical git repo: common core + adapters + projections
$HOME/.claude/              # Claude Code runtime home
$HOME/.codex/               # Codex runtime home
```

Do not make `$HOME/.claude` or `$HOME/.codex` the canonical repo. Those directories contain runtime-owned state such as credentials, sessions, logs, SQLite databases, caches, and shell snapshots.

## Claude Code Projection

Claude Code expects files under `$HOME/.claude`. Keep runtime-owned files there, and symlink harness-owned files from the versioned Claude projection:

```bash
export AGENT_HOME="$HOME/agent_setting"

for p in CLAUDE.md README.md core settings.json keybindings.json commands skills agents agent-modes hooks utilities tools scaffolds loops manifest.json statusline.sh track-toggle.sh; do
  ln -sfn "$AGENT_HOME/claude_setting/$p" "$HOME/.claude/$p"
done
```

Keep these local to `$HOME/.claude`: `.credentials.json`, `.dispatch/`, `cache/`, `daemon/`, `history.jsonl`, `ide/`, `projects/`, `sessions/`, `session-env/`, `shell-snapshots/`, runtime logs, and other runtime-generated state.

## Codex Projection

Codex does not currently consume the full harness natively. Keep `$HOME/.codex` runtime-owned and expose a stable pointer:

```bash
export AGENT_HOME="$HOME/agent_setting"
ln -sfn "$AGENT_HOME" "$HOME/.codex/agent-harness"
ln -sfn "$AGENT_HOME/adapters/codex/AGENTS.md" "$HOME/.codex/AGENTS.md"
```

Future Codex-specific bootstrap files should live under `adapters/codex/` and be symlinked or generated into `$HOME/.codex` without moving Codex credentials, logs, sessions, or SQLite state into the repo.

## Migration Order

1. Commit and push the current repo.
2. Stop long-running runtime processes that may write into `$HOME/.claude` or `$HOME/.codex`.
3. Move or clone the repo to `$HOME/agent_setting`.
4. In each runtime home, replace harness-owned files/directories with symlinks to `$HOME/agent_setting`.
5. Set `AGENT_HOME=$HOME/agent_setting` in shell/profile or runtime wrapper.
6. Run validation:

```bash
cd "$HOME/agent_setting"
python3 tools/build-manifest.py --check
python3 -m py_compile tools/build-manifest.py tools/memory/mem.py
sh utilities/agent-home.sh
```

Do not run drill automatically during migration; it invokes headless runtime sessions and can spend tokens. Run a targeted drill only after the symlink projection is confirmed.
