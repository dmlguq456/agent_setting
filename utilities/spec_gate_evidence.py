#!/usr/bin/env python3
"""SD-45 route-record evidence probe for the spec-read write gate.

Portable CLI, consumed by ``hooks/spec-skill-gate.sh`` as an additional,
purely-additive pass path alongside the existing session-local marker. The
route record is a caller-asserted claim (``capability-route.py`` writes
``spec_read.satisfied`` from a compiling caller's ``--spec-read`` string, not
from any machine-verified read), so this probe can never turn a marker PASS
into a deny and a caller that supplies a bogus or forged ``--route`` gains
nothing over today's marker-only behaviour: any failure here falls through to
the marker loop unchanged (documented trust boundary, plan.md §9).

Exit 0 only when every binding below holds. Any other outcome exits non-zero
and prints nothing to stdout — the caller must never treat stray output as a
pass signal.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _fail() -> int:
    return 1


def check(
    *,
    route_path: str,
    prd_path: str,
    project_root: str,
    artifact_root: str,
    route_id: str | None,
) -> int:
    route_file = Path(route_path)
    if not route_file.is_absolute():
        return _fail()
    try:
        raw = route_file.read_text(encoding="utf-8")
        record = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return _fail()
    if not isinstance(record, dict):
        return _fail()

    try:
        if record.get("schema_version") != 2:
            return _fail()
        if record.get("tracking") != "tracked":
            return _fail()
        gate = record.get("tracked_gate_evidence")
        if not isinstance(gate, dict):
            return _fail()
        if gate.get("workflow_mode") != "tracked":
            return _fail()
        spec_read = gate.get("spec_read")
        if not isinstance(spec_read, dict) or spec_read.get("satisfied") is not True:
            return _fail()

        if not route_id:
            return _fail()
        if record.get("route_id") != route_id:
            return _fail()

        record_cwd = record.get("cwd")
        record_artifact_root = record.get("artifact_root")
        if not record_cwd or not record_artifact_root:
            return _fail()
        if Path(record_cwd).resolve() != Path(project_root).resolve():
            return _fail()
        if Path(record_artifact_root).resolve() != Path(artifact_root).resolve():
            return _fail()

        prd_file = Path(prd_path)
        prd_mtime = prd_file.stat().st_mtime
        route_mtime = route_file.stat().st_mtime
        if prd_mtime > route_mtime:
            return _fail()
    except (OSError, KeyError, TypeError, ValueError):
        return _fail()

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--route", required=True)
    parser.add_argument("--prd", required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--route-id", default="")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return _fail()

    return check(
        route_path=args.route,
        prd_path=args.prd,
        project_root=args.project_root,
        artifact_root=args.artifact_root,
        route_id=args.route_id or None,
    )


if __name__ == "__main__":
    sys.exit(main())
