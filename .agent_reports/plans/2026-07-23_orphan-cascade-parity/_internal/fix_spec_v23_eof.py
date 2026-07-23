#!/usr/bin/env python3
"""Normalize the v23 pipeline summary EOF inside the spec lock."""

import os
from pathlib import Path


if os.environ.get("AGENT_SPEC_LOCK_HELD") != "1":
    raise SystemExit("spec lock is required")
spec_root = Path(os.environ["AGENT_SPEC_ROOT"]).resolve()
state = (spec_root / "pipeline_state.yaml").read_text(encoding="utf-8")
if "version: 23\n" not in state:
    raise SystemExit("expected stage-dispatch v23")
path = spec_root / "pipeline_summary.md"
text = path.read_text(encoding="utf-8")
if text.endswith("\n") and not text.endswith("\n\n"):
    raise SystemExit(0)
if not text.endswith("\n\n") or text.endswith("\n\n\n"):
    raise SystemExit("unexpected pipeline summary EOF")
path.write_text(text.rstrip() + "\n", encoding="utf-8")
