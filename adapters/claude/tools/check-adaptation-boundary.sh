#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v git >/dev/null 2>&1 && ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null); then
  :
else
  ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
fi
cd "$ROOT"

fail=0

say() {
  printf '%s\n' "$*"
}

fail_msg() {
  say "FAIL: $*"
  fail=1
}

check_projection_symlinks() {
  dir=$1
  [ -d "$dir" ] || { fail_msg "$dir is missing"; return; }

  non_links=$(find "$dir" -mindepth 1 -maxdepth 1 ! -type l -print)
  if [ -n "$non_links" ]; then
    fail_msg "$dir contains non-symlink projection entries:"
    printf '%s\n' "$non_links"
  fi
}

check_projection_entry_allowlist() {
  dir=$1
  shift
  allowed=" $* "
  [ -d "$dir" ] || return

  entries=$(find "$dir" -mindepth 1 -maxdepth 1 -exec basename {} \; 2>/dev/null || true)
  for entry in $entries; do
    case "$allowed" in
      *" $entry "*) ;;
      *) fail_msg "$dir/$entry is not an approved projection entry" ;;
    esac
  done
}

check_codex_forbidden_entries() {
  for p in CLAUDE.md settings.json keybindings.json commands statusline.sh track-toggle.sh skills agents agent-modes hooks; do
    if [ -e "codex_setting/$p" ] || [ -L "codex_setting/$p" ]; then
      fail_msg "codex_setting/$p exists; Codex projection must not expose Claude-native surfaces"
    fi
  done
}

check_codex_native_surface_debt() {
  for p in adapters/codex/.codex-plugin codex_setting/plugins codex_setting/.codex-plugin adapters/codex/prompts codex_setting/prompts; do
    if [ -e "$p" ] || [ -L "$p" ]; then
      fail_msg "$p exists; Codex must not expose unsupported native surfaces outside documented adapter-owned projections"
    fi
  done

  if grep -Fq 'Codex has no adapter-owned native agent projection yet' adapters/codex/README.md; then
    fail_msg "adapters/codex/README.md must not describe Codex-native agents as future-only"
  fi
}

check_opencode_forbidden_entries() {
  for p in CLAUDE.md settings.json keybindings.json commands statusline.sh track-toggle.sh skills agents agent-modes hooks; do
    if [ -e "opencode_setting/$p" ] || [ -L "opencode_setting/$p" ]; then
      fail_msg "opencode_setting/$p exists; OpenCode projection must not expose Claude-native surfaces"
    fi
  done
}

check_required_projection_entries() {
  for p in AGENTS.md README.md core capabilities roles bin tools utilities codex-skills codex-plugin-marketplace codex-hooks codex-agents; do
    if [ ! -L "codex_setting/$p" ]; then
      fail_msg "codex_setting/$p must be a symlink projection entry"
    fi
  done
}

check_codex_projection_targets() {
  check_link_target codex_setting/AGENTS.md ../adapters/codex/AGENTS.md
  check_link_target codex_setting/README.md ../adapters/codex/README.md
  check_link_target codex_setting/core ../core
  check_link_target codex_setting/capabilities ../capabilities
  check_link_target codex_setting/roles ../roles
  check_link_target codex_setting/bin ../adapters/codex/bin
  check_link_target codex_setting/tools ../adapters/codex/tools
  check_link_target codex_setting/utilities ../adapters/codex/utilities
  check_link_target codex_setting/codex-skills ../adapters/codex/skills
  check_link_target codex_setting/codex-plugin-marketplace ../adapters/codex
  check_link_target codex_setting/codex-hooks ../adapters/codex/hooks
  check_link_target codex_setting/codex-agents ../adapters/codex/agents
}

check_opencode_required_projection_entries() {
  for p in AGENTS.md README.md core capabilities roles bin tools utilities opencode-skills opencode-agents opencode-commands opencode-plugins; do
    if [ ! -L "opencode_setting/$p" ]; then
      fail_msg "opencode_setting/$p must be a symlink projection entry"
    fi
  done
}

check_opencode_projection_targets() {
  check_link_target opencode_setting/AGENTS.md ../adapters/opencode/AGENTS.md
  check_link_target opencode_setting/README.md ../adapters/opencode/README.md
  check_link_target opencode_setting/core ../core
  check_link_target opencode_setting/capabilities ../capabilities
  check_link_target opencode_setting/roles ../roles
  check_link_target opencode_setting/bin ../adapters/opencode/bin
  check_link_target opencode_setting/tools ../adapters/opencode/tools
  check_link_target opencode_setting/utilities ../adapters/opencode/utilities
  check_link_target opencode_setting/opencode-skills ../adapters/opencode/skills
  check_link_target opencode_setting/opencode-agents ../adapters/opencode/agents
  check_link_target opencode_setting/opencode-commands ../adapters/opencode/commands
  check_link_target opencode_setting/opencode-plugins ../adapters/opencode/plugins
}

check_claude_projection_targets() {
  check_link_target claude_setting/CLAUDE.md ../adapters/claude/CLAUDE.md
  check_link_target claude_setting/README.md ../README.md
  check_link_target claude_setting/core ../core
  check_link_target claude_setting/settings.json ../adapters/claude/settings.json
  check_link_target claude_setting/keybindings.json ../adapters/claude/keybindings.json
  check_link_target claude_setting/commands ../adapters/claude/commands
  check_link_target claude_setting/skills ../adapters/claude/skills
  check_link_target claude_setting/agents ../adapters/claude/agents
  check_link_target claude_setting/agent-modes ../adapters/claude/agent-modes
  check_link_target claude_setting/hooks ../adapters/claude/hooks
  check_link_target claude_setting/utilities ../adapters/claude/utilities
  check_link_target claude_setting/tools ../adapters/claude/tools
  check_link_target claude_setting/scaffolds ../adapters/claude/scaffolds
  check_link_target claude_setting/loops ../adapters/claude/loops
  check_link_target claude_setting/manifest.json ../manifest.json
  check_link_target claude_setting/statusline.sh ../adapters/claude/statusline.sh
  check_link_target claude_setting/track-toggle.sh ../adapters/claude/track-toggle.sh
  check_link_target claude_setting/bin ../adapters/claude/bin
}

check_claude_adapter_concrete_surfaces() {
  links=$(find adapters/claude -type l -print 2>/dev/null || true)
  if [ -n "$links" ]; then
    fail_msg "adapters/claude must contain adapter-owned concrete files, not symlink passthrough entries:"
    printf '%s\n' "$links"
  fi
}

check_non_claude_adapter_symlink_boundaries() {
  for adapter in codex opencode; do
    links=$(find "adapters/$adapter" -type l -print 2>/dev/null || true)
    [ -n "$links" ] || continue
    for link in $links; do
      target=$(readlink "$link")
      case "$target" in
        *adapters/claude*|*claude_setting*|*"/skills"*|*"/commands"*|*"/hooks"*)
          fail_msg "$link points to $target; $adapter adapter symlinks must not target Claude-native or compat surfaces"
          ;;
      esac
    done
  done
}

check_link_target() {
  path=$1
  expected=$2
  if [ ! -L "$path" ]; then
    fail_msg "$path must be a symlink to $expected"
    return
  fi
  target=$(readlink "$path")
  if [ "$target" != "$expected" ]; then
    fail_msg "$path points to $target; expected $expected"
  fi
}

check_install_layout_codex_projection() {
  [ -f INSTALL_LAYOUT.md ] || { fail_msg "INSTALL_LAYOUT.md is missing"; return; }

  for p in AGENTS.md README.md core capabilities roles bin tools utilities codex-skills codex-plugin-marketplace codex-hooks codex-agents; do
    if ! grep -Fq "\$AGENT_HOME/codex_setting/$p" INSTALL_LAYOUT.md; then
      fail_msg "INSTALL_LAYOUT.md must include Codex projection install step for codex_setting/$p"
    fi
  done

  for p in settings.json commands skills agents statusline.sh hooks; do
    if ! grep -Fq "$p" INSTALL_LAYOUT.md; then
      fail_msg "INSTALL_LAYOUT.md must explicitly keep Claude-native $p out of Codex runtime projection"
    fi
  done
}

