#!/usr/bin/env python3
"""Report checked nested headless eligibility without conflating runtime surfaces."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def broker_check(child_harness: str, worktree: str) -> tuple[str, str, str, str, str]:
    agent_home = Path(os.environ.get("AGENT_HOME", ROOT)).resolve()
    broker_root = Path(os.environ.get("AGENT_DISPATCH_BROKER_ROOT", agent_home / ".dispatch/broker")).resolve()
    jobs = Path(os.environ.get("AGENT_DISPATCH_JOBS", agent_home / ".dispatch/jobs.log")).resolve()
    broker = subprocess.run(
        [
            sys.executable,
            str(ROOT / "utilities/dispatch-broker.py"),
            "status",
            "--root",
            str(broker_root),
            "--jobs",
            str(jobs),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if broker.returncode:
        fields = dict(line.split("=", 1) for line in broker.stdout.splitlines() if "=" in line)
        return "unsupported", "depth-0-broker-status", fields.get("reason", "broker-unavailable"), str(broker_root), ""
    broker_fields = dict(line.split("=", 1) for line in broker.stdout.splitlines() if "=" in line)
    instance = broker_fields.get("broker_instance", "unknown")
    if child_harness == "codex":
        command = [str(ROOT / "adapters/codex/bin/preflight.sh"), "headless", "--check", worktree]
    elif child_harness == "opencode":
        command = [str(ROOT / "adapters/opencode/bin/preflight.sh"), "headless", "--check", worktree]
    elif child_harness == "claude":
        if shutil.which("claude") and Path(worktree).is_dir():
            return "supported", f"depth-0-broker:{instance}+command-check", "", str(broker_root), instance
        return "unsupported", f"depth-0-broker:{instance}+command-check", "command-unavailable", str(broker_root), instance
    else:
        return "unknown", "unsupported-child-harness", "unknown-harness", str(broker_root), instance
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode == 0:
        return "supported", f"depth-0-broker:{instance}+headless-check", "", str(broker_root), instance
    detail = (result.stdout + "\n" + result.stderr).strip().replace("\n", ";")
    return "unsupported", f"depth-0-broker:{instance}+headless-check", detail or f"exit-{result.returncode}", str(broker_root), instance


def evaluate(args: argparse.Namespace) -> dict[str, str]:
    if (
        args.parent_harness == "codex"
        and args.parent_transport == "headless"
        and args.parent_sandbox == "workspace-write"
        and args.child_harness == "codex"
        and args.launch_authority == "conductor"
    ):
        status, source, failure = (
            "unsupported",
            "2026-07-15-stage-dispatch-v10-local-probe",
            "network-operation-not-permitted",
        )
        broker_root, broker_instance = "", ""
    elif args.launch_authority == "ancestor-broker":
        status, source, failure, broker_root, broker_instance = broker_check(args.child_harness, args.worktree)
    else:
        status, source, failure = "unknown", "no-context-matched-probe", "unprobed-tuple"
        broker_root, broker_instance = "", ""
    return {
        "parent_harness": args.parent_harness,
        "parent_transport": args.parent_transport,
        "parent_sandbox": args.parent_sandbox,
        "child_harness": args.child_harness,
        "launch_authority": args.launch_authority,
        "status": status,
        "probe_source": source,
        "probe_time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "failure_class": failure,
        "broker_root": broker_root,
        "broker_instance": broker_instance,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--parent-harness", required=True, choices=("claude", "codex", "opencode"))
    p.add_argument("--parent-transport", required=True)
    p.add_argument("--parent-sandbox", required=True)
    p.add_argument("--child-harness", required=True, choices=("claude", "codex", "opencode"))
    p.add_argument("--launch-authority", required=True, choices=("conductor", "ancestor-broker"))
    p.add_argument("--worktree", required=True)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    row = evaluate(args)
    if args.json:
        print(json.dumps(row, sort_keys=True))
    else:
        for key, value in row.items():
            print(f"{key}={value or '-'}")
    return 0 if row["status"] == "supported" else 69


if __name__ == "__main__":
    raise SystemExit(main())
