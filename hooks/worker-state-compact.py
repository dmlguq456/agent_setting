#!/usr/bin/env python3
"""Portable hook bridge for worker ledger write and compaction fences."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(os.environ.get("AGENT_HOME") or Path(__file__).resolve().parents[1])
raise SystemExit(subprocess.run(
    [sys.executable, str(ROOT / "utilities/worker-state-hook.py"), *sys.argv[1:]],
    stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, check=False,
).returncode)
