#!/usr/bin/env sh
# harness.sh — thin POSIX sh launcher. Resolve the AGENT_HOME symlink and delegate
# to the installer.py command tree. Pass all options through unchanged.
# Installation exposes this script as the `harness` command on PATH.
set -eu

# Resolve the real script location even when invoked through a symlink.
SOURCE=$0
while [ -h "$SOURCE" ]; do
  DIR=$(CDPATH= cd -P "$(dirname "$SOURCE")" && pwd)
  SOURCE=$(readlink "$SOURCE")
  case $SOURCE in
    /*) ;;
    *) SOURCE="$DIR/$SOURCE" ;;
  esac
done
SCRIPT_DIR=$(CDPATH= cd -P "$(dirname "$SOURCE")" && pwd)
INSTALLER_PY="$SCRIPT_DIR/installer.py"

PY=$(command -v python3 || command -v python || true)
if [ -z "$PY" ]; then echo "harness: python3 is required." >&2; exit 1; fi
if [ ! -f "$INSTALLER_PY" ]; then echo "harness: installer.py was not found ($INSTALLER_PY)." >&2; exit 1; fi

exec "$PY" "$INSTALLER_PY" "$@"
