#!/usr/bin/env python3
"""Portable continuation supervisor for tracked workflows.

One implementation serves every capability (`core/OPERATIONS.md §5.12`). It is a
non-model process: it starts only the successor its sealed route already declares, it
opens no dispatch depth, and it never decides *what* work to do — only whether the
declared next stage may start yet.

Advance requires four independent proofs about the predecessor — exact process
identity, a terminal result, a sentinel or typed terminal handoff, and the declared
output artifacts — and it is claimed exactly once through the filesystem. Anything
missing is a refusal, not an assumption: the 2026-08-04 BC_ResNet_tf run finished
training and nothing owned what came next, so "the process is gone" must never be
read as "the stage succeeded".

  workflow-supervisor.py arm     --route R --node N --predecessor-kind resource|registered ...
  workflow-supervisor.py poll    --route R
  workflow-supervisor.py watch   --route R --max 3600
  workflow-supervisor.py gate    --route R --gate G --release|--block
  workflow-supervisor.py status  --route R [--json]
  workflow-supervisor.py complete --route R
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "utilities"))

import workflow_state as WS  # noqa: E402
import resource_run_registry as RR  # noqa: E402

ARMED_SCHEMA_VERSION = 1
PREDECESSOR_KINDS = ("resource", "registered")
DEFAULT_POLL_INTERVAL = 5.0
MAX_WATCH_SECONDS = 86400.0


class SupervisorError(ValueError):
    pass


def _load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


_RUNNER = None


def runner():
    """Load `resource-runner.py` (dashed name) for its shared settle/sentinel logic."""
    global _RUNNER
    if _RUNNER is None:
        _RUNNER = _load_module("resource_runner_cli", "utilities/resource-runner.py")
    return _RUNNER


def load_route(path):
    try:
        route = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SupervisorError(f"route unreadable: {exc}") from exc
    if not isinstance(route, dict) or "route_id" not in route or "nodes" not in route:
        raise SupervisorError("route record is not a compiled capability route")
    return route


def ledger_for(route):
    return WS.WorkflowLedger(route["route_id"], route.get("route_hash", ""))


def armed_dir(ledger):
    return ledger.root / "armed"


def read_armed(ledger):
    rows = {}
    directory = armed_dir(ledger)
    if not directory.is_dir():
        return rows
    for path in sorted(directory.glob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(row, dict) and row.get("node"):
            rows[row["node"]] = row
    return rows


# --------------------------------------------------------------------------------
# predecessor evidence
# --------------------------------------------------------------------------------

def resource_evidence(armed):
    """Terminal evidence for a detached resource child, settled if it is gone."""
    registry = Path(armed["resource_registry"])
    run_id = armed["predecessor_id"]
    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
        row = (data.get("runs") or {}).get(run_id)
    except (OSError, ValueError) as exc:
        return {"terminal": False, "reason": f"resource-registry-unreadable:{exc}"}
    if not isinstance(row, dict):
        return {"terminal": False, "reason": "resource-run-absent"}
    row, _settled = runner().settle(registry, run_id, row)
    liveness, _current, reason = RR.classify_identity(row)
    identity = f"{run_id}:{row.get('pid')}:{row.get('starttime')}:{row.get('exit_code')}"
    if liveness == "working":
        return {"terminal": False, "reason": "resource-still-running", "liveness": liveness,
                "identity": identity}
    status = row.get("status")
    if status not in ("succeeded", "failed"):
        # Gone but unsettled means the observation could not be persisted; refuse.
        return {"terminal": False, "reason": f"resource-unsettled:{status}", "liveness": liveness,
                "identity": identity}
    return {
        "terminal": True,
        "succeeded": status == "succeeded",
        "identity": identity,
        "liveness": liveness,
        "exit_code": row.get("exit_code"),
        "sentinel": row.get("sentinel"),
        "sentinel_present": bool(row.get("sentinel")) and Path(str(row["sentinel"])).is_file(),
        "ended_at": row.get("ended_at"),
        "failure_class": row.get("failure_class"),
        "reason": reason,
        "log": row.get("log"),
        "parent_attempt_id": row.get("parent_attempt_id"),
    }


def _registry_rows(jobs_path):
    try:
        raw = Path(jobs_path).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise SupervisorError(f"jobs registry unreadable: {exc}") from exc
    rows = []
    for line in raw.splitlines():
        fields = line.split("\t")
        if len(fields) != 6:
            continue
        metadata = dict(
            part.split("=", 1) for part in fields[5].split(",") if "=" in part
        )
        rows.append({"time": fields[0], "status": fields[1], "repo": fields[2],
                     "worktree": fields[3], "slug": fields[4], "meta": metadata})
    return rows


def registered_evidence(armed):
    """Terminal evidence for a registered headless attempt."""
    attempt_id = armed["predecessor_id"]
    try:
        rows = _registry_rows(armed["jobs"])
    except SupervisorError as exc:
        return {"terminal": False, "reason": str(exc)}
    matches = [row for row in rows if row["meta"].get("attempt_id") == attempt_id]
    if not matches:
        return {"terminal": False, "reason": "attempt-row-absent"}
    row = matches[-1]
    meta = row["meta"]
    identity = f"{attempt_id}:{meta.get('pid')}:{meta.get('pid_start')}:{row['status']}"
    if row["status"] != "done":
        return {"terminal": False, "reason": f"attempt-open:{row['status']}",
                "identity": identity}
    note = meta.get("note") or ""
    failure_class = meta.get("failure_class") or ""
    succeeded = (
        note in ("completed-marker", "completed-supervisor", "completed")
        and failure_class in ("", "pass")
    )
    # A live exact PID after a terminal row is draining, not quiescent: the successor
    # must not start while the predecessor's process group still holds resources.
    quiescent = True
    pid, pid_start = meta.get("pid"), meta.get("pid_start")
    if pid and pid_start:
        current = RR.proc_identity(pid)
        if current and str(current["starttime"]) == str(pid_start):
            quiescent = False
    return {
        "terminal": True,
        "succeeded": succeeded,
        "quiescent": quiescent,
        "identity": identity,
        "note": note,
        "failure_class": failure_class,
        "reason": "attempt-terminal",
    }


def artifact_evidence(armed):
    """Declared outputs must actually exist before a successor may consume them.

    Only concrete declared names are checked. A glob (`logs/**`) and an abstract
    handoff name are deliberately not invented into paths — an unverifiable check that
    silently passes is worse than a recorded `checked: false`.
    """
    base = armed.get("artifact_base")
    concrete = [name for name in (armed.get("declared_outputs") or [])
                if isinstance(name, str) and "*" not in name and "/" not in name and "." in name]
    if not base:
        return {"checked": False, "reason": "no-artifact-base", "missing": []}
    if not concrete:
        return {"checked": False, "reason": "no-concrete-declared-output", "missing": []}
    missing = [name for name in concrete if not (Path(base) / name).exists()]
    return {"checked": True, "missing": missing, "reason": "artifacts-present" if not missing
            else "declared-artifact-missing"}


# --------------------------------------------------------------------------------
# completion markers
# --------------------------------------------------------------------------------

def completion_dir(route):
    home = os.environ.get("AGENT_HOME")
    base = Path(home).expanduser() if home else ROOT
    return base / ".dispatch" / "completion" / route["route_id"]


def terminal_gate_state(route):
    """Report, per terminal node, whether its completion gate is actually proven."""
    rows = {}
    for node_id in WS.route_terminal_nodes(route):
        node = WS.route_node(route, node_id) or {}
        path = completion_dir(route) / f"{node_id}.json"
        try:
            marker = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            rows[node_id] = {"passed": False, "reason": "completion-marker-absent"}
            continue
        if (marker.get("route_id") != route["route_id"]
                or marker.get("route_hash") != route.get("route_hash")
                or marker.get("node_id") != node_id
                or marker.get("completion_gate") != node.get("terminal_gate")):
            rows[node_id] = {"passed": False, "reason": "completion-marker-identity-mismatch"}
            continue
        evidence = marker.get("evidence") or {}
        try:
            digest = hashlib.sha256(Path(evidence["path"]).read_bytes()).hexdigest()
        except (OSError, KeyError, TypeError):
            rows[node_id] = {"passed": False, "reason": "completion-evidence-unreadable"}
            continue
        if digest != evidence.get("sha256"):
            rows[node_id] = {"passed": False, "reason": "completion-evidence-hash-mismatch"}
            continue
        rows[node_id] = {"passed": True, "reason": "completion-marker-verified",
                         "evidence": evidence.get("path")}
    return rows


# --------------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------------

def cmd_arm(args):
    route = load_route(args.route)
    node = WS.route_node(route, args.node)
    if node is None:
        raise SupervisorError(f"unknown route node: {args.node}")
    continuation = node.get("continuation")
    if not isinstance(continuation, dict):
        raise SupervisorError(
            f"node {args.node} is terminal or declares no continuation; nothing to supervise"
        )
    kind = continuation["kind"]
    if kind not in ("supervised", "monitor"):
        raise SupervisorError(
            f"node {args.node} declares continuation {kind}; a supervisor governs only "
            "supervised and monitor continuations"
        )
    if args.predecessor_kind not in PREDECESSOR_KINDS:
        raise SupervisorError("invalid predecessor kind")
    if args.predecessor_kind == "resource" and not args.resource_registry:
        raise SupervisorError("--resource-registry is required for a resource predecessor")
    if args.predecessor_kind == "registered" and not args.jobs:
        raise SupervisorError("--jobs is required for a registered predecessor")
    successors = WS.route_successors(route, args.node)
    if not successors:
        raise SupervisorError(f"node {args.node} has no declared successor")
    command = None
    if args.successor_command:
        try:
            command = json.loads(args.successor_command)
        except ValueError as exc:
            raise SupervisorError(f"--successor-command must be a JSON argv array: {exc}")
        if not isinstance(command, list) or not command or not all(
                isinstance(part, str) for part in command):
            raise SupervisorError("--successor-command must be a non-empty JSON array of strings")
    elif not args.successor_external:
        # An armed watch with no way to start the next stage is the failure this tool
        # exists to prevent, so the caller must say so out loud.
        raise SupervisorError(
            "supervised continuation requires --successor-command, or an explicit "
            "--successor-external declaring that another checked surface starts it"
        )
    if kind == "monitor" and not args.monitor_evidence:
        raise SupervisorError("monitor continuation requires --monitor-evidence")
    record = {
        "schema_version": ARMED_SCHEMA_VERSION,
        "route_id": route["route_id"],
        "route_hash": route.get("route_hash"),
        "route_file": str(Path(args.route).resolve()),
        "node": args.node,
        "continuation_kind": kind,
        "monitor": continuation.get("monitor"),
        "monitor_evidence": args.monitor_evidence,
        "predecessor_kind": args.predecessor_kind,
        "predecessor_id": args.predecessor_id,
        "resource_registry": str(Path(args.resource_registry).resolve())
        if args.resource_registry else None,
        "jobs": str(Path(args.jobs).resolve()) if args.jobs else None,
        "successors": successors,
        "successor_command": command,
        "successor_external": bool(args.successor_external),
        "successor_cwd": args.successor_cwd or route.get("cwd"),
        "successor_log": args.successor_log,
        "artifact_base": str(Path(args.artifact_base).resolve()) if args.artifact_base else None,
        "declared_outputs": list(node.get("outputs") or []),
        "armed_at": WS.now_iso(),
    }
    ledger = ledger_for(route)
    with ledger.lock():
        armed_dir(ledger).mkdir(parents=True, exist_ok=True)
        target = armed_dir(ledger) / f"{args.node}.json"
        target.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        state = ledger.state()
        if state["workflow_state"] == "CREATED":
            ledger.set_workflow_state("READY", evidence={"armed": args.node}, actor="arm")
        if args.node not in state["nodes"]:
            ledger.record(args.node, "RUNNING", evidence={"armed": True}, actor="arm")
        # A watch is armed on a stage that is already executing, so the workflow is
        # RUNNING from this point; leaving it READY would make the first legitimate
        # failure an illegal transition.
        if ledger.state()["workflow_state"] == "READY":
            ledger.set_workflow_state("RUNNING", evidence={"armed": args.node}, actor="arm")
    print(json.dumps({"armed": args.node, "successors": successors,
                      "continuation": kind}, sort_keys=True))
    return 0


def _start_successor(armed, successor, key):
    command = armed.get("successor_command")
    if not command:
        return {"started": False, "surface": "external",
                "reason": "successor start is owned by a declared external checked surface"}
    log_path = armed.get("successor_log")
    stdout = None
    handle = None
    if log_path:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        handle = open(log_path, "ab", buffering=0)
        stdout = handle
    try:
        environment = {
            **os.environ,
            "AGENT_WORKFLOW_ROUTE_ID": armed["route_id"],
            "AGENT_WORKFLOW_NODE": successor,
            "AGENT_WORKFLOW_CLAIM": key,
        }
        proc = subprocess.Popen(
            command, cwd=armed.get("successor_cwd") or None, env=environment,
            stdout=stdout, stderr=subprocess.STDOUT if stdout else None,
            start_new_session=True,
        )
    finally:
        if handle is not None:
            handle.close()
    identity = RR.proc_identity(proc.pid) or {}
    return {"started": True, "surface": "detached", "pid": proc.pid,
            "starttime": identity.get("starttime"), "command": command,
            "log": log_path}


def _evaluate(route, ledger, armed, results):
    node_id = armed["node"]
    kind = armed["continuation_kind"]
    if armed["predecessor_kind"] == "resource":
        evidence = resource_evidence(armed)
    else:
        evidence = registered_evidence(armed)
    artifacts = artifact_evidence(armed)
    evidence["artifacts"] = artifacts
    row = {"node": node_id, "evidence": evidence}

    if not evidence.get("terminal"):
        row["action"] = "wait"
        results.append(row)
        return
    if evidence.get("quiescent") is False:
        row["action"] = "wait-draining"
        results.append(row)
        return
    if not evidence.get("succeeded"):
        ledger.record(node_id, "FAILED_RETRYABLE", evidence=evidence, actor="poll")
        ledger.set_workflow_state("FAILED_RETRYABLE", evidence={"node": node_id}, actor="poll")
        row["action"] = "halt-failed"
        results.append(row)
        return
    if artifacts.get("checked") and artifacts.get("missing"):
        ledger.record(node_id, "FAILED_RETRYABLE", evidence=evidence, actor="poll")
        ledger.set_workflow_state("FAILED_RETRYABLE", evidence={"node": node_id}, actor="poll")
        row["action"] = "halt-missing-artifact"
        results.append(row)
        return
    if kind == "monitor":
        matched = False
        try:
            monitor = json.loads(Path(armed["monitor_evidence"]).read_text(encoding="utf-8"))
            matched = monitor.get("condition") == "matched"
        except (OSError, ValueError, AttributeError, TypeError):
            matched = False
        if not matched:
            row["action"] = "wait-monitor"
            results.append(row)
            return
        evidence["monitor"] = "matched"

    ledger.record(node_id, "STAGE_SUCCEEDED", evidence=evidence, actor="poll")
    started = []
    for successor in armed["successors"]:
        key = WS.successor_key(route.get("route_hash", ""), node_id,
                               str(evidence.get("identity")), successor)
        created, claim = ledger.claim(key, {
            "route_id": route["route_id"], "predecessor": node_id, "successor": successor,
            "predecessor_identity": evidence.get("identity"),
        })
        if not created:
            started.append({"successor": successor, "claim": key, "created": False,
                            "note": "already claimed", "claim_record": claim})
            continue
        outcome = _start_successor(armed, successor, key)
        started.append({"successor": successor, "claim": key, "created": True, **outcome})
    row["action"] = "advanced"
    row["successors"] = started
    if any(entry.get("created") for entry in started):
        current = ledger.state()["workflow_state"]
        if WS.can_transition(current, "NEXT_REGISTERED"):
            ledger.set_workflow_state("NEXT_REGISTERED",
                                      evidence={"node": node_id, "successors": armed["successors"]},
                                      actor="poll")
        if any(entry.get("started") for entry in started):
            current = ledger.state()["workflow_state"]
            if WS.can_transition(current, "NEXT_RUNNING"):
                ledger.set_workflow_state("NEXT_RUNNING", evidence={"node": node_id},
                                          actor="poll")
    results.append(row)


def poll_once(route, ledger):
    results = []
    with ledger.lock():
        for node_id, armed in sorted(read_armed(ledger).items()):
            state = ledger.state()["nodes"].get(node_id, {}).get("state")
            if state in ("STAGE_SUCCEEDED", "FAILED_TERMINAL", "CANCELLED"):
                results.append({"node": node_id, "action": "settled", "state": state})
                continue
            if state == "FAILED_RETRYABLE":
                results.append({"node": node_id, "action": "halted", "state": state})
                continue
            if armed["continuation_kind"] == "human-gate":
                results.append({"node": node_id, "action": "human-gate"})
                continue
            _evaluate(route, ledger, armed, results)
    return results


def cmd_poll(args):
    route = load_route(args.route)
    ledger = ledger_for(route)
    results = poll_once(route, ledger)
    print(json.dumps({"route_id": route["route_id"],
                      "workflow_state": ledger.state()["workflow_state"],
                      "results": results}, sort_keys=True))
    return 0


def cmd_watch(args):
    route = load_route(args.route)
    ledger = ledger_for(route)
    interval = max(1.0, float(args.interval))
    deadline = time.monotonic() + min(max(1.0, float(args.max)), MAX_WATCH_SECONDS)
    last = []
    while True:
        last = poll_once(route, ledger)
        state = ledger.state()["workflow_state"]
        if state in ("COMPLETE", "TERMINAL_VERIFY", "FAILED_TERMINAL", "FAILED_RETRYABLE",
                     "CANCELLED", "BLOCKED_HUMAN_GATE"):
            break
        if all(row.get("action") in ("advanced", "settled", "halted", "human-gate")
               for row in last) and last:
            break
        if time.monotonic() >= deadline:
            print(json.dumps({"route_id": route["route_id"], "timeout": True,
                              "workflow_state": state, "results": last}, sort_keys=True))
            return 3
        time.sleep(interval)
    print(json.dumps({"route_id": route["route_id"], "timeout": False,
                      "workflow_state": ledger.state()["workflow_state"],
                      "results": last}, sort_keys=True))
    return 0


def cmd_gate(args):
    route = load_route(args.route)
    ledger = ledger_for(route)
    gates = {row["gate"]: row for row in (route.get("human_gate_bindings") or [])}
    if args.gate not in gates:
        raise SupervisorError(f"route declares no human gate {args.gate!r}")
    with ledger.lock():
        if args.release:
            state = ledger.state()["workflow_state"]
            if state != "BLOCKED_HUMAN_GATE":
                raise SupervisorError(f"workflow is {state}, not blocked on a human gate")
            ledger.set_workflow_state("RUNNING", evidence={"released_gate": args.gate,
                                                           "released_by": args.by or "user"},
                                      actor="gate")
            action = "released"
        else:
            ledger.set_workflow_state("BLOCKED_HUMAN_GATE",
                                      evidence={"gate": args.gate,
                                                "binding": gates[args.gate]}, actor="gate")
            action = "blocked"
    print(json.dumps({"gate": args.gate, "action": action,
                      "workflow_state": ledger.state()["workflow_state"]}, sort_keys=True))
    return 0


def resource_children(route, ledger):
    """Child resource jobs of this route, from the shared resource-run global index.

    A resource row belongs to this workflow when an armed watch names its run id, or
    when the row's own `route` record resolves to this route id. Visibility is a
    requirement, so an unreadable index degrades to the armed set rather than to
    silence.
    """
    armed_runs, armed_registries = set(), set()
    for armed in read_armed(ledger).values():
        if armed.get("predecessor_kind") == "resource":
            if armed.get("predecessor_id"):
                armed_runs.add(armed["predecessor_id"])
            if armed.get("resource_registry"):
                armed_registries.add(armed["resource_registry"])
    try:
        rows, _diagnostics = RR.scan()
    except Exception:
        rows = []
    unique = {}
    for row in rows:
        run_id = row.get("run_id")
        owned = run_id in armed_runs
        if not owned and str(row.get("registry_path")) in armed_registries:
            owned = True
        if not owned and row.get("route"):
            try:
                owned = json.loads(
                    Path(str(row["route"])).read_text(encoding="utf-8")
                ).get("route_id") == route["route_id"]
            except (OSError, ValueError):
                owned = False
        if owned:
            unique[run_id] = row
    # A child the global index has not seen yet is still this workflow's child: read it
    # from the registry the armed watch already names, so the fallback carries real
    # identity instead of the word "unknown".
    for armed in read_armed(ledger).values():
        run_id = armed.get("predecessor_id")
        if (armed.get("predecessor_kind") != "resource" or run_id in unique
                or not armed.get("resource_registry")):
            continue
        registry = Path(armed["resource_registry"])
        try:
            row = (json.loads(registry.read_text(encoding="utf-8")).get("runs")
                   or {}).get(run_id)
            unique[run_id] = RR.normalize_run(run_id, row, registry)
            unique[run_id]["index_state"] = "registry-direct"
        except Exception:
            unique[run_id] = {"run_id": run_id, "liveness": "unknown",
                              "registry_path": str(registry),
                              "state_evidence": {"reason": "resource-registry-unreadable"}}
    for run_id in sorted(armed_runs - set(unique)):
        unique[run_id] = {"run_id": run_id, "liveness": "unknown",
                          "state_evidence": {"reason": "not-in-resource-run-index"}}
    return [unique[key] for key in sorted(unique)]


def cmd_status(args):
    route = load_route(args.route)
    ledger = ledger_for(route)
    state = ledger.state()
    armed = read_armed(ledger)
    terminal_nodes = WS.route_terminal_nodes(route)
    gates = terminal_gate_state(route)
    node_states = state["nodes"]
    running = [node for node, row in node_states.items() if row.get("state") == "RUNNING"]
    failed = {node: row for node, row in node_states.items()
              if str(row.get("state", "")).startswith("FAILED")}
    next_stage = sorted({successor
                         for node, row in node_states.items()
                         if row.get("state") == "STAGE_SUCCEEDED"
                         for successor in WS.route_successors(route, node)
                         if node_states.get(successor, {}).get("state") != "STAGE_SUCCEEDED"})
    if not next_stage:
        satisfied = {node for node, row in node_states.items()
                     if row.get("state") == "STAGE_SUCCEEDED"}
        next_stage = sorted({
            node["id"] for node in route.get("nodes", [])
            if node["id"] not in node_states
            and set(node.get("depends_on") or []) <= satisfied
        })
    derived = WS.derive_workflow_state(
        node_states, terminal_nodes,
        terminal_gates_passed=bool(gates) and all(row["passed"] for row in gates.values()),
        pending_claims=len(ledger.claims()),
    )
    payload = {
        "route_id": route["route_id"],
        "route_file": str(Path(args.route).resolve()),
        "capability": route.get("capability"),
        "capability_mode": route.get("capability_mode"),
        "effective_intensity": route.get("effective_intensity"),
        "workflow_state": state["workflow_state"],
        "derived_workflow_state": derived,
        "updated_at": state["updated_at"],
        "current_stage": sorted(running),
        "next_stage": next_stage,
        "terminal_nodes": terminal_nodes,
        "terminal_gates": gates,
        "human_gate_bindings": route.get("human_gate_bindings") or [],
        "failure_reason": {node: row.get("evidence", {}).get("reason")
                           for node, row in failed.items()} or None,
        "nodes": node_states,
        "armed": {node: {"kind": row.get("continuation_kind"),
                         "predecessor_kind": row.get("predecessor_kind"),
                         "predecessor_id": row.get("predecessor_id"),
                         "successors": row.get("successors"),
                         "successor_external": row.get("successor_external")}
                  for node, row in armed.items()},
        "claims": ledger.claims(),
        "resource_children": resource_children(route, ledger),
        "ledger_root": str(ledger.root),
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True, indent=2))
    else:
        print(f"route      {payload['route_id']} ({payload['capability']}/"
              f"{payload['capability_mode']} {payload['effective_intensity']})")
        print(f"workflow   {payload['workflow_state']} (derived {derived})")
        print(f"stage      current={payload['current_stage'] or '-'} "
              f"next={payload['next_stage'] or '-'}")
        print(f"terminal   {terminal_nodes} gates="
              f"{ {k: v['passed'] for k, v in gates.items()} }")
        for child in payload["resource_children"]:
            print(f"resource   {child.get('run_id')} {child.get('liveness')} "
                  f"class={child.get('resource_class')} log={child.get('log_path')}")
        if payload["failure_reason"]:
            print(f"failure    {payload['failure_reason']}")
    return 0


def cmd_complete(args):
    route = load_route(args.route)
    ledger = ledger_for(route)
    terminal_nodes = WS.route_terminal_nodes(route)
    if not terminal_nodes:
        raise SupervisorError("route declares no terminal node")
    gates = terminal_gate_state(route)
    unproven = {node: row for node, row in gates.items() if not row["passed"]}
    with ledger.lock():
        state = ledger.state()
        if unproven:
            print(json.dumps({"complete": False, "reason": "terminal-gate-unproven",
                              "unproven": unproven,
                              "workflow_state": state["workflow_state"]}, sort_keys=True))
            return 3
        for node in terminal_nodes:
            if state["nodes"].get(node, {}).get("state") != "STAGE_SUCCEEDED":
                ledger.record(node, "STAGE_SUCCEEDED",
                              evidence={"terminal_gate": gates[node]}, actor="complete")
        if ledger.state()["workflow_state"] != "TERMINAL_VERIFY":
            ledger.set_workflow_state("TERMINAL_VERIFY", evidence={"terminal_gates": gates},
                                      actor="complete")
        ledger.set_workflow_state("COMPLETE", evidence={"terminal_gates": gates},
                                  actor="complete")
    print(json.dumps({"complete": True, "terminal_nodes": terminal_nodes,
                      "workflow_state": ledger.state()["workflow_state"]}, sort_keys=True))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="workflow-supervisor")
    sub = parser.add_subparsers(dest="command", required=True)

    arm = sub.add_parser("arm", help="register a continuation watch for one node")
    arm.add_argument("--route", required=True)
    arm.add_argument("--node", required=True)
    arm.add_argument("--predecessor-kind", required=True, choices=PREDECESSOR_KINDS)
    arm.add_argument("--predecessor-id", required=True)
    arm.add_argument("--resource-registry")
    arm.add_argument("--jobs")
    arm.add_argument("--successor-command", help="JSON argv array that starts the next stage")
    arm.add_argument("--successor-external", action="store_true",
                     help="another checked surface owns the successor start; recorded explicitly")
    arm.add_argument("--successor-cwd")
    arm.add_argument("--successor-log")
    arm.add_argument("--artifact-base", help="directory the node's declared outputs live under")
    arm.add_argument("--monitor-evidence")

    poll = sub.add_parser("poll", help="evaluate every armed watch once")
    poll.add_argument("--route", required=True)

    watch = sub.add_parser("watch", help="poll until terminal or the bounded deadline")
    watch.add_argument("--route", required=True)
    watch.add_argument("--max", type=float, default=3600.0)
    watch.add_argument("--interval", type=float, default=DEFAULT_POLL_INTERVAL)

    gate = sub.add_parser("gate", help="record or release a declared human gate")
    gate.add_argument("--route", required=True)
    gate.add_argument("--gate", required=True)
    gate.add_argument("--by")
    group = gate.add_mutually_exclusive_group(required=True)
    group.add_argument("--release", action="store_true")
    group.add_argument("--block", action="store_true")

    status = sub.add_parser("status", help="portable workflow/stage/resource projection")
    status.add_argument("--route", required=True)
    status.add_argument("--json", action="store_true")

    complete = sub.add_parser("complete", help="verify terminal gates, then close the workflow")
    complete.add_argument("--route", required=True)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    handler = {
        "arm": cmd_arm, "poll": cmd_poll, "watch": cmd_watch, "gate": cmd_gate,
        "status": cmd_status, "complete": cmd_complete,
    }[args.command]
    return handler(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SupervisorError, WS.WorkflowStateError) as exc:
        print(f"workflow-supervisor: {exc}", file=sys.stderr)
        raise SystemExit(64)
