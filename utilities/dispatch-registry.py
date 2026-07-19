#!/usr/bin/env python3
"""Current-work filtering and guarded registry reconciliation (SD-60)."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "utilities")]
from tools.fleet.model import ATTEMPT_CLASSIFIER_SOURCE, classify_attempt_evidence  # noqa: E402
from dispatch_contract import (close_attempt_row_if, reconcile_local_registry,
                               resolve_agent_home)  # noqa: E402
_cleanup_spec = importlib.util.spec_from_file_location("worktree_cleanup", ROOT / "utilities/worktree-cleanup.py")
cleanup = importlib.util.module_from_spec(_cleanup_spec)
sys.modules[_cleanup_spec.name] = cleanup
_cleanup_spec.loader.exec_module(cleanup)

OPEN = {"open", "running"}


def parse_meta(pipe):
    return dict(part.split("=", 1) for part in pipe.split(",") if "=" in part)


def read_rows(jobs):
    rows = []
    if not jobs.is_file(): return rows
    for order, line in enumerate(jobs.read_text(encoding="utf-8", errors="replace").splitlines()):
        fields = line.split("\t")
        if len(fields) != 6: continue
        rows.append({"order": order, "timestamp": fields[0], "status": fields[1],
                     "repo": fields[2], "worktree": fields[3], "slug": fields[4],
                     "pipe": fields[5], "meta": parse_meta(fields[5]), "raw": line})
    return rows


def matches(row, args):
    meta = row["meta"]
    checks = ((args.session, meta.get("session_id") or meta.get("parent_sid")),
              (args.route, meta.get("route_id")), (args.node, meta.get("route_node")),
              (args.attempt, meta.get("attempt_id")), (args.job, row["slug"]))
    return all(not expected or expected == actual for expected, actual in checks)


def current(rows):
    newest = {}
    passthrough = []
    for row in rows:
        key = (row["meta"].get("route_id"), row["meta"].get("route_node"))
        if all(key) and row["meta"].get("attempt_id"):
            newest[key] = row
        else: passthrough.append(row)
    return passthrough + sorted(newest.values(), key=lambda row: row["order"])


def attempt_heartbeat(home, meta):
    attempt = (meta.get("attempt_id") or "").replace("/", "_")
    if home is None or not attempt:
        return None
    path = home / ".dispatch" / "heartbeats" / f"{attempt}.json"
    try:
        if path.stat().st_size > 8192:
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError):
        return None


def proc_inputs(row, home=None):
    meta = row["meta"]; raw = meta.get("pid", "")
    pid = int(raw) if raw.isdigit() else None; expected = meta.get("pid_start", "")
    actual = ""; alive = False
    if pid is not None:
        try:
            actual = (Path("/proc") / str(pid) / "stat").read_text().split()[21]; alive = True
        except (OSError, IndexError): pass
    return {"pid": pid, "proc_start": expected, "actual_proc_start": actual,
            "pid_alive": alive, "proc_start_match": bool(alive and expected == actual),
            "pid_scope": meta.get("pid_scope"),
            "attempt_id": meta.get("attempt_id"), "route_id": meta.get("route_id"),
            "route_node": meta.get("route_node"),
            "heartbeat": attempt_heartbeat(home, meta)}


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except (AttributeError, ValueError):
        return None


def terminal_marker(row, home):
    meta = row["meta"]
    route, node = meta.get("route_id"), meta.get("route_node")
    route_hash, gate = meta.get("route_hash"), meta.get("completion_gate")
    if not route or not node or not route_hash or not gate:
        return False, "terminal-row-contract-incomplete"
    marker_path = home / ".dispatch" / "completion" / route / f"{node}.json"
    try: marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, ValueError): return False, "terminal-marker-invalid"
    evidence_record = marker.get("evidence") if isinstance(marker.get("evidence"), dict) else {}
    evidence = Path(str(evidence_record.get("path", "")))
    if (marker.get("route_id") != route or marker.get("route_hash") != route_hash
            or marker.get("node_id") != node or marker.get("completion_gate") != gate
            or not evidence.is_absolute() or not evidence.is_file()):
        return False, "terminal-marker-mismatch"
    try:
        digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    except OSError:
        return False, "terminal-evidence-unreadable"
    if not evidence_record.get("sha256") or digest != evidence_record.get("sha256"):
        return False, "terminal-evidence-changed"
    row_time = timestamp(row["timestamp"])
    marker_time = timestamp(marker.get("completed_at"))
    if row_time is None or marker_time is None:
        return False, "row-clock-ambiguous"
    if marker_time <= row_time or marker_path.stat().st_mtime <= row_time or evidence.stat().st_mtime <= row_time:
        return False, "terminal-marker-not-newer"
    updated = timestamp(meta.get("updated_at"))
    if updated is not None and updated > marker_time:
        return False, "newer-registry-transition"
    attempt = meta.get("attempt_id", "").replace("/", "_")
    heartbeat_path = home / ".dispatch" / "heartbeats" / f"{attempt}.json"
    try:
        heartbeat = json.loads(heartbeat_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        heartbeat = {}
    if float(heartbeat.get("updated_at", 0) or 0) > marker_time:
        return False, "newer-heartbeat"
    watchdog = home / ".dispatch" / "watchdog" / f"{meta.get('attempt_id', '').replace('/', '_')}.json"
    try: watch = json.loads(watchdog.read_text())
    except (OSError, ValueError): watch = {}
    quiet = int(watch.get("quiet_windows", 0) or 0)
    observed = float(watch.get("observed_at", 0) or 0)
    last_progress = float(watch.get("last_progress_at", 0) or 0)
    proved = quiet >= 2 and observed > marker_time and last_progress <= marker_time
    return (proved, "stale-terminal-proved" if proved else "stale-terminal-dwell")


def _marker_backed_repair(row, home):
    """SD-70: was ``complete``'s marker written but its row-close step failed?

    ``complete_node`` (capability-route.py) writes an attempt-linkage sibling
    file next to the completion marker before attempting the row close, so a
    later-dead row can be repaired by exact marker linkage rather than folded
    into the generic dead-exact-pid path.
    """
    meta = row["meta"]
    route_id, node, attempt_id = meta.get("route_id"), meta.get("route_node"), meta.get("attempt_id")
    if not (route_id and node and attempt_id and home): return False
    linkage_path = home / ".dispatch" / "completion" / route_id / f"{node}.attempt.json"
    try: linkage = json.loads(linkage_path.read_text(encoding="utf-8"))
    except (OSError, ValueError): return False
    if (linkage.get("attempt_id") != attempt_id or linkage.get("route_id") != route_id
            or linkage.get("node_id") != node):
        return False
    marker_path = home / ".dispatch" / "completion" / route_id / f"{node}.json"
    return marker_path.is_file()


def route_incomplete(row, home):
    """SD-64/71: route nodes lacking a completion marker for a conductor row's route.

    Fails closed (returns an empty set) when the route record cannot be read
    safely, so an unreadable route never itself justifies an orphan claim.
    """
    meta = row["meta"]
    route_id = meta.get("route_id")
    if not route_id or not home: return set(), "no-route"
    route_file = meta.get("route_file")
    try:
        record = json.loads(Path(route_file).read_text(encoding="utf-8")) if route_file else None
        node_ids = [n["id"] for n in record["nodes"]] if record else None
    except (OSError, ValueError, KeyError, TypeError):
        node_ids = None
    if node_ids is None:
        return set(), "route-record-unreadable"
    completion_dir = home / ".dispatch" / "completion" / route_id
    missing = {node_id for node_id in node_ids if not (completion_dir / f"{node_id}.json").is_file()}
    return missing, "ok"


def has_orphaned_dependents(row, rows, incomplete_nodes, args):
    """SD-64/71: a genuine open/live child, or an un-started successor node."""
    if not incomplete_nodes: return False
    slug = row["slug"]
    for other in rows:
        if other is row or other["status"] not in OPEN: continue
        if other["meta"].get("parent") != slug: continue
        exact = classify_attempt_evidence(proc_inputs(other, args.agent_home), args.now)
        state = exact["state"] if exact else "unknown"
        if state in ("working", "unknown"): return True
    route_id = row["meta"].get("route_id")
    route_file = row["meta"].get("route_file")
    try:
        record = json.loads(Path(route_file).read_text(encoding="utf-8")) if route_file else None
        depends = {n["id"]: n.get("depends_on", []) for n in record["nodes"]} if record else None
    except (OSError, ValueError, KeyError, TypeError):
        return False
    if depends is None: return False
    attempted_nodes = {r["meta"].get("route_node") for r in rows if r["meta"].get("route_id") == route_id}
    for node_id in incomplete_nodes:
        if node_id in attempted_nodes: continue
        predecessors = depends.get(node_id, [])
        if all(predecessor not in incomplete_nodes for predecessor in predecessors): return True
    return False


def resume_boundary(route_file, incomplete_nodes):
    """SD-64/71: the first incomplete node in route order, or None if unreadable."""
    if not route_file or not incomplete_nodes: return None
    try:
        record = json.loads(Path(route_file).read_text(encoding="utf-8"))
        for node in record.get("nodes", []):
            if node.get("id") in incomplete_nodes: return node["id"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return None


def classify(row, args, newest_orders, rows=None):
    if row["status"] not in OPEN: return "terminal", "already-terminal", None
    exact = classify_attempt_evidence(proc_inputs(row, args.agent_home), args.now)
    if exact and exact["state"] == "working": return "active", exact["rule"], None
    if exact and exact["state"] == "done": return "terminal-heartbeat", exact["rule"], "completed-terminal-heartbeat"
    if exact and exact["state"] == "dead":
        if _marker_backed_repair(row, args.agent_home):
            return "marker-backed-stale", "completed-marker-linkage", "completed-marker"
        meta = row["meta"]
        if (rows is not None and meta.get("worker_type") == "owner"
                and meta.get("route_id") and not meta.get("route_node")):
            incomplete, record_status = route_incomplete(row, args.agent_home)
            if record_status == "ok" and incomplete and has_orphaned_dependents(row, rows, incomplete, args):
                return "orphan", "dead-parent-orphaned", "dead-parent-orphaned"
        return "exact-dead", exact["rule"], "dead-exact-pid"
    meta = row["meta"]
    key = (meta.get("route_id"), meta.get("route_node"))
    if all(key) and newest_orders.get(key) == row["order"]:
        proven, reason = terminal_marker(row, args.agent_home)
        if proven: return "stale-terminal", reason, "dead-stale-terminal"
    worktree = Path(row["worktree"])
    if worktree.is_absolute() and worktree.is_dir():
        try: verdict = cleanup.evaluate(worktree.resolve(), args.jobs, args.integration_ref)
        except (OSError, RuntimeError): verdict = None
        if verdict and verdict.eligible: return "merged", "sd29-safety-approved", "cleanup-merged"
        if verdict and verdict.reasons: return "unsafe", ",".join(verdict.reasons), None
    return "unsafe", "legacy-weak-or-unverifiable", None


def emit_current(rows, args):
    selected = [row for row in rows if matches(row, args)]
    if not args.all: selected = current(selected)
    payload = {"classifier_source": ATTEMPT_CLASSIFIER_SOURCE,
               "filters": {"session": args.session, "route": args.route, "node": args.node,
                           "attempt": args.attempt, "job": args.job},
               "total": len(selected), "rows": selected}
    print(json.dumps(payload, sort_keys=True)); return 0


def emit_liveness(rows, args):
    """Emit a TSV view with superseded route/node attempts folded by default."""
    selected = [row for row in rows if matches(row, args)]
    if not args.all:
        selected = current(selected)
    for row in selected:
        print(row["raw"])
    return 0


def reconcile(rows, args):
    selected = [row for row in rows if matches(row, args)]
    newest = {}
    for row in rows:
        key = (row["meta"].get("route_id"), row["meta"].get("route_node"))
        if all(key): newest[key] = row["order"]
    decisions = []
    for row in selected:
        category, reason, note = classify(row, args, newest, rows)
        closed = False
        revalidated = None
        if args.apply and note and row["meta"].get("attempt_id"):
            fresh_decision = {}

            def still_safe(_fields):
                fresh_rows = read_rows(args.jobs)
                fresh = next((item for item in fresh_rows
                              if item["meta"].get("attempt_id") == row["meta"]["attempt_id"]), None)
                if fresh is None:
                    fresh_decision.update(category="missing", reason="attempt-row-missing")
                    return False
                latest = {}
                for item in fresh_rows:
                    key = (item["meta"].get("route_id"), item["meta"].get("route_node"))
                    if all(key): latest[key] = item["order"]
                fresh_category, fresh_reason, fresh_note = classify(fresh, args, latest, fresh_rows)
                fresh_decision.update(category=fresh_category, reason=fresh_reason, note=fresh_note)
                return fresh_note == note and fresh_category == category

            closed = close_attempt_row_if(
                args.jobs, row["meta"]["attempt_id"], note, still_safe,
                evidence={"classifier_source": ATTEMPT_CLASSIFIER_SOURCE,
                          "reconcile_reason": reason},
            )
            revalidated = bool(closed)
            if not closed and fresh_decision:
                reason = f"revalidation-veto:{fresh_decision.get('category')}:{fresh_decision.get('reason')}"
        decisions.append({"attempt_id": row["meta"].get("attempt_id"), "slug": row["slug"],
                          "category": category, "reason": reason, "proposed_note": note,
                          "revalidated": revalidated, "closed": closed})
    record = {"at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
              "apply": args.apply, "classifier_source": ATTEMPT_CLASSIFIER_SOURCE,
              "attempted": len(selected), "closed": sum(item["closed"] for item in decisions),
              "decisions": decisions[:256]}
    if args.audit:
        cleanup.append_audit(args.audit, record)
    print(json.dumps(record, sort_keys=True)); return 0


def emit_orphan_status(rows, args):
    """SD-64/71: single-attempt orphan verdict for liveness/preflight/Fleet surfaces.

    Reuses the same exact-attempt classifier and route_incomplete/
    has_orphaned_dependents primitives as ``reconcile`` (read-only; never
    closes a row) so surfaces never re-derive the classification themselves.
    """
    if not args.attempt:
        print("check=failed\nreason=attempt-required"); return 64
    row = next((r for r in rows if r["meta"].get("attempt_id") == args.attempt), None)
    if row is None:
        print("check=ok\norphan=0\nreason=attempt-not-found"); return 0
    newest = {}
    for item in rows:
        key = (item["meta"].get("route_id"), item["meta"].get("route_node"))
        if all(key): newest[key] = item["order"]
    category, reason, note = classify(row, args, newest, rows)
    if note == "dead-parent-orphaned":
        incomplete, _ = route_incomplete(row, args.agent_home)
        boundary = resume_boundary(row["meta"].get("route_file"), incomplete)
        print("check=ok\norphan=1")
        print(f"route_id={row['meta'].get('route_id')}")
        print(f"resume_boundary={boundary or '-'}")
    else:
        print("check=ok\norphan=0")
    return 0


def emit_orphan_scan(rows, args):
    """SD-64/71: fail-open registry-wide orphan count for preflight status.

    No filter is required (unlike ``reconcile``) since a status probe does
    not know a specific route ahead of time; it only ever reads.
    """
    newest = {}
    for item in rows:
        key = (item["meta"].get("route_id"), item["meta"].get("route_node"))
        if all(key): newest[key] = item["order"]
    orphans = []
    for row in rows:
        if row["status"] not in OPEN: continue
        meta = row["meta"]
        if meta.get("worker_type") != "owner" or not meta.get("route_id") or meta.get("route_node"):
            continue
        _, _, note = classify(row, args, newest, rows)
        if note == "dead-parent-orphaned":
            incomplete, _ = route_incomplete(row, args.agent_home)
            boundary = resume_boundary(meta.get("route_file"), incomplete)
            orphans.append({"attempt_id": meta.get("attempt_id"), "route_id": meta.get("route_id"),
                            "slug": row["slug"], "resume_boundary": boundary or "-"})
    print(f"check=ok\norphaned_conductor_jobs={len(orphans)}")
    if orphans:
        print(f"orphaned_resume_boundary={orphans[0]['resume_boundary']}")
        print(json.dumps(orphans, sort_keys=True))
    return 0


def main(argv):
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("operation", choices=("current", "liveness", "reconcile", "attempt-state", "orphan-status", "orphan-scan"))
    p.add_argument("--jobs", type=Path); p.add_argument("--global-jobs", type=Path); p.add_argument("--local-jobs", type=Path)
    p.add_argument("--session"); p.add_argument("--route")
    p.add_argument("--node"); p.add_argument("--attempt"); p.add_argument("--job"); p.add_argument("--all", action="store_true")
    p.add_argument("--apply", action="store_true"); p.add_argument("--audit", type=Path); p.add_argument("--integration-ref")
    p.add_argument("--agent-home", type=Path); p.add_argument("--now", type=float, default=time.time(), help=argparse.SUPPRESS)
    p.add_argument("--pid", type=int); p.add_argument("--pid-start"); p.add_argument("--pid-scope")
    args = p.parse_args(argv[1:]); args.agent_home = (args.agent_home or resolve_agent_home()).resolve()
    if args.operation == "attempt-state":
        if args.pid is None or not args.pid_start:
            print("check=failed\nreason=exact-identity-required"); return 64
        row = {"meta": {"pid": str(args.pid), "pid_start": args.pid_start,
                        "pid_scope": args.pid_scope, "attempt_id": args.attempt,
                        "route_id": args.route, "route_node": args.node}}
        verdict = classify_attempt_evidence(proc_inputs(row, args.agent_home), args.now)
        if verdict is None:
            print("check=failed\nreason=exact-identity-required"); return 65
        print("check=ok")
        print(f"state={verdict['state']}")
        print(f"source={verdict['source']}")
        print(f"rule={verdict['rule']}")
        print(f"classifier_source={verdict['classifier_source']}")
        print(f"pid={verdict['pid']}")
        print(f"proc_start={verdict['proc_start']}")
        print(f"actual_proc_start={verdict['actual_proc_start']}")
        return 0
    if args.global_jobs or args.local_jobs:
        if args.operation != "reconcile" or not args.global_jobs or not args.local_jobs:
            print("check=failed\nreason=legacy-reconcile-arguments-invalid"); return 64
        count, malformed = reconcile_local_registry(args.global_jobs.resolve(), args.local_jobs.resolve())
        print(f"check=ok\nglobal_registry={args.global_jobs.resolve()}\nlocal_registry={args.local_jobs.resolve()}\nreconciled={count}\nmalformed={malformed}")
        return 0
    if not args.jobs:
        print("check=failed\nreason=jobs-required"); return 64
    args.jobs = args.jobs.resolve()
    if args.operation not in ("liveness", "orphan-scan") and not any((args.session, args.route, args.node, args.attempt, args.job)):
        print("check=failed\nreason=current-filter-required"); return 64
    rows = read_rows(args.jobs)
    if args.operation == "current":
        return emit_current(rows, args)
    if args.operation == "liveness":
        return emit_liveness(rows, args)
    if args.operation == "orphan-status":
        return emit_orphan_status(rows, args)
    if args.operation == "orphan-scan":
        return emit_orphan_scan(rows, args)
    return reconcile(rows, args)


if __name__ == "__main__": raise SystemExit(main(sys.argv))
