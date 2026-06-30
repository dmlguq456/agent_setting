#!/usr/bin/env sh
# check-runtime-projection.sh — read-only validation that the Codex runtime home
# ($CODEX_HOME, default $HOME/.codex) is wired to the harness projection. Emits
# machine-readable `check=<name>:ok|failed|skipped` lines plus a final
# `status=ok|failed`. Hard checks (symlink wiring, linked skills/agents) drive
# status; bootstrap/plugin checks are soft (skipped when codex is unavailable,
# the plugin reports install commands when missing). config.toml stays
# runtime-owned, so only the harness config fragment pointer is checked.
# Set CODEX_REQUIRE_HOOK_TRUST=1 to make missing `/hooks` trust records fail.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME=${AGENT_HOME:-}
if [ -z "$AGENT_HOME" ] || [ ! -f "$AGENT_HOME/core/CORE.md" ]; then
  AGENT_HOME=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)
fi
CODEX_HOME=${CODEX_HOME:-$HOME/.codex}
CLI_TIMEOUT=${CODEX_RUNTIME_PROJECTION_CLI_TIMEOUT:-15}
S="$AGENT_HOME/codex_setting"

case "${1:-}" in
  -h|--help)
    echo "usage: check-runtime-projection.sh   # validates \$CODEX_HOME wiring, read-only"
    exit 0 ;;
esac

fails=0
printf 'runtime_surface=codex-runtime-projection-check\n'
printf 'codex_home=%s\n' "$CODEX_HOME"

real() { readlink -f "$1" 2>/dev/null || true; }

expect_link() {  # <linkpath> <expected-target> <checkname>
  lp=$1; exp=$2; name=$3
  if [ -L "$lp" ] && [ -n "$(real "$lp")" ] && [ "$(real "$lp")" = "$(real "$exp")" ]; then
    printf 'check=%s:ok\n' "$name"
  else
    printf 'check=%s:failed reason=expected-symlink-to:%s\n' "$name" "$exp"
    fails=$((fails + 1))
  fi
}

expect_link "$CODEX_HOME/agent-harness"            "$AGENT_HOME"                  agent-harness
expect_link "$CODEX_HOME/AGENTS.md"                "$S/AGENTS.md"                 agents-md
expect_link "$CODEX_HOME/agent-harness-readme.md"  "$S/README.md"                 agent-harness-readme
expect_link "$CODEX_HOME/agent-core"               "$S/core"                      agent-core
expect_link "$CODEX_HOME/agent-capabilities"       "$S/capabilities"              agent-capabilities
expect_link "$CODEX_HOME/agent-roles"              "$S/roles"                     agent-roles
expect_link "$CODEX_HOME/agent-bin"                "$S/bin"                       agent-bin
expect_link "$CODEX_HOME/agent-tools"              "$S/tools"                     agent-tools
expect_link "$CODEX_HOME/agent-utilities"          "$S/utilities"                 agent-utilities
expect_link "$CODEX_HOME/agent-scaffolds"          "$S/scaffolds"                 agent-scaffolds
expect_link "$CODEX_HOME/agent-skills"             "$S/codex-skills"              agent-skills
expect_link "$CODEX_HOME/agent-agents"             "$S/codex-agents"              agent-agents
expect_link "$CODEX_HOME/agent-modes"              "$S/codex-modes"               agent-modes
expect_link "$CODEX_HOME/agent-hooks"              "$S/codex-hooks"               agent-hooks
expect_link "$CODEX_HOME/agent-config"             "$S/codex-config"              agent-config
expect_link "$CODEX_HOME/agent-plugin-marketplace" "$S/codex-plugin-marketplace" agent-plugin-marketplace

