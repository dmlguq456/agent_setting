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
import time

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
        if (not metadata.get("note", "").startswith("dead-")
                or metadata.get("note") == "dead-capacity"):
            continue
        required = ("parent_harness", "parent_transport", "parent_sandbox", "child_harness", "launch_authority")
        if any(not metadata.get(key) for key in required):
            continue
        key = "/".join(metadata[name] for name in required)
        failures.setdefault(key, []).append(metadata.get("attempt_id", "legacy-attempt"))
    return failures


def registry_rows(jobs: Path, route_id: str, node_id: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not jobs.is_file():
        return rows
    for order, line in enumerate(jobs.read_text(encoding="utf-8", errors="replace").splitlines()):
        fields = line.split("\t")
        if len(fields) != 6:
            continue
        metadata = dict(part.split("=", 1) for part in fields[5].split(",") if "=" in part)
        if metadata.get("route_id") != route_id or metadata.get("route_node") != node_id:
            continue
        rows.append({**metadata, "_status": fields[1], "_slug": fields[4], "_order": str(order)})
    return rows


def metadata_tuple_key(metadata: dict[str, str]) -> str:
    required = ("parent_harness", "parent_transport", "parent_sandbox",
                "child_harness", "launch_authority")
    return "/".join(metadata.get(key, "") for key in required)


def capacity_context(jobs: Path, route_id: str, node_id: str) -> dict:
    rows = registry_rows(jobs, route_id, node_id)
    capacity = [row for row in rows if row.get("note") == "dead-capacity"]
    retries = [row for row in rows if row.get("capacity_retry") == "1"]
    cooled = {row.get("model") for row in capacity if row.get("model") not in (None, "", "inherit")}
    cooled.update(row.get("cooled_model") for row in retries
                  if row.get("cooled_model") not in (None, "", "unknown", "inherit"))
    return {"capacity": capacity, "retries": retries, "cooled": cooled}


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


def native_child_proof(args: argparse.Namespace, route: dict, node: dict) -> str:
    """Return the proof source for a real route-owned native child, else ''."""
    if args.native_attempt_id and registry_has_attempt(args.jobs, args.native_attempt_id):
        for line in args.jobs.read_text(encoding="utf-8", errors="replace").splitlines():
            fields = line.split("\t")
            if len(fields) != 6:
                continue
            meta = dict(part.split("=", 1) for part in fields[5].split(",") if "=" in part)
            if (meta.get("attempt_id") == args.native_attempt_id
                    and meta.get("route_id") == route["route_id"]
                    and meta.get("route_node") == node["id"]
                    and meta.get("pid", "").isdigit() and meta.get("pid_start")):
                pid = int(meta["pid"])
                try:
                    actual = (Path("/proc") / str(pid) / "stat").read_text().split()[21]
                except (OSError, IndexError):
                    continue
                if actual == meta["pid_start"]:
                    return "registry-exact-pid"
    if args.native_artifact:
        path = args.native_artifact.resolve()
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            record = {}
        producer = record.get("producer_attempt_id")
        if (record.get("route_id") == route["route_id"]
                and record.get("route_hash") == route["route_hash"]
                and record.get("route_node") == node["id"] and producer):
            for item in registry_rows(args.jobs, route["route_id"], node["id"]):
                if item.get("attempt_id") == producer:
                    return "route-owned-artifact"
    return ""


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


def capacity_attempt_identity(args, route, node, row, ordinal, model):
    payload = {
        "route_id": route["route_id"], "route_node": node["id"], "slug": args.slug,
        "parent": args.parent, "target_harness": row["child_harness"],
        "fallback_ordinal": ordinal, "capacity_retry": 1, "model": model,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return "att-" + digest[:48]


def allowed_capacity_settings(harness: str, model: str, paired: str) -> bool:
    roles = ("deep maker", "deep reviewer", "deep editor", "deep orchestrator",
             "fast implementer", "fast reviewer", "fast fact checker", "fast writer",
             "fast tool worker", "orchestrator", "external adversary")
    mapper = ROOT / f"adapters/{harness}/bin/model-map.sh"
    if not mapper.is_file():
        return False
    for role in roles:
        result = subprocess.run([str(mapper), role], cwd=ROOT, text=True, capture_output=True)
        fields = output_fields(result.stdout)
        if (result.returncode == 0 and fields.get("status", "supported") != "unknown"
                and fields.get("exact_model_id") == model
                and fields.get("reasoning") == paired):
            return True
    return False


def wrapper_command(
    args: argparse.Namespace,
    route: dict,
    node: dict,
    row: dict,
    ordinal: int,
    attempt_id: str,
    capacity_settings: tuple[str, str] | None = None,
    capacity_prior: dict[str, str] | None = None,
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
    if capacity_settings:
        model, paired = capacity_settings
        command += ["--model", model]
        command += [{"codex": "--reasoning", "claude": "--effort", "opencode": "--variant"}[harness], paired]
        if capacity_prior:
            command += [
                "--capacity-retry", "1",
                "--prior-attempt-id", capacity_prior.get("attempt_id", "unknown"),
                "--cooled-model", capacity_prior.get("model", "unknown"),
                "--selection-source", "orchestrator-explicit",
            ]
    else:
        command += ["--model-role", args.model_role or node.get("role", "fast implementer")]
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


def watch_launched_attempt(args, route, node, attempt_id, launch_fields):
    """Synchronously observe one exact attempt for a bounded number of windows."""
    progress = ROOT / "utilities/dispatch-progress.py"
    common = [sys.executable, str(progress), "--attempt-id", attempt_id,
              "--route-id", route["route_id"], "--route-node", node["id"],
              "--jobs", str(args.jobs)]
    seed = subprocess.run(common[:2] + ["heartbeat"] + common[2:] +
        ["--phase", "launch", "--kind", "registry",
         "--evidence", f"pid={launch_fields.get('child_pid', '-')};start={launch_fields.get('child_pid_start', '-')}"],
        cwd=ROOT, text=True, capture_output=True, check=False, env=direct_env())
    if seed.returncode:
        return "fail-closed", output_fields(seed.stdout + seed.stderr)
    def observe():
        result = subprocess.run(common[:2] + ["watchdog"] + common[2:] +
            ["--progress-window-seconds", str(args.progress_window_seconds),
             "--watchdog-max-windows", "2", "--apply"], cwd=ROOT, text=True,
            capture_output=True, check=False, env=direct_env())
        last = output_fields(result.stdout + result.stderr)
        if result.returncode or last.get("action", "").startswith("fail-closed"):
            return "fail-closed", last
        if last.get("terminal_action") == "dead-capacity":
            return "capacity", last
        if last.get("terminal_action") == "dead-no-progress":
            return "fallback", last
        if last.get("terminal_action") in {"process-exited", "registry-terminal"}:
            return "terminal", last
        return "observed", last

    # Establish a file/heartbeat fingerprint before the first deadline. This
    # prevents a write made during the first window from being mistaken for the
    # baseline, and also catches a capacity death that happened just after the
    # wrapper's short early-exit watch.
    state, last = observe()
    if state != "observed":
        return state, last

    window = max(0.1, float(args.progress_window_seconds))
    deadline = time.monotonic() + window * max(1, args.watchdog_max_windows)
    poll = min(1.0, max(0.1, window / 10.0))
    while time.monotonic() < deadline:
        time.sleep(poll)
        state, last = observe()
        if state != "observed":
            return state, last
    return "observed", last


def capacity_pair(args, harness: str) -> str | None:
    return {
        "codex": args.capacity_reasoning,
        "claude": args.capacity_effort,
        "opencode": args.capacity_variant,
    }[harness]


def capacity_retry(
    args: argparse.Namespace,
    route: dict,
    node: dict,
    row: dict,
    ordinal: int,
    failed: dict[str, str],
    attempts: list[str],
) -> tuple[str, dict[str, str], str]:
    """Run or reuse the single canonical SD-59 retry for this route node."""
    context = capacity_context(args.jobs, route["route_id"], node["id"])
    existing = context["retries"]
    if existing:
        retry = existing[-1]
        attempts.append(
            f"{ordinal}:{tuple_key(row)}:capacity-retry-existing:attempt-{retry.get('attempt_id', 'unknown')}"
        )
        if retry.get("_status") in {"open", "running"} or not retry.get("note", "").startswith("dead-"):
            return "existing", retry, ""
        return "descend", retry, "capacity-retry-terminal"

    paired = capacity_pair(args, row["child_harness"])
    failed_model = failed.get("model", "")
    rejected = ""
    if not args.capacity_model or not paired:
        rejected = "capacity-alternative-unpaired"
    elif args.capacity_model in context["cooled"] or args.capacity_model == failed_model:
        rejected = "capacity-alternative-cooled"
    elif not allowed_capacity_settings(row["child_harness"], args.capacity_model, paired):
        rejected = "capacity-alternative-unproved"
    if rejected:
        attempts.append(f"{ordinal}:{tuple_key(row)}:{rejected}")
        return "descend", {}, rejected

    retry_id = capacity_attempt_identity(
        args, route, node, row, ordinal, f"{args.capacity_model}/{paired}"
    )
    retry_command = wrapper_command(
        args, route, node, row, ordinal, retry_id,
        (args.capacity_model, paired), failed,
    )
    try:
        retry = subprocess.run(
            retry_command, cwd=ROOT, text=True, capture_output=True,
            check=False, timeout=args.direct_timeout, env=direct_env(),
        )
    except subprocess.TimeoutExpired:
        if registry_has_attempt(args.jobs, retry_id):
            return "fail-closed", {"attempt_id": retry_id}, "capacity-launch-outcome-unknown"
        return "descend", {}, "capacity-launch-timeout"
    retry_output = (retry.stdout + retry.stderr).strip()
    retry_fields = output_fields(retry_output)
    attempts.append(
        f"{ordinal}:{tuple_key(row)}:capacity-retry:exit-{retry.returncode}:attempt-{retry_id}"
    )
    if retry_fields.get("duplicate_attempt") == "1":
        refreshed = capacity_context(args.jobs, route["route_id"], node["id"])["retries"]
        if refreshed:
            return "existing", refreshed[-1], retry_output
        return "fail-closed", retry_fields, "capacity-exclusive-claim-lost"
    if (retry.returncode == 0 and retry_fields.get("early_death", "-") == "-"
            and retry_fields.get("check") != "failed"):
        if args.action == "start":
            watch_state, watch_fields = watch_launched_attempt(
                args, route, node, retry_id, retry_fields
            )
            attempts.append(f"{ordinal}:{tuple_key(row)}:capacity-watchdog-{watch_state}")
            if watch_state == "fallback":
                return "descend", watch_fields, retry_output
            if watch_state == "capacity":
                return "descend", watch_fields, retry_output
            if watch_state == "fail-closed":
                return "fail-closed", watch_fields, "capacity-watchdog-fail-closed"
        return "success", {**retry_fields, "attempt_id": retry_id}, retry_output
    # The wrapper already closed a second capacity death. Exactly one retry
    # has now been consumed; ordinary SD-50 descent owns the next action.
    return "descend", retry_fields, retry_output


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
    p.add_argument("--progress-window-seconds", type=float, default=300.0)
    p.add_argument("--watchdog-max-windows", type=int, default=12)
    p.add_argument("--native-attempt-id")
    p.add_argument("--native-artifact", type=Path)
    p.add_argument("--capacity-model")
    p.add_argument("--capacity-reasoning")
    p.add_argument("--capacity-effort")
    p.add_argument("--capacity-variant")
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
                pending_capacity = [
                    item for item in capacity_context(
                        args.jobs, route["route_id"], node["id"]
                    )["capacity"]
                    if item.get("capacity_retry") != "1"
                    and metadata_tuple_key(item) == key
                ]
                if pending_capacity:
                    retry_state, retry_fields, retry_output = capacity_retry(
                        args, route, node, row, ordinal, pending_capacity[-1], attempts
                    )
                    if retry_state in {"success", "existing"}:
                        print("check=ok")
                        print(f"selected_hop={hop['hop']}")
                        print(f"fallback_ordinal={ordinal}")
                        print(f"child_harness={row['child_harness']}")
                        print("capacity_retry=1")
                        print(f"cooled_model={pending_capacity[-1].get('model', 'unknown')}")
                        print(f"selected_model={retry_fields.get('model', args.capacity_model or 'existing')}")
                        print(f"attempt_id={retry_fields.get('attempt_id', 'existing')}")
                        print("attempt_trace=" + "|".join(attempts))
                        if retry_output:
                            print(retry_output)
                        return 0
                    if retry_state == "fail-closed":
                        return fail(
                            retry_output or "capacity-retry-fail-closed", 76,
                            attempt_trace="|".join(attempts),
                        )
                    failed_tuples.add(key)
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
                    if args.action == "start":
                        watch_state, watch_fields = watch_launched_attempt(
                            args, route, node, attempt_id, fields)
                        attempts.append(f"{ordinal}:{key}:watchdog-{watch_state}")
                        if watch_state == "fallback":
                            failed_tuples.add(key)
                            continue
                        if watch_state == "capacity":
                            early = "capacity"
                            fields = {**fields, **watch_fields, "early_death": "capacity"}
                        if watch_state == "fail-closed":
                            return fail("progress-watchdog-fail-closed", 76,
                                        attempt_id=attempt_id,
                                        watchdog_action=watch_fields.get("action", "unknown"),
                                        attempt_trace="|".join(attempts))
                    if early != "capacity":
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
                if early == "capacity":
                    failed = {
                        **fields, "attempt_id": attempt_id,
                        "model": fields.get("model", "unknown"),
                    }
                    retry_state, retry_fields, retry_output = capacity_retry(
                        args, route, node, row, ordinal, failed, attempts
                    )
                    if retry_state in {"success", "existing"}:
                        print("check=ok")
                        print(f"selected_hop={hop['hop']}")
                        print(f"fallback_ordinal={ordinal}")
                        print(f"child_harness={row['child_harness']}")
                        print("capacity_retry=1")
                        print(f"cooled_model={failed['model']}")
                        print(f"selected_model={retry_fields.get('model', args.capacity_model or 'existing')}")
                        print(f"attempt_id={retry_fields.get('attempt_id', 'existing')}")
                        print("attempt_trace=" + "|".join(attempts))
                        if retry_output:
                            print(retry_output)
                        return 0
                    if retry_state == "fail-closed":
                        return fail(
                            retry_output or "capacity-retry-fail-closed", 76,
                            attempt_trace="|".join(attempts),
                        )
                    failed_tuples.add(key)
                    # Exactly one retry. A second capacity death descends through SD-50.
        elif hop["hop"] == "native-subagent":
            candidate = next((row for row in hop.get("candidates", []) if row.get("status") == "supported"), None)
            if candidate:
                proof = native_child_proof(args, route, node)
                if proof:
                    print("check=degraded")
                    print("selected_hop=native-subagent")
                    print("fleet_visibility=degraded")
                    print(f"native_harness={candidate['harness']}")
                    print(f"child_proof={proof}")
                    print("attempt_trace=" + "|".join(attempts))
                    print("prior_attempt_ids=" + ",".join(x for values in prior_failures.values() for x in values))
                    return 78
                attempts.append(f"{ordinal}:native-subagent:skipped-child-proof-missing")
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