check_install_layout_opencode_projection() {
  [ -f INSTALL_LAYOUT.md ] || { fail_msg "INSTALL_LAYOUT.md is missing"; return; }

  for p in AGENTS.md README.md core capabilities roles bin tools utilities opencode-skills opencode-agents opencode-commands opencode-plugins; do
    if ! grep -Fq "\$AGENT_HOME/opencode_setting/$p" INSTALL_LAYOUT.md; then
      fail_msg "INSTALL_LAYOUT.md must include OpenCode projection install step for opencode_setting/$p"
    fi
  done

  if ! grep -Fq 'OPENCODE_CONFIG_CONTENT=' INSTALL_LAYOUT.md \
    || ! grep -Fq 'opencode_setting/opencode-skills' INSTALL_LAYOUT.md \
    || ! grep -Fq 'OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1' INSTALL_LAYOUT.md; then
    fail_msg "INSTALL_LAYOUT.md must validate OpenCode skills through adapter-owned paths with Claude compat autoload disabled"
  fi
  if ! grep -Fq 'opencode_setting/opencode-plugins/agent-harness-guards.js' INSTALL_LAYOUT.md \
    || ! grep -Fq 'opencode debug config >/tmp/opencode-plugin.json' INSTALL_LAYOUT.md \
    || ! grep -Fq "rg 'agent-harness-guards.js' /tmp/opencode-plugin.json" INSTALL_LAYOUT.md; then
    fail_msg "INSTALL_LAYOUT.md must validate the OpenCode native plugin projection"
  fi
}

check_codex_bin_wrappers() {
  if [ ! -L codex_setting/bin ]; then
    fail_msg "codex_setting/bin must project adapters/codex/bin"
    return
  fi

  target=$(readlink codex_setting/bin)
  if [ "$target" != "../adapters/codex/bin" ]; then
    fail_msg "codex_setting/bin points to $target; expected ../adapters/codex/bin"
  fi

  for p in preflight.sh role-map.sh capability-map.sh mode-map.sh distill-worker.sh sync-native-plugin.py sync-native-agents.py; do
    if [ ! -x "adapters/codex/bin/$p" ]; then
      fail_msg "adapters/codex/bin/$p is missing or not executable"
    fi
  done

  if ! grep -Fq 'utilities/workflow-toggle.sh' adapters/codex/bin/preflight.sh; then
    fail_msg "adapters/codex/bin/preflight.sh must realize workflow toggle through utilities/workflow-toggle.sh"
  fi

  if ! grep -Fq -- '--event start' adapters/codex/bin/preflight.sh; then
    fail_msg "adapters/codex/bin/preflight.sh must expose workflow start cleanup"
  fi

  if ! grep -Fq -- '--toggle-label "preflight.sh track"' adapters/codex/bin/preflight.sh; then
    fail_msg "adapters/codex/bin/preflight.sh must adapt workflow signal toggle text"
  fi

  if ! grep -Fq 'ARTIFACT_GUARD_TOGGLE_LABEL="preflight.sh track"' adapters/codex/bin/preflight.sh; then
    fail_msg "adapters/codex/bin/preflight.sh must adapt artifact guard toggle text"
  fi

  if ! grep -Fq 'preflight.sh start' adapters/codex/AGENTS.md; then
    fail_msg "adapters/codex/AGENTS.md must document the Codex workflow start cleanup wrapper"
  fi

  if ! grep -Fq 'preflight.sh track' adapters/codex/AGENTS.md; then
    fail_msg "adapters/codex/AGENTS.md must document the Codex workflow toggle wrapper"
  fi

  if ! grep -Fq 'codex_setting/codex-plugin-marketplace' adapters/codex/AGENTS.md; then
    fail_msg "adapters/codex/AGENTS.md must document the Codex native plugin projection"
  fi

  if ! grep -Fq 'codex_setting/codex-hooks' adapters/codex/AGENTS.md; then
    fail_msg "adapters/codex/AGENTS.md must document the Codex native hook projection"
  fi

  if ! grep -Fq 'named `tool_contract`' adapters/codex/AGENTS.md; then
    fail_msg "adapters/codex/AGENTS.md must document named mode tool contracts"
  fi

  if ! grep -Fq 'visual-harness)' adapters/codex/bin/preflight.sh; then
    fail_msg "adapters/codex/bin/preflight.sh must expose the Codex visual harness tool-contract"
  fi
  if grep -Eq 'Claude Design MCP|Claude visual harness' adapters/codex/bin/preflight.sh adapters/codex/bin/capability-map.sh; then
    fail_msg "Codex runtime-facing visual harness output must use legacy/adapter-specific wording, not Claude implementation names"
  fi

  if ! grep -Fq 'preflight.sh visual-harness' adapters/codex/AGENTS.md; then
    fail_msg "adapters/codex/AGENTS.md must document the Codex visual harness tool-contract"
  fi
}

check_codex_utility_projection() {
  if [ ! -L codex_setting/utilities ]; then
    fail_msg "codex_setting/utilities must project adapters/codex/utilities"
    return
  fi

  target=$(readlink codex_setting/utilities)
  if [ "$target" != "../adapters/codex/utilities" ]; then
    fail_msg "codex_setting/utilities points to $target; expected ../adapters/codex/utilities"
  fi

  if [ ! -x "adapters/codex/utilities/agent-home.sh" ]; then
    fail_msg "adapters/codex/utilities/agent-home.sh must be an executable Codex-owned utility"
  elif [ -L "adapters/codex/utilities/agent-home.sh" ]; then
    fail_msg "adapters/codex/utilities/agent-home.sh must be concrete, not a symlink to the shared Claude-compatible fallback"
  elif grep -q '\.claude' "adapters/codex/utilities/agent-home.sh"; then
    fail_msg "adapters/codex/utilities/agent-home.sh must not fall back to Claude runtime home"
  fi

  for p in artifact-root.sh agent-worklog-state.sh workflow-guard-hook.sh workflow-toggle.sh; do
    if [ ! -L "adapters/codex/utilities/$p" ]; then
      fail_msg "adapters/codex/utilities/$p must be a selective portable utility projection"
      continue
    fi
    link=$(readlink "adapters/codex/utilities/$p")
    if [ "$link" != "../../../utilities/$p" ]; then
      fail_msg "adapters/codex/utilities/$p points to $link; expected ../../../utilities/$p"
    fi
  done

  extra=$(find adapters/codex/utilities -mindepth 1 -maxdepth 1 ! \( -name agent-home.sh -o -name artifact-root.sh -o -name agent-worklog-state.sh -o -name workflow-guard-hook.sh -o -name workflow-toggle.sh \) -print 2>/dev/null || true)
  if [ -n "$extra" ]; then
    fail_msg "adapters/codex/utilities contains unapproved entries:"
    printf '%s\n' "$extra"
  fi

  for p in dispatch-liveness.sh extract_web_figures.py; do
    if [ -e "adapters/codex/utilities/$p" ] || [ -L "adapters/codex/utilities/$p" ]; then
      fail_msg "adapters/codex/utilities/$p must not be projected until Codex support is documented"
    fi
  done
}

