#!/usr/bin/env python3
"""Codex bridge for the portable worker state hook."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(os.environ.get("AGENT_HOME") or Path(__file__).resolve().parents[3])
raise SystemExit(subprocess.run(
    [sys.executable, str(ROOT / "utilities/worker-state-hook.py"), *sys.argv[1:]],
    stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, check=False,
).returncode)
