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
from dispatch_contract import (  # noqa: E402
    CANONICAL_PARENT_TRANSPORTS,
    PARENT_TRANSPORT_BY_DISPATCH_DEPTH,
    WRAPPER_PARENT_SANDBOXES,
)

# WHOSE RUNTIME THIS PROBE DESCRIBES
# ---------------------------------
# Every tuple this probe emits answers one question: "may the parent of a
# dispatch-depth-2 node spawn that child?" The parent is therefore the
# dispatch-depth-1 registered-headless capability owner -- never the caller
# running the probe, which is normally the dispatch-depth-0 interactive
# session about to launch that owner. A sealed tuple whose parent identity is
# not the launching wrapper's real identity only fails much later, at depth-2
# launch (dispatch-evidence-parent-runtime-mismatch), after the owner has
# already been paid for.
#
# Both known incidents are the same trap on different fields of the same
# tuple: 2026-07-31 v2-audit sealed parent_sandbox=none, and 2026-08-04
# agent-note sealed the caller's own parent_transport=interactive and lost a
# whole standard cycle to the inline hop. All three fields are therefore
# resolved or rejected here, at probe time, and cross-checked again at route
# compile (capability-route.py) and at launch (dispatch_contract.py).


def resolve_parent_harness(requested: str, environ=None) -> tuple[str, str]:
    """Return (resolved_harness, failure_class) for the depth-2 node's parent.

    `auto` is honest only inside a running wrapper, which exports its own
    identity: there the value is the parent. A dispatch-depth-0 caller has no
    such export and the owner's harness is not yet decided -- `dispatch-owner`
    picks it later from its configured/eligibility cascade -- so `auto` fails
    closed rather than guessing the caller's own harness. Replicating that
    selection here would create a second authority that can disagree with the
    real one.
    """

    environ = os.environ if environ is None else environ
    if requested != "auto":
        return requested, "" if requested in WRAPPER_PARENT_SANDBOXES else "parent-harness-unknown"
    current = environ.get("AGENT_DISPATCH_CURRENT_HARNESS")
    if not current:
        return requested, "parent-harness-underivable"
    if current not in WRAPPER_PARENT_SANDBOXES:
        return current, "parent-harness-unknown"
    return current, ""


def resolve_parent_transport(requested: str, environ=None) -> tuple[str, str]:
    """Return (resolved_transport, failure_class) for the depth-2 node's parent.

    Unlike the harness, this axis has one structurally correct answer. Inside a
    wrapper the exported value is authoritative; from a dispatch-depth-0 caller
    the parent-to-be is the depth-1 owner it is about to launch, and every
    registered owner is headless. An explicit `interactive` is canonical
    vocabulary for the caller and a contradiction for this tuple.
    """

    environ = os.environ if environ is None else environ
    expected = PARENT_TRANSPORT_BY_DISPATCH_DEPTH[1]
    if requested == "auto":
        return environ.get("AGENT_DISPATCH_CURRENT_TRANSPORT") or expected, ""
    if requested not in CANONICAL_PARENT_TRANSPORTS:
        return requested, "noncanonical-parent-transport"
    if requested != expected:
        return requested, "parent-transport-not-registered-headless"
    return requested, ""


def resolve_parent_sandbox(parent_harness: str, requested: str) -> tuple[str, str]:
    """Return (resolved_label, failure_class) for the requested parent sandbox."""

    labels = WRAPPER_PARENT_SANDBOXES[parent_harness]
    if requested == "auto":
        return labels[0], ""
    if requested in labels:
        return requested, ""
    return requested, "parent-sandbox-label-unknown"


def codex_login_status(output: str) -> bool:
    """Accept a valid status line without letting unrelated warnings reorder it."""

    return any(
        line.strip().startswith("Logged in")
        for line in output.splitlines()
        if line.strip()
    )


def auth_check(child_harness: str, worktree: str | Path | None = None) -> tuple[bool, str]:
    """Check that the target CLI has a usable local authentication profile.

    This deliberately avoids printing command output because auth status may
    contain account metadata. A live nested request is still kept as a release
    smoke test; this gate is the cheap per-route check.
    """
    if child_harness == "codex":
        command = ["codex", "login", "status"]
        accepted = codex_login_status
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
    return (
        "unsupported",
        "direct-headless-check",
        preflight_failure_reason(result.stdout) or detail or f"exit-{result.returncode}",
    )


def preflight_failure_reason(output: str) -> str:
    """Return the adapter preflight's own `reason=` word, when it emitted one.

    A checked hop records this value as its `failure_class`, and a route reads it
    back to decide whether the failure is worth another attempt. The joined
    stdout+stderr blob is a diagnostic string, not a class, so prefer the
    structured word the preflight already prints and fall back only when absent.
    """

    for line in output.splitlines():
        key, sep, value = line.strip().partition("=")
        if sep and key == "reason" and value:
            return value
    return ""


def evaluate(args: argparse.Namespace) -> dict[str, str]:
    args.parent_harness, harness_failure = resolve_parent_harness(args.parent_harness)
    args.parent_transport, transport_failure = resolve_parent_transport(args.parent_transport)
    sandbox_failure = ""
    if not harness_failure:
        args.parent_sandbox, sandbox_failure = resolve_parent_sandbox(
            args.parent_harness, args.parent_sandbox
        )
    if harness_failure:
        status, source, failure = "unsupported", "parent-harness-vocabulary", harness_failure
    elif sandbox_failure:
        status, source, failure = "unsupported", "parent-sandbox-vocabulary", sandbox_failure
    elif args.launch_authority == "ancestor-broker":
        status, source, failure = "unsupported", "dispatch-contract-v3", "launch-broker-retired"
    elif transport_failure == "noncanonical-parent-transport":
        status, source, failure = (
            "unsupported",
            "dispatch-contract-v3",
            "noncanonical-parent-transport",
        )
    elif transport_failure:
        status, source, failure = "unsupported", "parent-transport-vocabulary", transport_failure
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
    # Every --parent-* value describes the process that will actually launch the
    # dispatch-depth-2 child -- the dispatch-depth-1 registered-headless owner --
    # NOT the caller running this probe.
    p.add_argument(
        "--parent-harness", required=True, choices=("auto", "claude", "codex", "opencode"),
        help="harness of the depth-2 node's parent (the depth-1 owner), not the caller;"
             " 'auto' reads AGENT_DISPATCH_CURRENT_HARNESS and fails closed without it",
    )
    p.add_argument(
        "--parent-transport", default="auto",
        help="transport of the depth-2 node's parent, not the caller; 'auto' (default)"
             " reads AGENT_DISPATCH_CURRENT_TRANSPORT and otherwise resolves to the"
             " headless depth-1 owner about to be launched",
    )
    p.add_argument(
        "--parent-sandbox", default="auto",
        help="sandbox label of the depth-2 node's parent, not the caller; 'auto'"
             " (default) resolves the parent harness wrapper's canonical export",
    )
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
