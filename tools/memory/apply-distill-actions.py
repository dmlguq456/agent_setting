#!/usr/bin/env python3
"""Apply memory distillation JSON-lines actions.

The distiller model only proposes JSON objects. This script owns shape checks,
snapshot membership checks, and argv-only calls into mem.py.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _load_snapshot_ids(path):
    if not path:
        return set()
    try:
        with open(path, encoding="utf-8") as fh:
            return set(fh.read().split())
    except OSError:
        return set()


def _write_receipt(path, receipt):
    if not path:
        return
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_text(json.dumps(receipt, sort_keys=True, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    os.replace(tmp, dest)


def apply_actions(out_path, mem_path, mode="increment", snapshot_ids_path="",
                  focus_ids_path="", receipt_path="", strict=False,
                  validate_only=False):
    # In curate mode this is a destructive allowlist, not every id printed in the
    # snapshot. `curate-snapshot` deliberately omits PROTECTED PENDING handoff/
    # thread ids, so model output cannot prune or merge them through this layer.
    destructive_ids = _load_snapshot_ids(snapshot_ids_path)
    focus_ids = _load_snapshot_ids(focus_ids_path)
    stats = {"schema": 1, "mode": mode, "applied": [], "invalid": 0, "failed": 0,
             "validation_only": bool(validate_only)}

    def member(rid):
        return (mode not in ("curate", "daily")) or (rid in destructive_ids)

    def focus_member(rid):
        return mode != "daily" or rid in focus_ids

    def invalid(message):
        stats["invalid"] += 1
        sys.stderr.write(message + "\n")

    def run_mem(action, argv, target=None):
        if validate_only:
            return True
        result = subprocess.run(["python3", mem_path, *argv], env=mem_env)
        if result.returncode != 0:
            stats["failed"] += 1
            sys.stderr.write(
                f"[distill-apply] {action} failed rc={result.returncode}: {target or ''}\n")
            return False
        entry = {"action": action}
        if target is not None:
            entry["target"] = target
        if len(stats["applied"]) < 100:
            stats["applied"].append(entry)
        return True

    # D-37: mode=curate is the D-18 session-end curator path. Attribute its
    # journal actor deterministically as curator rather than distiller, even
    # when the parent runs with MEM_DISTILL=1.
    mem_env = os.environ.copy()
    if mode in ("curate", "daily"):
        mem_env["MEM_ACTOR"] = "curator"

    try:
        with open(out_path, "r", encoding="utf-8", errors="replace") as fh:
            payload = fh.read(131073)
        lines = payload[:131072].splitlines()
        if len(payload) > 131072:
            invalid("[distill-parse] output exceeds 128 KiB bound")
    except OSError:
        lines = []

    action_lines = 0
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("```"):
            continue
        action_lines += 1
        if action_lines > 100:
            invalid("[distill-parse] action count exceeds 100")
            continue
        try:
            rec = json.loads(line)
        except Exception:
            invalid(f"[distill-parse] skip malformed: {line[:120]!r}")
            continue
        if not isinstance(rec, dict):
            invalid("[distill-parse] skip non-object")
            continue

        action = rec.get("action")
        if action is None and rec.get("tier") and rec.get("type") and isinstance(rec.get("body"), str):
            action = "add"

        # `mem delete` is a user-controlled path and is never a curator action.
        # Keep this explicit so a future mem.py delete surface cannot accidentally
        # become reachable from untrusted distiller output.
        if action == "delete":
            invalid("[distill-parse] skip delete: unsupported destructive action")
            continue

        # increment = add-only, enforced (not merely prompted). The turn-nudge/fast
        # tier reads untrusted transcript delta with no snapshot whitelist, so a
        # prompt-injected model could name id-mutations (prune/merge/graduate/...)
        # that member() would wave through under mode != "curate" (always True).
        # Reject id-mutations outside curate mode so only the snapshot-grounded deep
        # curator can ever delete/merge/graduate. Closes the P-25 whitelist bypass
        # for every adapter at the shared applier (deterministic, §0.5).
        if action in ("reinforce", "prune", "graduate", "reattribute", "merge") \
                and mode not in ("curate", "daily"):
            invalid(f"[distill-parse] skip {action}: id-mutation not allowed in {mode} mode (add-only)")
            continue

        if action == "add":
            if mode == "daily":
                invalid("[distill-parse] skip add: daily curator is cleanup-only")
                continue
            tier = rec.get("tier")
            rtype = rec.get("type")
            body = rec.get("body")
            if tier not in ("working", "durable"):
                invalid(f"[distill-parse] skip bad tier: {tier!r}")
                continue
            if not isinstance(rtype, str) or not rtype:
                invalid("[distill-parse] skip missing/empty type")
                continue
            if not isinstance(body, str) or not body:
                invalid("[distill-parse] skip missing/empty body")
                continue
            if len(body) > 2000:
                invalid(f"[distill-parse] skip body too long ({len(body)})")
                continue
            run_mem("add", ["add", tier, rtype, body])

        elif action in ("reinforce", "prune", "graduate", "reattribute"):
            rid = rec.get("id")
            if not isinstance(rid, str) or not rid:
                invalid(f"[distill-parse] skip {action}: missing id")
                continue
            if not member(rid):
                invalid(f"[distill-parse] skip non-destructive-allowlist id ({action}): {rid!r}")
                continue
            if mode == "daily" and action == "reinforce":
                invalid("[distill-parse] skip reinforce: daily curator is cleanup-only")
                continue
            if mode == "daily" and action == "reattribute":
                invalid("[distill-parse] skip reattribute: daily curator cannot change ownership")
                continue
            if not focus_member(rid):
                invalid(f"[distill-parse] skip non-focus id ({action}): {rid!r}")
                continue
            if action == "graduate":
                run_mem(action, ["graduate", rid, "--to", "durable"], rid)
            else:
                run_mem(action, [action, rid], rid)

        elif action == "merge":
            ids = rec.get("ids")
            canonical = rec.get("canonical")
            if (not isinstance(ids, list) or len(ids) < 2
                    or not all(isinstance(i, str) and i for i in ids)):
                invalid("[distill-parse] skip merge: bad ids")
                continue
            if not isinstance(canonical, str) or canonical not in ids:
                invalid("[distill-parse] skip merge: bad canonical")
                continue
            if not all(member(i) for i in ids):
                invalid("[distill-parse] skip merge: id outside destructive allowlist")
                continue
            if mode == "daily" and not any(i in focus_ids for i in ids):
                invalid("[distill-parse] skip merge: daily merge requires a focus id")
                continue
            run_mem("merge", ["merge", "--canonical", canonical, *ids], ids)

        else:
            invalid(f"[distill-parse] skip unknown action: {action!r}")

    stats["status"] = "ok" if stats["invalid"] == 0 and stats["failed"] == 0 else "failed"
    stats["applied_count"] = len(stats["applied"])
    _write_receipt(receipt_path, stats)
    return 1 if strict and stats["status"] != "ok" else 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("out_path")
    parser.add_argument("mem_path")
    parser.add_argument("--mode", choices=("increment", "curate", "daily"), default="increment")
    parser.add_argument("--snapshot-ids", default="")
    parser.add_argument("--focus-ids", default="")
    parser.add_argument("--receipt", default="")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    return apply_actions(args.out_path, args.mem_path, args.mode, args.snapshot_ids,
                         args.focus_ids, args.receipt, args.strict, args.validate_only)


if __name__ == "__main__":
    raise SystemExit(main())
