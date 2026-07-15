#!/usr/bin/env python3
"""Execute the checked SD-50 fallback order for one immutable route node."""

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


def request_identity(args: argparse.Namespace, route: dict, node: dict, row: dict, ordinal: int) -> tuple[str, str]:
    payload = {
        "action": args.action,
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
    return "req-" + digest[:32], "att-" + digest[32:]


def broker_envelope(args: argparse.Namespace, route: dict, node: dict, row: dict, ordinal: int) -> dict:
    request_id, attempt_id = request_identity(args, route, node, row, ordinal)
    envelope = {
        "schema_version": 1,
        "request_id": request_id,
        "attempt_id": attempt_id,
        "action": args.action,
        "target_harness": row["child_harness"],
        "worktree": route["cwd"],
        "artifact_root": route["artifact_root"],
        "jobs": str(args.jobs),
        "slug": args.slug,
        "capability": route["capability"],
        "mode": args.mode,
        "intensity": route["effective_intensity"],
        "depth": 2,
        "parent": args.parent,
        "worker_role": args.worker_role or node.get("role", node["id"]),
        "owner": route["capability"],
        "model_role": args.model_role or node.get("role", "fast implementer"),
        "route_file": str(args.route),
        "route_id": route["route_id"],
        "route_hash": route["route_hash"],
        "route_node": node["id"],
        "registry_digest": route["registry_digest"],
        "write_scope": ";".join(node.get("write_scope", [])),
        "completion_gate": node["completion_gate"],
        "parent_harness": row["parent_harness"],
        "parent_transport": row["parent_transport"],
        "parent_sandbox": row["parent_sandbox"],
        "requested_launch_authority": row["launch_authority"],
        "fallback_ordinal": ordinal,
        "probe_source": row["probe_source"],
        "probe_failure_class": row.get("failure_class") or "",
        "broker_root": row["broker_root"],
        "broker_instance": row["broker_instance"],
    }
    optional = {
        "prompt_file": str(args.prompt_file) if args.prompt_file else "",
        "parent_session_id": os.environ.get("AGENT_DISPATCH_PARENT_SESSION_ID", ""),
        "parent_cwd": os.environ.get("AGENT_DISPATCH_PARENT_CWD", ""),
    }
    envelope.update({key: value for key, value in optional.items() if value})
    return envelope


def submit_broker(args: argparse.Namespace, envelope: dict) -> tuple[dict | None, str, str]:
    command = [
        sys.executable,
        str(ROOT / "utilities/dispatch-broker.py"),
        "request",
        "--root",
        str(args.broker_root),
        "--jobs",
        str(args.jobs),
        "--timeout",
        str(args.broker_timeout),
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        input=json.dumps(envelope, ensure_ascii=False),
        capture_output=True,
        check=False,
    )
    try:
        reply = json.loads(result.stdout)
    except json.JSONDecodeError:
        reply = None
    return reply, result.stdout, result.stderr


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
    p.add_argument("--broker-root", type=Path)
    p.add_argument("--broker-timeout", type=float, default=45.0)
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
    inherited_jobs = os.environ.get("AGENT_DISPATCH_JOBS")
    args.jobs = (args.jobs or Path(inherited_jobs or ROOT / ".dispatch/jobs.log")).resolve()
    if inherited_jobs and args.jobs != Path(inherited_jobs).resolve():
        return fail("noncanonical-nested-jobs", 73, explicit=str(args.jobs), inherited=str(Path(inherited_jobs).resolve()))
    if args.action in {"register", "start"} and not inherited_jobs:
        return fail("global-registry-unset", 73, child_spawned="0")
    args.broker_root = (
        args.broker_root
        or Path(os.environ.get("AGENT_DISPATCH_BROKER_ROOT", Path(os.environ.get("AGENT_HOME", ROOT)) / ".dispatch/broker"))
    ).resolve()
    if not os.environ.get("AGENT_DISPATCH_BROKER_INSTANCE"):
        return fail("broker-binding-unset", 76, broker_root=str(args.broker_root), child_spawned="0")
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
                direct_disabled = row.get("launch_authority") != "ancestor-broker"
                if row.get("status") != "supported" or tuple_key in failed_tuples or direct_disabled:
                    skip_reason = (
                        "prior-unchanged-failure" if tuple_key in failed_tuples
                        else "direct-executor-disabled" if direct_disabled
                        else row.get("status")
                    )
                    attempts.append(f"{ordinal}:{tuple_key}:skipped-{skip_reason}")
                    continue
                envelope = broker_envelope(args, route, node, row, ordinal)
                reply, raw_stdout, raw_stderr = submit_broker(args, envelope)
                if not reply or not reply.get("ok"):
                    reason = (reply or {}).get("reason", "broker-unavailable")
                    detail = (reply or {}).get("detail") or raw_stderr.strip() or raw_stdout.strip()
                    return fail(reason, 76, detail=detail, broker_root=str(args.broker_root), child_spawned="0")
                state = reply.get("state", {})
                response = state.get("response", {})
                result_code = int(response.get("returncode", 76))
                output = (str(response.get("stdout", "")) + str(response.get("stderr", ""))).strip()
                attempts.append(f"{ordinal}:{tuple_key}:broker-{response.get('broker_pid', '-')}:exit-{result_code}")
                early = next((line.split("=", 1)[1] for line in output.splitlines() if line.startswith("early_death=")), "-")
                if result_code == 0 and early == "-":
                    print("check=ok")
                    print(f"selected_hop={hop['hop']}")
                    print(f"fallback_ordinal={ordinal}")
                    print(f"child_harness={row['child_harness']}")
                    print("launch_authority=ancestor-broker")
                    print(f"requested_launch_authority={row['launch_authority']}")
                    print(f"broker_root={args.broker_root}")
                    print(f"broker_instance={response.get('broker_instance', '-')}")
                    print(f"broker_pid={response.get('broker_pid', '-')}")
                    print(f"request_id={envelope['request_id']}")
                    print(f"attempt_id={response.get('attempt_id', envelope['attempt_id'])}")
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