check_codex_tool_projection() {
  if [ ! -L codex_setting/tools ]; then
    fail_msg "codex_setting/tools must project adapters/codex/tools"
    return
  fi

  target=$(readlink codex_setting/tools)
  if [ "$target" != "../adapters/codex/tools" ]; then
    fail_msg "codex_setting/tools points to $target; expected ../adapters/codex/tools"
  fi

  for p in mem.py recall.sh; do
    if [ ! -x "adapters/codex/tools/memory/$p" ]; then
      fail_msg "adapters/codex/tools/memory/$p must be an executable Codex-owned memory launcher"
    elif [ -L "adapters/codex/tools/memory/$p" ]; then
      fail_msg "adapters/codex/tools/memory/$p must be concrete, not a symlink to the shared Claude-compatible fallback"
    elif grep -q '\.claude\|CLAUDE_HOME' "adapters/codex/tools/memory/$p"; then
      fail_msg "adapters/codex/tools/memory/$p must not fall back to Claude runtime home"
    fi
  done

  for p in apply-distill-actions.py; do
    if [ ! -L "adapters/codex/tools/memory/$p" ]; then
      fail_msg "adapters/codex/tools/memory/$p must be a selective portable memory tool projection"
      continue
    fi
    link=$(readlink "adapters/codex/tools/memory/$p")
    if [ "$link" != "../../../../tools/memory/$p" ]; then
      fail_msg "adapters/codex/tools/memory/$p points to $link; expected ../../../../tools/memory/$p"
    fi
  done

  extra=$(find adapters/codex/tools -mindepth 1 ! \( -path adapters/codex/tools/memory -o -path adapters/codex/tools/memory/mem.py -o -path adapters/codex/tools/memory/apply-distill-actions.py -o -path adapters/codex/tools/memory/recall.sh \) -print 2>/dev/null || true)
  if [ -n "$extra" ]; then
    fail_msg "adapters/codex/tools contains unapproved entries:"
    printf '%s\n' "$extra"
  fi

  for p in build-manifest.py check-adaptation-boundary.sh design-mcp web-bundle; do
    if [ -e "adapters/codex/tools/$p" ] || [ -L "adapters/codex/tools/$p" ]; then
      fail_msg "adapters/codex/tools/$p must not be projected until Codex support is documented"
    fi
  done
}

check_codex_native_skill_projection() {
  if [ ! -x adapters/codex/bin/sync-native-skills.py ]; then
    fail_msg "adapters/codex/bin/sync-native-skills.py must be executable"
    return
  fi

  if ! adapters/codex/bin/sync-native-skills.py --check >/tmp/codex-sync-skills.out 2>/tmp/codex-sync-skills.err; then
    fail_msg "Codex native skill projections are stale; run adapters/codex/bin/sync-native-skills.py"
    cat /tmp/codex-sync-skills.err
  fi

  for f in capabilities/*.md; do
    [ -f "$f" ] || continue
    [ "$(basename "$f")" = "README.md" ] && continue
    slug=$(basename "$f" .md)
    skill="adapters/codex/skills/$slug/SKILL.md"
    if [ ! -f "$skill" ]; then
      fail_msg "$skill is missing"
      continue
    fi
    if ! grep -Fq "capabilities/$slug.md" "$skill"; then
      fail_msg "$skill must reference capabilities/$slug.md as portable source"
    fi
    if ! grep -Fq "adapters/codex/bin/preflight.sh capability-info $slug" "$skill"; then
      fail_msg "$skill must reference the Codex capability-info wrapper"
    fi
    if ! grep -Fq "not a legacy compatibility Skill copy" "$skill"; then
      fail_msg "$skill must state that it is not a legacy compatibility Skill copy"
    fi
    if ! grep -Fq 'named `tool_contract`' "$skill"; then
      fail_msg "$skill must instruct Codex to report named tool contracts"
    fi
    if grep -Fq "metadata:" "$skill"; then
      fail_msg "$skill must use Codex Skill frontmatter only, without adapter metadata"
    fi
  done
  for skill in adapters/codex/skills/*/SKILL.md; do
    [ -f "$skill" ] || continue
    slug=$(basename "$(dirname "$skill")")
    if [ ! -f "capabilities/$slug.md" ]; then
      fail_msg "$skill has no matching portable capability source"
    fi
  done

  bad=$(rg -n 'adapters/claude|claude_setting|claude_realization' adapters/codex/skills adapters/codex/plugins/agent-harness-codex/skills adapters/codex/bin/capability-map.sh 2>/dev/null || true)
  if [ -n "$bad" ]; then
    fail_msg "Codex native capability surfaces must not expose Claude adapter paths:"
    printf '%s\n' "$bad"
  fi
}

