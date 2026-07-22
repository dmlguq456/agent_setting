#!/bin/sh
# Compatibility wrapper — logic moved to sync-missing-projections.py (2026-07-22)
# so tools/generate.py (python-exec) can run it with --check in the standard battery.
exec python3 "$(dirname "$0")/sync-missing-projections.py" "$@"