hook_trust_check() {
  cfg="$CODEX_HOME/config.toml"
  hook_file="$CODEX_HOME/hooks.json"
  if [ ! -f "$cfg" ]; then
    printf 'check=hook-trust:review-needed reason=config-missing\n'
    printf 'hook_trust_hint=run /hooks in Codex CLI and trust changed agent harness hooks\n'
    [ "${CODEX_REQUIRE_HOOK_TRUST:-0}" = "1" ] && return 1
    return 0
  fi
  has_trust() {
    grep -Fq "$hook_file:$1:" "$cfg"
  }
  session_end_stop_alias() {
    [ -f "$hook_file" ] \
      && grep -Fq '"SessionEnd"' "$hook_file" \
      && grep -Fq '"Stop"' "$hook_file" \
      && [ "$(grep -Fc 'sessionend-lifecycle.py' "$hook_file")" -ge 2 ] \
      && has_trust stop
  }
  missing=""
  alias_note=""
  for event in session_start stop user_prompt_submit permission_request pre_tool_use post_tool_use; do
    if ! has_trust "$event"; then
      missing="$missing $event"
    fi
  done
  if has_trust session_end; then
    :
  elif session_end_stop_alias; then
    alias_note=" session_end=stop-alias"
  else
    missing="$missing session_end"
  fi
  if [ -n "$missing" ]; then
    printf 'check=hook-trust:review-needed missing=%s\n' "$(printf '%s' "$missing" | sed 's/^ //')"
    printf 'hook_trust_hint=run /hooks in Codex CLI and trust changed agent harness hooks\n'
    [ "${CODEX_REQUIRE_HOOK_TRUST:-0}" = "1" ] && return 1
    return 0
  fi
  printf 'check=hook-trust:ok%s\n' "$alias_note"
  return 0
}

if ! hook_trust_check; then
  fails=$((fails + 1))
fi

# hooks.json: harness projection symlink, or a real file with matching content.
if [ -L "$CODEX_HOME/hooks.json" ] && [ "$(real "$CODEX_HOME/hooks.json")" = "$(real "$S/codex-hooks/hooks.json")" ]; then
  printf 'check=hooks-json:ok\n'
elif [ -f "$CODEX_HOME/hooks.json" ] && cmp -s "$CODEX_HOME/hooks.json" "$S/codex-hooks/hooks.json"; then
  printf 'check=hooks-json:ok reason=content-match\n'
else
  printf 'check=hooks-json:failed reason=not-harness-hook-projection\n'
  fails=$((fails + 1))
fi