check_codex_native_plugin_projection() {
  plugin_root="adapters/codex/plugins/agent-harness-codex"
  plugin_manifest="$plugin_root/.codex-plugin/plugin.json"
  marketplace="adapters/codex/.agents/plugins/marketplace.json"

  if [ ! -x adapters/codex/bin/sync-native-plugin.py ]; then
    fail_msg "adapters/codex/bin/sync-native-plugin.py must be executable"
    return
  fi

  if ! adapters/codex/bin/sync-native-plugin.py --check >/tmp/codex-sync-plugin.out 2>/tmp/codex-sync-plugin.err; then
    fail_msg "Codex native plugin projection is stale; run adapters/codex/bin/sync-native-plugin.py"
    cat /tmp/codex-sync-plugin.err
  fi

  plugin_entries=$(find adapters/codex/plugins -mindepth 1 -maxdepth 1 -exec basename {} \; 2>/dev/null || true)
  for entry in $plugin_entries; do
    if [ "$entry" != "agent-harness-codex" ]; then
      fail_msg "adapters/codex/plugins/$entry is not an approved Codex plugin projection"
    fi
  done
  marketplace_entries=$(find adapters/codex/.agents/plugins -mindepth 1 -maxdepth 1 -exec basename {} \; 2>/dev/null || true)
  for entry in $marketplace_entries; do
    if [ "$entry" != "marketplace.json" ]; then
      fail_msg "adapters/codex/.agents/plugins/$entry is not an approved Codex marketplace projection"
    fi
  done

  if [ ! -d "$plugin_root" ] || [ -L "$plugin_root" ]; then
    fail_msg "$plugin_root must be a concrete adapter-owned Codex plugin directory"
  fi
  plugin_links=$(find "$plugin_root" -type l -print 2>/dev/null || true)
  if [ -n "$plugin_links" ]; then
    fail_msg "$plugin_root must not contain symlinked plugin files:"
    printf '%s\n' "$plugin_links"
  fi

  if [ ! -f "$plugin_manifest" ]; then
    fail_msg "Codex native plugin manifest is missing"
  fi
  if [ ! -f "$marketplace" ]; then
    fail_msg "Codex native plugin marketplace is missing"
  fi
  if [ ! -f "$plugin_root/skills/autopilot-code/SKILL.md" ]; then
    fail_msg "Codex native plugin must include generated capability skills"
  fi
  for skill in "$plugin_root"/skills/*/SKILL.md; do
    [ -f "$skill" ] || continue
    slug=$(basename "$(dirname "$skill")")
    if [ ! -f "capabilities/$slug.md" ]; then
      fail_msg "$skill has no matching portable capability source"
    fi
  done
  if ! grep -Fq '"name": "agent-harness-codex"' "$plugin_manifest" \
    || ! grep -Fq '"skills": "./skills/"' "$plugin_manifest"; then
    fail_msg "$plugin_manifest must define the agent-harness-codex plugin and plugin-local skills path"
  fi
  if grep -Eq 'Claude-native|Claude Code|adapters/claude|claude_setting' "$plugin_manifest"; then
    fail_msg "$plugin_manifest must not expose Claude implementation names in Codex runtime-facing metadata"
  fi
  if ! grep -Fq '"name": "agent-harness"' "$marketplace" \
    || ! grep -Fq '"path": "./plugins/agent-harness-codex"' "$marketplace"; then
    fail_msg "$marketplace must expose agent-harness-codex through the repo-local plugin path"
  fi

  if ! grep -Fq "Custom prompts are deprecated" adapters/codex/README.md; then
    fail_msg "adapters/codex/README.md must document why command-like entries use skills/plugins instead of custom prompts"
  fi
}

check_codex_native_agent_projection() {
  if [ ! -x adapters/codex/bin/sync-native-agents.py ]; then
    fail_msg "adapters/codex/bin/sync-native-agents.py must be executable"
    return
  fi

  if ! adapters/codex/bin/sync-native-agents.py --check >/tmp/codex-sync-agents.out 2>/tmp/codex-sync-agents.err; then
    fail_msg "Codex native agent projections are stale; run adapters/codex/bin/sync-native-agents.py"
    cat /tmp/codex-sync-agents.err
  fi

  for profile in plan-team dev-team qa-team research-team material-team design-team editorial-team external-adversary; do
    agent="adapters/codex/agents/$profile.toml"
    if [ ! -f "$agent" ]; then
      fail_msg "$agent is missing"
      continue
    fi
    if [ -L "$agent" ]; then
      fail_msg "$agent must be a concrete adapter-owned Codex custom agent"
    fi
    if ! python3 - "$agent" >/tmp/codex-agent-toml.out 2>/tmp/codex-agent-toml.err <<'PY'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
for key in ("name", "description"):
    if not re.search(rf'^{key} = "[^"]+"$', text, re.MULTILINE):
        raise SystemExit(f"missing required Codex custom agent field: {key}")
if not re.search(r'^developer_instructions = """\n.+\n"""$', text, re.MULTILINE | re.DOTALL):
    raise SystemExit("missing required Codex custom agent field: developer_instructions")
PY
    then
      fail_msg "$agent must be valid Codex custom agent TOML"
      cat /tmp/codex-agent-toml.err
    fi
    if ! grep -Fq "roles/README.md" "$agent"; then
      fail_msg "$agent must reference roles/README.md as portable source"
    fi
    if ! grep -Fq "adapters/codex/bin/preflight.sh role" "$agent"; then
      fail_msg "$agent must reference the Codex role mapper"
    fi
    mapped_role=$(sed -n 's/^Codex role-map input: `\(.*\)`$/\1/p' "$agent" | head -n 1)
    if [ -z "$mapped_role" ] || ! adapters/codex/bin/role-map.sh "$mapped_role" >/tmp/codex-agent-role.out 2>/tmp/codex-agent-role.err; then
      fail_msg "$agent must include a Codex role-map input that resolves through adapters/codex/bin/role-map.sh"
      cat /tmp/codex-agent-role.err
    fi
    if ! grep -Fq "not a legacy compatibility Agent copy" "$agent"; then
      fail_msg "$agent must state that it is not a legacy compatibility Agent copy"
    fi
  done
  for agent in adapters/codex/agents/*.toml; do
    [ -f "$agent" ] || continue
    profile=$(basename "$agent" .toml)
    case " plan-team dev-team qa-team research-team material-team design-team editorial-team external-adversary " in
      *" $profile "*) ;;
      *) fail_msg "$agent is not an approved Codex native agent projection" ;;
    esac
  done

  bad=$(rg -n 'adapters/claude|claude_setting|adapters/opencode|opencode_setting' adapters/codex/agents 2>/dev/null || true)
  if [ -n "$bad" ]; then
    fail_msg "Codex native agent surfaces must not expose non-Codex adapter paths:"
    printf '%s\n' "$bad"
  fi
}

check_codex_native_hook_projection() {
  hook_dir="adapters/codex/hooks"
  hook_json="$hook_dir/hooks.json"
  pre_bridge="$hook_dir/pretooluse-write-guard.py"
  post_bridge="$hook_dir/posttooluse-design-check.py"

  if [ ! -f "$hook_json" ]; then
    fail_msg "$hook_json is missing"
    return
  fi
  for bridge in "$pre_bridge" "$post_bridge"; do
    if [ ! -x "$bridge" ]; then
      fail_msg "$bridge must be executable"
    fi
    if [ -L "$bridge" ]; then
      fail_msg "$bridge must be a concrete adapter-owned Codex hook bridge"
    fi
  done
  if ! python3 -m json.tool "$hook_json" >/tmp/codex-hooks-json.out 2>/tmp/codex-hooks-json.err; then
    fail_msg "$hook_json must be valid JSON"
    cat /tmp/codex-hooks-json.err
  fi
  if ! grep -Fq '"PreToolUse"' "$hook_json" || ! grep -Fq 'pretooluse-write-guard.py' "$hook_json"; then
    fail_msg "$hook_json must register the Codex PreToolUse write guard"
  fi
  if ! grep -Fq '"PostToolUse"' "$hook_json" || ! grep -Fq 'posttooluse-design-check.py' "$hook_json"; then
    fail_msg "$hook_json must register the Codex PostToolUse design check"
  fi
  for bridge in "$pre_bridge" "$post_bridge"; do
    if ! grep -Fq 'adapters" / "codex" / "bin" / "preflight.sh' "$bridge"; then
      fail_msg "$bridge must call the Codex preflight wrapper"
    fi
  done
  if ! grep -Fq '"design"' "$post_bridge"; then
    fail_msg "$post_bridge must call the Codex design preflight"
  fi
  if ! grep -Fq 'PreToolUse' adapters/codex/README.md \
    || ! grep -Fq 'PostToolUse' adapters/codex/README.md \
    || ! grep -Fq 'preflight.sh design' adapters/codex/README.md; then
    fail_msg "adapters/codex/README.md must document the Codex native hook bridges"
  fi
  if grep -Eq 'adapters/claude|claude_setting|settings\.json|statusline\.sh' "$hook_json" "$pre_bridge" "$post_bridge"; then
    fail_msg "Codex hook projection must not reference Claude-native surfaces"
  fi
}

check_portable_agent_home_resolution() {
  command -v rg >/dev/null 2>&1 || return 0

  bad=$(rg -n 'AGENT_HOME=.*CLAUDE_HOME.*HOME/\.claude|os\.environ\.get\("AGENT_HOME"\).*os\.environ\.get\("CLAUDE_HOME"\).*HOME / "\.claude"' \
    tools/memory utilities/dispatch-liveness.sh \
    --glob '!*.test.sh' 2>/dev/null || true)
  if [ -n "$bad" ]; then
    fail_msg "portable tools must use neutral agent-home resolution before legacy Claude fallback:"
    printf '%s\n' "$bad"
  fi

  for p in tools/memory/mem.py adapters/claude/tools/memory/mem.py; do
    if ! grep -Fq 'HOME / "agent_setting"' "$p"; then
      fail_msg "$p must prefer neutral ~/agent_setting before legacy runtime home"
    fi
  done
}

check_claude_bin_wrappers() {
  if [ ! -L claude_setting/bin ]; then
    fail_msg "claude_setting/bin must project adapters/claude/bin"
    return
  fi

  target=$(readlink claude_setting/bin)
  if [ "$target" != "../adapters/claude/bin" ]; then
    fail_msg "claude_setting/bin points to $target; expected ../adapters/claude/bin"
  fi

  if [ ! -x adapters/claude/bin/mem-distill-worker.sh ]; then
    fail_msg "adapters/claude/bin/mem-distill-worker.sh is missing or not executable"
  fi
}

check_opencode_bin_wrappers() {
  if [ ! -L opencode_setting/bin ]; then
    fail_msg "opencode_setting/bin must project adapters/opencode/bin"
    return
  fi

  target=$(readlink opencode_setting/bin)
  if [ "$target" != "../adapters/opencode/bin" ]; then
    fail_msg "opencode_setting/bin points to $target; expected ../adapters/opencode/bin"
  fi

  for p in preflight.sh role-map.sh capability-map.sh mode-map.sh distill-worker.sh sync-native-agents.py sync-native-commands.py; do
    if [ ! -x "adapters/opencode/bin/$p" ]; then
      fail_msg "adapters/opencode/bin/$p is missing or not executable"
    fi
  done

  if ! grep -Fq 'utilities/workflow-toggle.sh' adapters/opencode/bin/preflight.sh; then
    fail_msg "adapters/opencode/bin/preflight.sh must realize workflow toggle through utilities/workflow-toggle.sh"
  fi

  if ! grep -Fq -- '--event start' adapters/opencode/bin/preflight.sh; then
    fail_msg "adapters/opencode/bin/preflight.sh must expose workflow start cleanup"
  fi

  if ! grep -Fq -- '--toggle-label "preflight.sh track"' adapters/opencode/bin/preflight.sh; then
    fail_msg "adapters/opencode/bin/preflight.sh must adapt workflow signal toggle text"
  fi

  if ! grep -Fq 'ARTIFACT_GUARD_TOGGLE_LABEL="preflight.sh track"' adapters/opencode/bin/preflight.sh; then
    fail_msg "adapters/opencode/bin/preflight.sh must adapt artifact guard toggle text"
  fi

  if ! grep -Fq 'preflight.sh start' adapters/opencode/AGENTS.md; then
    fail_msg "adapters/opencode/AGENTS.md must document the OpenCode workflow start cleanup wrapper"
  fi

  if ! grep -Fq 'preflight.sh track' adapters/opencode/AGENTS.md; then
    fail_msg "adapters/opencode/AGENTS.md must document the OpenCode workflow toggle wrapper"
  fi

  if ! grep -Fq 'opencode_setting/opencode-plugins' adapters/opencode/AGENTS.md; then
    fail_msg "adapters/opencode/AGENTS.md must document the OpenCode native plugin projection"
  fi

  if ! grep -Fq 'opencode_setting/opencode-agents' adapters/opencode/AGENTS.md \
    || ! grep -Fq 'opencode_setting/opencode-commands' adapters/opencode/AGENTS.md \
    || ! grep -Fq 'opencode_setting/opencode-skills' adapters/opencode/AGENTS.md; then
    fail_msg "adapters/opencode/AGENTS.md must document OpenCode native surface projections"
  fi

  if ! grep -Fq 'named `tool_contract`' adapters/opencode/AGENTS.md; then
    fail_msg "adapters/opencode/AGENTS.md must document named mode tool contracts"
  fi

  if ! grep -Fq 'visual-harness)' adapters/opencode/bin/preflight.sh; then
    fail_msg "adapters/opencode/bin/preflight.sh must expose the OpenCode visual harness tool-contract"
  fi
  if grep -Eq 'Claude Design MCP|Claude visual harness' adapters/opencode/bin/preflight.sh adapters/opencode/bin/capability-map.sh; then
    fail_msg "OpenCode runtime-facing visual harness output must use legacy/adapter-specific wording, not Claude implementation names"
  fi

  if ! grep -Fq 'preflight.sh visual-harness' adapters/opencode/AGENTS.md; then
    fail_msg "adapters/opencode/AGENTS.md must document the OpenCode visual harness tool-contract"
  fi
}

check_opencode_utility_projection() {
  if [ ! -L opencode_setting/utilities ]; then
    fail_msg "opencode_setting/utilities must project adapters/opencode/utilities"
    return
  fi

  target=$(readlink opencode_setting/utilities)
  if [ "$target" != "../adapters/opencode/utilities" ]; then
    fail_msg "opencode_setting/utilities points to $target; expected ../adapters/opencode/utilities"
  fi

  if [ ! -x "adapters/opencode/utilities/agent-home.sh" ]; then
    fail_msg "adapters/opencode/utilities/agent-home.sh must be an executable OpenCode-owned utility"
  elif [ -L "adapters/opencode/utilities/agent-home.sh" ]; then
    fail_msg "adapters/opencode/utilities/agent-home.sh must be concrete, not a symlink to the shared Claude-compatible fallback"
  elif grep -q '\.claude' "adapters/opencode/utilities/agent-home.sh"; then
    fail_msg "adapters/opencode/utilities/agent-home.sh must not fall back to Claude runtime home"
  fi

  for p in artifact-root.sh agent-worklog-state.sh workflow-guard-hook.sh workflow-toggle.sh; do
    if [ ! -L "adapters/opencode/utilities/$p" ]; then
      fail_msg "adapters/opencode/utilities/$p must be a selective portable utility projection"
      continue
    fi
    link=$(readlink "adapters/opencode/utilities/$p")
    if [ "$link" != "../../../utilities/$p" ]; then
      fail_msg "adapters/opencode/utilities/$p points to $link; expected ../../../utilities/$p"
    fi
  done

  extra=$(find adapters/opencode/utilities -mindepth 1 -maxdepth 1 ! \( -name agent-home.sh -o -name artifact-root.sh -o -name agent-worklog-state.sh -o -name workflow-guard-hook.sh -o -name workflow-toggle.sh \) -print 2>/dev/null || true)
  if [ -n "$extra" ]; then
    fail_msg "adapters/opencode/utilities contains unapproved entries:"
    printf '%s\n' "$extra"
  fi

  for p in dispatch-liveness.sh extract_web_figures.py; do
    if [ -e "adapters/opencode/utilities/$p" ] || [ -L "adapters/opencode/utilities/$p" ]; then
      fail_msg "adapters/opencode/utilities/$p must not be projected until OpenCode support is documented"
    fi
  done
}

check_opencode_tool_projection() {
  if [ ! -L opencode_setting/tools ]; then
    fail_msg "opencode_setting/tools must project adapters/opencode/tools"
    return
  fi

  target=$(readlink opencode_setting/tools)
  if [ "$target" != "../adapters/opencode/tools" ]; then
    fail_msg "opencode_setting/tools points to $target; expected ../adapters/opencode/tools"
  fi

  for p in mem.py recall.sh; do
    if [ ! -x "adapters/opencode/tools/memory/$p" ]; then
      fail_msg "adapters/opencode/tools/memory/$p must be an executable OpenCode-owned memory launcher"
    elif [ -L "adapters/opencode/tools/memory/$p" ]; then
      fail_msg "adapters/opencode/tools/memory/$p must be concrete, not a symlink to the shared Claude-compatible fallback"
    elif grep -q '\.claude\|CLAUDE_HOME' "adapters/opencode/tools/memory/$p"; then
      fail_msg "adapters/opencode/tools/memory/$p must not fall back to Claude runtime home"
    fi
  done

  for p in apply-distill-actions.py; do
    if [ ! -L "adapters/opencode/tools/memory/$p" ]; then
      fail_msg "adapters/opencode/tools/memory/$p must be a selective portable memory tool projection"
      continue
    fi
    link=$(readlink "adapters/opencode/tools/memory/$p")
    if [ "$link" != "../../../../tools/memory/$p" ]; then
      fail_msg "adapters/opencode/tools/memory/$p points to $link; expected ../../../../tools/memory/$p"
    fi
  done

  extra=$(find adapters/opencode/tools -mindepth 1 ! \( -path adapters/opencode/tools/memory -o -path adapters/opencode/tools/memory/mem.py -o -path adapters/opencode/tools/memory/apply-distill-actions.py -o -path adapters/opencode/tools/memory/recall.sh \) -print 2>/dev/null || true)
  if [ -n "$extra" ]; then
    fail_msg "adapters/opencode/tools contains unapproved entries:"
    printf '%s\n' "$extra"
  fi

  for p in build-manifest.py check-adaptation-boundary.sh design-mcp web-bundle; do
    if [ -e "adapters/opencode/tools/$p" ] || [ -L "adapters/opencode/tools/$p" ]; then
      fail_msg "adapters/opencode/tools/$p must not be projected until OpenCode support is documented"
    fi
  done
}

check_opencode_native_skill_projection() {
  if [ ! -x adapters/opencode/bin/sync-native-skills.py ]; then
    fail_msg "adapters/opencode/bin/sync-native-skills.py must be executable"
    return
  fi

  if ! adapters/opencode/bin/sync-native-skills.py --check >/tmp/opencode-sync-skills.out 2>/tmp/opencode-sync-skills.err; then
    fail_msg "OpenCode native skill projections are stale; run adapters/opencode/bin/sync-native-skills.py"
    cat /tmp/opencode-sync-skills.err
  fi

  for f in capabilities/*.md; do
    [ -f "$f" ] || continue
    [ "$(basename "$f")" = "README.md" ] && continue
    slug=$(basename "$f" .md)
    skill="adapters/opencode/skills/$slug/SKILL.md"
    if [ ! -f "$skill" ]; then
      fail_msg "$skill is missing"
      continue
    fi
    if ! grep -Fq "capabilities/$slug.md" "$skill"; then
      fail_msg "$skill must reference capabilities/$slug.md as portable source"
    fi
    if ! grep -Fq "adapters/opencode/bin/preflight.sh capability-info $slug" "$skill"; then
      fail_msg "$skill must reference the OpenCode capability-info wrapper"
    fi
    if ! grep -Fq "not a legacy compatibility Skill copy" "$skill"; then
      fail_msg "$skill must state that it is not a legacy compatibility Skill copy"
    fi
    if ! grep -Fq 'named `tool_contract`' "$skill"; then
      fail_msg "$skill must instruct OpenCode to report named tool contracts"
    fi
  done
  for skill in adapters/opencode/skills/*/SKILL.md; do
    [ -f "$skill" ] || continue
    slug=$(basename "$(dirname "$skill")")
    if [ ! -f "capabilities/$slug.md" ]; then
      fail_msg "$skill has no matching portable capability source"
    fi
  done

  bad=$(rg -n 'adapters/claude|claude_setting|claude_realization' adapters/opencode/skills adapters/opencode/bin/capability-map.sh 2>/dev/null || true)
  if [ -n "$bad" ]; then
    fail_msg "OpenCode native skill surfaces must not expose Claude adapter paths:"
    printf '%s\n' "$bad"
  fi
}

