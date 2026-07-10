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

# Harness-owned, read-only at runtime: symlink so repo edits flow through.
for p in CLAUDE.md README.md core commands skills agents agent-modes hooks utilities tools scaffolds loops manifest.json statusline.sh track-toggle.sh; do
  ln -sfn "$AGENT_HOME/claude_setting/$p" "$HOME/.claude/$p"
done

# Runtime-owned: Claude Code rewrites these in place (/model, /config, in-app
# keybinding edits). An atomic settings write replaces a symlink with a regular
# file, so a linked settings.json silently diverges from — and pollutes — the
# repo. Copy once and let the runtime own them; never re-link.
for p in settings.json keybindings.json; do
  [ -e "$HOME/.claude/$p" ] || cp "$AGENT_HOME/claude_setting/$p" "$HOME/.claude/$p"
done
```

Keep these local to `$HOME/.claude`: `.credentials.json`, `.dispatch/`, `cache/`, `daemon/`, `history.jsonl`, `ide/`, `projects/`, `sessions/`, `session-env/`, `shell-snapshots/`, runtime logs, and other runtime-generated state.

If present, existing `worklog-board/` and `worklog-board-wt/` directories under
`$HOME/.claude` are local worklog app workspaces, not harness projection
targets. Do not move their data during harness installation. Their notes data
root is `<agent-notes-root>`, which is mutable continuity state and should not
be committed to this repo. Adapter docs own concrete local path realizations.

## Windows Projection (Git Bash)

Claude Code runs on Windows, but the harness assumes a POSIX runtime. Two
Windows-specific facts break the projection silently — a one-shot installer
(`adapters/claude/bin/install-windows.sh`, run from Git Bash) repairs both and
is idempotent:

```bash
bash ~/.claude/adapters/claude/bin/install-windows.sh
```

1. **Unreliable `$HOME`.** The shell Claude Code spawns for hook / statusLine
   commands sees `$HOME` as either empty or the MSYS `/home/<user>` — never the
   real `%USERPROFILE%` where `.claude` actually lives. Every
   `bash "$HOME/.claude/hooks/<x>.sh"` command therefore fails to resolve and the
   hook/statusline no-ops with no obvious cause. The installer injects
   `HOME` / `CLAUDE_HOME` / `AGENT_HOME` into the runtime `settings.json` `env`
   block (which Claude Code applies to command execution) so those paths resolve.

2. **`core.symlinks=false`.** A Windows checkout writes repo symlinks out as
   small pointer-TEXT files (content = the link target path), not real files. So
   the entry files the Linux projection step symlinks into the runtime home
   (`CLAUDE.md`, `statusline.sh`, `track-toggle.sh`) are absent or pointer-text on
   Windows, and `~/.claude/CLAUDE.md` never loads. The installer copies each from
   its single source of truth (`adapters/claude/<name>`) into the runtime home
   when the target is missing or a pointer — the Windows equivalent of the Linux
   `ln -sfn` step.

The installer also restores the per-machine memory DB from the git-tracked
`dump.jsonl` mirror when it is missing (`mem import`).

**Known limitation — `fleet`.** The `fleet` dashboard is a `curses` TUI, and
native Windows Python ships no `curses` module. `fleet` is therefore
unsupported on native Windows; run it under WSL or Linux. Everything else
(hooks, memory, statusline, skills) runs under Git Bash.

## Cross-harness CLI — `fleet`

`fleet` (the cross-harness live dashboard, `tools/fleet/`) is runtime-neutral — it
observes every harness (Claude Code · Codex · opencode) from the process table and
on-disk state, so it belongs to no single adapter. The launcher `tools/fleet/fleet.sh`
runs from the repo directly; to get the one-word `fleet` command, symlink it onto `PATH`:

```bash
export AGENT_HOME="$HOME/agent_setting"
mkdir -p "$HOME/.local/bin"
ln -sfn "$AGENT_HOME/tools/fleet/fleet.sh" "$HOME/.local/bin/fleet"   # needs ~/.local/bin on PATH
```

No install step at all still works — run it by path: `bash "$AGENT_HOME/tools/fleet/fleet.sh"`
(or, via the Claude projection above, `bash ~/.claude/tools/fleet/fleet.sh`). Zero-dep
(stdlib python3 + curses); nothing to build.

## Codex Projection

Keep `$HOME/.codex` runtime-owned. Project the portable harness through a
stable pointer plus adapter-owned Codex-native Skills, custom Agents, plugin
marketplace, mode guides, and hook bridges:

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
ln -sfn "$AGENT_HOME/codex_setting/scaffolds" "$HOME/.codex/agent-scaffolds"
ln -sfn "$AGENT_HOME/codex_setting/codex-skills" "$HOME/.codex/agent-skills"
ln -sfn "$AGENT_HOME/codex_setting/codex-modes" "$HOME/.codex/agent-modes"
ln -sfn "$AGENT_HOME/codex_setting/codex-agents" "$HOME/.codex/agent-agents"
ln -sfn "$AGENT_HOME/codex_setting/codex-plugin-marketplace" "$HOME/.codex/agent-plugin-marketplace"
ln -sfn "$AGENT_HOME/codex_setting/codex-hooks" "$HOME/.codex/agent-hooks"
ln -sfn "$AGENT_HOME/codex_setting/codex-config" "$HOME/.codex/agent-config"
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
Codex-native mode guides must come from `codex_setting/codex-modes`, which is
generated from `roles/modes/` and checked through `mode-info`.
Codex-native plugin installation must use
`codex_setting/codex-plugin-marketplace`, which points at the adapter-owned
repo-local marketplace projection rather than the whole Codex adapter.
Codex-native hook configuration must come from
`codex_setting/codex-hooks`, which points at adapter-owned hook bridges.
Reusable design scaffold assets must come from `codex_setting/scaffolds`,
which points at the Codex-owned scaffold projection. Do not point Codex at
Claude Design MCP files or Claude runtime paths.
Codex `/statusline` writes user TUI preferences into runtime-owned
`$HOME/.codex/config.toml`; do not project that full file. The harness records
only the recommended footer fragment at
`codex_setting/codex-config/tui-statusline.toml`, exposed through the
read-only `$HOME/.codex/agent-config` pointer. To apply that fragment to
`config.toml`, run `codex_setting/bin/preflight.sh tui-config`; it updates only
`[tui].status_line` and `[tui].status_line_use_colors`.
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
non_claude_runtime_re='adapters/claude|claude_setting|settings\.json|statusline\.sh|CLAUDE\.md|track-toggle\.sh|agent-modes|allowedTools|/\.claude/'
python3 tools/build-manifest.py --check
python3 -c "import sys; [compile(open(f, encoding='utf-8').read(), f, 'exec') for f in sys.argv[1:]]" tools/build-manifest.py tools/memory/mem.py
sh utilities/agent-home.sh
tools/check-adaptation-boundary.sh
adapters/codex/bin/sync-native-skills.py --check
adapters/codex/bin/sync-native-agents.py --check
adapters/codex/bin/sync-native-modes.py --check
adapters/codex/bin/sync-native-plugin.py --check
codex_setting/bin/preflight.sh capability-info autopilot-code >/tmp/codex-capability.txt
rg '^native_skill_path=adapters/codex/skills/autopilot-code/SKILL.md$' /tmp/codex-capability.txt
rg '^native_plugin_skill_path=adapters/codex/plugins/agent-harness-codex/skills/autopilot-code/SKILL.md$' /tmp/codex-capability.txt
rg '^compat_reference=not-projected$' /tmp/codex-capability.txt
codex_setting/bin/preflight.sh role fast reviewer >/tmp/codex-role.txt
rg '^adapter=codex$' /tmp/codex-role.txt
rg '^source=roles/README.md$' /tmp/codex-role.txt
rg '^family=fast$' /tmp/codex-role.txt
codex_setting/bin/preflight.sh permissions >/tmp/codex-permissions.txt
rg '^runtime_surface=codex-native-approval-sandbox$' /tmp/codex-permissions.txt
rg '^claude_allowed_tools=unsupported$' /tmp/codex-permissions.txt
codex_setting/bin/preflight.sh mcp >/tmp/codex-mcp.txt
rg '^runtime_surface=codex-native-mcp$' /tmp/codex-mcp.txt
rg '^claude_settings_mcp=unsupported$' /tmp/codex-mcp.txt
codex_setting/bin/preflight.sh headless >/tmp/codex-headless.txt
rg '^runtime_surface=codex-exec-headless$' /tmp/codex-headless.txt
rg '^liveness_surface=codex-session-jsonl-mtime$' /tmp/codex-headless.txt
codex_setting/bin/preflight.sh dispatch --dry-run --worktree "$PWD" --slug install-check --capability audit --mode qa/plan-review --qa quick --model-role "fast reviewer" >/tmp/codex-dispatch.txt
rg '^registered=0$' /tmp/codex-dispatch.txt
codex_setting/bin/preflight.sh harvest --jobs /tmp/codex-missing-jobs.log --slug install-check >/tmp/codex-harvest.txt
rg '^matched=0$' /tmp/codex-harvest.txt
codex_setting/bin/preflight.sh liveness "$AGENT_HOME/.dispatch/jobs.log" >/tmp/codex-liveness.txt
codex_setting/bin/preflight.sh mode-info dev/backend >/tmp/codex-mode.txt
rg '^adapter=codex$' /tmp/codex-mode.txt
rg '^status=portable$' /tmp/codex-mode.txt
rg '^native_mode_path=adapters/codex/modes/dev/backend.md$' /tmp/codex-mode.txt
test -f codex_setting/codex-modes/dev/backend.md
codex_setting/bin/preflight.sh status "$PWD" install-check >/tmp/codex-status.txt
rg '^adapter=codex$' /tmp/codex-status.txt
rg '^runtime_surface=adapter-owned-harness-status$' /tmp/codex-status.txt
test -x codex_setting/utilities/harness-status.sh
codex_setting/bin/preflight.sh loop-info drill >/tmp/codex-loop-drill.txt
rg '^status=manual-contract$' /tmp/codex-loop-drill.txt
rg '^auto_run=unsupported$' /tmp/codex-loop-drill.txt
codex_setting/bin/preflight.sh loop-info study >/tmp/codex-loop-study.txt
rg '^status=manual-contract$' /tmp/codex-loop-study.txt
rg '^action=proposal-report-only$' /tmp/codex-loop-study.txt
rg '^fallback=read-source-and-draft-proposal-in-main-session$' /tmp/codex-loop-study.txt
codex_setting/bin/preflight.sh loop-info note >/tmp/codex-loop-note.txt
rg '^status=unsupported$' /tmp/codex-loop-note.txt
rg '^related_capability=autopilot-note$' /tmp/codex-loop-note.txt
rg '^native_capability_surface=codex-native-skill-plugin$' /tmp/codex-loop-note.txt
rg '^scheduler_surface=external-worklog-board$' /tmp/codex-loop-note.txt
rg '^fallback=worklog-board-or-manual-post-it-flow$' /tmp/codex-loop-note.txt
if codex_setting/bin/preflight.sh distill-propose install-check "$PWD" >/tmp/codex-distill-propose.txt; then false; else test "$?" -eq 69; fi
rg '^status=tool-contract$' /tmp/codex-distill-propose.txt
rg '^reason=distill-proposal-disabled$' /tmp/codex-distill-propose.txt
rg '^enable=CODEX_DISTILL_ENABLE=1$' /tmp/codex-distill-propose.txt
codex_setting/bin/preflight.sh mode-info material/browser-fetch >/tmp/codex-browser-fetch-mode.txt
rg '^tool_contract=browser-fetch$' /tmp/codex-browser-fetch-mode.txt
rg '^runtime_surface=adapter-owned-browser-fetch$' /tmp/codex-browser-fetch-mode.txt
rg '^native_mode_path=adapters/codex/modes/material/browser-fetch.md$' /tmp/codex-browser-fetch-mode.txt
test -x codex_setting/tools/material/browser-fetch.sh
codex_setting/bin/preflight.sh mode-info material/data-script >/tmp/codex-data-script-mode.txt
rg '^tool_contract=data-script$' /tmp/codex-data-script-mode.txt
rg '^runtime_surface=adapter-owned-data-script$' /tmp/codex-data-script-mode.txt
test -x codex_setting/tools/material/data-script.sh
codex_setting/bin/preflight.sh mode-info material/figure-gen >/tmp/codex-figure-gen-mode.txt
rg '^tool_contract=figure-gen$' /tmp/codex-figure-gen-mode.txt
rg '^runtime_surface=adapter-owned-figure-gen$' /tmp/codex-figure-gen-mode.txt
test -x codex_setting/tools/material/figure-gen.sh
codex_setting/bin/preflight.sh mode-info material/pdf-extract >/tmp/codex-pdf-extract-mode.txt
rg '^tool_contract=pdf-extract$' /tmp/codex-pdf-extract-mode.txt
rg '^runtime_surface=adapter-owned-pdf-extract$' /tmp/codex-pdf-extract-mode.txt
test -x codex_setting/tools/material/pdf-extract.sh
codex_setting/bin/preflight.sh mode-info material/web-image-search >/tmp/codex-web-image-search-mode.txt
rg '^tool_contract=web-image-search$' /tmp/codex-web-image-search-mode.txt
rg '^runtime_surface=adapter-owned-web-image-search$' /tmp/codex-web-image-search-mode.txt
test -x codex_setting/tools/material/web-image-search.sh
codex_setting/bin/preflight.sh mode-info qa/test >/tmp/codex-test-mode.txt
rg '^tool_contract=verification-runner$' /tmp/codex-test-mode.txt
rg '^runtime_surface=adapter-owned-verification-runner$' /tmp/codex-test-mode.txt
rg '^native_mode_path=adapters/codex/modes/qa/test.md$' /tmp/codex-test-mode.txt
test -x codex_setting/tools/qa/verification-runner.sh
codex_setting/bin/preflight.sh mode-info research/claim-verify >/tmp/codex-claim-verify-mode.txt
rg '^tool_contract=external-claim-verification$' /tmp/codex-claim-verify-mode.txt
rg '^runtime_surface=adapter-owned-claim-verify$' /tmp/codex-claim-verify-mode.txt
test -x codex_setting/tools/research/claim-verify.sh
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
! rg "$non_claude_runtime_re" /tmp/codex-skills.json
tmp_codex_plugin_home=$(mktemp -d)
CODEX_HOME="$tmp_codex_plugin_home" codex plugin marketplace add "$PWD/codex_setting/codex-plugin-marketplace" --json >/tmp/codex-plugin-marketplace.json
CODEX_HOME="$tmp_codex_plugin_home" codex plugin add agent-harness-codex@agent-harness --json >/tmp/codex-plugin-add.json
CODEX_HOME="$tmp_codex_plugin_home" codex debug prompt-input autopilot-code >/tmp/codex-plugin-skills.json
! rg "$non_claude_runtime_re" /tmp/codex-plugin-skills.json
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
assert "SessionEnd" in hooks, hooks
assert "Stop" in hooks, hooks
assert "UserPromptSubmit" in hooks, hooks
assert "PermissionRequest" in hooks, hooks
assert "PreToolUse" in hooks, hooks
assert "PostToolUse" in hooks, hooks
body = hook_json.read_text(encoding="utf-8")
assert "sessionstart-lifecycle.py" in body, hook_json
assert "sessionend-lifecycle.py" in body, hook_json
assert "userprompt-lifecycle.py" in body, hook_json
assert "permissionrequest-lifecycle.py" in body, hook_json
assert "pretooluse-write-guard.py" in body, hook_json
assert "posttooluse-read-marker.py" in body, hook_json
assert "posttooluse-design-check.py" in body, hook_json
PY
! rg "$non_claude_runtime_re" "$tmp_codex_hook_home/hooks.json"
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
! rg "$non_claude_runtime_re" "$tmp_codex_agent_home/agents"
opencode_setting/bin/preflight.sh capability-info autopilot-code >/tmp/opencode-capability.txt
rg '^native_skill_path=adapters/opencode/skills/autopilot-code/SKILL.md$' /tmp/opencode-capability.txt
rg '^native_command_path=adapters/opencode/commands/autopilot-code.md$' /tmp/opencode-capability.txt
rg '^compat_reference=not-projected$' /tmp/opencode-capability.txt
adapters/opencode/bin/sync-native-skills.py --check
adapters/opencode/bin/sync-native-agents.py --check
adapters/opencode/bin/sync-native-commands.py --check
tmp_opencode_bootstrap_home=$(mktemp -d)
opencode_setting/bin/preflight.sh role fast reviewer >/tmp/opencode-role.txt
rg '^adapter=opencode$' /tmp/opencode-role.txt
rg '^source=roles/README.md$' /tmp/opencode-role.txt
rg '^family=fast$' /tmp/opencode-role.txt
opencode_setting/bin/preflight.sh permissions >/tmp/opencode-permissions.txt
rg '^runtime_surface=opencode-native-permission-config$' /tmp/opencode-permissions.txt
rg '^claude_allowed_tools=unsupported$' /tmp/opencode-permissions.txt
opencode_setting/bin/preflight.sh mcp >/tmp/opencode-mcp.txt
rg '^runtime_surface=opencode-native-mcp$' /tmp/opencode-mcp.txt
rg '^claude_settings_mcp=unsupported$' /tmp/opencode-mcp.txt
opencode_setting/bin/preflight.sh headless >/tmp/opencode-headless.txt
rg '^runtime_surface=opencode-run-headless$' /tmp/opencode-headless.txt
rg '^liveness_surface=opencode-sqlite-session-mtime$' /tmp/opencode-headless.txt
opencode_setting/bin/preflight.sh dispatch --dry-run --worktree "$PWD" --slug install-check --capability audit --mode qa/plan-review --qa quick --inherit-model-settings >/tmp/opencode-dispatch.txt
rg '^registered=0$' /tmp/opencode-dispatch.txt
opencode_setting/bin/preflight.sh harvest --jobs /tmp/opencode-missing-jobs.log --slug install-check >/tmp/opencode-harvest.txt
rg '^matched=0$' /tmp/opencode-harvest.txt
opencode_setting/bin/preflight.sh liveness "$AGENT_HOME/.dispatch/jobs.log" >/tmp/opencode-liveness.txt
opencode_setting/bin/preflight.sh mode-info dev/backend >/tmp/opencode-mode.txt
rg '^adapter=opencode$' /tmp/opencode-mode.txt
rg '^status=portable$' /tmp/opencode-mode.txt
opencode_setting/bin/preflight.sh status "$PWD" install-check >/tmp/opencode-status.txt
rg '^adapter=opencode$' /tmp/opencode-status.txt
rg '^runtime_surface=adapter-owned-harness-status$' /tmp/opencode-status.txt
test -x opencode_setting/utilities/harness-status.sh
opencode_setting/bin/preflight.sh loop-info drill >/tmp/opencode-loop-drill.txt
rg '^status=manual-contract$' /tmp/opencode-loop-drill.txt
rg '^auto_run=unsupported$' /tmp/opencode-loop-drill.txt
opencode_setting/bin/preflight.sh loop-info study >/tmp/opencode-loop-study.txt
rg '^status=manual-contract$' /tmp/opencode-loop-study.txt
rg '^action=proposal-report-only$' /tmp/opencode-loop-study.txt
rg '^fallback=read-source-and-draft-proposal-in-main-session$' /tmp/opencode-loop-study.txt
opencode_setting/bin/preflight.sh loop-info note >/tmp/opencode-loop-note.txt
rg '^status=unsupported$' /tmp/opencode-loop-note.txt
rg '^related_capability=autopilot-note$' /tmp/opencode-loop-note.txt
rg '^native_capability_surface=opencode-native-skill-command$' /tmp/opencode-loop-note.txt
rg '^scheduler_surface=external-worklog-board$' /tmp/opencode-loop-note.txt
rg '^fallback=worklog-board-or-manual-post-it-flow$' /tmp/opencode-loop-note.txt
if opencode_setting/bin/preflight.sh distill-propose install-check "$PWD" >/tmp/opencode-distill-propose.txt; then false; else test "$?" -eq 69; fi
rg '^status=tool-contract$' /tmp/opencode-distill-propose.txt
rg '^reason=distill-proposal-disabled$' /tmp/opencode-distill-propose.txt
rg '^tool_contract=no-tools-distill-worker$' /tmp/opencode-distill-propose.txt
opencode_setting/bin/preflight.sh mode-info material/browser-fetch >/tmp/opencode-browser-fetch-mode.txt
rg '^tool_contract=browser-fetch$' /tmp/opencode-browser-fetch-mode.txt
rg '^runtime_surface=adapter-owned-browser-fetch$' /tmp/opencode-browser-fetch-mode.txt
test -x opencode_setting/tools/material/browser-fetch.sh
opencode_setting/bin/preflight.sh mode-info material/data-script >/tmp/opencode-data-script-mode.txt
rg '^tool_contract=data-script$' /tmp/opencode-data-script-mode.txt
rg '^runtime_surface=adapter-owned-data-script$' /tmp/opencode-data-script-mode.txt
test -x opencode_setting/tools/material/data-script.sh
opencode_setting/bin/preflight.sh mode-info material/figure-gen >/tmp/opencode-figure-gen-mode.txt
rg '^tool_contract=figure-gen$' /tmp/opencode-figure-gen-mode.txt
rg '^runtime_surface=adapter-owned-figure-gen$' /tmp/opencode-figure-gen-mode.txt
test -x opencode_setting/tools/material/figure-gen.sh
opencode_setting/bin/preflight.sh mode-info material/pdf-extract >/tmp/opencode-pdf-extract-mode.txt
rg '^tool_contract=pdf-extract$' /tmp/opencode-pdf-extract-mode.txt
rg '^runtime_surface=adapter-owned-pdf-extract$' /tmp/opencode-pdf-extract-mode.txt
test -x opencode_setting/tools/material/pdf-extract.sh
opencode_setting/bin/preflight.sh mode-info material/web-image-search >/tmp/opencode-web-image-search-mode.txt
rg '^tool_contract=web-image-search$' /tmp/opencode-web-image-search-mode.txt
rg '^runtime_surface=adapter-owned-web-image-search$' /tmp/opencode-web-image-search-mode.txt
test -x opencode_setting/tools/material/web-image-search.sh
opencode_setting/bin/preflight.sh mode-info qa/test >/tmp/opencode-test-mode.txt
rg '^tool_contract=verification-runner$' /tmp/opencode-test-mode.txt
rg '^runtime_surface=adapter-owned-verification-runner$' /tmp/opencode-test-mode.txt
test -x opencode_setting/tools/qa/verification-runner.sh
opencode_setting/bin/preflight.sh mode-info research/claim-verify >/tmp/opencode-claim-verify-mode.txt
rg '^tool_contract=external-claim-verification$' /tmp/opencode-claim-verify-mode.txt
rg '^runtime_surface=adapter-owned-claim-verify$' /tmp/opencode-claim-verify-mode.txt
test -x opencode_setting/tools/research/claim-verify.sh
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
! rg "$non_claude_runtime_re" /tmp/opencode-agent.json
! rg "$non_claude_runtime_re" /tmp/opencode-command.json
tmp_opencode_plugin_project=$(mktemp -d)
mkdir -p "$tmp_opencode_plugin_project/.opencode/plugins"
ln -s "$PWD/opencode_setting/opencode-plugins/agent-harness-guards.js" "$tmp_opencode_plugin_project/.opencode/plugins/agent-harness-guards.js"
(cd "$tmp_opencode_plugin_project" && HOME="$tmp_opencode_home" XDG_CONFIG_HOME="$tmp_opencode_home/.config" XDG_DATA_HOME="$tmp_opencode_home/.local/share" opencode debug config >/tmp/opencode-plugin.json)
rg 'agent-harness-guards.js' /tmp/opencode-plugin.json
! rg "$non_claude_runtime_re" /tmp/opencode-plugin.json
OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1 \
OPENCODE_CONFIG_CONTENT="{\"skills\":{\"paths\":[\"$PWD/opencode_setting/opencode-skills\"]}}" \
  opencode debug skill --pure >/tmp/opencode-skills.json
! rg "$non_claude_runtime_re" /tmp/opencode-skills.json
```

Do not run drill automatically during migration; it invokes headless runtime sessions and can spend tokens. Run a targeted drill only after the symlink projection is confirmed.
