#!/usr/bin/env python3
"""Claude thin projection onto portable route and node dispatch interfaces."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
argv=[sys.executable,str(ROOT/"utilities/dispatch-node.py"),"--adapter","claude",*sys.argv[2:]] if len(sys.argv)>1 and sys.argv[1]=="dispatch-node" else [sys.executable,str(ROOT/"utilities/capability-route.py"),*sys.argv[1:]]
raise SystemExit(subprocess.run(argv).returncode)