check_opencode_native_agent_projection() {
  if [ ! -x adapters/opencode/bin/sync-native-agents.py ]; then
    fail_msg "adapters/opencode/bin/sync-native-agents.py must be executable"
    return
  fi

  if ! adapters/opencode/bin/sync-native-agents.py --check >/tmp/opencode-sync-agents.out 2>/tmp/opencode-sync-agents.err; then
    fail_msg "OpenCode native agent projections are stale; run adapters/opencode/bin/sync-native-agents.py"
    cat /tmp/opencode-sync-agents.err
  fi

  for profile in plan-team dev-team qa-team research-team material-team design-team editorial-team external-adversary; do
    agent="adapters/opencode/agents/$profile/$profile.md"
    if [ ! -f "$agent" ]; then
      fail_msg "$agent is missing"
      continue
    fi
    if ! grep -Fq "roles/README.md" "$agent"; then
      fail_msg "$agent must reference roles/README.md as portable source"
    fi
    if ! grep -Fq "adapters/opencode/bin/preflight.sh role" "$agent"; then
      fail_msg "$agent must reference the OpenCode role mapper"
    fi
    if ! grep -Fq "mode: subagent" "$agent"; then
      fail_msg "$agent must declare OpenCode-native subagent mode"
    fi
    if ! grep -Fq "not a non-OpenCode Agent copy" "$agent"; then
      fail_msg "$agent must state that it is not a non-OpenCode Agent copy"
    fi
  done
  for dir in adapters/opencode/agents/*; do
    [ -d "$dir" ] || continue
    profile=$(basename "$dir")
    case " plan-team dev-team qa-team research-team material-team design-team editorial-team external-adversary " in
      *" $profile "*) ;;
      *) fail_msg "$dir is not an approved OpenCode native agent projection" ;;
    esac
  done

  bad=$(rg -n 'adapters/claude|claude_setting' adapters/opencode/agents 2>/dev/null || true)
  if [ -n "$bad" ]; then
    fail_msg "OpenCode native agent surfaces must not expose Claude adapter paths:"
    printf '%s\n' "$bad"
  fi

  if ! grep -Fq 'adapters/opencode/agents/<role>/<role>.md' adapters/opencode/README.md; then
    fail_msg "adapters/opencode/README.md must map role profiles to OpenCode-native agent projections"
  fi
  if grep -Fq 'until OpenCode-native role prompts exist' adapters/opencode/README.md; then
    fail_msg "adapters/opencode/README.md must not describe OpenCode-native role prompts as future-only"
  fi
}

check_opencode_native_command_projection() {
  if [ ! -x adapters/opencode/bin/sync-native-commands.py ]; then
    fail_msg "adapters/opencode/bin/sync-native-commands.py must be executable"
    return
  fi

  if ! adapters/opencode/bin/sync-native-commands.py --check >/tmp/opencode-sync-commands.out 2>/tmp/opencode-sync-commands.err; then
    fail_msg "OpenCode native command projections are stale; run adapters/opencode/bin/sync-native-commands.py"
    cat /tmp/opencode-sync-commands.err
  fi

  for f in capabilities/*.md; do
    [ -f "$f" ] || continue
    [ "$(basename "$f")" = "README.md" ] && continue
    slug=$(basename "$f" .md)
    command="adapters/opencode/commands/$slug.md"
    if [ ! -f "$command" ]; then
      fail_msg "$command is missing"
      continue
    fi
    if ! grep -Fq "capabilities/$slug.md" "$command"; then
      fail_msg "$command must reference capabilities/$slug.md as portable source"
    fi
    if ! grep -Fq "adapters/opencode/bin/preflight.sh capability-info $slug" "$command"; then
      fail_msg "$command must reference the OpenCode capability-info wrapper"
    fi
    if ! grep -Fq "not a runtime-specific command copy" "$command"; then
      fail_msg "$command must state that it is not a runtime-specific command copy"
    fi
    if ! grep -Fq '$ARGUMENTS' "$command"; then
      fail_msg "$command must pass OpenCode command arguments through $ARGUMENTS"
    fi
    if ! grep -Fq 'named `tool_contract`' "$command"; then
      fail_msg "$command must instruct OpenCode to report named tool contracts"
    fi
  done
  for command in adapters/opencode/commands/*.md; do
    [ -f "$command" ] || continue
    slug=$(basename "$command" .md)
    if [ ! -f "capabilities/$slug.md" ]; then
      fail_msg "$command has no matching portable capability source"
    fi
  done

  bad=$(rg -n 'adapters/claude|claude_setting' adapters/opencode/commands 2>/dev/null || true)
  if [ -n "$bad" ]; then
    fail_msg "OpenCode native command surfaces must not expose Claude adapter paths:"
    printf '%s\n' "$bad"
  fi
}

check_opencode_native_plugin_projection() {
  plugin="adapters/opencode/plugins/agent-harness-guards.js"
  plugin_entries=$(find adapters/opencode/plugins -mindepth 1 -maxdepth 1 -exec basename {} \; 2>/dev/null || true)
  for entry in $plugin_entries; do
    if [ "$entry" != "agent-harness-guards.js" ]; then
      fail_msg "adapters/opencode/plugins/$entry is not an approved OpenCode plugin projection"
    fi
  done

  if [ ! -f "$plugin" ]; then
    fail_msg "$plugin is missing"
    return
  fi
  if [ -L "$plugin" ]; then
    fail_msg "$plugin must be a concrete adapter-owned OpenCode plugin"
  fi
  if ! node --check "$plugin" >/tmp/opencode-plugin-check.out 2>/tmp/opencode-plugin-check.err; then
    fail_msg "$plugin must parse as JavaScript"
    cat /tmp/opencode-plugin-check.err
  fi
  if ! grep -Fq '"tool.execute.before"' "$plugin"; then
    fail_msg "$plugin must use OpenCode tool.execute.before hook"
  fi
  if ! grep -Fq '"tool.execute.after"' "$plugin"; then
    fail_msg "$plugin must use OpenCode tool.execute.after hook for design checks"
  fi
  if ! grep -Fq 'adapters", "opencode", "bin", "preflight.sh' "$plugin"; then
    fail_msg "$plugin must bridge to the OpenCode preflight wrapper"
  fi
  if ! grep -Fq 'runPreflight("design"' "$plugin"; then
    fail_msg "$plugin must bridge design HTML writes to the OpenCode design preflight"
  fi
  if ! grep -Fq 'tool.execute.after' adapters/opencode/README.md \
    || ! grep -Fq 'preflight.sh design' adapters/opencode/README.md; then
    fail_msg "adapters/opencode/README.md must document the OpenCode design post-write plugin bridge"
  fi
  if grep -Eq 'adapters/claude|claude_setting|settings\.json|statusline\.sh' "$plugin"; then
    fail_msg "$plugin must not reference Claude-native surfaces"
  fi
}

check_claude_skill_projection() {
  if [ ! -L claude_setting/skills ]; then
    fail_msg "claude_setting/skills must project adapters/claude/skills"
    return
  fi

  target=$(readlink claude_setting/skills)
  if [ "$target" != "../adapters/claude/skills" ]; then
    fail_msg "claude_setting/skills points to $target; expected ../adapters/claude/skills"
  fi

  for d in skills/*; do
    [ -d "$d" ] || continue
    [ -f "$d/SKILL.md" ] || continue
    slug=${d#skills/}
    if [ ! -d "adapters/claude/skills/$slug" ]; then
      fail_msg "adapters/claude/skills/$slug must be an adapter-owned skill directory"
      continue
    fi
    if [ ! -f "adapters/claude/skills/$slug/SKILL.md" ]; then
      fail_msg "adapters/claude/skills/$slug/SKILL.md is missing"
    fi
  done

  diff_out=$(diff -qr --exclude=.sync_state.json skills adapters/claude/skills 2>/dev/null || true)
  if [ -n "$diff_out" ]; then
    fail_msg "skills/ compatibility refs must stay byte-equivalent to adapters/claude/skills/ except .sync_state.json:"
    printf '%s\n' "$diff_out"
  fi
}

check_claude_mode_projection() {
  if [ ! -L claude_setting/agent-modes ]; then
    fail_msg "claude_setting/agent-modes must project adapters/claude/agent-modes"
    return
  fi

  target=$(readlink claude_setting/agent-modes)
  if [ "$target" != "../adapters/claude/agent-modes" ]; then
    fail_msg "claude_setting/agent-modes points to $target; expected ../adapters/claude/agent-modes"
  fi

  for d in roles/modes/*; do
    [ -d "$d" ] || continue
    family=${d#roles/modes/}
    if [ ! -d "adapters/claude/agent-modes/$family" ]; then
      fail_msg "adapters/claude/agent-modes/$family must be an adapter-owned mode directory"
      continue
    fi
    if [ -L "adapters/claude/agent-modes/$family" ]; then
      fail_msg "adapters/claude/agent-modes/$family must be a concrete adapter-owned mode projection"
      continue
    fi
    for f in "$d"/*.md; do
      [ -f "$f" ] || continue
      name=${f#"$d"/}
      if [ ! -f "adapters/claude/agent-modes/$family/$name" ]; then
        fail_msg "adapters/claude/agent-modes/$family/$name is missing"
      fi
    done
  done
}

check_claude_hook_projection() {
  if [ ! -L claude_setting/hooks ]; then
    fail_msg "claude_setting/hooks must project adapters/claude/hooks"
    return
  fi

  target=$(readlink claude_setting/hooks)
  if [ "$target" != "../adapters/claude/hooks" ]; then
    fail_msg "claude_setting/hooks points to $target; expected ../adapters/claude/hooks"
  fi

  for f in hooks/*; do
    [ -f "$f" ] || continue
    name=${f#hooks/}
    if [ ! -f "adapters/claude/hooks/$name" ]; then
      fail_msg "adapters/claude/hooks/$name is missing"
      continue
    fi
    if [ -L "adapters/claude/hooks/$name" ]; then
      fail_msg "adapters/claude/hooks/$name must be a concrete adapter-owned hook projection"
    fi
  done
}

check_claude_utility_projection() {
  if [ ! -L claude_setting/utilities ]; then
    fail_msg "claude_setting/utilities must project adapters/claude/utilities"
    return
  fi

  target=$(readlink claude_setting/utilities)
  if [ "$target" != "../adapters/claude/utilities" ]; then
    fail_msg "claude_setting/utilities points to $target; expected ../adapters/claude/utilities"
  fi

  for f in utilities/*; do
    [ -f "$f" ] || continue
    name=${f#utilities/}
    if [ ! -f "adapters/claude/utilities/$name" ]; then
      fail_msg "adapters/claude/utilities/$name is missing"
      continue
    fi
    if [ -L "adapters/claude/utilities/$name" ]; then
      fail_msg "adapters/claude/utilities/$name must be a concrete adapter-owned utility projection"
    fi
  done

  if [ ! -x adapters/claude/utilities/workflow-toggle.sh ]; then
    fail_msg "adapters/claude/utilities/workflow-toggle.sh must be an executable concrete workflow toggle helper"
  elif ! cmp -s utilities/workflow-toggle.sh adapters/claude/utilities/workflow-toggle.sh; then
    fail_msg "adapters/claude/utilities/workflow-toggle.sh must stay byte-equivalent to utilities/workflow-toggle.sh"
  fi
}

check_claude_boundary_guard_projection() {
  adapter_guard=adapters/claude/tools/check-adaptation-boundary.sh
  root_guard=tools/check-adaptation-boundary.sh

  if [ ! -x "$adapter_guard" ]; then
    fail_msg "$adapter_guard must be an executable concrete boundary guard projection"
    return
  fi
  if [ -L "$adapter_guard" ]; then
    fail_msg "$adapter_guard must be concrete, not a symlink passthrough"
    return
  fi
  if ! cmp -s "$root_guard" "$adapter_guard"; then
    fail_msg "$adapter_guard must stay byte-equivalent to $root_guard"
  fi
}

check_claude_scaffold_projection() {
  if [ ! -L claude_setting/scaffolds ]; then
    fail_msg "claude_setting/scaffolds must project adapters/claude/scaffolds"
    return
  fi

  target=$(readlink claude_setting/scaffolds)
  if [ "$target" != "../adapters/claude/scaffolds" ]; then
    fail_msg "claude_setting/scaffolds points to $target; expected ../adapters/claude/scaffolds"
  fi

  for p in $(find scaffolds -mindepth 1 ! -name '.*' -print); do
    rel=${p#scaffolds/}
    adapter_p=adapters/claude/scaffolds/$rel
    if [ -L "$adapter_p" ]; then
      fail_msg "$adapter_p must be a concrete adapter-owned scaffold projection"
      continue
    fi
    if [ -d "$p" ]; then
      [ -d "$adapter_p" ] || fail_msg "$adapter_p is missing"
    elif [ -f "$p" ]; then
      [ -f "$adapter_p" ] || fail_msg "$adapter_p is missing"
    fi
  done
}

check_claude_loop_projection() {
  if [ ! -L claude_setting/loops ]; then
    fail_msg "claude_setting/loops must project adapters/claude/loops"
    return
  fi

  target=$(readlink claude_setting/loops)
  if [ "$target" != "../adapters/claude/loops" ]; then
    fail_msg "claude_setting/loops points to $target; expected ../adapters/claude/loops"
  fi

  for p in $(find loops -mindepth 1 -print); do
    rel=${p#loops/}
    adapter_p=adapters/claude/loops/$rel
    if [ -L "$adapter_p" ]; then
      fail_msg "$adapter_p must be a concrete adapter-owned loop projection"
      continue
    fi
    if [ -d "$p" ]; then
      [ -d "$adapter_p" ] || fail_msg "$adapter_p is missing"
    elif [ -f "$p" ]; then
      [ -f "$adapter_p" ] || fail_msg "$adapter_p is missing"
    fi
  done
}

check_claude_tool_projection() {
  if [ ! -L claude_setting/tools ]; then
    fail_msg "claude_setting/tools must project adapters/claude/tools"
    return
  fi

  target=$(readlink claude_setting/tools)
  if [ "$target" != "../adapters/claude/tools" ]; then
    fail_msg "claude_setting/tools points to $target; expected ../adapters/claude/tools"
  fi

  for p in $(find tools -mindepth 1 ! -path '*/__pycache__' ! -path '*/__pycache__/*' -print); do
    rel=${p#tools/}
    adapter_p=adapters/claude/tools/$rel
    if [ -L "$adapter_p" ]; then
      fail_msg "$adapter_p must be a concrete adapter-owned tool projection"
      continue
    fi
    if [ -d "$p" ]; then
      [ -d "$adapter_p" ] || fail_msg "$adapter_p is missing"
    elif [ -f "$p" ]; then
      [ -f "$adapter_p" ] || fail_msg "$adapter_p is missing"
    fi
  done
}

check_removed_root_surfaces() {
  if [ -e agents ] || [ -L agents ]; then
    fail_msg "root agents/ exists; Claude-native agents must live under adapters/claude/agents and portable meaning under roles/"
  fi
  if [ -e agent-modes ] || [ -L agent-modes ]; then
    fail_msg "root agent-modes/ exists; portable mode fragments must live under roles/modes and runtime projection under adapters/*/agent-modes"
  fi
}

