#!/usr/bin/env sh
# install-runtime-projection.sh — wire the Codex runtime home ($CODEX_HOME,
# default $HOME/.codex) to the portable harness projection under
# codex_setting/. Idempotent: re-running only refreshes harness-owned symlinks.
#
# It NEVER touches Codex-owned credentials, sessions, history, logs, caches,
# config.toml, or local databases. It only creates/refreshes the harness
# `agent-*` pointers, `hooks.json`, and per-skill / per-agent symlinks. A pre-existing real
# `hooks.json` is backed up once to `hooks.json.pre-harness` before it is
# replaced by the projection symlink.
#
# Plugin install is opt-in: pass --install-plugin to run the `codex plugin`
# commands; otherwise the plugin is left untouched (the checker reports it).
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME=${AGENT_HOME:-}
if [ -z "$AGENT_HOME" ] || [ ! -f "$AGENT_HOME/core/CORE.md" ]; then
  AGENT_HOME=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)
fi
CODEX_HOME=${CODEX_HOME:-$HOME/.codex}

install_plugin=0
for arg in "$@"; do
  case "$arg" in
    --install-plugin) install_plugin=1 ;;
    -h|--help)
      cat <<EOF
usage: install-runtime-projection.sh [--install-plugin]

Wires \$CODEX_HOME (default \$HOME/.codex) to the harness projection in
codex_setting/. Idempotent; never mutates Codex-owned runtime state.
  --install-plugin   also run codex plugin marketplace add + plugin add
EOF
      exit 0 ;;
    *) echo "install-runtime-projection: unknown option: $arg" >&2; exit 64 ;;
  esac
done

if [ ! -d "$AGENT_HOME/codex_setting" ]; then
  echo "install-runtime-projection: codex_setting projection missing under $AGENT_HOME" >&2
  exit 69
fi

mkdir -p "$CODEX_HOME"

# link <target> <linkpath>: refresh a harness-owned symlink. Refuses to clobber a
# real (non-symlink) file or directory, except hooks.json which is backed up.
link() {
  target=$1
  linkpath=$2
  if [ ! -e "$target" ]; then
    printf 'skip=%s reason=projection-target-missing\n' "$linkpath"
    return 0
  fi
  if [ -e "$linkpath" ] && [ ! -L "$linkpath" ]; then
    if [ "$(basename "$linkpath")" = "hooks.json" ]; then
      [ -e "$linkpath.pre-harness" ] || cp "$linkpath" "$linkpath.pre-harness"
      rm -f "$linkpath"
    else
      printf 'skip=%s reason=non-symlink-exists\n' "$linkpath"
      return 0
    fi
  fi
  ln -sfn "$target" "$linkpath"
  printf 'link=%s\n' "$linkpath"
}

S="$AGENT_HOME/codex_setting"

# Stable harness pointers consumed by the Codex adapter at runtime.
link "$AGENT_HOME"                       "$CODEX_HOME/agent-harness"
link "$S/AGENTS.md"                      "$CODEX_HOME/AGENTS.md"
link "$S/README.md"                      "$CODEX_HOME/agent-harness-readme.md"
link "$S/core"                           "$CODEX_HOME/agent-core"
link "$S/capabilities"                   "$CODEX_HOME/agent-capabilities"
link "$S/roles"                          "$CODEX_HOME/agent-roles"
link "$S/bin"                            "$CODEX_HOME/agent-bin"
link "$S/tools"                          "$CODEX_HOME/agent-tools"
link "$S/utilities"                      "$CODEX_HOME/agent-utilities"
link "$S/codex-skills"                   "$CODEX_HOME/agent-skills"
link "$S/codex-modes"                    "$CODEX_HOME/agent-modes"
link "$S/codex-agents"                   "$CODEX_HOME/agent-agents"
link "$S/codex-plugin-marketplace"       "$CODEX_HOME/agent-plugin-marketplace"
link "$S/codex-hooks"                    "$CODEX_HOME/agent-hooks"
link "$S/codex-config"                   "$CODEX_HOME/agent-config"
link "$S/codex-hooks/hooks.json"         "$CODEX_HOME/hooks.json"

# Native Codex skill discovery: one symlink per generated skill directory.
skills_linked=0
mkdir -p "$CODEX_HOME/skills"
for d in "$S/codex-skills"/*; do
  [ -d "$d" ] || continue
  ln -sfn "$d" "$CODEX_HOME/skills/$(basename "$d")"
  skills_linked=$((skills_linked + 1))
done
printf 'skills_linked=%s\n' "$skills_linked"

# Native Codex custom-agent discovery: one symlink per generated TOML.
agents_linked=0
mkdir -p "$CODEX_HOME/agents"
for f in "$S/codex-agents"/*.toml; do
  [ -f "$f" ] || continue
  ln -sfn "$f" "$CODEX_HOME/agents/$(basename "$f")"
  agents_linked=$((agents_linked + 1))
done
printf 'agents_linked=%s\n' "$agents_linked"

if [ "$install_plugin" = "1" ]; then
  if command -v codex >/dev/null 2>&1; then
    CODEX_HOME="$CODEX_HOME" codex plugin marketplace add "$S/codex-plugin-marketplace" >/dev/null 2>&1 || true
    CODEX_HOME="$CODEX_HOME" codex plugin add agent-harness-codex@agent-harness >/dev/null 2>&1 || true
    printf 'plugin_install=attempted\n'
  else
    printf 'plugin_install=skipped reason=codex-command-not-found\n'
  fi
else
  printf 'plugin_install=not-requested hint=rerun-with---install-plugin\n'
fi

printf 'status=ok\n'
printf 'codex_home=%s\n' "$CODEX_HOME"