# Native skill links: every projected skill must be linked to the matching
# adapter-owned directory. A count-only check can miss stale or wrong targets.
projected_skills=$(find -L "$S/codex-skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
linked_skills=$(find "$CODEX_HOME/skills" -mindepth 1 -maxdepth 1 -type l 2>/dev/null | wc -l | tr -d ' ')
printf 'skills_projected=%s skills_linked=%s\n' "$projected_skills" "$linked_skills"
skill_link_fails=0
for d in "$S/codex-skills"/*; do
  [ -d "$d" ] || continue
  name=$(basename "$d")
  linkpath="$CODEX_HOME/skills/$name"
  if [ -L "$linkpath" ] && [ -n "$(real "$linkpath")" ] && [ "$(real "$linkpath")" = "$(real "$d")" ]; then
    printf 'check=skill-link:%s:ok\n' "$name"
  else
    printf 'check=skill-link:%s:failed reason=expected-symlink-to:%s\n' "$name" "$d"
    skill_link_fails=$((skill_link_fails + 1))
  fi
done
if [ "$skill_link_fails" -eq 0 ] && [ "$projected_skills" -gt 0 ]; then
  printf 'check=skills-linked:ok\n'
else
  printf 'check=skills-linked:failed reason=harness-skills-not-linked-or-miswired\n'
  fails=$((fails + 1))
fi

# Native agent links: every projected custom-agent TOML must be linked to the
# matching adapter-owned file.
projected_agents=$(find -L "$S/codex-agents" -mindepth 1 -maxdepth 1 -type f -name '*.toml' 2>/dev/null | wc -l | tr -d ' ')
linked_agents=$(find "$CODEX_HOME/agents" -mindepth 1 -maxdepth 1 -type l 2>/dev/null | wc -l | tr -d ' ')
printf 'agents_projected=%s agents_linked=%s\n' "$projected_agents" "$linked_agents"
agent_link_fails=0
for f in "$S/codex-agents"/*.toml; do
  [ -f "$f" ] || continue
  name=$(basename "$f")
  linkpath="$CODEX_HOME/agents/$name"
  if [ -L "$linkpath" ] && [ -n "$(real "$linkpath")" ] && [ "$(real "$linkpath")" = "$(real "$f")" ]; then
    printf 'check=agent-link:%s:ok\n' "$name"
  else
    printf 'check=agent-link:%s:failed reason=expected-symlink-to:%s\n' "$name" "$f"
    agent_link_fails=$((agent_link_fails + 1))
  fi
done
if [ "$agent_link_fails" -eq 0 ] && [ "$projected_agents" -gt 0 ]; then
  printf 'check=agents-linked:ok\n'
else
  printf 'check=agents-linked:failed reason=harness-agents-not-linked-or-miswired\n'
  fails=$((fails + 1))
fi

# Bootstrap discovery (soft): requires the codex CLI. Headless preflight may
# intentionally skip this when `codex` is stubbed for launch testing.
if [ "${CODEX_RUNTIME_PROJECTION_SKIP_CLI_DISCOVERY:-0}" = "1" ]; then
  printf 'check=bootstrap:skipped reason=codex-cli-discovery-skipped\n'
  printf 'check=plugin:skipped reason=codex-cli-discovery-skipped\n'
elif command -v codex >/dev/null 2>&1; then
  bootstrap_out=""
  if bootstrap_out=$(CODEX_HOME="$CODEX_HOME" timeout "$CLI_TIMEOUT" codex debug prompt-input 'agent harness runtime projection check' 2>/dev/null); then
    if printf '%s\n' "$bootstrap_out" | grep -q 'AGENTS.md — Codex Adapter Bootstrap'; then
      printf 'check=bootstrap:ok\n'
    else
      printf 'check=bootstrap:failed reason=harness-bootstrap-not-loaded\n'
      fails=$((fails + 1))
    fi
  else
    rc=$?
    if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
      printf 'check=bootstrap:skipped reason=codex-cli-timeout timeout=%s\n' "$CLI_TIMEOUT"
    else
      printf 'check=bootstrap:failed reason=codex-debug-failed exit=%s\n' "$rc"
      fails=$((fails + 1))
    fi
  fi
  # Plugin presence (soft): report install commands when missing.
  plugin_out=""
  if plugin_out=$(CODEX_HOME="$CODEX_HOME" timeout "$CLI_TIMEOUT" codex plugin list --json 2>/dev/null); then
    if printf '%s\n' "$plugin_out" | grep -q 'agent-harness-codex'; then
      printf 'check=plugin:ok\n'
    else
      printf 'check=plugin:missing\n'
      printf 'plugin_install_1=codex plugin marketplace add %s/codex-plugin-marketplace\n' "$S"
      printf 'plugin_install_2=codex plugin add agent-harness-codex@agent-harness\n'
      printf 'plugin_hint=run install-runtime-projection.sh --install-plugin\n'
    fi
  else
    rc=$?
    if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
      printf 'check=plugin:skipped reason=codex-cli-timeout timeout=%s\n' "$CLI_TIMEOUT"
    else
      printf 'check=plugin:missing reason=codex-plugin-list-failed exit=%s\n' "$rc"
      printf 'plugin_install_1=codex plugin marketplace add %s/codex-plugin-marketplace\n' "$S"
      printf 'plugin_install_2=codex plugin add agent-harness-codex@agent-harness\n'
      printf 'plugin_hint=run install-runtime-projection.sh --install-plugin\n'
    fi
  fi
else
  printf 'check=bootstrap:skipped reason=codex-command-not-found\n'
  printf 'check=plugin:skipped reason=codex-command-not-found\n'
fi

if [ "$fails" -eq 0 ]; then
  printf 'status=ok\n'
  exit 0
else
  printf 'status=failed fails=%s\n' "$fails"
  exit 1
fi