check_capability_catalog() {
  if [ ! -f capabilities/README.md ]; then
    fail_msg "capabilities/README.md is missing"
    return
  fi

  for d in skills/*; do
    [ -d "$d" ] || continue
    [ -f "$d/SKILL.md" ] || continue
    slug=${d#skills/}
    if ! grep -Fq "| \`$slug\` |" capabilities/README.md; then
      fail_msg "capabilities/README.md is missing skill capability: $slug"
    fi
    if [ ! -f "capabilities/$slug.md" ]; then
      fail_msg "capabilities/$slug.md is missing portable capability spec"
    fi
  done
}

check_codex_capability_map() {
  mapper=adapters/codex/bin/capability-map.sh
  if [ ! -x "$mapper" ]; then
    fail_msg "$mapper is missing or not executable"
    return
  fi

  for d in skills/*; do
    [ -d "$d" ] || continue
    [ -f "$d/SKILL.md" ] || continue
    slug=${d#skills/}
    if ! "$mapper" "$slug" >/dev/null 2>&1; then
      fail_msg "Codex capability map cannot resolve skill capability: $slug"
    fi
  done
}

check_codex_mode_map() {
  mapper=adapters/codex/bin/mode-map.sh
  if [ ! -x "$mapper" ]; then
    fail_msg "$mapper is missing or not executable"
    return
  fi

  for f in roles/modes/*/*.md; do
    [ -f "$f" ] || continue
    rel=${f#roles/modes/}
    rel=${rel%.md}
    if ! "$mapper" "$rel" >/dev/null 2>&1; then
      fail_msg "Codex mode map cannot resolve agent mode: $rel"
    fi
  done
}

check_opencode_capability_map() {
  mapper=adapters/opencode/bin/capability-map.sh
  if [ ! -x "$mapper" ]; then
    fail_msg "$mapper is missing or not executable"
    return
  fi

  for d in skills/*; do
    [ -d "$d" ] || continue
    [ -f "$d/SKILL.md" ] || continue
    slug=${d#skills/}
    if ! "$mapper" "$slug" >/dev/null 2>&1; then
      fail_msg "OpenCode capability map cannot resolve skill capability: $slug"
    fi
  done
}

check_opencode_mode_map() {
  mapper=adapters/opencode/bin/mode-map.sh
  if [ ! -x "$mapper" ]; then
    fail_msg "$mapper is missing or not executable"
    return
  fi

  for f in roles/modes/*/*.md; do
    [ -f "$f" ] || continue
    rel=${f#roles/modes/}
    rel=${rel%.md}
    if ! "$mapper" "$rel" >/dev/null 2>&1; then
      fail_msg "OpenCode mode map cannot resolve agent mode: $rel"
    fi
  done
}

check_hook_catalog() {
  if [ ! -f core/HOOKS.md ]; then
    fail_msg "core/HOOKS.md is missing"
    return
  fi

  for f in hooks/*.sh; do
    [ -f "$f" ] || continue
    case "$f" in
      *.test.sh) continue ;;
    esac
    if ! grep -Fq "\`$f\`" core/HOOKS.md; then
      fail_msg "core/HOOKS.md is missing hook script: $f"
    fi
  done
}

check_legacy_root_links() {
  command -v rg >/dev/null 2>&1 || return 0

  legacy_skill_links=$(rg -n '\]\(\.\./\.\./(CLAUDE|MEMORY|CORE|WORKFLOW|CONVENTIONS|OPERATIONS|DESIGN_PRINCIPLES|VISION)\.md\)' \
    skills adapters README.md MANUAL.md INSTALL_LAYOUT.md 2>/dev/null || true)
  if [ -n "$legacy_skill_links" ]; then
    fail_msg "legacy ../../ tier1 markdown links remain:"
    printf '%s\n' "$legacy_skill_links"
  fi

  legacy_root_links=$(rg -n '\]\((CLAUDE|MEMORY|CORE|WORKFLOW|CONVENTIONS|OPERATIONS|DESIGN_PRINCIPLES|VISION)\.md\)' \
    README.md MANUAL.md INSTALL_LAYOUT.md adapters skills 2>/dev/null || true)
  if [ -n "$legacy_root_links" ]; then
    fail_msg "legacy root tier1 markdown links remain outside core/:"
    printf '%s\n' "$legacy_root_links"
  fi
}

warn_concrete_runtime_terms() {
  command -v rg >/dev/null 2>&1 || return 0

  count=$(rg -n 'sonnet|opus|haiku|claude -p|~/.claude|Claude adapter:' \
    core tools utilities hooks \
    --glob '!tools/check-adaptation-boundary.sh' \
    --glob '!hooks/*.test.sh' 2>/dev/null | wc -l | tr -d ' ')

  if [ "$count" != "0" ]; then
    say "WARN: $count concrete Claude/model references remain in portable areas."
    say "      This is allowed only where documented as adapter mapping, compat-reference, or compat-passthrough."
  fi
}

check_projection_symlinks claude_setting
check_projection_symlinks codex_setting
check_projection_symlinks opencode_setting
check_projection_entry_allowlist claude_setting CLAUDE.md README.md agent-modes agents bin commands core hooks keybindings.json loops manifest.json scaffolds settings.json skills statusline.sh tools track-toggle.sh utilities
check_projection_entry_allowlist codex_setting AGENTS.md README.md core capabilities roles bin tools utilities codex-skills codex-plugin-marketplace codex-hooks codex-agents
check_projection_entry_allowlist opencode_setting AGENTS.md README.md core capabilities roles bin tools utilities opencode-skills opencode-agents opencode-commands opencode-plugins
check_codex_forbidden_entries
check_codex_native_surface_debt
check_required_projection_entries
check_codex_projection_targets
check_opencode_forbidden_entries
check_opencode_required_projection_entries
check_opencode_projection_targets
check_claude_projection_targets
check_claude_adapter_concrete_surfaces
check_non_claude_adapter_symlink_boundaries
check_install_layout_codex_projection
check_install_layout_opencode_projection
check_codex_bin_wrappers
check_opencode_bin_wrappers
check_codex_tool_projection
check_codex_native_skill_projection
check_codex_native_plugin_projection
check_codex_native_agent_projection
check_codex_native_hook_projection
check_portable_agent_home_resolution
check_opencode_tool_projection
check_opencode_native_skill_projection
check_opencode_native_agent_projection
check_opencode_native_command_projection
check_opencode_native_plugin_projection
check_codex_utility_projection
check_opencode_utility_projection
check_claude_bin_wrappers
check_claude_skill_projection
check_claude_mode_projection
check_claude_hook_projection
check_claude_utility_projection
check_claude_boundary_guard_projection
check_claude_scaffold_projection
check_claude_loop_projection
check_claude_tool_projection
check_removed_root_surfaces
check_capability_catalog
check_codex_capability_map
check_opencode_capability_map
check_codex_mode_map
check_opencode_mode_map
check_hook_catalog
check_legacy_root_links
warn_concrete_runtime_terms

if [ "$fail" -eq 0 ]; then
  say "OK: adaptation boundary checks passed"
fi

exit "$fail"
