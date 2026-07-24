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
sys.path.insert(0, str(ROOT / "utilities"))
from dispatch_contract import CANONICAL_PARENT_TRANSPORTS  # noqa: E402


def auth_check(child_harness: str, worktree: str | Path | None = None) -> tuple[bool, str]:
    """Check that the target CLI has a usable local authentication profile.

    This deliberately avoids printing command output because auth status may
    contain account metadata. A live nested request is still kept as a release
    smoke test; this gate is the cheap per-route check.
    """
    if child_harness == "codex":
        command = ["codex", "login", "status"]
        accepted = lambda output: output.lstrip().startswith("Logged in")
    elif child_harness == "claude":
        command = ["claude", "auth", "status"]
        def accepted(output):
            try:
                return json.loads(output).get("loggedIn") is True
            except (ValueError, AttributeError):
                return False
    elif child_harness == "opencode":
        command = ["opencode", "auth", "list"]
        accepted = lambda output: "\u25cf" in output
    else:
        return False, "unknown-harness"
    if shutil.which(command[0]) is None:
        return False, "command-unavailable"
    # A nested workspace-write owner may execute only from its checked
    # worktree.  Running the auth probe from the primary checkout falsely
    # reported auth-unavailable even though the projected CODEX_HOME was valid.
    cwd = Path(worktree).resolve() if worktree else ROOT
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0 or not (
        accepted(result.stdout) or accepted(result.stderr)
    ):
        return False, "auth-unavailable"
    return True, ""


def command_check(child_harness: str, worktree: str) -> tuple[str, str, str]:
    if not Path(worktree).is_dir():
        return "unsupported", "direct-command-check", "worktree-not-found"
    authenticated, auth_failure = auth_check(child_harness, worktree)
    if not authenticated:
        return "unsupported", "direct-auth-check", auth_failure
    if child_harness == "codex":
        command = [str(ROOT / "adapters/codex/bin/preflight.sh"), "headless", "--check", worktree]
    elif child_harness == "opencode":
        command = [str(ROOT / "adapters/opencode/bin/preflight.sh"), "headless", "--check", worktree]
    elif child_harness == "claude":
        if shutil.which("claude") and Path(worktree).is_dir():
            return "supported", "direct-command-check", ""
        return "unsupported", "direct-command-check", "command-unavailable"
    else:
        return "unknown", "unsupported-child-harness", "unknown-harness"
    result = subprocess.run(command, cwd=worktree, text=True, capture_output=True, check=False)
    if result.returncode == 0:
        return "supported", "direct-auth+headless-check", ""
    detail = (result.stdout + "\n" + result.stderr).strip().replace("\n", ";")
    return "unsupported", "direct-headless-check", detail or f"exit-{result.returncode}"


def evaluate(args: argparse.Namespace) -> dict[str, str]:
    if args.launch_authority == "ancestor-broker":
        status, source, failure = "unsupported", "dispatch-contract-v3", "launch-broker-retired"
    elif args.parent_transport not in CANONICAL_PARENT_TRANSPORTS:
        status, source, failure = (
            "unsupported",
            "dispatch-contract-v3",
            "noncanonical-parent-transport",
        )
    elif args.child_harness == "opencode":
        status, source, failure = (
            "unsupported",
            "dispatch-contract-v3",
            "opencode-standard-depth2-unsupported",
        )
    elif (
        args.parent_harness == "codex"
        and args.parent_transport == "headless"
        and args.parent_sandbox == "workspace-write"
        and os.environ.get("AGENT_NESTED_HEADLESS_NETWORK") != "1"
    ):
        status, source, failure = "unsupported", "codex-owner-network-contract", "nested-network-unconfirmed"
    else:
        status, source, failure = command_check(args.child_harness, args.worktree)
        if status == "supported" and args.parent_harness == "codex":
            source = "codex-owner-network-contract+" + source
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
