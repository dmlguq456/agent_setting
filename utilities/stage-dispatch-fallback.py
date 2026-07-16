#!/usr/bin/env python3
"""Execute a checked dispatch-contract-v3 fallback for one route node."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
ORDER = ["same-harness-headless", "cross-harness-headless", "native-subagent", "inline"]


def fail(reason: str, code: int, **fields: str) -> int:
    print("check=failed")
    print(f"reason={reason}")
    for key, value in fields.items():
        print(f"{key}={value}")
    return code


def output_fields(output: str) -> dict[str, str]:
    return dict(line.split("=", 1) for line in output.splitlines() if "=" in line)


def load_node(route_path: Path, node_id: str) -> tuple[dict, dict]:
    route = json.loads(route_path.read_text(encoding="utf-8"))
    verify = subprocess.run(
        [sys.executable, str(ROOT / "utilities/capability-route.py"), "verify", "--route", str(route_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if verify.returncode:
        raise ValueError((verify.stderr or verify.stdout).strip())
    node = next((row for row in route.get("nodes", []) if row.get("id") == node_id), None)
    if not node:
        raise ValueError(f"unknown route node: {node_id}")
    chain = node.get("dispatch_fallback")
    if not isinstance(chain, list) or [row.get("hop") for row in chain] != ORDER:
        raise ValueError("route node lacks checked ordered fallback")
    return route, node


def tuple_key(row: dict) -> str:
    return "/".join(str(row[key]) for key in (
        "parent_harness", "parent_transport", "parent_sandbox", "child_harness", "launch_authority"
    ))


def registry_failures(jobs: Path, route_id: str, node_id: str) -> dict[str, list[str]]:
    failures: dict[str, list[str]] = {}
    if not jobs.is_file():
        return failures
    for line in jobs.read_text(encoding="utf-8", errors="replace").splitlines():
        fields = line.split("\t")
        if len(fields) != 6 or fields[1] != "done":
            continue
        metadata = dict(part.split("=", 1) for part in fields[5].split(",") if "=" in part)
        if metadata.get("route_id") != route_id or metadata.get("route_node") != node_id:
            continue
        if not metadata.get("note", "").startswith("dead-"):
            continue
        required = ("parent_harness", "parent_transport", "parent_sandbox", "child_harness", "launch_authority")
        if any(not metadata.get(key) for key in required):
            continue
        key = "/".join(metadata[name] for name in required)
        failures.setdefault(key, []).append(metadata.get("attempt_id", "legacy-attempt"))
    return failures


def registry_has_attempt(jobs: Path, attempt_id: str) -> bool:
    if not jobs.is_file():
        return False
    for line in jobs.read_text(encoding="utf-8", errors="replace").splitlines():
        fields = line.split("\t")
        if len(fields) != 6:
            continue
        metadata = dict(part.split("=", 1) for part in fields[5].split(",") if "=" in part)
        if metadata.get("attempt_id") == attempt_id:
            return True
    return False


def attempt_identity(args: argparse.Namespace, route: dict, node: dict, row: dict, ordinal: int) -> str:
    """Stable across dry-run/register/start and concurrent conductor retries."""

    payload = {
        "route_id": route["route_id"],
        "route_node": node["id"],
        "slug": args.slug,
        "parent": args.parent,
        "target_harness": row["child_harness"],
        "fallback_ordinal": ordinal,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return "att-" + digest[:48]


def wrapper_command(
    args: argparse.Namespace,
    route: dict,
    node: dict,
    row: dict,
    ordinal: int,
    attempt_id: str,
) -> list[str]:
    harness = row["child_harness"]
    wrapper = ROOT / f"adapters/{harness}/bin/dispatch-headless.py"
    if harness not in {"codex", "claude", "opencode"} or not wrapper.is_file():
        raise ValueError(f"unsupported child harness: {harness}")
    command = [
        sys.executable,
        str(wrapper),
        f"--{args.action}",
        "--worktree", route["cwd"],
        "--slug", args.slug,
        "--capability", route["capability"],
        "--mode", args.mode,
        "--qa", args.qa,
        "--intensity", route["effective_intensity"],
        "--depth", "2",
        "--parent", args.parent,
        "--worker-role", args.worker_role or node.get("role", node["id"]),
        "--owner", route["capability"],
        "--owner-harness", row["parent_harness"],
        "--model-role", args.model_role or node.get("role", "fast implementer"),
        "--route-file", str(args.route),
        "--route-id", route["route_id"],
        "--route-hash", route["route_hash"],
        "--route-node", node["id"],
        "--registry-digest", route["registry_digest"],
        "--write-scope", ";".join(node.get("write_scope", [])),
        "--completion-gate", node["completion_gate"],
        "--jobs", str(args.jobs),
        "--attempt-id", attempt_id,
        "--parent-harness", row["parent_harness"],
        "--parent-transport", row["parent_transport"],
        "--parent-sandbox", row["parent_sandbox"],
        "--launch-authority", "conductor",
        "--nested-eligibility", "supported",
        "--eligibility-source", row["probe_source"],
        "--eligibility-failure-class", row.get("failure_class") or "-",
        "--fallback-ordinal", str(ordinal),
    ]
    optional = (
        (args.prompt_file, "--prompt-file"),
        (os.environ.get("AGENT_DISPATCH_PARENT_SESSION_ID"), "--parent-session-id"),
        (os.environ.get("AGENT_DISPATCH_PARENT_CWD"), "--parent-cwd"),
    )
    for value, flag in optional:
        if value:
            command += [flag, str(value)]
    return command


def direct_env() -> dict[str, str]:
    """Never project a retired broker binding into a direct adapter call."""

    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("AGENT_DISPATCH_BROKER_")
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--route", type=Path, required=True)
    p.add_argument("--node", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--parent", required=True)
    p.add_argument("--mode", required=True)
    p.add_argument("--qa", default="standard")
    p.add_argument("--worker-role")
    p.add_argument("--model-role")
    p.add_argument("--prompt-file", type=Path)
    p.add_argument("--jobs", type=Path)
    p.add_argument("--broker-root", type=Path, help=argparse.SUPPRESS)
    p.add_argument("--broker-timeout", type=float, help=argparse.SUPPRESS)
    p.add_argument("--direct-timeout", type=float, default=45.0)
    p.add_argument("--failed-tuple", action="append", default=[], help="tuple key already failed without evidence change")
    action = p.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", dest="action", action="store_const", const="dry-run")
    action.add_argument("--register", dest="action", action="store_const", const="register")
    action.add_argument("--start", dest="action", action="store_const", const="start")
    args = p.parse_args()

    try:
        args.route = args.route.resolve()
        route, node = load_node(args.route, args.node)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return fail("invalid-fallback-route", 65, detail=str(exc))
    contract = route.get("dispatch_contract_version") or route.get("broker_contract_version")
    if contract != 3:
        return fail("legacy-broker-route-read-only", 76, contract_version=str(contract or 1), child_spawned="0")
    if args.broker_root is not None or args.broker_timeout is not None:
        return fail("retired-broker-option", 64, child_spawned="0")

    inherited_jobs = os.environ.get("AGENT_DISPATCH_JOBS")
    args.jobs = (args.jobs or Path(inherited_jobs or ROOT / ".dispatch/jobs.log")).resolve()
    if inherited_jobs and args.jobs != Path(inherited_jobs).resolve():
        return fail("noncanonical-nested-jobs", 73, explicit=str(args.jobs), inherited=str(Path(inherited_jobs).resolve()))
    if args.action in {"register", "start"} and not inherited_jobs:
        return fail("global-registry-unset", 73, child_spawned="0")

    prior_failures = registry_failures(args.jobs, route["route_id"], node["id"])
    failed_tuples = set(args.failed_tuple) | set(prior_failures)
    attempts: list[str] = []
    for hop in node["dispatch_fallback"]:
        ordinal = int(hop["ordinal"])
        if hop["hop"] in {"same-harness-headless", "cross-harness-headless"}:
            for row in hop.get("candidates", []):
                key = tuple_key(row)
                unsupported = row.get("status") != "supported" or row.get("launch_authority") != "conductor"
                if unsupported or key in failed_tuples:
                    reason = "prior-unchanged-failure" if key in failed_tuples else row.get("failure_class") or row.get("status")
                    attempts.append(f"{ordinal}:{key}:skipped-{reason}")
                    continue
                attempt_id = attempt_identity(args, route, node, row, ordinal)
                try:
                    command = wrapper_command(args, route, node, row, ordinal, attempt_id)
                    result = subprocess.run(
                        command,
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                        timeout=args.direct_timeout,
                        env=direct_env(),
                    )
                    output = (result.stdout + result.stderr).strip()
                    fields = output_fields(output)
                    early = fields.get("early_death", "-")
                    attempts.append(f"{ordinal}:{key}:direct:exit-{result.returncode}:attempt-{attempt_id}")
                except subprocess.TimeoutExpired as exc:
                    attempts.append(f"{ordinal}:{key}:direct-timeout:attempt-{attempt_id}")
                    if registry_has_attempt(args.jobs, attempt_id):
                        return fail(
                            "direct-launch-outcome-unknown", 76,
                            attempt_id=attempt_id, child_spawned="unknown",
                            attempt_trace="|".join(attempts),
                        )
                    continue
                except (OSError, ValueError) as exc:
                    attempts.append(f"{ordinal}:{key}:direct-error-{type(exc).__name__}:attempt-{attempt_id}")
                    continue
                if result.returncode == 0 and early == "-" and fields.get("check") != "failed":
                    print("check=ok")
                    print(f"selected_hop={hop['hop']}")
                    print(f"fallback_ordinal={ordinal}")
                    print(f"child_harness={row['child_harness']}")
                    print("launch_authority=conductor")
                    print("broker_lifecycle=retired")
                    print(f"attempt_id={attempt_id}")
                    print(f"job_registry={args.jobs}")
                    print("attempt_trace=" + "|".join(attempts))
                    print("prior_attempt_ids=" + ",".join(x for values in prior_failures.values() for x in values))
                    if output:
                        print(output)
                    return 0
        elif hop["hop"] == "native-subagent":
            candidate = next((row for row in hop.get("candidates", []) if row.get("status") == "supported"), None)
            if candidate:
                print("check=degraded")
                print("selected_hop=native-subagent")
                print("fleet_visibility=degraded")
                print(f"native_harness={candidate['harness']}")
                print("attempt_trace=" + "|".join(attempts))
                print("prior_attempt_ids=" + ",".join(x for values in prior_failures.values() for x in values))
                return 78
        else:
            print("check=degraded")
            print("selected_hop=inline")
            print(f"reason={hop['reason_enum']}")
            print("fleet_visibility=none")
            print("attempt_trace=" + "|".join(attempts))
            print("prior_attempt_ids=" + ",".join(x for values in prior_failures.values() for x in values))
            return 79
    return fail("fallback-chain-exhausted", 79, attempt_trace="|".join(attempts))


if __name__ == "__main__":
    raise SystemExit(main())
