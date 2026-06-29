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

check_codex_forbidden_entries() {
  for p in CLAUDE.md settings.json keybindings.json commands statusline.sh track-toggle.sh skills agents agent-modes hooks; do
    if [ -e "codex_setting/$p" ] || [ -L "codex_setting/$p" ]; then
      fail_msg "codex_setting/$p exists; Codex projection must not expose Claude-native surfaces"
    fi
  done
}

check_required_projection_entries() {
  for p in AGENTS.md README.md core capabilities bin tools utilities; do
    if [ ! -L "codex_setting/$p" ]; then
      fail_msg "codex_setting/$p must be a symlink projection entry"
    fi
  done
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

  for p in preflight.sh role-map.sh capability-map.sh mode-map.sh distill-worker.sh; do
    if [ ! -x "adapters/codex/bin/$p" ]; then
      fail_msg "adapters/codex/bin/$p is missing or not executable"
    fi
  done
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

  for p in agent-home.sh artifact-root.sh agent-worklog-state.sh workflow-guard-hook.sh; do
    if [ ! -L "adapters/codex/utilities/$p" ]; then
      fail_msg "adapters/codex/utilities/$p must be a selective portable utility projection"
      continue
    fi
    link=$(readlink "adapters/codex/utilities/$p")
    if [ "$link" != "../../../utilities/$p" ]; then
      fail_msg "adapters/codex/utilities/$p points to $link; expected ../../../utilities/$p"
    fi
  done

  extra=$(find adapters/codex/utilities -mindepth 1 -maxdepth 1 ! \( -name agent-home.sh -o -name artifact-root.sh -o -name agent-worklog-state.sh -o -name workflow-guard-hook.sh \) -print 2>/dev/null || true)
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
check_codex_forbidden_entries
check_required_projection_entries
check_codex_bin_wrappers
check_codex_utility_projection
check_claude_bin_wrappers
check_claude_skill_projection
check_claude_mode_projection
check_claude_hook_projection
check_claude_utility_projection
check_claude_scaffold_projection
check_claude_loop_projection
check_claude_tool_projection
check_removed_root_surfaces
check_capability_catalog
check_codex_capability_map
check_codex_mode_map
check_hook_catalog
check_legacy_root_links
warn_concrete_runtime_terms

if [ "$fail" -eq 0 ]; then
  say "OK: adaptation boundary checks passed"
fi

exit "$fail"
