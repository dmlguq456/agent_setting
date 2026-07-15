#!/usr/bin/env python3
"""Execute the checked SD-50 fallback order for one immutable route node."""

from __future__ import annotations

import argparse
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


def wrapper_command(harness: str) -> list[str]:
    if harness == "claude":
        return [sys.executable, str(ROOT / "adapters/claude/bin/dispatch-headless.py")]
    if harness in {"codex", "opencode"}:
        return [str(ROOT / f"adapters/{harness}/bin/preflight.sh"), "dispatch"]
    raise ValueError(f"unsupported child harness: {harness}")


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


def headless_command(args: argparse.Namespace, route: dict, node: dict, row: dict, ordinal: int) -> list[str]:
    command = wrapper_command(row["child_harness"])
    command += [
        f"--{args.action}",
        "--worktree", route["cwd"],
        "--slug", args.slug,
        "--capability", route["capability"],
        "--mode", args.mode,
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
        "--parent-harness", row["parent_harness"],
        "--parent-transport", row["parent_transport"],
        "--parent-sandbox", row["parent_sandbox"],
        "--launch-authority", row["launch_authority"],
        "--nested-eligibility", row["status"],
        "--eligibility-source", row["probe_source"],
        "--eligibility-failure-class", row.get("failure_class") or "-",
        "--fallback-ordinal", str(ordinal),
    ]
    if args.prompt_file:
        command += ["--prompt-file", str(args.prompt_file)]
    return command


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--route", type=Path, required=True)
    p.add_argument("--node", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--parent", required=True)
    p.add_argument("--mode", required=True)
    p.add_argument("--worker-role")
    p.add_argument("--model-role")
    p.add_argument("--prompt-file", type=Path)
    p.add_argument("--jobs", type=Path)
    p.add_argument("--failed-tuple", action="append", default=[], help="tuple key already failed without evidence change")
    action = p.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", dest="action", action="store_const", const="dry-run")
    action.add_argument("--register", dest="action", action="store_const", const="register")
    action.add_argument("--start", dest="action", action="store_const", const="start")
    args = p.parse_args()
    try:
        route, node = load_node(args.route.resolve(), args.node)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return fail("invalid-fallback-route", 65, detail=str(exc))
    args.jobs = (args.jobs or Path(os.environ.get("AGENT_DISPATCH_JOBS", ROOT / ".dispatch/jobs.log"))).resolve()
    env = {**os.environ, "AGENT_DISPATCH_JOBS": str(args.jobs)}
    prior_failures = registry_failures(args.jobs, route["route_id"], node["id"])
    failed_tuples = set(args.failed_tuple) | set(prior_failures)
    attempts: list[str] = []
    for hop in node["dispatch_fallback"]:
        ordinal = int(hop["ordinal"])
        if hop["hop"] in {"same-harness-headless", "cross-harness-headless"}:
            for row in hop.get("candidates", []):
                tuple_key = "/".join(str(row[key]) for key in (
                    "parent_harness", "parent_transport", "parent_sandbox", "child_harness", "launch_authority"
                ))
                if row.get("status") != "supported" or tuple_key in failed_tuples:
                    skip_reason = "prior-unchanged-failure" if tuple_key in failed_tuples else row.get("status")
                    attempts.append(f"{ordinal}:{tuple_key}:skipped-{skip_reason}")
                    continue
                command = headless_command(args, route, node, row, ordinal)
                result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False)
                output = (result.stdout + result.stderr).strip()
                attempts.append(f"{ordinal}:{tuple_key}:exit-{result.returncode}")
                early = next((line.split("=", 1)[1] for line in output.splitlines() if line.startswith("early_death=")), "-")
                if result.returncode == 0 and early == "-":
                    print("check=ok")
                    print(f"selected_hop={hop['hop']}")
                    print(f"fallback_ordinal={ordinal}")
                    print(f"child_harness={row['child_harness']}")
                    print(f"launch_authority={row['launch_authority']}")
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
