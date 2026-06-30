#!/usr/bin/env sh
# apply-tui-config.sh — apply harness-recommended Codex TUI preferences to the
# runtime-owned $CODEX_HOME/config.toml without taking ownership of that file.
#
# Only the [tui] status_line and status_line_use_colors keys are managed here.
# Project trust, hook trust hashes, plugin state, model defaults, credentials
# pointers, sessions, logs, caches, and other runtime state remain untouched.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME=${AGENT_HOME:-}
if [ -z "$AGENT_HOME" ] || [ ! -f "$AGENT_HOME/core/CORE.md" ]; then
  AGENT_HOME=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)
fi
CODEX_HOME=${CODEX_HOME:-$HOME/.codex}
CONFIG="$CODEX_HOME/config.toml"
FRAGMENT="$AGENT_HOME/adapters/codex/config/tui-statusline.toml"

case "${1:-}" in
  -h|--help)
    echo "usage: apply-tui-config.sh   # updates [tui] status_line keys in \$CODEX_HOME/config.toml"
    exit 0 ;;
  "")
    ;;
  *)
    echo "apply-tui-config: unknown option: $1" >&2
    exit 64 ;;
esac

[ -f "$FRAGMENT" ] || { echo "apply-tui-config: fragment missing: $FRAGMENT" >&2; exit 69; }
mkdir -p "$CODEX_HOME"

python3 - "$CONFIG" "$FRAGMENT" <<'PY'
import pathlib
import re
import sys

config_path = pathlib.Path(sys.argv[1])
fragment_path = pathlib.Path(sys.argv[2])

fragment = fragment_path.read_text(encoding="utf-8")
wanted = {}
for key in ("status_line", "status_line_use_colors"):
    match = re.search(rf"(?m)^{key}\s*=\s*(.+)$", fragment)
    if not match:
        raise SystemExit(f"apply-tui-config: missing {key} in {fragment_path}")
    wanted[key] = f"{key} = {match.group(1).strip()}"

text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
lines = text.splitlines()

section_re = re.compile(r"^\s*\[[^\]]+\]\s*$")
tui_start = None
tui_end = None
for idx, line in enumerate(lines):
    if re.match(r"^\s*\[tui\]\s*$", line):
        tui_start = idx
        tui_end = len(lines)
        for j in range(idx + 1, len(lines)):
            if section_re.match(lines[j]):
                tui_end = j
                break
        break

if tui_start is None:
    if lines and lines[-1].strip():
        lines.append("")
    lines.extend(["[tui]", wanted["status_line"], wanted["status_line_use_colors"]])
else:
    seen = set()
    key_re = re.compile(r"^\s*(status_line|status_line_use_colors)\s*=")
    new_section = []
    for line in lines[tui_start:tui_end]:
        match = key_re.match(line)
        if match:
            key = match.group(1)
            if key not in seen:
                new_section.append(wanted[key])
                seen.add(key)
            continue
        new_section.append(line)
    for key in ("status_line", "status_line_use_colors"):
        if key not in seen:
            new_section.append(wanted[key])
    lines = lines[:tui_start] + new_section + lines[tui_end:]

new_text = "\n".join(lines) + "\n"
if config_path.exists() and config_path.read_text(encoding="utf-8") == new_text:
    changed = False
else:
    if config_path.exists():
        backup = config_path.with_name(config_path.name + ".pre-harness-tui")
        if not backup.exists():
            backup.write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
    config_path.write_text(new_text, encoding="utf-8")
    changed = True

print("adapter=codex")
print("runtime_surface=codex-runtime-tui-config")
print(f"config={config_path}")
print(f"fragment={fragment_path}")
print("managed_keys=status_line,status_line_use_colors")
print(f"changed={'yes' if changed else 'no'}")
print("status=ok")
PY
